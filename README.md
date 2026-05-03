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
  literature_review.md
  coding_agent_harness_literature_review.md
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

## Developer Setup

Create and activate a virtual environment, then install the package with test
dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Run the test suite:

```powershell
python -m pytest
```

Or run the local check wrapper:

```powershell
python scripts/check.py
```

## Smoke Run

The committed fixture under `tests/fixtures/` is intentionally tiny and does not
require network access, secrets, or an LLM provider. Use it to verify the
metadata-only run path from a fresh checkout:

```powershell
python scripts/run_experiment.py tests/fixtures/synthetic_subset_fixture.json --limit 2 --run-id fixture_smoke --output results/runs/fixture_smoke.json
python scripts/summarize_results.py results/runs/fixture_smoke.json
```

Run the deterministic baseline harness against the same fixture:

```powershell
python scripts/run_experiment.py tests/fixtures/synthetic_subset_fixture.json --harness deterministic_baseline --limit 2 --run-id deterministic_fixture --output results/runs/deterministic_fixture.json
python scripts/summarize_results.py results/runs/deterministic_fixture.json
```

Prompt and schema assets are versioned as normal files under `prompts/` and
`schemas/`. Loader utilities in `epilepsy_extraction.assets` return the asset
path, version ID, and content so LLM harnesses can record them in run records.

Provider-backed anchor harnesses can run from replayed JSON responses:

```powershell
python scripts/run_experiment.py tests/fixtures/synthetic_subset_fixture.json --harness single_prompt_anchor --limit 1 --replay path/to/replay.json --output results/runs/anchor_replay.json
```

The full-contract single-prompt baseline uses the same replay mechanism:

```powershell
python scripts/run_experiment.py tests/fixtures/synthetic_subset_fixture.json --harness single_prompt_full_contract --limit 1 --replay path/to/replay.json --output results/runs/full_contract_replay.json
```
