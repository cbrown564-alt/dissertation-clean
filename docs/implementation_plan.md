# Comprehensive Implementation Plan

This plan builds from the repo's current contract-first state into a runnable
dissertation evidence pipeline for the revised research question:

> How do CLINES-inspired modular architecture, clinical extraction baselines,
> and model capacity affect correctness, evidence support, auditability, cost,
> latency, token use, and harness complexity in epilepsy clinic-letter
> extraction?

The implementation should no longer optimize for a single binary comparison
between direct prompting and a role-separated system. It should build an
architecture ladder, map clinical NLP baselines, and support frozen model-family
experiments.

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

## Phase 1: Contract And Schema Hardening

Goal: strengthen the shared contract before adding baselines and harnesses.

Tasks:

- Add JSON serialization helpers for extraction payloads, not just run records.
- Add schema validation-style checks for required final payload keys.
- Add `architecture_family`, `model_registry_entry`, `complexity`, and
  `external_baseline` fields to run records.
- Add field coverage helpers for full contract, partial contract, unsupported
  fields, and `not_attempted` baseline fields.
- Add parse-validity metric helpers for component validity rates.
- Add helpers for evidence grades, field-family mapping, and literature-aligned
  field names.
- Make run-record `code_version` configurable from git commit when available.
- Add tests for payload serialization, coverage helpers, baseline mapping, and
  run-record metadata.

Files likely touched:

- `src/epilepsy_extraction/schemas/extraction.py`
- `src/epilepsy_extraction/schemas/contracts.py`
- `src/epilepsy_extraction/schemas/runs.py`
- `src/epilepsy_extraction/evaluation/mapping.py`
- `tests/test_schemas.py`
- `tests/test_evaluation_mapping.py`

Acceptance criteria:

- Every harness can emit the same payload shape or an explicitly mapped partial
  baseline payload.
- Missing, partial, failed, and not-attempted fields are represented
  consistently.
- Run records include reproducibility, model registry, architecture, budget,
  and complexity metadata in standard places.

## Phase 2: Model Registry And Provider Abstraction

Goal: define the boundary between harness logic and model calls, and make
model-family experiments reproducible.

Tasks:

- Add provider protocol/interface for chat/completion requests.
- Define provider request, response, usage, latency, cost, and error dataclasses.
- Add mock provider for tests.
- Add local JSON replay provider so old or captured outputs can be evaluated
  without calling an API.
- Add model registry loader and validator.
- Add candidate and frozen registry file locations.
- Add parse failure/recovery conventions.
- Keep closed-provider clients optional and outside core tests.

Files likely touched:

- `src/epilepsy_extraction/providers/base.py`
- `src/epilepsy_extraction/providers/mock.py`
- `src/epilepsy_extraction/providers/replay.py`
- `src/epilepsy_extraction/providers/__init__.py`
- `src/epilepsy_extraction/models/registry.py`
- `config/model_registry.candidate.yaml`
- `tests/test_providers.py`
- `tests/test_model_registry.py`

Acceptance criteria:

- Harnesses can call a provider without knowing whether it is mock, replay,
  local, or closed.
- Token, call, latency, and cost metadata flow into run records.
- A frozen model registry entry can be attached to a run.
- Tests do not require network or secrets.

## Phase 3: Prompt, Schema, And Mapping Assets

Goal: make prompts, output schemas, and baseline mapping rules versioned,
inspectable, and tied to run records.

Tasks:

- Add prompt directories for direct, evidence-contract, retrieval, and
  CLINES-inspired modular harnesses.
- Add final output schema description or JSON schema-like contract.
- Add baseline mapping specs for deterministic, ExECT-lite, and ExECTv2 outputs.
- Add prompt version IDs.
- Add loader utilities for prompt and mapping files.
- Store prompt path/version, schema version, and mapping version in run records.

Suggested structure:

```text
prompts/
  direct/
    full_contract_v1.md
    evidence_contract_v1.md
  retrieval/
    field_extractors_v1/
  clines_inspired/
    chunking_v1.md
    field_extractors_v1/
    verification_v1.md
schemas/
  final_extraction_v1.md or final_extraction_v1.json
mappings/
  exect_v2_mapping_v1.yaml
  exect_lite_mapping_v1.yaml
```

