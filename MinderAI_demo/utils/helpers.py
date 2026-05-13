"""Helper utility functions"""

from typing import List


def estimate_tokens(text: str, tokens_per_word: float = 0.25) -> int:
    """Estimate token count: ~4 words per token (0.25 tokens per word)"""
    word_count = len(text.split())
    return int(word_count * (1 / tokens_per_word))


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    dot_product = sum(x * y for x, y in zip(vec_a, vec_b))
    norm_a = sum(x * x for x in vec_a) ** 0.5
    norm_b = sum(y * y for y in vec_b) ** 0.5
    return dot_product / (norm_a * norm_b) if norm_a and norm_b else 0.0
