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

## Registry Entry Schema

Each model entry should include:

```yaml
- id: qwen_medium_YYYYMMDD
  family: Qwen
  tier: medium
  model_id: provider-or-repo/model-name
  provider: provider-name
  access_route: local | hosted_api | provider_api
  release_date: YYYY-MM-DD
  freeze_date: YYYY-MM-DD
  context_window_tokens: 0
  input_modalities: [text]
  output_modalities: [text]
  parameters_total: null
  parameters_active: null
  quantization: null
  inference_backend: vllm | llama_cpp | ollama | provider_api | other
  hardware: null
  pricing:
    input_per_million_tokens_usd: null
    output_per_million_tokens_usd: null
    source_url: null
    checked_date: YYYY-MM-DD
  decoding_defaults:
    temperature: 0
    top_p: null
    max_output_tokens: null
    reasoning_effort: null
  governance_notes: ""
  source_urls: []
  status: candidate | canonical | deprecated | unavailable
```

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
- `runs/*/model_registry_snapshot.yaml` copied into run artifacts;
- `docs/model_registry_protocol.md` as the method description.
