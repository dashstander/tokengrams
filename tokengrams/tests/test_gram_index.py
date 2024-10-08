from itertools import pairwise
from tempfile import NamedTemporaryFile

from tokengrams import InMemoryIndex, MemmapIndex
from hypothesis import given, strategies as st

import numpy as np


def check_gram_index(index: InMemoryIndex | MemmapIndex, tokens: list[int]):
    assert index.is_sorted()

    # Check unigram counts
    for t in tokens:
        assert index.contains([t]) == (t in tokens)
        assert index.count([t]) == tokens.count(t)

    # Check bigram counts
    bigrams = list(pairwise(tokens))
    for b in bigrams:
        assert index.contains(list(b)) == (b in bigrams)
        assert index.count(list(b)) == bigrams.count(b)

@given(
    st.lists(
        st.integers(0, 2 ** 16 - 1), min_size=1,
    )
)
def test_gram_index(tokens: list[int]):
    index = InMemoryIndex(tokens)
    check_gram_index(index, tokens)

    # Save to disk and check that we can load it back
    with NamedTemporaryFile() as f:
        index.save_tokens(f.name)

        index = InMemoryIndex.from_token_file(f.name)
        
        check_gram_index(index, tokens)

        with NamedTemporaryFile() as idx:
            index = MemmapIndex.build(f.name, idx.name)
            check_gram_index(index, tokens)

            index = MemmapIndex(f.name, idx.name)
            check_gram_index(index, tokens)

        # Now check limited token loading
        for limit in range(1, len(tokens) + 1):
            index = InMemoryIndex.from_token_file(f.name, limit)
            check_gram_index(index, tokens[:limit])
