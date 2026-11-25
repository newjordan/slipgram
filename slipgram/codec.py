"""Lossless protected codec for ordinary prose.

``encode`` compresses unprotected prose and copies protected spans (code,
math, identifiers, paths, URLs, and quoted strings) through unchanged,
except for escaping the few control bytes the codec uses as codewords.
``decode`` is the inverse: ``decode(encode(text)) == text``.

Codewords are C0 controls, so they are one UTF-8 byte. A two-byte code is
the introducer followed by an index character. Indexes 0-127 are one UTF-8
byte; indexes 128-255 are two, and those later entries save fewer bytes.

The one-byte vocabulary is the function words and endings with the largest
marginal savings. The two-byte vocabulary is other common English words and
endings, capped at 256 and ordered by savings. It does not contain proper
names from the benchmark books. Order is part of the code assignment.
"""

from __future__ import annotations

import re
from typing import Final

from .core import protect_spans

ESCAPE: Final[str] = "\x01"
MULTI: Final[str] = "\x1e"

# HT, LF, and CR stay literal so ordinary line breaks are not escaped.
_SINGLE_BYTE_EXCLUDED: Final[frozenset[int]] = frozenset({0x01, 0x09, 0x0A, 0x0D, 0x1E})

# A word is a letter run with internal ASCII or curly apostrophes or hyphens.
# Digits stay outside the token so identifiers like "the2" are not split.
_WORD_RE: Final[re.Pattern[str]] = re.compile(
    "(?<![A-Za-z0-9])[A-Za-z]+(?:['\u2019-][A-Za-z]+)*(?![A-Za-z0-9])"
)

_SINGLE_SUFFIXES: tuple[str, ...] = (
    'ed',
    'ing',
    'er',
    'ly',
    'es',
)

_SINGLE_WORDS: tuple[str, ...] = (
    'the',
    'and',
    'of',
    'to',
    'in',
    'was',
    'it',
    'his',
    'that',
    'you',
    'he',
    'with',
    'as',
    'had',
    'my',
    'is',
    'for',
    'she',
    'not',
    'at',
    'be',
    'on',
)

_MULTI_SUFFIXES: tuple[str, ...] = (
    'ation',
    'tion',
    'able',
    'ness',
    'ance',
    'ers',
    'ent',
    'ence',
    'sion',
    'ally',
    'ate',
    'ment',
    'ious',
    'est',
    'ture',
    'ive',
    'ity',
    'age',
    'ical',
    'less',
    'ory',
    'ist',
    'ings',
    'ant',
    'ible',
    'selves',
    'ous',
    'self',
    'ary',
    'ure',
    'ful',
    "n't",
    'n’t',
    "'ll",
    '’ll',
    "'re",
    '’re',
    "'ve",
    '’ve',
)

