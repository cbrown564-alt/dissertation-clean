# Comprehensive Implementation Plan

This plan builds from the repo's current contract-first state into a runnable
dissertation evidence pipeline.

## Phase 0: Repo Readiness

Goal: make the existing foundation easy to run and hard to accidentally break.

Tasks:

- Add a tiny committed fixture dataset under `tests/fixtures/`.
- Ensure `pytest` is available through a documented dev setup.
- Add `README` commands for install, test, smoke run, summarize run.
- Confirm all schema, data, and evaluation tests pass from a fresh checkout.
- Add a lightweight CI command or local `scripts/check.py` if desired.

Files likely touched:

- `README.md`
- `pyproject.toml`
- `tests/fixtures/*.json`
- `tests/test_*.py`

Acceptance criteria:

- A new developer can install dev dependencies and run tests.
- Existing smoke metadata run works against a fixture.
- No LLM/provider dependency is needed for tests.

## Phase 1: Foundation Hardening

Goal: strengthen the contract layer before adding harnesses.

Tasks:

- Add JSON serialization helpers for extraction payloads, not just run records.
- Add schema validation-style checks for required final payload keys.
- Add field coverage helper functions for full contract, partial contract, and
  failed components.
- Add parse-validity metric helpers for component validity rates.
- Make run-record `code_version` configurable from git commit when available.
- Add tests for payload serialization, coverage helpers, and run-record metadata.

Files likely touched:

- `src/epilepsy_extraction/schemas/extraction.py`
- `src/epilepsy_extraction/schemas/contracts.py`
- `src/epilepsy_extraction/schemas/runs.py`
- `tests/test_schemas.py`

Acceptance criteria:

- Every harness can emit the same payload shape.
- Missing, partial, and failed fields are represented consistently.
- Run records include reproducibility metadata in a standard place.

## Phase 2: Deterministic Baseline

Goal: create a reproducible floor that exercises the whole run path without
LLMs.

Tasks:

- Implement `deterministic_baseline` harness.
- Use simple rules against source letter text only. Gold labels must be reserved
  for evaluation and fixtures; a gold-derived plumbing check must never be
  reported as a benchmark.
- Emit valid `ExtractionPayload` rows.
- Emit `RunRecord` with dataset slice, budget metadata, parse validity, metrics,
  warnings, and row outputs.
- Add CLI support in `scripts/run_experiment.py` for selecting harnesses.

Files likely touched:

- `src/epilepsy_extraction/harnesses/deterministic.py`
- `src/epilepsy_extraction/harnesses/__init__.py`
- `scripts/run_experiment.py`
- `tests/test_harnesses.py`

Acceptance criteria:

- `python scripts/run_experiment.py dataset.json --harness deterministic_baseline --limit 5`
  writes a valid run record.
- The run has zero LLM calls and deterministic budget metadata.
- The run can be summarized by `scripts/summarize_results.py`.
- No benchmark path reads gold labels as input.

## Phase 3: Provider Abstraction

Goal: define the boundary between harness logic and model calls.

Tasks:

- Add provider protocol/interface for chat/completion requests.
- Define provider request, response, usage, latency, and error dataclasses.
- Add mock provider for tests.
- Add local JSON replay provider so old or captured outputs can be evaluated
  without calling an API.
- Add parse failure/recovery conventions.
- Keep closed-provider clients optional and outside core tests.

Files likely touched:

- `src/epilepsy_extraction/providers/base.py`
- `src/epilepsy_extraction/providers/mock.py`
- `src/epilepsy_extraction/providers/replay.py`
- `src/epilepsy_extraction/providers/__init__.py`
- `tests/test_providers.py`

Acceptance criteria:

- Harnesses can call a provider without knowing whether it is mock, replay,
  local, or closed.
- Token, call, and latency budget metadata flows into run records.
- Tests do not require network or secrets.

## Phase 4: Prompt And Schema Assets

Goal: make prompts versioned, inspectable, and tied to run records.

Tasks:

- Add prompt directories for anchor and full-contract harnesses.
- Add final output schema description or JSON schema-like contract.
- Add prompt version IDs.
- Add loader utilities for prompt files.
- Store prompt path/version in run records.

Suggested structure:

```text
prompts/
  anchor/
    single_prompt_v1.md
    multi_agent_v1/
  full_contract/
    single_prompt_v1.md
    multi_agent_v1/
schemas/
  final_extraction_v1.md or final_extraction_v1.json
```

Acceptance criteria:

- Every LLM run records prompt version and schema version.
- Prompt changes are reviewable as normal files.
- The same final schema is shared by single-prompt and multi-agent systems.

## Phase 5: Anchor Seizure-Frequency Harnesses

Goal: rebuild the compact reliability microcosm first.

Tasks:

- Implement `single_prompt_anchor`.
- Implement `multi_agent_anchor`.
- Implement self-consistency variants `multi_agent_anchor_sc3` and
  `multi_agent_anchor_sc5`.
- Reuse existing label parsing and metrics.
- Emit row-level predictions, evidence spans, confidence, warnings, and budget.
- Add replay/mock-provider tests for successful parse, invalid JSON, abstention,
  and unsupported evidence.
- Timebox this phase as an infrastructure exercise so seizure frequency does
  not crowd out the full-contract comparison.

Files likely touched:

- `src/epilepsy_extraction/harnesses/anchor.py`
- `src/epilepsy_extraction/evaluation/metrics.py`
- `scripts/run_experiment.py`
- `tests/test_anchor_harnesses.py`

Acceptance criteria:

- Anchor harnesses produce comparable run records.
- `summarize()` can generate anchor metrics from run rows.
- Self-consistency reports extra cost explicitly.

## Phase 6: Full-Contract Single-Prompt Baseline

Goal: create the main comparator.

Tasks:

- Implement `single_prompt_full_contract`.
- One provider call reads the letter and emits the final schema.
- Parse into `ExtractionPayload`.
- Validate field-family coverage and component parse validity.
- Preserve warnings, citations, confidence, invalid output state, and raw
  provider artifact.
- Add recovery policy for invalid/malformed output.

Files likely touched:

- `src/epilepsy_extraction/harnesses/full_contract_single.py`
- `src/epilepsy_extraction/schemas/extraction.py`
- `tests/test_full_contract_single.py`

Acceptance criteria:

- Emits the same final payload shape expected of the multi-agent pipeline.
- Records field coverage for all core families.
- Invalid output is measurable by component, not only globally.

## Phase 7: Role-Separated Multi-Agent Pipeline

Goal: implement the dissertation system.

Build roles in this order:

1. Section/timeline agent.
2. Field extractor agents.
3. Verification agent.
4. Aggregator agent.

The section/timeline agent emits sections, span IDs, candidate evidence spans,
temporal anchors, and warnings.

Field extractors should cover:

- Seizure frequency.
- Current medications.
- Investigations.
- Seizure type, semiology, and pattern modifiers.
- Epilepsy type and syndrome.

The verification agent grades support using `EvidenceGrade` and checks value,
status, temporality, and normalization. The aggregator merges verified outputs
into the final `ExtractionPayload` without inventing facts.

Files likely touched:

- `src/epilepsy_extraction/agents/section_timeline.py`
- `src/epilepsy_extraction/agents/field_extractors.py`
- `src/epilepsy_extraction/agents/verification.py`
- `src/epilepsy_extraction/agents/aggregation.py`
- `src/epilepsy_extraction/harnesses/full_contract_multi.py`
- `tests/test_agents.py`
- `tests/test_full_contract_multi.py`

Acceptance criteria:

- Multi-agent final schema matches single-prompt final schema.
- Intermediate artifacts are preserved in `artifacts`.
- Verifier grades more than quote presence.
- Aggregator does not create new clinical claims.

## Phase 8: Evaluation And Result Tables

Goal: turn runs into dissertation-ready evidence.

Tasks:

- Generate harness coverage table.
- Generate budget comparison table.
- Generate component parse-validity table.
- Generate evidence-support table.
- Generate field-level correctness/adjudication table skeletons.
- Generate seizure-frequency anchor table.
- Generate self-consistency cost table.
- Add CSV/JSON output under `results/tables/`.

Files likely touched:

- `scripts/summarize_results.py`
- `src/epilepsy_extraction/evaluation/tables.py`
- `tests/test_tables.py`

Acceptance criteria:

- Given one or more run records, scripts produce stable machine-readable tables.
- Tables follow the order in `docs/evaluation_contract.md`.
- Missing adjudication is explicit, not silently treated as zero.

## Phase 9: Adjudication Workflow

Goal: support matched clinical review without blending adjudication into model
output.

Tasks:

- Add adjudication sheet generator.
- Include row ID, harness, field family, emitted value, evidence, scores, error
  tags, and notes.
- Add adjudication importer.
- Add adjudication summary metrics.
- Keep adjudication files under `results/adjudication/`.

Files likely touched:

- `src/epilepsy_extraction/evaluation/adjudication.py`
- `scripts/build_adjudication_sheet.py`
- `scripts/summarize_adjudication.py`
- `tests/test_adjudication.py`

Acceptance criteria:

- Matched single-prompt vs multi-agent outputs can be exported for review.
- Completed adjudication can be re-imported.
- Error tags align with `docs/adjudication_protocol.md`.

## Phase 10: Generated Unified Cockpit

Goal: provide a compact, regularly regenerated visibility layer that preserves
the best qualities of the original unified document without recreating the old
dashboard sprawl.

The cockpit should be a beautiful supervisor/examiner-facing visual narrative,
not just a JSON dump. It should make the research arc legible at a glance:
harness evolution, decisions, branch detail, linked records, current claims,
uncertainties, timelines, example rows, and budget/performance tradeoffs.

Tasks:

- Expand `build_cockpit_data.py` into the source-backed data compiler for the
  cockpit.
- Generate `site/cockpit-data.json` from docs, run records, result tables,
  adjudication files, and decision notes.
- Add a small static `site/index.html` inspired by the original unified doc's
  editorial research-review style.
- Show research docs, run records, current canonical/supporting/archive runs,
  and table summaries.
- Include the core visual views that made the unified doc valuable: phase map,
  harness tradeoff surface, branch detail, linked decisions, session timeline,
  current-status claim panel, and source-letter/extracted-output example view.
- Keep it generated, data-driven, and minimal enough to maintain.
- Treat `site/cockpit-data.json` as generated output by default. Commit the
  generator and source artifacts; commit generated snapshots only when they are
  intentionally used as review/reproducibility artifacts.

Files likely touched:

- `scripts/build_cockpit_data.py`
- `site/index.html`
- `site/cockpit-data.json`

Acceptance criteria:

- Cockpit is regenerated by a documented command, not hand-maintained.
- Cockpit loads generated JSON and links every visible claim back to docs,
  run records, tables, adjudication, or decision notes.
- Cockpit captures the essence of the original unified review document:
  visually polished, source-backed, timeline-aware, and useful in supervision.
- It does not become a second source of truth.
- It only surfaces canonical/supporting/archive labels already present in run
  records.

## Recommended Build Order

1. Phase 0: repo readiness.
2. Phase 1: schema/run hardening.
3. Phase 2: deterministic baseline.
4. Phase 3: provider abstraction.
5. Phase 4: prompt and schema assets.
6. Phase 5: anchor harnesses.
7. Phase 6: full-contract single-prompt.
8. Phase 7: full-contract multi-agent.
9. Phase 8: result tables.
10. Phase 9: adjudication workflow.
11. Phase 10: cockpit.

The anchor harnesses should come before the full-contract systems. They are
smaller, they exercise provider calls and run metadata, and they expose the
awkward parts of parsing, invalid output handling, evidence spans, and budget
accounting before those problems get multiplied across all field families.