Acceptance criteria:

- Every LLM run records prompt version and schema version.
- Every external or partial baseline run records mapping version.
- Prompt and mapping changes are reviewable as normal files.
- Direct, retrieval, and modular systems share the same final schema.

## Phase 4: Clinical NLP Baselines

Goal: create reproducible floors and serious non-LLM comparators before LLM
architecture work.

Tasks:

- Implement `deterministic_baseline` harness.
- Implement `exect_lite_cleanroom_baseline` using independently authored rules
  based on published field definitions.
- Add an `exect_v2_external_baseline` adapter that can ingest ExECTv2 outputs
  when generated outside this repo.
- Document ExECTv2 setup assumptions, source repository, commit hash, GATE
  version, and licensing caveat.
- Ensure gold labels are reserved for evaluation and fixtures; no benchmark path
  may read gold labels as input.
- Emit valid mapped run records with `clinical_nlp_baseline` architecture
  family.

Files likely touched:

- `src/epilepsy_extraction/harnesses/deterministic.py`
- `src/epilepsy_extraction/harnesses/exect_lite.py`
- `src/epilepsy_extraction/harnesses/exect_v2_external.py`
- `src/epilepsy_extraction/harnesses/__init__.py`
- `scripts/run_experiment.py`
- `tests/test_baseline_harnesses.py`

Acceptance criteria:

- `python scripts/run_experiment.py dataset.json --harness deterministic_baseline --limit 5`
  writes a valid run record.
- ExECT-lite emits mapped partial/full outputs without copying ExECTv2 source
  logic.
- ExECTv2 external outputs can be mapped when available.
- Baseline field coverage distinguishes attempted, supported, and
  `not_attempted` fields.
- No benchmark path reads gold labels as input.

## Phase 5: Anchor Seizure-Frequency Harnesses ✓ COMPLETE

Goal: rebuild the compact reliability microcosm around the new architecture
ladder.

Tasks:

- Implement `direct_anchor`.
- Implement `retrieval_anchor`.
- Implement a separable CLINES-style anchor if useful.
- Implement self-consistency variants `anchor_sc3` and `anchor_sc5`.
- Reuse existing label parsing and metrics.
- Emit row-level predictions, evidence spans, confidence, warnings, and budget.
- Add replay/mock-provider tests for successful parse, invalid JSON, abstention,
  unsupported evidence, and retrieval recall loss.
- Timebox this phase as an infrastructure exercise so seizure frequency does
  not crowd out the full-contract architecture ladder.

Files likely touched:

- `src/epilepsy_extraction/harnesses/anchor.py`
- `src/epilepsy_extraction/retrieval/candidates.py`
- `src/epilepsy_extraction/evaluation/metrics.py`
- `scripts/run_experiment.py`
- `tests/test_anchor_harnesses.py`

Acceptance criteria:

- Anchor harnesses produce comparable run records.
- `summarize()` can generate anchor metrics from run rows.
- Self-consistency reports extra cost explicitly.
- Retrieval failures are visible as retrieval recall or candidate-span warnings.

## Phase 6: Direct Full-Contract LLM Baselines ✓ COMPLETE

Goal: create strong direct-prompt comparators.

Tasks:

- Implement `direct_full_contract`.
- Implement `direct_evidence_contract`.
- One provider call reads the letter and emits the final schema.
- Parse into `ExtractionPayload`.
- Validate field-family coverage and component parse validity.
- Preserve warnings, citations, confidence, invalid output state, and raw
  provider artifact.
- Add recovery policy for invalid/malformed output.

Files likely touched:

- `src/epilepsy_extraction/harnesses/direct_full_contract.py`
- `src/epilepsy_extraction/schemas/extraction.py`
- `tests/test_direct_full_contract.py`

Acceptance criteria:

- Direct harnesses emit the same final payload shape expected of retrieval and
  modular pipelines.
- Records field coverage for all core families.
- Invalid output is measurable by component, not only globally.
- Evidence-contract behavior is separately measurable from direct prompting.

## Phase 7: Retrieval-Plus-Field Extraction ✓ COMPLETE

Goal: test whether candidate-span selection and local-context extraction improve
output quality before the full modular pipeline.

