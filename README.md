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
- Tokenizer-native Slip Grammar: build the vocab system into tokenizer training
  instead of only transforming prompts at runtime.
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
