"""Slip Grammar protected vocabulary canonicalization."""

from .codec import compression_ratio, decode, encode, utf8_compression_ratio
from .core import ProtectedSpan, TransformLogEntry, TransformResult, canonicalize_word, protect_spans, transform

__version__ = "0.2.0"

__all__ = [
    "ProtectedSpan",
    "TransformLogEntry",
    "TransformResult",
    "canonicalize_word",
    "compression_ratio",
    "decode",
    "encode",
    "protect_spans",
    "transform",
    "utf8_compression_ratio",
]