Tasks:

- Implement document normalization and basic section detection.
- Implement candidate-span retrieval grouped by field family.
- Implement field-specific extractors over candidate spans plus local context.
- Preserve candidate-span artifacts, token counts, and retrieval warnings.
- Add recall-loss error tags when retrieved context appears insufficient.
- Aggregate field outputs into the shared final payload.

Files likely touched:

- `src/epilepsy_extraction/document/normalization.py`
- `src/epilepsy_extraction/document/sections.py`
- `src/epilepsy_extraction/retrieval/candidates.py`
- `src/epilepsy_extraction/harnesses/retrieval_field_extractors.py`
- `tests/test_retrieval.py`
- `tests/test_retrieval_field_extractors.py`

Acceptance criteria:

- Retrieval artifacts are preserved in `artifacts`.
- Field extractors emit schema-valid outputs using the shared final schema.
- Retrieval can be compared against direct prompting on matched rows.
- Candidate-span recall failures are observable and not collapsed into generic
  wrong-answer errors.

## Phase 8: CLINES-Inspired Modular Pipeline ✓ COMPLETE

Goal: implement the main revised architecture as a clinical modular pipeline,
not as a claimed CLINES replication.

Build modules in this order:

1. Document normalization and sectioning.
2. Semantic chunking and candidate-span retrieval.
3. Field-specific extraction.
4. Assertion, status, and temporality enrichment.
5. Normalization and value/unit handling.
6. Evidence verification.
7. Cross-chunk aggregation and schema adaptation.

Field extractors should cover:

- Seizure frequency and seizure freedom.
- Current medications.
- Investigations.
- Seizure type, semiology, and pattern modifiers.
- Epilepsy type and syndrome.

Files likely touched:

- `src/epilepsy_extraction/modules/chunking.py`
- `src/epilepsy_extraction/modules/field_extractors.py`
- `src/epilepsy_extraction/modules/status_temporality.py`
- `src/epilepsy_extraction/modules/normalization.py`
- `src/epilepsy_extraction/modules/verification.py`
- `src/epilepsy_extraction/modules/aggregation.py`
- `src/epilepsy_extraction/harnesses/clines_epilepsy_modular.py`
- `src/epilepsy_extraction/harnesses/clines_epilepsy_verified.py`
- `tests/test_modules.py`
- `tests/test_clines_epilepsy_modular.py`

Acceptance criteria:

- Modular final schema matches direct-prompt final schema.
- Intermediate artifacts are preserved for chunking, candidate spans,
  extraction, status/temporality, normalization, verification, and aggregation.
- Verifier grades more than quote presence.
- Aggregator does not create new clinical claims.
- The run record clearly labels this as `clines_inspired_modular`, not CLINES
  replication.

## Phase 9: Evaluation And Result Tables

Goal: turn runs into dissertation-ready evidence under the revised evaluation
contract.

Tasks:

- Generate architecture and harness coverage table.
- Generate baseline comparability table.
- Generate model registry table.
- Generate budget, latency, token, and complexity table.
- Generate component parse-validity table.
- Generate field-level correctness/adjudication table skeletons.
- Generate evidence-support table.
- Generate architecture ablation table.
- Generate model-family and model-tier table.
- Generate seizure-frequency anchor table.
- Generate self-consistency cost table.
- Add CSV/JSON output under `results/tables/`.

Files likely touched:

- `scripts/summarize_results.py`
- `src/epilepsy_extraction/evaluation/tables.py`
- `src/epilepsy_extraction/evaluation/metrics.py`
- `tests/test_tables.py`

Acceptance criteria:

- Given one or more run records, scripts produce stable machine-readable tables.
- Tables follow the order in `docs/evaluation_contract.md`.
- Missing adjudication is explicit, not silently treated as zero.
- Architecture deltas can be computed on matched rows where available.

## Phase 10: Adjudication Workflow

Goal: support matched clinical review without blending adjudication into model
output.

Tasks:

- Add adjudication sheet generator.
- Include row ID, harness, architecture family, model registry entry, field
  family, emitted value, evidence, scores, error tags, and notes.
- Add adjudication importer.
- Add adjudication summary metrics.
- Keep adjudication files under `results/adjudication/`.
- Align error tags with `docs/evaluation_contract.md` and
  `docs/adjudication_protocol.md`.

