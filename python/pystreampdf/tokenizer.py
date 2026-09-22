"""Token counting utilities.

Historically every token-count "estimate" across this codebase used a fixed
`len(text) / 4` heuristic. That's a reasonable ballpark for English prose but
can be off by a large margin for code, non-English text, or anything with
unusual punctuation density — and callers had no way to tell whether a given
number was a real count or a guess.

This module centralizes token counting:
- If `tiktoken` is installed (``pip install pystreampdf[tiktoken]`` or
  ``pip install tiktoken``), counts are exact BPE token counts using the
  `cl100k_base` encoding (used by GPT-3.5/GPT-4-class models).
- Otherwise, it falls back to the same `len(text) // 4` heuristic as before,
  clearly labeled as approximate via `is_exact()` / `TOKENIZER_MODE`.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import tiktoken as _tiktoken

    try:
        _ENCODING = _tiktoken.get_encoding("cl100k_base")
    except Exception:
        _ENCODING = None
except ImportError:
    _tiktoken = None
    _ENCODING = None


#: Human-readable description of which counting mode is active. Surface this
#: in any report/output that includes token counts so consumers know whether
#: the numbers are exact or approximate.
TOKENIZER_MODE = (
    "tiktoken (cl100k_base, exact)" if _ENCODING is not None else "heuristic (len/4, approximate)"
)

# Chars-per-token used only by the fallback heuristic when tiktoken is
# unavailable. Kept as a module constant so callers that need the *ratio*
# itself (rather than a count) still have a single source of truth.
HEURISTIC_CHARS_PER_TOKEN = 4.0


def is_exact() -> bool:
    """Return True if `count_tokens()` returns exact tiktoken-based counts,
    False if it's using the len/4 approximation."""
    return _ENCODING is not None


def count_tokens(text: Optional[str]) -> int:
    """Return a token count for `text`.

    Uses tiktoken's `cl100k_base` encoding when available for an exact count;
    otherwise falls back to `len(text) // 4` (approximate — see `is_exact()`
    / `TOKENIZER_MODE` to check which mode produced a given number).
    """
    if not text:
        return 0

    if _ENCODING is not None:
        try:
            return len(_ENCODING.encode(text))
        except ValueError as e:
            # tiktoken's Encoding.encode() raises ValueError when text
            # contains a "special token" sequence (e.g. "<|endoftext|>")
            # that isn't in `allowed_special` -- fall through to the
            # heuristic instead of raising, but log it since a silent
            # switch to the approximate count is exactly the kind of
            # "token count looks wrong" report this masks.
            logger.debug("tiktoken encode() failed, falling back to heuristic: %s", e)

    return max(1, int(len(text) / HEURISTIC_CHARS_PER_TOKEN))
