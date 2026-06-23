from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Iterable


@dataclass(frozen=True)
class ProtectedSpan:
    start: int
    end: int
    kind: str
    text: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TransformLogEntry:
    start: int
    end: int
    original: str
    canonical: str
    rule: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TransformResult:
    slipped_text: str
    protected_spans: list[ProtectedSpan]
    transform_log: list[TransformLogEntry]

    def to_dict(self) -> dict[str, object]:
        return {
            "slipped_text": self.slipped_text,
            "protected_spans": [span.to_dict() for span in self.protected_spans],
            "transform_log": [entry.to_dict() for entry in self.transform_log],
        }


PROTECTED_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("fenced_code", re.compile(r"```[\s\S]*?```")),
    ("inline_code", re.compile(r"`[^`\n]+`")),
    ("url", re.compile(r"https?://[^\s)>\]}]+")),
    ("path", re.compile(r"(?<!\w)(?:\.{1,2}/|/|~\/)[^\s`'\"<>]+")),
    ("windows_path", re.compile(r"(?<!\w)[A-Za-z]:\\[^\s`'\"<>]+")),
    ("quoted_string", re.compile(r"(?P<quote>['\"])(?:(?!(?P=quote)).){2,}(?P=quote)")),
    ("identifier", re.compile(r"\b(?:[A-Z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*|[a-z]+[A-Z][A-Za-z0-9]*|[A-Za-z_][A-Za-z0-9]*_[A-Za-z0-9_]*|[A-Z][A-Z0-9_]{1,})\b")),
    ("package", re.compile(r"(?<!\w)@?[a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._-]*(?!\w)")),
    ("math", re.compile(r"(?<!\w)(?:\d+(?:\.\d+)?\s*(?:[+\-*/=<>^]|<=|>=|==|!=)\s*)+\d+(?:\.\d+)?(?!\w)")),
    ("number", re.compile(r"(?<!\w)\d+(?:\.\d+)?(?:[eE][+\-]?\d+)?%?(?!\w)")),
)

WORD_RE = re.compile(r"\b[A-Za-z][A-Za-z'-]*\b")

EXCEPTIONS = {
    "analysis",
    "axis",
    "basis",
    "bias",
    "business",
    "class",
    "css",
    "does",
    "gas",
    "his",
    "is",
    "its",
    "js",
    "math",
    "news",
    "physics",
    "plus",
    "promise",
    "this",
    "was",
    "yes",
}

DOUBLE_CONSONANT_SUFFIXES = ("bb", "dd", "ff", "gg", "ll", "mm", "nn", "pp", "rr", "tt")


def protect_spans(text: str) -> list[ProtectedSpan]:
    """Return non-overlapping protected spans in source order."""
    candidates: list[ProtectedSpan] = []
    for kind, pattern in PROTECTED_PATTERNS:
        for match in pattern.finditer(text):
            candidates.append(ProtectedSpan(match.start(), match.end(), kind, match.group(0)))

    candidates.sort(key=lambda span: (span.start, -(span.end - span.start)))
    protected: list[ProtectedSpan] = []
    occupied_until = -1
    for span in candidates:
        if span.start < occupied_until:
            continue
        protected.append(span)
        occupied_until = span.end
    return protected


def canonicalize_word(word: str) -> tuple[str, str | None]:
    """Return canonical form and rule name for a single unprotected prose word."""
    if not _is_plain_word(word):
        return word, None

    lower = word.lower()
    if lower in EXCEPTIONS or len(lower) < 4:
        canonical = lower if word != lower and len(lower) >= 4 else word
        if canonical != word:
            return canonical, "case"
        return word, None

    base, marker, rule = _suffix_canonical(lower)
    if marker:
        canonical = f"{base}<{marker}>"
    else:
        canonical = lower
        rule = "case" if canonical != word else None

    if canonical == word:
        return word, None
    return canonical, rule


def transform(text: str, *, strict_protect: bool = False) -> TransformResult:
    protected_spans = protect_spans(text)
    log: list[TransformLogEntry] = []
    out: list[str] = []
    cursor = 0

    for span in protected_spans:
        _append_transformed_segment(text[cursor:span.start], cursor, out, log)
        out.append(span.text)
        cursor = span.end

    _append_transformed_segment(text[cursor:], cursor, out, log)

    if strict_protect:
        slipped_text = "".join(out)
        _assert_protected_text_survived(slipped_text, protected_spans)

    return TransformResult("".join(out), protected_spans, log)


def _append_transformed_segment(
    segment: str,
    source_offset: int,
    out: list[str],
    log: list[TransformLogEntry],
) -> None:
    cursor = 0
    for match in WORD_RE.finditer(segment):
        out.append(segment[cursor:match.start()])
        original = match.group(0)
        canonical, rule = canonicalize_word(original)
        out.append(canonical)
        if rule:
            log.append(
                TransformLogEntry(
                    source_offset + match.start(),
                    source_offset + match.end(),
                    original,
                    canonical,
                    rule,
                )
            )
        cursor = match.end()
    out.append(segment[cursor:])


def _suffix_canonical(word: str) -> tuple[str, str | None, str | None]:
    if word.endswith("ies") and len(word) > 5:
        return word[:-3] + "y", "PL", "suffix:ies"
    if word.endswith("ing") and len(word) > 5:
        return _clean_suffix_base(word[:-3]), "ING", "suffix:ing"
    if word.endswith("ers") and len(word) > 5:
        return _clean_suffix_base(word[:-3]), "ER_PL", "suffix:ers"
    if word.endswith("er") and len(word) > 4:
        return _clean_suffix_base(word[:-2]), "ER", "suffix:er"
    if word.endswith("ed") and len(word) > 4:
        return _clean_suffix_base(word[:-2]), "ED", "suffix:ed"
    if word.endswith("es") and len(word) > 4 and not word.endswith(("ses", "xes", "zes")):
        return word[:-2], "PL", "suffix:es"
    if word.endswith("s") and len(word) > 4 and not word.endswith(("ss", "us", "is")):
        return word[:-1], "PL", "suffix:s"
    return word, None, None


def _clean_suffix_base(base: str) -> str:
    for doubled in DOUBLE_CONSONANT_SUFFIXES:
        if base.endswith(doubled):
            return base[:-1]
    if len(base) > 3 and base.endswith("i"):
        return base[:-1] + "y"
    return base


def _is_plain_word(word: str) -> bool:
    if "_" in word or "-" in word or "'" in word:
        return False
    if not word.isalpha():
        return False
    if len(word) > 1 and word.isupper():
        return False
    return True


def _assert_protected_text_survived(slipped_text: str, protected_spans: Iterable[ProtectedSpan]) -> None:
    missing = [span for span in protected_spans if span.text not in slipped_text]
    if missing:
        joined = ", ".join(f"{span.kind}@{span.start}:{span.end}" for span in missing)
        raise ValueError(f"protected spans missing after transform: {joined}")
