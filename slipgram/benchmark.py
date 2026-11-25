"""Compression ratios for the public-domain sample excerpts.

Run ``python -m slipgram.benchmark`` from a source checkout. The samples and
their Project Gutenberg provenance live in ``benchmarks/samples``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .codec import decode, encode
from .core import protect_spans

_MANIFEST_NAME = "manifest.json"


@dataclass(frozen=True)
class Sample:
    """One excerpt plus the provenance recorded in the manifest."""

    file: str
    title: str
    author: str
    year: int
    rights: str
    source: str
    gutenberg_id: int
    ebook_url: str
    text_url: str
    retrieved_from: str
    retrieved: str
    excerpt: str
    sha256: str
    text: str


@dataclass(frozen=True)
class SampleReport:
    """Sizes for one excerpt after a checked round-trip."""

    title: str
    original_chars: int
    original_utf8_bytes: int
    encoded_chars: int
    encoded_utf8_bytes: int
    protected_chars: int

    @property
    def char_ratio(self) -> float:
        return self.encoded_chars / self.original_chars

    @property
    def utf8_ratio(self) -> float:
        return self.encoded_utf8_bytes / self.original_utf8_bytes

    @property
    def protected_fraction(self) -> float:
        return self.protected_chars / self.original_chars


def samples_dir() -> Path:
    """Locate ``benchmarks/samples`` from the checkout that contains this file."""
    for root in (Path.cwd(), *Path(__file__).resolve().parents):
        candidate = root / "benchmarks" / "samples"
        if (candidate / _MANIFEST_NAME).is_file():
            return candidate
    raise FileNotFoundError(
        "Could not find benchmarks/samples/manifest.json. Run from a slipgram source checkout."
    )


def load_samples(directory: Path | None = None) -> list[Sample]:
    """Load excerpts and reject a manifest entry whose bytes do not match."""
    root = samples_dir() if directory is None else directory
    manifest_path = root / _MANIFEST_NAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise TypeError(f"{manifest_path} must contain a list")

    samples: list[Sample] = []
    for index, entry in enumerate(payload):
        samples.append(_load_entry(root, entry, index))
    if not samples:
        raise ValueError(f"{manifest_path} does not list any excerpts")
    return samples


def measure_samples(samples: list[Sample] | None = None) -> list[SampleReport]:
    """Encode every excerpt, require an exact round-trip, and record sizes."""
    reports: list[SampleReport] = []
    for sample in load_samples() if samples is None else samples:
        encoded = encode(sample.text)
        if decode(encoded) != sample.text:
            raise AssertionError(f"round-trip failed for {sample.file}")
        protected = sum(span.end - span.start for span in protect_spans(sample.text))
        reports.append(
            SampleReport(
                title=sample.title,
                original_chars=len(sample.text),
                original_utf8_bytes=len(sample.text.encode("utf-8")),
                encoded_chars=len(encoded),
                encoded_utf8_bytes=len(encoded.encode("utf-8")),
                protected_chars=protected,
            )
        )
    return reports


def total_report(reports: list[SampleReport]) -> SampleReport:
    """Sum a set of reports. Ratios are weighted by size, not averaged."""
    if not reports:
        raise ValueError("no reports to total")
    return SampleReport(
        title="All excerpts",
        original_chars=sum(report.original_chars for report in reports),
        original_utf8_bytes=sum(report.original_utf8_bytes for report in reports),
        encoded_chars=sum(report.encoded_chars for report in reports),
        encoded_utf8_bytes=sum(report.encoded_utf8_bytes for report in reports),
        protected_chars=sum(report.protected_chars for report in reports),
    )


def format_markdown(reports: list[SampleReport]) -> str:
    """Markdown table of UTF-8 and character compression ratios."""
    rows = [*reports, total_report(reports)]
    lines = [
        "| Work | Characters | UTF-8 bytes | Encoded UTF-8 bytes | UTF-8 ratio | Character ratio | Protected |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for report in rows:
        lines.append(
            "| {title} | {chars} | {utf8} | {encoded} | {utf8_ratio:.3f} | {char_ratio:.3f} | {protected:.1%} |".format(
                title=report.title,
                chars=f"{report.original_chars:,}",
                utf8=f"{report.original_utf8_bytes:,}",
                encoded=f"{report.encoded_utf8_bytes:,}",
                utf8_ratio=report.utf8_ratio,
                char_ratio=report.char_ratio,
                protected=report.protected_fraction,
            )
        )
    return "\n".join(lines)


def format_text(reports: list[SampleReport]) -> str:
    """Plain-text report, including the markdown table the README quotes."""
    lines = [
        "Slipgram lossless compression",
        "",
        "UTF-8 ratio = encoded UTF-8 bytes / original UTF-8 bytes.",
        "Character ratio = encoded Unicode code points / original code points.",
        "Protected is the share of characters kept inside protected spans.",
        "Values below 1 mean the encoded form is smaller.",
        "",
        format_markdown(reports),
        "",
        "Sources: benchmarks/samples/manifest.json",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    """Print the benchmark report. Exits non-zero if a round-trip fails."""
    print(format_text(measure_samples()), end="")
    return 0


def _load_entry(root: Path, entry: object, index: int) -> Sample:
    label = f"manifest entry {index}"
    data = _as_object(entry, label)
    file_name = _as_str(data, "file", label)
    text_path = root / file_name
    blob = text_path.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    expected = _as_str(data, "sha256", label)
    if digest != expected:
        raise ValueError(f"{file_name} sha256 is {digest}, manifest has {expected}")
    text = blob.decode("utf-8")
    characters = _as_int(data, "characters", label)
    if len(text) != characters:
        raise ValueError(f"{file_name} has {len(text)} characters, manifest says {characters}")
    return Sample(
        file=file_name,
        title=_as_str(data, "title", label),
        author=_as_str(data, "author", label),
        year=_as_int(data, "year", label),
        rights=_as_str(data, "rights", label),
        source=_as_str(data, "source", label),
        gutenberg_id=_as_int(data, "gutenberg_id", label),
        ebook_url=_as_str(data, "ebook_url", label),
        text_url=_as_str(data, "text_url", label),
        retrieved_from=_as_str(data, "retrieved_from", label),
        retrieved=_as_str(data, "retrieved", label),
        excerpt=_as_str(data, "excerpt", label),
        sha256=expected,
        text=text,
    )


def _as_object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError(f"{label} must be an object")
    parsed: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise TypeError(f"{label} has a non-string key")
        parsed[key] = item
    return parsed


def _as_str(data: dict[str, object], key: str, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise TypeError(f"{label} field {key} must be a non-empty string")
    return value


def _as_int(data: dict[str, object], key: str, label: str) -> int:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} field {key} must be an integer")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
