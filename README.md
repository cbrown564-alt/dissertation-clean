# Training-Free Multi-Agent Epilepsy Extraction

This repository is the clean rebuild of the dissertation project. It starts from
the final research contract rather than the chronology of the exploratory repo.

The project evaluates whether a training-free, role-separated multi-agent
extractor can improve reliability, auditability, and evidence support for
structured extraction from epilepsy clinic letters when compared with a strong
single-prompt baseline under controlled budget constraints.

## Research Frame

The system reads an epilepsy clinic letter and emits structured clinical fields
with evidence, confidence, citations, warnings, and run metadata. The target is
not summarisation. The target is clinically adjudicable extraction.

The main comparison is:

1. a full-contract single-prompt extractor;
2. a full-contract role-separated multi-agent extractor.

Both systems must emit the same final schema so that field-level validity,
correctness, evidence support, and budget can be compared directly.

## Initial Scope

This repo begins docs-first and contract-first. Implementation will be ported in
small batches after the contracts are stable.

First-class scope:

- field-family evaluation contract;
- clinical adjudication protocol;
- fixed-slice experiment discipline;
- full-contract single-prompt baseline;
- role-separated multi-agent pipeline;
- anchor seizure-frequency reliability harnesses;
- canonical run records and result tables;
- compact static visibility cockpit.

Out of scope for the clean rebuild:

- the full Evidence Notebook;
- the Pipeline Observatory;
- agent-state workflow machinery;
- generated dashboard payload churn;
- rejected harness implementations as maintained code paths;
- production-readiness claims from synthetic-only sensitivity runs.

## Repository Shape

Planned structure:

```text
docs/
  research_question.md
  evaluation_contract.md
  adjudication_protocol.md
  architecture.md
  experiment_protocol.md
  porting_notes.md
src/
  data/
  evaluation/
  schemas/
  providers/
  harnesses/
  agents/
scripts/
  run_experiment.py
  summarize_results.py
  build_cockpit_data.py
results/
  runs/
  tables/
  adjudication/
tests/
site/
```

## Current Status

The repo currently contains the documentation spine plus the first foundation
code batch: data loading, fixed-slice helpers, schema definitions, anchor label
metrics, and run metadata writing. No LLM harness should be treated as canonical
until these foundations are exercised on a fixed slice.
