from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)

# Cache for tiktoken encoders
_encoder_cache: dict[str, Any] = {}


def _get_encoder(model: str = "gpt-4o-mini"):
    """Get tiktoken encoder for a model, with caching."""
    if model in _encoder_cache:
        return _encoder_cache[model]

    try:
        import tiktoken

        # Map model names to encoding
        if "gpt-4" in model or "gpt-3.5" in model:
            encoder = tiktoken.encoding_for_model(model)
        else:
            encoder = tiktoken.get_encoding("cl100k_base")

        _encoder_cache[model] = encoder
        return encoder
    except ImportError:
        logger.warning("tiktoken not installed, falling back to word-based counting")
        return None
    except Exception as e:
        logger.warning("Failed to get encoder for model %s: %s", model, e)
        return None


def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """Count tokens in text using tiktoken.

    Args:
        text: The text to count tokens for
        model: The model to use for counting

    Returns:
        Number of tokens
    """
    if not text:
        return 0

    encoder = _get_encoder(model)
    if encoder is None:
        # Fallback to word-based counting (rough estimate)
        return len(text.split())

    try:
        return len(encoder.encode(text))
    except Exception as e:
        logger.warning("Token counting failed: %s", e)
        return len(text.split())


def count_messages_tokens(messages: list[dict[str, Any]], model: str = "gpt-4o-mini") -> int:
    """Count tokens in a list of messages.

    Args:
        messages: List of message dicts with 'role' and 'content'
        model: The model to use for counting

    Returns:
        Total number of tokens
    """
    if not messages:
        return 0

    encoder = _get_encoder(model)
    if encoder is None:
        # Fallback to word-based counting
        total = 0
        for msg in messages:
            total += len(msg.get("content", "").split())
        return total

    try:
        # Approximate token count per message for overhead
        tokens_per_message = 3  # Every reply is primed with <|start|>assistant<|message|>
        tokens_per_name = 1     # If there's a name, the role is omitted

        total = 0
        for msg in messages:
            total += tokens_per_message
            for key, value in msg.items():
                if isinstance(value, str):
                    total += len(encoder.encode(value))
                if key == "name":
                    total += tokens_per_name

        total += 3  # Every reply is primed with <|start|>assistant<|message|>
        return total
    except Exception as e:
        logger.warning("Message token counting failed: %s", e)
        # Fallback
        total = 0
        for msg in messages:
            total += len(msg.get("content", "").split())
        return total


def truncate_to_tokens(text: str, max_tokens: int, model: str = "gpt-4o-mini") -> str:
    """Truncate text to a maximum number of tokens.

    Args:
        text: The text to truncate
        max_tokens: Maximum number of tokens
        model: The model to use for counting

    Returns:
        Truncated text
    """
    if not text:
        return ""

    encoder = _get_encoder(model)
    if encoder is None:
        # Fallback to word-based truncation
        words = text.split()
        return " ".join(words[:max_tokens])

    try:
        tokens = encoder.encode(text)
        if len(tokens) <= max_tokens:
            return text
        truncated_tokens = tokens[:max_tokens]
        return encoder.decode(truncated_tokens)
    except Exception as e:
        logger.warning("Token truncation failed: %s", e)
        words = text.split()
        return " ".join(words[:max_tokens])
