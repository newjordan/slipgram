"""Property tests: decoding an encoding returns the input."""

from __future__ import annotations

from hypothesis import example, given, settings, strategies as st

from slipgram import decode, encode
from slipgram.codec import reserved_codepoints

_RESERVED = "".join(sorted(reserved_codepoints()))


@settings(max_examples=200, deadline=None)
@given(st.text(max_size=300))
@example("")
@example("the")
@example("The programmers were running tests in `src/main.py`.")
@example("Don’t change it’s API.\nThe tests were running.")
@example("\x00\x01\x1e")
def test_decode_inverts_encode(text: str) -> None:
    assert decode(encode(text)) == text


@settings(max_examples=150, deadline=None)
@given(
    st.text(
        alphabet=st.characters(blacklist_characters=_RESERVED),
        max_size=300,
    )
)
def test_text_without_code_bytes_does_not_grow(text: str) -> None:
    assert len(encode(text)) <= len(text)


@settings(max_examples=100, deadline=None)
@given(
    st.lists(
        st.sampled_from(
            [
                "the",
                "programmers",
                "were",
                "running",
                "tests",
                "and",
                "don't",
                "don’t",
                "`src/main.py`",
                "https://example.com/x",
                "user_id",
                "2 + 2 = 4",
            ]
        ),
        min_size=1,
        max_size=40,
    )
)
@example(["the", "`the`", "the"])
def test_mixed_prose_and_protected_spans_roundtrip(tokens: list[str]) -> None:
    text = " ".join(tokens)
    assert decode(encode(text)) == text
    assert len(encode(text)) <= len(text)
