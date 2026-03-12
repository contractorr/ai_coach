"""Tests for shared RRF ranking utility and token counter."""

from services.ranking import rrf_fuse
from services.tokens import count_tokens


class TestRRFFuse:
    def test_single_list(self):
        items = [{"url": "a"}, {"url": "b"}]
        result = rrf_fuse([items], [1.0], key_fn=lambda x: x["url"])
        assert [r["url"] for r in result] == ["a", "b"]

    def test_two_lists_overlap_boosts(self):
        """Items appearing in both lists should rank higher."""
        list_a = [{"url": "x"}, {"url": "y"}]
        list_b = [{"url": "y"}, {"url": "z"}]
        result = rrf_fuse([list_a, list_b], [0.5, 0.5], key_fn=lambda x: x["url"])
        # y appears in both → highest score
        assert result[0]["url"] == "y"

    def test_disjoint_lists(self):
        list_a = [{"url": "a"}]
        list_b = [{"url": "b"}]
        result = rrf_fuse([list_a, list_b], [0.7, 0.3], key_fn=lambda x: x["url"])
        # a has higher weight so ranks first
        assert result[0]["url"] == "a"
        assert len(result) == 2

    def test_weights_affect_order(self):
        list_a = [{"url": "a"}]
        list_b = [{"url": "b"}]
        # Give b's list higher weight
        result = rrf_fuse([list_a, list_b], [0.2, 0.8], key_fn=lambda x: x["url"])
        assert result[0]["url"] == "b"

    def test_empty_lists(self):
        result = rrf_fuse([[], []], [0.5, 0.5], key_fn=lambda x: x["url"])
        assert result == []

    def test_one_empty_list(self):
        items = [{"url": "a"}]
        result = rrf_fuse([items, []], [0.7, 0.3], key_fn=lambda x: x["url"])
        assert len(result) == 1
        assert result[0]["url"] == "a"

    def test_custom_k(self):
        """Different k values change score distribution but not relative order for single-list."""
        items = [{"url": "a"}, {"url": "b"}]
        r1 = rrf_fuse([items], [1.0], key_fn=lambda x: x["url"], k=1)
        r2 = rrf_fuse([items], [1.0], key_fn=lambda x: x["url"], k=100)
        # Order preserved regardless of k
        assert [r["url"] for r in r1] == ["a", "b"]
        assert [r["url"] for r in r2] == ["a", "b"]

    def test_keeps_first_item_dict_on_duplicate_key(self):
        """When same key appears in multiple lists, the first occurrence's dict is kept."""
        list_a = [{"url": "x", "source": "semantic"}]
        list_b = [{"url": "x", "source": "keyword"}]
        result = rrf_fuse([list_a, list_b], [0.5, 0.5], key_fn=lambda x: x["url"])
        assert len(result) == 1
        assert result[0]["source"] == "semantic"

    def test_empty_key_gets_unique_id(self):
        """Items with empty key_fn result get unique keys (no collisions)."""
        list_a = [{"title": "no-url-1"}, {"title": "no-url-2"}]
        result = rrf_fuse([list_a], [1.0], key_fn=lambda x: x.get("url", ""))
        assert len(result) == 2

    def test_three_lists(self):
        a = [{"url": "1"}, {"url": "2"}]
        b = [{"url": "2"}, {"url": "3"}]
        c = [{"url": "3"}, {"url": "1"}]
        result = rrf_fuse([a, b, c], [0.33, 0.33, 0.34], key_fn=lambda x: x["url"])
        # All items in 2 lists; scores should be close but 2 and 3 appear at rank 0 in some list
        assert len(result) == 3


class TestCountTokens:
    def test_returns_int(self):
        assert isinstance(count_tokens("Hello world"), int)

    def test_empty_string(self):
        assert count_tokens("") == 0

    def test_longer_text_more_tokens(self):
        short = count_tokens("hi")
        long = count_tokens("This is a significantly longer piece of text with many words")
        assert long > short

    def test_reasonable_token_ratio(self):
        text = "The quick brown fox jumps over the lazy dog"
        tokens = count_tokens(text)
        # Should be roughly 1 token per word, give or take
        assert 5 <= tokens <= 20
