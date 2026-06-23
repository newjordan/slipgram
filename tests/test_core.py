import json
import subprocess
import sys

from slipgram import canonicalize_word, protect_spans, transform


def test_protects_code_math_paths_urls_and_identifiers():
    source = (
        "The Programmers are running tests in `src/main.py` with user_id and "
        "API_KEY at ./pkg/mod.py. Keep 2 + 2 = 4 and https://example.com/x."
    )

    result = transform(source, strict_protect=True)

    assert "`src/main.py`" in result.slipped_text
    assert "user_id" in result.slipped_text
    assert "API_KEY" in result.slipped_text
    assert "./pkg/mod.py" in result.slipped_text
    assert "2 + 2 = 4" in result.slipped_text
    assert "https://example.com/x." in result.slipped_text
    assert "Programmers" not in result.slipped_text
    assert "program<ER_PL>" in result.slipped_text
    assert "run<ING>" in result.slipped_text


def test_protect_spans_are_non_overlapping_and_source_ordered():
    source = "Use `https://example.com/pkg_name` and then ./src/App.tsx"
    spans = protect_spans(source)

    assert spans == sorted(spans, key=lambda span: span.start)
    assert all(left.end <= right.start for left, right in zip(spans, spans[1:]))
    assert any(span.kind == "inline_code" for span in spans)
    assert any(span.text == "./src/App.tsx" for span in spans)


def test_canonicalize_morphology_first_rules():
    assert canonicalize_word("running") == ("run<ING>", "suffix:ing")
    assert canonicalize_word("runner") == ("run<ER>", "suffix:er")
    assert canonicalize_word("tested") == ("test<ED>", "suffix:ed")
    assert canonicalize_word("models") == ("model<PL>", "suffix:s")
    assert canonicalize_word("libraries") == ("library<PL>", "suffix:ies")


def test_canonicalize_preserves_ambiguous_or_exact_words():
    assert canonicalize_word("math") == ("math", None)
    assert canonicalize_word("CSS") == ("CSS", None)
    assert canonicalize_word("snake_case") == ("snake_case", None)
    assert canonicalize_word("does") == ("does", None)


def test_transform_log_explains_changes():
    result = transform("Programmers were testing models.")

    assert result.slipped_text == "program<ER_PL> were test<ING> model<PL>."
    assert [(entry.original, entry.canonical, entry.rule) for entry in result.transform_log] == [
        ("Programmers", "program<ER_PL>", "suffix:ers"),
        ("testing", "test<ING>", "suffix:ing"),
        ("models", "model<PL>", "suffix:s"),
    ]


def test_cli_json_output():
    completed = subprocess.run(
        [sys.executable, "-m", "slipgram.cli", "transform", "--json"],
        input="Coders are testing `do_not_touch()`.",
        text=True,
        check=True,
        capture_output=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["slipped_text"] == "cod<ER_PL> are test<ING> `do_not_touch()`."
    assert payload["protected_spans"][0]["text"] == "`do_not_touch()`"
    assert payload["transform_log"][0]["original"] == "Coders"
