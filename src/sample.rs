use anyhow::Result;
use funty::Unsigned;
use rand::distributions::{Distribution, WeightedIndex};
use rand::thread_rng;
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::ops::Mul;

#[derive(Clone, Deserialize, Serialize, Default)]
pub struct KneserNeyCache {
    unigram_probs: Option<Vec<f64>>,
    n_delta: HashMap<usize, f64>,
}

pub trait Sample<T: Unsigned>: Send + Sync {
    fn count_next_slice(&self, query: &[T]) -> Vec<usize>;

    /// Generate a frequency map from occurrence frequency to the number of
    /// unique n-grams in the corpus with that frequency.
    fn count_ngrams(&self, n: usize) -> HashMap<usize, usize>;

    fn get_cache(&self) -> &KneserNeyCache;

    fn get_mut_cache(&mut self) -> &mut KneserNeyCache;

    /// Autoregressively sample num_samples of k characters from an unsmoothed n-gram model."""
    fn sample_unsmoothed(
        &self,
        query: &[T],
        n: usize,
        k: usize,
        num_samples: usize,
    ) -> Result<Vec<Vec<T>>> {
        (0..num_samples)
            .into_par_iter()
            .map(|_| self.sample(query, n, k))
            .collect()
    }

    //// Autoregressively sample a sequence of k characters from an unsmoothed n-gram model."""
    fn sample(&self, query: &[T], n: usize, k: usize) -> Result<Vec<T>> {
        let mut rng = thread_rng();
        let mut sequence = Vec::from(query);

        for _ in 0..k {
            // look at the previous (n - 1) characters to predict the n-gram completion
            let start = sequence.len().saturating_sub(n - 1);
            let prev = &sequence[start..];

            let counts = self.count_next_slice(prev);
            let dist = WeightedIndex::new(&counts)?;
            let sampled_index: T = dist
                .sample(&mut rng)
                .try_into()
                .unwrap_or_else(|_| panic!("Sampled token > T::MAX"));

            sequence.push(sampled_index);
        }

        Ok(sequence)
    }

    /// Returns interpolated Kneser-Ney smoothed token probability distribution using all previous
    /// tokens in the query.
    fn get_smoothed_probs(&mut self, query: &[T]) -> Vec<f64> {
        self.estimate_deltas(1);
        self.compute_smoothed_unigram_probs();
        self.smoothed_probs(query)
    }

    /// Returns interpolated Kneser-Ney smoothed token probability distribution using all previous
    /// tokens in the query.
    fn batch_get_smoothed_probs(&mut self, queries: &[Vec<T>]) -> Vec<Vec<f64>> {
        self.estimate_deltas(1);
        self.compute_smoothed_unigram_probs();

        queries
            .into_par_iter()
            .map(|query| self.smoothed_probs(query))
            .collect()
    }

    /// Autoregressively sample num_samples of k characters from a Kneser-Ney smoothed n-gram model.
    fn sample_smoothed(
        &mut self,
        query: &[T],
        n: usize,
        k: usize,
        num_samples: usize,
    ) -> Result<Vec<Vec<T>>> {
        self.estimate_deltas(1);
        self.compute_smoothed_unigram_probs();

        (0..num_samples)
            .into_par_iter()
            .map(|_| self.kn_sample(query, n, k))
            .collect()
    }