_MULTI_WORDS: tuple[str, ...] = (
    'which',
    'said',
    'have',
    'little',
    'this',
    'were',
    'would',
    'from',
    'before',
    'there',
    'very',
    'about',
    'could',
    'should',
    'will',
    'thought',
    'herself',
    'when',
    'nothing',
    'her',
    'but',
    'down',
    'through',
    'been',
    'into',
    'looked',
    'again',
    'they',
    'other',
    'think',
    'all',
    'himself',
    'their',
    'The',
    'more',
    'never',
    'your',
    'him',
    'know',
    'Time',
    'them',
    'like',
    'time',
    'shall',
    'another',
    'though',
    'what',
    'being',
    'seemed',
    'without',
    'There',
    'one',
    'enough',
    'friend',
    'are',
    'every',
    'such',
    'than',
    'must',
    'great',
    'quite',
    'much',
    'only',
    'some',
    'things',
    'then',
    'towards',
    'upon',
    'first',
    'perhaps',
    'might',
    'thing',
    'always',
    'over',
    'night',
    'dear',
    'after',
    'found',
    'three',
    'between',
    'anything',
    'moment',
    'people',
    'rather',
    'something',
    'still',
    'years',
    'those',
    'out',
    'cried',
    'heard',
    'who',
    'You',
    'already',
    'replied',
    'What',
    'back',
    'myself',
    'Then',
    'come',
    'most',
    'right',
    'good',
    'here',
    'But',
    'came',
    'large',
    'went',
    'young',
    'because',
    'morning',
    'eyes',
    'having',
    'made',
    'well',
    'man',
    'these',
    'ever',
    'And',
    'better',
    'door',
    'evening',
    'face',
    'small',
    'while',
    'don’t',
    'how',
    'everything',
    'half',
    'life',
    'see',
    'may',
    'own',
    'among',
    'hand',
    'has',
    'its',
    'just',
    'under',
    'They',
    'either',
    'last',
    'make',
    'room',
    'any',
    'going',
    'house',
    'until',
    'words',
    'against',
    'long',
    'once',
    'way',
    'This',
    'almost',
    'asked',
    'light',
    'now',
    'opened',
    'sister',
    'times',
    'turned',
    'whole',
    'can',
    'Miss',
    'many',
    'say',
    'took',
    'two',
    'o’clock',
    'voice',
    'where',
    'across',
    'father',
    'sure',
    'window',
    'even',
    'felt',
    'our',
    'However',
    'That',
    'called',
    'did',
    'look',
    'tell',
    'too',
    'whether',
    'woman',
    'world',
    'head',
    'next',
    'same',
    'away',
    'children',
    'together',
    'brother',
    'Mrs',
    'left',
    'take',
    'want',
    'often',
    'place',
    'since',
    'I’ll',
    'really',
    'within',
    'When',
    'can’t',
    'doesn’t',
    'hear',
    'wouldn’t',
    "don't",
    "I'll",
    "o'clock",
    "can't",
    "doesn't",
    "wouldn't",
)


def _single_byte_alphabet() -> tuple[str, ...]:
    return tuple(chr(code) for code in range(0x20) if code not in _SINGLE_BYTE_EXCLUDED)


def _build_tables() -> tuple[dict[str, str], tuple[tuple[str, str], ...], dict[str, str], dict[str, str], frozenset[str]]:
    alphabet = _single_byte_alphabet()
    single_items: list[tuple[str, str]] = [("suffix", suffix) for suffix in _SINGLE_SUFFIXES]
    single_items.extend(("word", word) for word in _SINGLE_WORDS)
    if len(single_items) != len(alphabet):
        raise RuntimeError(
            f"expected {len(alphabet)} one-byte entries, found {len(single_items)}"
        )

    word_to_code: dict[str, str] = {}
    single_decode: dict[str, str] = {}
    suffix_pairs: list[tuple[str, str]] = []
    for (kind, text), code in zip(single_items, alphabet, strict=True):
        if len(code) >= len(text):
            raise RuntimeError(f"one-byte code does not shrink {text!r}")
        single_decode[code] = text
        if kind == "word":
            word_to_code[text] = code
        else:
            suffix_pairs.append((text, code))

    multi_items: list[tuple[str, str]] = [("suffix", suffix) for suffix in _MULTI_SUFFIXES]
    multi_items.extend(("word", word) for word in _MULTI_WORDS)
    if len(multi_items) > 256:
        raise RuntimeError(f"two-byte table has {len(multi_items)} entries; the limit is 256")

    multi_decode: dict[str, str] = {}
    for index, (kind, text) in enumerate(multi_items):
        if len(text) < 3:
            raise RuntimeError(f"two-byte entry is too short: {text!r}")
        code = MULTI + chr(index)
        if len(code) >= len(text):
            raise RuntimeError(f"two-byte code does not shrink {text!r}")
        if kind == "word":
            if text in word_to_code:
                raise RuntimeError(f"duplicate word code for {text!r}")
            word_to_code[text] = code
        else:
            suffix_pairs.append((text, code))
        multi_decode[chr(index)] = text

    suffix_pairs.sort(key=lambda item: len(item[0]), reverse=True)
    reserved = frozenset(single_decode) | {ESCAPE, MULTI}
    return word_to_code, tuple(suffix_pairs), single_decode, multi_decode, reserved


