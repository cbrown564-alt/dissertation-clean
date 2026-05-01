# System Architecture

## Purpose

The clean repo implements the original research architecture directly: a
training-free extraction system that compares a full-contract single-prompt
baseline with a role-separated multi-agent pipeline.

## High-Level Flow

```text
clinic letter
  -> section/timeline agent
  -> field extractor agents
  -> verification agent
  -> aggregator agent
  -> final JSON + confidence + citations + warnings
```

## Baseline: Full-Contract Single Prompt

The baseline is one LLM call that reads the letter and emits the full final
schema.

Requirements:

- same final schema as the multi-agent pipeline;
- evidence spans required;
- parse failures and recovery logged;
- component validity metrics emitted;
- call/token budget emitted.

This is the main comparator for the research question.

## Role 1: Section And Timeline Agent

Responsibilities:

- segment the letter into clinically meaningful sections;
- identify sentence or span offsets;
- extract candidate spans relevant to seizure history, medications,
  investigations, diagnosis, and plan;
- identify dates, time anchors, and temporal expressions;
- produce a lightweight event timeline.

This role should be deterministic where possible. It is not expected to solve
the extraction task alone.

Output should include:

- section labels;
- sentence/span IDs;
- candidate spans grouped by field family;
- timeline events;
- warnings for missing or unusual structure.

## Role 2: Field Extractor Agents

Recommended first extractor groups:

| Extractor | Scope |
| --- | --- |
| Seizure frequency extractor | Current/recent seizure frequency, seizure freedom, most recent seizure anchor. |
| Medication extractor | Current anti-seizure medications, planned changes, rescue medication if supported. |
| Investigation extractor | EEG/MRI/CT/genetics/other investigations, result, status. |
| Seizure classification extractor | Seizure types, semiology features, pattern modifiers. |
| Epilepsy classification extractor | Epilepsy type, syndrome, certainty. |

Each extractor should:

- receive the full letter plus relevant candidate spans, or a controlled subset
  of the letter;
- emit structured JSON;
- cite evidence spans;
- abstain when unsupported;
- preserve uncertainty rather than forcing normalization.

## Role 3: Verification Agent

The verifier checks whether each extracted item is supported by source text. It
must verify support quality rather than checking only for a non-empty evidence
string.

Verifier checks:

- value support;
- status/temporality support;
- normalization support;
- field-family placement;
- known clinical edge cases.

Verifier output should include:

- item-level support grade;
- warning text;
- error tags;
- suggested downgrade or removal policy;
- confidence adjustment.

Unsupported items should remain inspectable in role artifacts even if excluded
or downgraded in the final output.

## Role 4: Aggregator Agent

The aggregator produces the final structured extraction payload.

Responsibilities:

- merge field extractor outputs;
- attach verifier grades and warnings;
- resolve duplicates;
- produce final confidence values;
- preserve citations;
- expose parse validity and field coverage.

The aggregator must not invent new clinical facts. It only combines and labels
outputs from earlier stages.

## Final Payload Shape

Every extraction run should produce:

```json
{
  "pipeline_id": "multi_agent_full_contract",
  "schema_version": "1.0.0",
  "field_coverage": {},
  "final": {},
  "artifacts": {},
  "invalid_output": false,
  "warnings": [],
  "metadata": {}
}
```

The `final` object should include:

- `seizure_frequency`;
- `current_medications`;
- `investigations`;
- `seizure_types`;
- `seizure_features`;
- `seizure_pattern_modifiers`;
- `epilepsy_type`;
- `epilepsy_syndrome`;
- `citations`;
- `confidence`;
- `warnings`.

## Metadata Requirements

Required metadata:

- dataset ID;
- data hash;
- row ID;
- model;
- provider;
- temperature;
- call budget;
- input tokens;
- output tokens;
- latency;
- prompt version;
- schema version;
- code version.

## Acceptance Criteria

The architecture is implemented well enough when:

1. single-prompt and multi-agent systems emit the same final schema;
2. multi-agent runs expose inspectable role artifacts;
3. verification grades evidence support beyond quote presence;
4. aggregation preserves warnings rather than hiding uncertainty;
5. run records contain budget and reproducibility metadata;
6. evaluation can compare field-level correctness across harnesses.
