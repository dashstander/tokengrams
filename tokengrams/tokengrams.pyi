class InMemoryIndex:
    """An n-gram index."""

    def __init__(self, tokens: list[int], vocab: int = 2**16, verbose: bool = False) -> None:
        ...
    
    @staticmethod
    def from_token_file(path: str, token_limit: int | None = None, vocab: int = 2**16, verbose: bool = False) -> "InMemoryIndex":
        """Construct a `InMemoryIndex` from a file containing raw little-endian tokens."""

    def from_disk(self, token_path: str, index_path: str, vocab: int = 2**16) -> "InMemoryIndex":
        """Load a pretrained index from disk."""

    def save_tokens(self, path: str):
        """Save the tokens to a file."""

    def save_index(self, path: str):
        """Save the index to disk."""

    def is_sorted(self) -> bool:
        """Check if the index's suffix table is sorted lexicographically. 
        This is always true for valid indices."""

    def contains(self, query: list[int]) -> bool:
        """Check if `query` has nonzero count. Faster than `count(query) > 0`."""
    
    def count(self, query: list[int]) -> int:
        """Count the number of occurrences of `query` in the index."""

    def positions(self, query: list[int]) -> list[int]:
        """Returns an unordered list of positions where `query` starts in `tokens`."""

    def count_next(self, query: list[int]) -> list[int]:
        """Count the occurrences of each token directly following `query`."""

    def batch_count_next(self, queries: list[list[int]]) -> list[list[int]]:
        """Count the occurrences of each token that directly follows each sequence in `queries`."""

    def get_smoothed_probs(self, query: list[int]) -> list[float]:
        """Compute interpolated Kneser-Ney smoothed token probability distribution using all previous tokens in the query."""

    def batch_get_smoothed_probs(self, queries: list[list[int]]) -> list[list[float]]:
        """Compute interpolated Kneser-Ney smoothed token probability distributions using all previous tokens in each query."""

    def sample_smoothed(self, query: list[int], n: int, k: int, num_samples: int) -> list[list[int]]:
        """Autoregressively samples num_samples of k characters each from Kneser-Ney smoothed conditional 
        distributions based on the previous (n - 1) characters (n-gram prefix) in the sequence. If there are 
        fewer than (n - 1) characters all available characters are used."""
   
    def sample_unsmoothed(self, query: list[int], n: int, k: int, num_samples: int) -> list[list[int]]:
        """Autoregressively samples num_samples of k characters each from conditional distributions based 
        on the previous (n - 1) characters (n-gram prefix) in the sequence. If there are fewer than 
        (n - 1) characters all available characters are used."""

    def estimate_deltas(self, n: int):
        """Warning: O(k**n) where k is vocabulary size, use with caution.
        Improve smoothed model quality by replacing the default delta hyperparameters
        for models of order n and below with improved estimates over the entire index.
        https://people.eecs.berkeley.edu/~klein/cs294-5/chen_goodman.pdf, page 16."""

