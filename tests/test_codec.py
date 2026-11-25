"""Example tests for the lossless protected codec."""

from __future__ import annotations

import subprocess
import sys

import pytest

from slipgram import compression_ratio, decode, encode, transform, utf8_compression_ratio
from slipgram.codec import ESCAPE, MULTI, reserved_codepoints


@pytest.mark.parametrize(
    "word",
    ["the", "and", "running", "programmers", "don't", "don’t", "something", "libraries", "seemingly"],
)
def test_common_tokens_shrink_and_roundtrip(word: str) -> None:
    encoded = encode(word)
    assert decode(encoded) == word
    assert len(encoded) < len(word)


def test_empty_string_and_ratios() -> None:
    assert encode("") == ""
    assert decode("") == ""
    assert compression_ratio("") == 1.0
    assert utf8_compression_ratio("") == 1.0


def test_protected_spans_are_copied_when_they_have_no_code_bytes() -> None:
    text = "Keep `src/main.py`, user_id, API_KEY, ./pkg/mod.py, 2 + 2 = 4, and https://example.com/x."
    encoded = encode(text)
    for snippet in ("`src/main.py`", "user_id", "API_KEY", "./pkg/mod.py", "2 + 2 = 4", "https://example.com/x"):
        assert snippet in encoded
    assert decode(encoded) == text
    assert len(encoded) < len(text)


def test_fenced_code_is_not_rewritten() -> None:
    text = "the programmers\n```\nthe programmers\n```\nthe"
    encoded = encode(text)
    assert "```\nthe programmers\n```" in encoded
    assert decode(encoded) == text
    assert len(encoded) < len(text)


def test_documented_transform_example() -> None:
    result = transform("The programmers were running tests in `src/main.py`.")
    assert result.slipped_text == "The program<ER_PL> were run<ING> test<PL> in `src/main.py`."


@pytest.mark.parametrize("char", sorted(reserved_codepoints()))
def test_reserved_character_roundtrips_and_is_escaped(char: str) -> None:
    assert decode(encode(char)) == char
    assert encode(char) == ESCAPE + char


def test_truncated_and_unknown_codes_raise() -> None:
    with pytest.raises(ValueError, match="truncated"):
        decode(ESCAPE)
    with pytest.raises(ValueError, match="truncated"):
        decode(MULTI)
    with pytest.raises(ValueError, match="unknown"):
        decode(MULTI + "\u0100")


def test_long_repeated_suffix_roundtrips() -> None:
    word = "ed" * 500
    assert decode(encode(word)) == word
    assert len(encode(word)) < len(word)


def test_cli_encode_decode_roundtrip() -> None:
    text = "The programmers were running tests.\nDon't touch `x`.\n"
    encoded = subprocess.run(
        [sys.executable, "-m", "slipgram", "encode"],
        input=text,
        text=True,
        capture_output=True,
        check=True,
    )
    decoded = subprocess.run(
        [sys.executable, "-m", "slipgram", "decode"],
        input=encoded.stdout,
        text=True,
        capture_output=True,
        check=True,
    )
    assert decoded.stdout == text


def test_cli_version() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "slipgram", "--version"],
        text=True,
        capture_output=True,
        check=True,
    )
    assert completed.stdout.strip().startswith("slipgram ")
