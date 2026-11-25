"""The published benchmark numbers have to match a fresh run."""

from __future__ import annotations

from pathlib import Path

from slipgram.benchmark import format_markdown, load_samples, measure_samples
from slipgram.codec import decode, encode


def test_samples_roundtrip_and_compress() -> None:
    samples = load_samples()
    assert len(samples) >= 4
    for sample in samples:
        assert sample.source == "Project Gutenberg"
        assert sample.year <= 1928
        assert "gutenberg.org" in sample.ebook_url
        encoded = encode(sample.text)
        assert decode(encoded) == sample.text
        assert len(encoded.encode("utf-8")) < len(sample.text.encode("utf-8"))


def test_readme_reports_current_benchmark() -> None:
    table = format_markdown(measure_samples())
    readme = Path("README.md").read_text(encoding="utf-8")
    assert table in readme
    assert "The program<ER_PL> were run<ING> test<PL> in `src/main.py`." in readme
