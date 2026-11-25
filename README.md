# Slip Grammar

Slip Grammar is an experiment in a protected vocabulary layer for code-oriented models.

The idea: ordinary human prose may spend too much model capacity on spelling,
morphology, casing, and repeated language variants. A code-focused model may benefit
from a vocabulary layer that compresses low-value prose variation while preserving
all exact technical material.

The repository is a small prototype: a lossy morphology transform, a lossless
`encode` / `decode` codec with a round-trip guarantee, and a compression benchmark
on public-domain prose. The ratios below measure encoded bytes against the original
text.

## Current Prototype

The prototype implements a protected pre-tokenizer transform. It canonicalizes
ordinary prose while preserving code, math, identifiers, paths, URLs, quoted exact
strings, packages, numbers, and other exact technical spans.

The v1 grammar is intentionally conservative and morphology-first. It focuses on
suffix and casing compression before attempting any rhyme or phonetic merging.

## Install

```bash
pip install -e ".[dev]"
```

The `dev` extra installs pytest, Hypothesis, and mypy. `pip install -e ".[test]"` is enough to run the tests.

## Usage

The lossy morphology transform rewrites ordinary prose and leaves technical spans alone:

```bash
python -m slipgram transform <<'EOF'
The programmers were running tests in `src/main.py`.
EOF
```

```text
The program<ER_PL> were run<ING> test<PL> in `src/main.py`.
```

`encode` / `decode` are a separate lossless codec. Decoding an encoding returns the input, including case, punctuation, and protected spans:

```python
from slipgram import decode, encode

text = "The programmers were running tests in `src/main.py`."
encoded = encode(text)
assert decode(encoded) == text
print(len(text.encode()), len(encoded.encode()))  # 52 45
```

```bash
python -m slipgram encode < excerpt.txt > excerpt.slip
python -m slipgram decode < excerpt.slip > excerpt.txt
```

Codewords are control bytes. Read the text back with `decode`. `slipgram --version` prints the package version.

## Benchmark

`python -m slipgram.benchmark` (or `python scripts/benchmark.py`) encodes the excerpts in `benchmarks/samples` and checks that each one round-trips.

UTF-8 ratio is encoded UTF-8 bytes divided by original UTF-8 bytes. Character ratio uses Unicode code points. Protected is the share of characters inside spans copied through as exact text: code, math, identifiers, paths, URLs, numbers, packages, and ASCII quotes. On these books that share is small because dialogue uses curly quotes, which this protector leaves in the prose.

Measured on this tree:

| Work | Characters | UTF-8 bytes | Encoded UTF-8 bytes | UTF-8 ratio | Character ratio | Protected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Pride and Prejudice | 31,704 | 32,282 | 25,477 | 0.789 | 0.768 | 1.0% |
| Frankenstein; or, The Modern Prometheus | 31,620 | 31,751 | 25,405 | 0.800 | 0.786 | 0.1% |
| Alice’s Adventures in Wonderland | 31,792 | 32,801 | 25,416 | 0.775 | 0.752 | 0.9% |
| The Adventures of Sherlock Holmes | 31,907 | 32,817 | 26,377 | 0.804 | 0.782 | 0.1% |
| A Tale of Two Cities | 31,281 | 31,803 | 25,212 | 0.793 | 0.776 | 0.2% |
| The Time Machine | 31,967 | 32,769 | 26,052 | 0.795 | 0.775 | 0.3% |
| All excerpts | 190,271 | 194,223 | 153,939 | 0.793 | 0.773 | 0.4% |

Across all six excerpts the encoded form is 20.7% smaller in UTF-8 (194,223 bytes to 153,939). The tests fail if this table drifts from a fresh run.

The excerpts are public-domain books from Project Gutenberg, retrieved on 2026-11-25. `benchmarks/samples/manifest.json` records the author, year, Gutenberg id, source URL, the mirror the bytes were fetched from, the excerpt rule, and the SHA-256 of each file. Gutenberg headers, footers, and contents lists are omitted. Line endings were normalized from CRLF to LF, and each excerpt ends on a paragraph boundary at or before 32,000 characters.