Files likely touched:

- `src/epilepsy_extraction/evaluation/adjudication.py`
- `scripts/build_adjudication_sheet.py`
- `scripts/summarize_adjudication.py`
- `tests/test_adjudication.py`

Acceptance criteria:

- Matched architecture-ladder outputs can be exported for review.
- Completed adjudication can be re-imported.
- Error tags distinguish wrong value, wrong status, wrong temporality, wrong
  normalization, unsupported evidence, retrieval recall loss, aggregation
  conflict, and baseline mapping error.

## Phase 11: Model-Family Sensitivity Runs

Goal: evaluate whether architecture benefits change across open and closed
model families and model-size tiers.

Tasks:

- Freeze `config/model_registry.YYYY-MM-DD.yaml`.
- Run anchor smoke tests across candidate model entries.
- Select bounded small/medium/frontier model sets.
- Run selected architecture rungs across frozen model entries.
- Report model-family metrics, token use, cost, latency, parse stability, and
  evidence-supported correctness.
- Keep closed-provider and frontier runs bounded, especially on synthetic data.

Files likely touched:

- `config/model_registry.YYYY-MM-DD.yaml`
- `scripts/run_model_matrix.py`
- `scripts/summarize_results.py`
- `results/runs/*`
- `results/tables/model_family*.csv`

Acceptance criteria:

- Every canonical model run references a frozen registry entry.
- Results can compare model family, tier, architecture, budget, and evidence
  support.
- Moving aliases such as "latest" are not used in canonical result tables.
- Closed-provider sensitivity runs are clearly labelled and bounded.

## Phase 12: Generated Unified Cockpit

Goal: provide a compact, regularly regenerated visibility layer that preserves
the best qualities of the original unified document without recreating the old
dashboard sprawl.

The cockpit should be a supervisor/examiner-facing visual narrative, not just a
JSON dump. It should make the research arc legible at a glance: architecture
ladder, baselines, model registry, decisions, linked records, current claims,
uncertainties, timelines, example rows, and budget/performance tradeoffs.

Design reference screenshots and notes from the previous unified simplified
view are preserved in `docs/visibility_cockpit_reference/`. They should inspire
the interaction model and information hierarchy, while the clean repo rebuilds
the content model around benchmark comparison, wider field coverage, evidence
support, adjudication, and model registry governance.

Tasks:

- Expand `build_cockpit_data.py` into the source-backed data compiler for the
  cockpit.
- Generate `site/cockpit-data.json` from docs, run records, result tables,
  adjudication files, and decision notes.
- Add a small static `site/index.html` inspired by the original unified doc's
  editorial research-review style.
- Show research docs, run records, current canonical/supporting/archive runs,
  table summaries, and model registry snapshots.
- Include core visual views: architecture ladder, harness tradeoff surface,
  baseline comparability, model-family matrix, branch detail, linked decisions,
  session timeline, current-status claim panel, and source-letter/extracted
  output example view.
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
  run records, tables, adjudication, model registry entries, or decision notes.
- It does not become a second source of truth.
- It only surfaces canonical/supporting/archive labels already present in run
  records.

## Recommended Build Order

1. Phase 0: repo readiness.
2. Phase 1: contract and schema hardening.
3. Phase 2: model registry and provider abstraction.
4. Phase 3: prompt, schema, and mapping assets.
5. Phase 4: clinical NLP baselines.
6. Phase 5: anchor seizure-frequency harnesses.
7. Phase 6: direct full-contract LLM baselines.
8. Phase 7: retrieval-plus-field extraction.
9. Phase 8: CLINES-inspired modular pipeline.
10. Phase 9: evaluation and result tables.
11. Phase 10: adjudication workflow.
12. Phase 11: model-family sensitivity runs.
13. Phase 12: cockpit.

The anchor harnesses still come before the full-contract systems. They are
smaller, they exercise provider calls and run metadata, and they expose the
awkward parts of parsing, invalid output handling, evidence spans, retrieval,
and budget accounting before those problems get multiplied across all field
families. Clinical NLP baselines should also come early so the project does not
accidentally optimize only against LLM comparators.