_WORD_TO_CODE, _SUFFIXES, _SINGLE_DECODE, _MULTI_DECODE, _RESERVED = _build_tables()


def reserved_codepoints() -> frozenset[str]:
    """Control characters that are escaped when they appear as literal input."""
    return _RESERVED


def encode(text: str) -> str:
    """Compress unprotected prose. Protected spans survive except for code-byte escapes."""
    spans = protect_spans(text)
    parts: list[str] = []
    cursor = 0
    for span in spans:
        parts.append(_encode_prose(text[cursor : span.start]))
        parts.append(_escape(span.text))
        cursor = span.end
    parts.append(_encode_prose(text[cursor:]))
    return "".join(parts)


def decode(data: str) -> str:
    """Invert :func:`encode`.

    Raises:
        ValueError: ``data`` is truncated or contains an unknown code.
    """
    out: list[str] = []
    index = 0
    limit = len(data)
    while index < limit:
        char = data[index]
        if char == ESCAPE:
            index += 1
            if index >= limit:
                raise ValueError("truncated escape in slipgram encoding")
            out.append(data[index])
            index += 1
            continue
        if char == MULTI:
            index += 1
            if index >= limit:
                raise ValueError("truncated multi-byte code in slipgram encoding")
            key = data[index]
            try:
                out.append(_MULTI_DECODE[key])
            except KeyError as exc:
                raise ValueError(f"unknown slipgram code index U+{ord(key):04X}") from exc
            index += 1
            continue
        expansion = _SINGLE_DECODE.get(char)
        if expansion is not None:
            out.append(expansion)
        else:
            out.append(char)
        index += 1
    return "".join(out)


def compression_ratio(text: str) -> float:
    """Encoded Unicode code points divided by original code points.

    Empty input has ratio 1. Values below 1 mean the encoded form is shorter.
    """
    if not text:
        return 1.0
    return len(encode(text)) / len(text)


def utf8_compression_ratio(text: str) -> float:
    """Encoded UTF-8 bytes divided by original UTF-8 bytes.

    Empty input has ratio 1. Values below 1 mean the encoded form is smaller.
    """
    original = text.encode("utf-8")
    if not original:
        return 1.0
    return len(encode(text).encode("utf-8")) / len(original)


def _encode_prose(segment: str) -> str:
    parts: list[str] = []
    cursor = 0
    for match in _WORD_RE.finditer(segment):
        parts.append(_escape(segment[cursor : match.start()]))
        parts.append(_encode_token(match.group(0)))
        cursor = match.end()
    parts.append(_escape(segment[cursor:]))
    return "".join(parts)


def _encode_token(token: str) -> str:
    """Replace a whole word by codes, stripping endings from the right.

    Dictionary hits win over endings. Each replacement is shorter than the
    text it stands for, so the result is never longer than ``token``.
    """
    direct = _WORD_TO_CODE.get(token)
    if direct is not None:
        return direct

    parts: list[str] = []
    remaining = token
    while remaining:
        coded = _WORD_TO_CODE.get(remaining)
        if coded is not None:
            parts.append(coded)
            break
        suffix_code: str | None = None
        suffix_length = 0
        for suffix, code in _SUFFIXES:
            if len(code) < len(suffix) and remaining.endswith(suffix):
                suffix_code = code
                suffix_length = len(suffix)
                break
        if suffix_code is None:
            parts.append(remaining)
            break
        parts.append(suffix_code)
        remaining = remaining[:-suffix_length]
    parts.reverse()
    return "".join(parts)


def _escape(text: str) -> str:
    if not any(char in _RESERVED for char in text):
        return text
    return "".join(ESCAPE + char if char in _RESERVED else char for char in text)