- Jane Austen, *Pride and Prejudice* (1813), [ebook 1342](https://www.gutenberg.org/ebooks/1342). Starts at “It is a truth universally acknowledged”.
- Mary Wollstonecraft Shelley, *Frankenstein; or, The Modern Prometheus* (1818), [ebook 84](https://www.gutenberg.org/ebooks/84). Starts at the opening of Letter 1.
- Lewis Carroll, *Alice’s Adventures in Wonderland* (1865), [ebook 11](https://www.gutenberg.org/ebooks/11). Starts at “Alice was beginning to get very tired”.
- Arthur Conan Doyle, *The Adventures of Sherlock Holmes* (1892), [ebook 1661](https://www.gutenberg.org/ebooks/1661). Starts at “To Sherlock Holmes she is always”.
- Charles Dickens, *A Tale of Two Cities* (1859), [ebook 98](https://www.gutenberg.org/ebooks/98). Starts at “It was the best of times”.
- H. G. Wells, *The Time Machine* (1895), [ebook 35](https://www.gutenberg.org/ebooks/35). Starts at “The Time Traveller (for so it will be convenient to speak of him)”.

These ratios are for the lossless codec. The morphology transform is a vocabulary sketch: markers such as `<ING>` are longer than the endings they replace.

## Python API

```python
from slipgram import transform

result = transform("The programmers were running tests in `src/main.py`.")
print(result.slipped_text)
print(result.transform_log)
```

## Concept Rules

Slip Grammar should never mutate:

- math
- code
- identifiers
- paths
- commands
- package names
- API names
- quoted exact strings
- filenames
- error messages
- anything the model may need to reproduce exactly

The transform should only touch ordinary natural-language prose around the technical
content.

## Tokenizer Vision

All of the Slip Grammar ideas should come together as a tokenizer, not as scattered
prompt tricks.

The intended tokenizer stack is:

1. Protect exact spans: detect code, math, identifiers, APIs, paths, shell, config,
   JSON, stack traces, quoted exact strings, and error text before compression.
2. Compress intent prose: reduce instruction scaffolding with morphology compression,
   casing normalization, and optional caveman-speak simplification.
3. Bridge related languages: map compatible Latin-root word families across languages
   into shared root-plus-extension forms when context makes that safe.
4. Explore sound families: optionally test rhyme and phonetic endings after safer
   morphology and Latin-root compression are measurable.
5. Emit tokenizer-native units: train or adapt a tokenizer so these compressed forms
   become native vocab units rather than only runtime text substitutions.

The goal is a code-model tokenizer that spends less vocabulary and parameter budget
on redundant natural-language surface forms, while keeping exact technical material
lossless.

## Language Bridge Idea

A later Slip Grammar direction is a Latin-root compressor for bridging related
languages. The goal would be to map compatible words across English, Spanish,
French, Italian, Portuguese, and other Latin-influenced vocabularies into shared
root-plus-extension forms.

For example, related terms around `compute`, `computation`, `computacion`,
`computazione`, and `computacao` could be represented through a shared root family
when the surrounding context makes that safe. This is not translation. It is a
cross-language vocabulary compression layer that tries to reduce duplicate language
surface forms while preserving intent.

This would need stricter safeguards than morphology-only English compression because
false friends, idioms, named entities, and domain terms can drift across languages.

## Caveman Speak Idea

Another experimental direction is a "caveman speak" compressor: reduce ordinary
instruction prose to sparse, blunt intent words while preserving exact technical
content.

For example, a prompt like "please refactor this function so it handles missing
values without changing the public API" could compress toward "refactor function.
handle missing values. no change public API." The point is not style. The point is
testing whether models need less grammatical scaffolding around code tasks than we
usually provide.

This mode should be opt-in and measured carefully. It may help compress intent, but
it can also remove nuance, politeness constraints, ordering, and scope boundaries.

## Wishlist

- Train-time Slip Grammar: canonicalize non-code natural language in training data so
  the same size code model can spend more capacity on code, logic, APIs, and exact
  syntax.
- Tokenizer-native Slip Grammar: combine protected spans, morphology compression,
  caveman-speak simplification, Latin-root bridging, and optional phonetic/rhyme
  groups into one tokenizer training pipeline.
- Strong protected-region parser: identify code, math, shell, paths, config, JSON,
  stack traces, quoted strings, and identifiers before any vocab rewrite happens.
- Morphology compression: collapse casing, plural, `-ing`, `-er`, `-ed`, and related
  forms into base-plus-extension vocabulary markers.
- Rhyme and phonetic compression: later experiments for endings like `-ing`, `-er`,
  `-ning`, `-ang`, `-oach`, and `-ther`, with clear measurement because semantic
  drift risk is higher.
- Latin bridge compressor: map compatible Latin-root word families across related
  languages into shared root-plus-extension forms for multilingual prompt and corpus
  compression.
- Caveman speak compressor: strip ordinary prose down to terse intent words and
  minimal grammar while preserving code, math, identifiers, APIs, paths, and exact
  strings.
- Reversible transform mode: `encode` / `decode` restore the original text exactly,
  including case and protected spans. Hypothesis checks this on arbitrary strings.
- Evaluation harness: compare original and slipped prompts on coding tasks, compile
  rate, exactness failures, token count, and reasoning quality.
- Corpus experiments: test whether a small model trained on slipped prose plus exact
  code outperforms the same-size baseline.
- Human-readable debug logs: every changed word should explain its rule and source
  span.
- Multiple compression levels: conservative morphology-only, morphology-plus-rhyme,
  and maximum compression for research sweeps.

## Development

```bash
pip install -e ".[dev]"
pytest
python -m mypy
python -m slipgram.benchmark
```

GitHub Actions runs the tests on Python 3.10–3.13, mypy on 3.12, and the benchmark.

## Status

The lossless codec round-trips and the ratios above are measured. The morphology
transform, Latin bridge, and caveman-speak ideas are still sketches. Nothing here
is evidence that the approach improves model quality.
