# Slip Grammar

Slip Grammar is a concept-only experiment for a protected vocabulary system aimed at
code-oriented models.

The idea: ordinary human prose may spend too much model capacity on spelling,
morphology, casing, and repeated language variants. A code-focused model may benefit
from a vocabulary layer that compresses low-value prose variation while preserving
all exact technical material.

This repository is not a production tokenizer, model, benchmark, or claim of proven
performance. It is a small prototype for exploring the concept.

## Current Prototype

The prototype implements a protected pre-tokenizer transform. It canonicalizes
ordinary prose while preserving code, math, identifiers, paths, URLs, quoted exact
strings, packages, numbers, and other exact technical spans.

The v1 grammar is intentionally conservative and morphology-first. It focuses on
suffix and casing compression before attempting any rhyme or phonetic merging.

## Usage

```bash
slipgram transform < prompt.txt
slipgram transform --json < prompt.txt
slipgram transform --show-log < prompt.txt
```

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

## Wishlist

- Train-time Slip Grammar: canonicalize non-code natural language in training data so
  the same size code model can spend more capacity on code, logic, APIs, and exact
  syntax.
- Tokenizer-native Slip Grammar: build the vocab system into tokenizer training
  instead of only transforming prompts at runtime.
- Strong protected-region parser: identify code, math, shell, paths, config, JSON,
  stack traces, quoted strings, and identifiers before any vocab rewrite happens.
- Morphology compression: collapse casing, plural, `-ing`, `-er`, `-ed`, and related
  forms into base-plus-extension vocabulary markers.
- Rhyme and phonetic compression: later experiments for endings like `-ing`, `-er`,
  `-ning`, `-ang`, `-oach`, and `-ther`, with clear measurement because semantic
  drift risk is higher.
- Reversible transform mode: preserve enough metadata to reconstruct original prose
  when needed.
- Evaluation harness: compare original and slipped prompts on coding tasks, compile
  rate, exactness failures, token count, and reasoning quality.
- Corpus experiments: test whether a small model trained on slipped prose plus exact
  code outperforms the same-size baseline.
- Human-readable debug logs: every changed word should explain its rule and source
  span.
- Multiple compression levels: conservative morphology-only, morphology-plus-rhyme,
  and maximum compression for research sweeps.

## Status

Concept only. Use this repo as a sketchpad for the vocab-system idea, not as evidence
that the approach improves model performance yet.
