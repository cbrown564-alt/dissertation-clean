# Model Registry Protocol

## Purpose

The dissertation should evaluate contemporary open and closed models, including
recent releases from families such as Qwen, Llama, Gemma, Phi, DeepSeek, GPT,
and Claude. Because model availability, aliases, pricing, and context windows
change quickly, canonical experiments must use frozen model registry entries
rather than vague "latest model" labels.

This protocol defines how to select, freeze, document, and report model
snapshots.

## Registry Principle

Use model families and tiers during proposal design. Use exact model IDs during
experiments.

Proposal language can say:

> We evaluate latest available model snapshots from selected open and closed
> model families, frozen before canonical runs.

Canonical results must say:

> We evaluated `provider/model-id` as listed in registry snapshot
> `model_registry_YYYY-MM-DD.yaml`.

## Model Families

Initial family set:

| Category | Families | Rationale |
| --- | --- | --- |
| Open or open-weight | Qwen, Llama, Gemma, Phi, DeepSeek | Covers major accessible model families with different sizes, licenses, and deployment profiles. |
| Closed frontier | GPT, Claude | Provides high-capacity proprietary comparators. |
| Optional closed or hosted | Gemini, Mistral, hosted open models | Include only if access, pricing, and governance are practical. |

Family inclusion should be justified by availability, clinical extraction
relevance, cost, context window, and ability to run under the evaluation
contract.

## Size And Capacity Tiers

Use tiers to make model comparisons interpretable.

| Tier | Typical role | Examples of metadata to capture |
| --- | --- | --- |
| Small / cheap | Low-cost extraction and local/privacy-sensitive settings | parameter count, quantization, hardware, throughput |
| Medium | Practical quality/cost tradeoff | context window, cost per supported extraction, parse stability |
| Large / frontier | Upper-bound quality and architecture sensitivity | pricing, latency, governance constraints, token efficiency |

Exact thresholds can vary by family. For mixture-of-experts models, record total
parameters and active parameters where known.

## Freeze Process

Before canonical experiments:

1. Set a model-freeze date.
2. Search official provider documentation, model cards, and repository pages.
3. Select exact model IDs for each family/tier.
4. Record pricing, context window, access route, and deprecation status.
5. Run a one-row smoke test for schema compatibility.
6. Save a registry snapshot.
7. Do not change canonical model entries unless a model becomes unavailable or a
   serious configuration error is discovered.

If a model changes behind a moving alias, either pin a dated snapshot or record
the alias resolution date and provider documentation.

## Implemented Registry Entry Schema

The current loader in `src/epilepsy_extraction/models/registry.py` expects a
compact schema:

```yaml
registry_version: "0.1"
created: "YYYY-MM-DD"
frozen_at: "YYYY-MM-DD"  # blank only for candidate registries

models:
  - model_id: exact-provider-or-repo-model-id
    display_name: Human-readable model name
    provider: provider-name
    family: model-family
    tier: frontier | medium | small | open_frontier | open_medium | open_small
    context_window: 128000
    cost_per_1k_input: 0.0
    cost_per_1k_output: 0.0
    notes: ""
```

Required keys are `model_id`, `display_name`, `provider`, `family`, `tier`,
and `context_window`. Candidate and frozen registries should use this schema so
`scripts/run_model_matrix.py` and result-table generation can load them without
extra dependencies.

## Extended Metadata To Preserve In Notes Or Future Schema

When producing dissertation evidence, preserve the following information either
in `notes`, a companion registry source note, or a future schema extension:

```yaml
- access route: local, hosted API, provider API;
- release date or model-card snapshot date;
- input and output modalities;
- total and active parameters, where known;
- quantization and inference backend for local/open runs;
- hardware;
- pricing source URL and checked date;
- decoding defaults such as temperature, top-p, max output tokens, and
  reasoning effort;
- governance notes;
- source URLs;
- status: candidate, canonical, deprecated, or unavailable.

## Decoding Settings

Clinical extraction should default to deterministic or near-deterministic
settings:

- temperature `0` or the provider's closest deterministic setting;
- fixed maximum output tokens;
- fixed reasoning effort where providers expose it;
- no hidden prompt changes between architecture conditions;
- no provider-side web browsing or tools unless explicitly part of the harness.

If a provider does not support deterministic decoding, record the closest
available settings.

## Cost Reporting

Every canonical run should compute:

- input tokens;
- output tokens;
- total tokens;
- estimated API cost;
- local inference runtime cost proxy if available;
- latency;
- cost per row;
- cost per valid extraction;
- cost per evidence-supported extraction;
- cost per correctly adjudicated field item.

For local models, report hardware and throughput even if dollar cost is not
estimated.

## Model Availability And Deprecation

If a model is deprecated after canonical runs, keep the result and mark the
entry as deprecated. Do not silently rerun with a successor model.

If a model disappears before canonical runs, replace it through a documented
registry update:

- old entry ID;
- reason for removal;
- replacement entry ID;
- date;
- source evidence.

## Open Versus Closed Interpretation

Closed frontier models may establish an upper-bound performance estimate, but
they do not automatically define the best clinical system. Interpret results
against:

- governance constraints;
- data-sharing restrictions;
- cost;
- latency;
- reproducibility;
- ability to run locally;
- robustness under exact evidence requirements.

Open models may be less accurate in direct prompting but more attractive if
they become competitive under retrieval, verification, and modular extraction.

## Reporting Rules

Dissertation tables should report:

- family;
- exact model ID;
- tier;
- provider/backend;
- context window;
- cost per million input/output tokens or local hardware;
- mean calls per row;
- mean tokens per row;
- mean latency per row;
- parse validity;
- evidence-supported correctness;
- field-family metrics.

Avoid reporting only "GPT", "Claude", "Qwen", or "latest model" in results.

## Suggested Files

Use:

- `config/model_registry.candidate.yaml` for scouting;
- `config/model_registry.YYYY-MM-DD.yaml` for frozen canonical entries;
- run-record `model_registry_entry` fields plus the registry snapshot path used
  for result-table generation;
- `docs/model_registry_protocol.md` as the method description.