class MemmapIndex:
    """An n-gram index backed by a memory-mapped file."""

    def __init__(self, token_path: str, index_path: str, vocab: int = 2**16) -> None:
        """Load a prebuilt memory-mapped index from a pair of files."""

    @staticmethod
    def build(token_path: str, index_path: str, vocab: int = 2**16, verbose: bool = False) -> "MemmapIndex":
        """Build a memory-mapped index from a token file."""

    def is_sorted(self) -> bool:
        """Check if the index's suffix table is sorted lexicographically. 
        This is always true for valid indices."""
    
    def contains(self, query: list[int]) -> bool:
        """Check if `query` has nonzero count. Faster than `count(query) > 0`."""
    
    def count(self, query: list[int]) -> int:
        """Count the number of occurrences of `query` in the index."""

    def positions(self, query: list[int]) -> list[int]:
        """Returns an unordered list of positions where `query` starts in `tokens`."""

    def count_next(self, query: list[int]) -> list[int]:
        """Count the occurrences of each token directly following `query`."""

    def batch_count_next(self, queries: list[list[int]]) -> list[list[int]]:
        """Count the occurrences of each token that directly follows each sequence in `queries`."""

    def sample_smoothed(self, query: list[int], n: int, k: int, num_samples: int) -> list[list[int]]:
        """Autoregressively samples num_samples of k characters each from Kneser-Ney smoothed conditional 
        distributions based on the previous (n - 1) characters (n-gram prefix) in the sequence. If there are 
        fewer than (n - 1) characters all available characters are used."""
   
    def sample_unsmoothed(self, query: list[int], n: int, k: int, num_samples: int) -> list[list[int]]:
        """Autoregressively samples num_samples of k characters each from conditional distributions based 
        on the previous (n - 1) characters (n-gram prefix) in the sequence. If there are fewer than 
        (n - 1) characters all available characters are used."""

    def get_smoothed_probs(self, query: list[int]) -> list[float]:
        """Compute interpolated Kneser-Ney smoothed token probability distribution using all previous tokens in the query."""

    def batch_get_smoothed_probs(self, queries: list[list[int]]) -> list[list[float]]:
        """Compute interpolated Kneser-Ney smoothed token probability distributions using all previous tokens in each query."""
    
    def estimate_deltas(self, n: int):
        """Warning: O(k**n) where k is vocabulary size, use with caution.
        Improve smoothed model quality by replacing the default delta hyperparameters
        for models of order n and below with improved estimates over the entire index.
        https://people.eecs.berkeley.edu/~klein/cs294-5/chen_goodman.pdf, page 16."""

class ShardedMemmapIndex:
    """An n-gram index backed by several memory-mapped files."""

    def __init__(self, paths: list[tuple[str, str]], vocab: int = 2**16) -> None:
        """Load a prebuilt memory-mapped index from a list of pairs of files in form (token_file, index_file)."""

    @staticmethod
    def build(paths: list[tuple[str, str]], vocab: int = 2**16, verbose: bool = False) -> "ShardedMemmapIndex":
        """Build a memory-mapped index from a token file."""

    def is_sorted(self) -> bool:
        """Check if the index's suffix table is sorted lexicographically. 
        This is always true for valid indices."""
    
    def contains(self, query: list[int]) -> bool:
        """Check if `query` has nonzero count. Faster than `count(query) > 0`."""
    
    def count(self, query: list[int]) -> int:
        """Count the number of occurrences of `query` in the index."""

    def count_next(self, query: list[int]) -> list[int]:
        """Count the occurrences of each token directly following `query`."""

    def batch_count_next(self, queries: list[list[int]]) -> list[list[int]]:
        """Count the occurrences of each token that directly follows each sequence in `queries`."""

    def sample_smoothed(self, query: list[int], n: int, k: int, num_samples: int) -> list[list[int]]:
        """Autoregressively samples num_samples of k characters each from Kneser-Ney smoothed conditional 
        distributions based on the previous (n - 1) characters (n-gram prefix) in the sequence. If there are 
        fewer than (n - 1) characters all available characters are used."""
   
    def sample_unsmoothed(self, query: list[int], n: int, k: int, num_samples: int) -> list[list[int]]:
        """Autoregressively samples num_samples of k characters each from conditional distributions based 
        on the previous (n - 1) characters (n-gram prefix) in the sequence. If there are fewer than 
        (n - 1) characters all available characters are used."""

    def get_smoothed_probs(self, query: list[int]) -> list[float]:
        """Compute interpolated Kneser-Ney smoothed token probability distribution using all previous tokens in the query."""

    def batch_get_smoothed_probs(self, queries: list[list[int]]) -> list[list[float]]:
        """Compute interpolated Kneser-Ney smoothed token probability distributions using all previous tokens in each query."""
    
    def estimate_deltas(self, n: int):
        """Warning: O(k**n) where k is vocabulary size, use with caution.
        Improve smoothed model quality by replacing the default delta hyperparameters
        for models of order n and below with improved estimates over the entire index.
        https://people.eecs.berkeley.edu/~klein/cs294-5/chen_goodman.pdf, page 16."""
