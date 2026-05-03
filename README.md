# Training-Free Epilepsy Extraction Evidence Pipeline

This repository is the clean rebuild of the dissertation project. It starts from
the final research contract rather than the chronology of the exploratory repo.

The project evaluates how training-free extraction harnesses perform on
structured epilepsy clinic-letter extraction: clinical NLP baselines, direct
LLM prompting, retrieval-plus-field extraction, CLINES-inspired modular
pipelines, model-family sensitivity runs, and costed reliability variants.

## Research Frame

The system reads an epilepsy clinic letter and emits structured clinical fields
with evidence, confidence, citations, warnings, and run metadata. The target is
not summarisation. The target is clinically adjudicable extraction.

The central evidence object is a run record: a fixed dataset slice, harness,
model/provider configuration, shared final schema, artifacts, budget metadata,
manifest hash, and PHI-safe harness event summary. Comparable systems emit the
same final payload shape or an explicitly mapped partial baseline payload.

## Initial Scope

This repo is now implemented through the harness-native refactor in
`docs/implementation_plan.md`. The remaining work is evidence production:
freeze model entries, run matched slices, summarize result tables, export
adjudication sheets, and regenerate the cockpit.

First-class scope:

- field-family evaluation contract;
- clinical adjudication protocol;
- fixed-slice experiment discipline;
- full-contract direct-prompt baseline;
- CLINES-inspired modular pipeline;
- anchor seizure-frequency reliability harnesses;
- canonical run records and result tables;
- compact static visibility cockpit.

Out of scope for the clean rebuild:

- the full Evidence Notebook;
- the Pipeline Observatory;
- generated dashboard payload churn;
- rejected harness implementations as maintained code paths;
- production-readiness claims from synthetic-only sensitivity runs.

## Repository Shape

Repository structure:

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

The implementation supports deterministic and ExECT-lite baselines, anchor
harnesses, direct full-contract and evidence-contract LLM harnesses,
retrieval-field extraction, CLINES-inspired modular and verified pipelines,
model-matrix runs, result tables, adjudication export/import, a generated
cockpit, harness manifests, event summaries, workflow-unit metadata, a
Clinical-Document Interface, verifier gates, budgeted escalation, and replayed
external harness adapters.

No run should be treated as dissertation-canonical merely because the harness
exists. Canonical evidence still requires frozen model entries, fixed matched
slices, generated tables, and adjudication where clinical correctness is
claimed.

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

The full-contract direct-prompt baseline uses the same replay mechanism:

```powershell
python scripts/run_experiment.py tests/fixtures/synthetic_subset_fixture.json --harness single_prompt_full_contract --limit 1 --replay path/to/replay.json --output results/runs/full_contract_replay.json
```

Generate result tables from one or more run records:

```powershell
python scripts/summarize_results.py results/runs/*.json --tables-dir results/tables --model-registry config/model_registry.2026-05-02.yaml
```

Build an adjudication sheet for matched outputs:

```powershell
python scripts/build_adjudication_sheet.py results/runs/run_a.json results/runs/run_b.json --output results/adjudication/matched_sheet.csv
```

Regenerate cockpit data:

```powershell
python scripts/build_cockpit_data.py --output site/cockpit-data.json
```

Harness manifests live under `config/harnesses/` and are loaded automatically
by harness name. They record the architecture family, allowed modules, prompt
and schema versions, context policy, output contract, repair/verifier/
aggregation policies, budget limits, gold-label isolation, and artifact
retention. A run record written through `run_experiment.py` or
`run_model_matrix.py` includes the manifest ID and SHA-256 hash; pass
`--manifest path/to/manifest.yaml` to override the default for a one-off run.