    /// Returns the Kneser-Ney smoothed token probability distribution for a query
    /// continuation using absolute discounting as described in
    /// "On structuring probabilistic dependences in stochastic language modelling", page 25,
    /// doi:10.1006/csla.1994.1001
    fn smoothed_probs(&self, query: &[T]) -> Vec<f64> {
        let p_continuations = if query.is_empty() {
            self.get_cached_smoothed_unigram_probs().to_vec()
        } else {
            self.smoothed_probs(&query[1..])
        };

        let counts = self.count_next_slice(&query);
        let suffix_count_recip = {
            let suffix_count: usize = counts.iter().sum();
            if suffix_count == 0 {
                return p_continuations;
            }
            1.0 / suffix_count as f64
        };

        let (gt_zero_count, eq_one_count) = get_occurrence_counts(&counts);
        let used_suffix_count = gt_zero_count as f64;
        let used_once_suffix_count = eq_one_count as f64;

        // Interpolation budget to be distributed according to lower order n-gram distribution
        let delta = self.get_cached_delta(query.len() + 1);
        let lambda = if delta < 1.0 {
            delta.mul(used_suffix_count).mul(suffix_count_recip)
        } else {
            used_once_suffix_count
                + delta
                    .mul(used_suffix_count - used_once_suffix_count)
                    .mul(suffix_count_recip)
        };

        let mut probs = Vec::with_capacity(counts.len());
        counts
            .iter()
            .zip(p_continuations.iter())
            .for_each(|(&count, &p_continuation)| {
                let prob = (count as f64 - delta).max(0.0).mul(suffix_count_recip)
                    + lambda.mul(p_continuation);
                probs.push(prob);
            });
        probs
    }

    /// Autoregressively sample k characters from a Kneser-Ney smoothed n-gram model.
    fn kn_sample(&self, query: &[T], n: usize, k: usize) -> Result<Vec<T>> {
        let mut rng = thread_rng();
        let mut sequence = Vec::from(query);

        for _ in 0..k {
            let start = sequence.len().saturating_sub(n - 1);
            let prev = &sequence[start..];
            let probs = self.smoothed_probs(prev);
            let dist = WeightedIndex::new(&probs)?;
            let sampled_index: T = dist
                .sample(&mut rng)
                .try_into()
                .unwrap_or_else(|_| panic!("Sampled token > usize::MAX"));

            sequence.push(sampled_index);
        }

        Ok(sequence)
    }

    /// Warning: O(k**n) where k is vocabulary size, use with caution.
    /// Improve smoothed model quality by replacing the default delta hyperparameters
    /// for models of order n and below with improved estimates over the entire index.
    /// https://people.eecs.berkeley.edu/~klein/cs294-5/chen_goodman.pdf, page 16."""
    fn estimate_deltas(&mut self, n: usize) {
        for i in 1..n + 1 {
            if self.get_cache().n_delta.contains_key(&i) {
                continue;
            }

            let count_map = self.count_ngrams(i);
            let n1 = *count_map.get(&1).unwrap_or(&0) as f64;
            let n2 = *count_map.get(&2).unwrap_or(&0) as f64;

            // n1 and n2 are greater than 0 for non-trivial datasets
            let delta = if n1 == 0. || n2 == 0. {
                1.
            } else {
                n1 / (n1 + n2.mul(2.))
            };

            self.get_mut_cache().n_delta.insert(i, delta);
        }
    }

    fn get_cached_delta(&self, n: usize) -> f64 {
        *self.get_cache().n_delta.get(&n).unwrap_or(&0.5)
    }

    /// Returns unigram probabilities with additive smoothing applied.
    fn compute_smoothed_unigram_probs(&mut self) {
        if let Some(_) = &self.get_cache().unigram_probs {
            return;
        }

        let eps = 1e-9;

        // Count the number of unique bigrams that end with each token
        let counts = self.count_next_slice(&[]);

        let total_count: usize = counts.iter().sum();
        let adjusted_total_count = total_count as f64 + eps.mul(counts.len() as f64);
        let unigram_probs: Vec<f64> = counts
            .iter()
            .map(|&count| (count as f64 + eps) / adjusted_total_count)
            .collect();

        self.get_mut_cache().unigram_probs = Some(unigram_probs);
    }

    fn get_cached_smoothed_unigram_probs(&self) -> &[f64] {
        self.get_cache().unigram_probs.as_ref().unwrap()
    }
}

fn get_occurrence_counts(slice: &[usize]) -> (usize, usize) {
    slice
        .iter()
        .fold((0, 0), |(gt_zero_count, eq_one_count), &c| {
            let gt_zero_count = gt_zero_count + (c > 0) as usize;
            let eq_one_count = eq_one_count + (c == 1) as usize;
            (gt_zero_count, eq_one_count)
        })
}
