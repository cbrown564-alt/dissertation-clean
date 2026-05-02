# System Architecture

## Purpose

The clean repo should implement a CLINES-inspired modular extraction framework
for epilepsy clinic letters, while retaining strong direct-prompt and clinical
NLP baselines. The architecture is training-free unless a later sensitivity
study explicitly introduces fine-tuning.

This is not a direct CLINES replication. CLINES code, exact prompts, and
evaluation scripts are not currently public. The repo should therefore describe
the main system as CLINES-inspired and document which design choices are taken
from the paper-level architecture.

## Architecture Families

The repo should support several architecture families behind a shared final
schema and evaluation contract.

| Family | Example harness | Purpose |
| --- | --- | --- |
| Clinical NLP baselines | `deterministic_baseline`, `exect_v2_external_baseline`, `exect_lite_cleanroom_baseline` | Establish reproducible non-LLM and epilepsy-specific floors. |
| Direct LLM baselines | `direct_full_contract`, `direct_evidence_contract` | Test strong full-letter prompting. |
| Retrieval-field pipeline | `retrieval_field_extractors` | Test candidate-span retrieval and field-specific local-context extraction. |
| CLINES-inspired modular pipeline | `clines_epilepsy_modular`, `clines_epilepsy_verified` | Test clinical modularization, normalization, temporality, evidence grading, and aggregation. |
| Costed reliability variants | `*_sc3`, `*_sc5`, model escalation, stronger verifier | Test reliability gains against added cost and latency. |

All LLM-based systems should emit the same final payload shape, so architecture
changes are evaluated without changing the target contract.

## High-Level Modular Flow

```text
clinic letter
  -> document normalization and sectioning
  -> semantic chunking / candidate-span retrieval
  -> field-specific extraction
  -> assertion, status, and temporality enrichment
  -> normalization and value/unit handling
  -> evidence grading and verification
  -> cross-chunk aggregation
  -> final JSON + artifacts + budget metadata
```

## Module 0: Document Normalization

Responsibilities:

- normalize line endings, whitespace, and document identifiers;
- preserve original character offsets where possible;
- detect obvious sections such as diagnosis, history, investigations,
  medications, impression, and plan;
- record letter-level dates and document metadata;
- avoid rewriting clinical text before extraction.

Output should include:

- normalized text;
- original-to-normalized offset mapping if available;
- section labels and span ranges;
- document metadata;
- warnings about missing or unusual structure.

## Module 1: Semantic Chunking And Candidate Retrieval

This module is inspired by CLINES' use of semantic chunking for long notes, but
adapted to epilepsy letters.

Responsibilities:

- split long letters into semantically coherent chunks;
- preserve section labels and letter-level date anchors in chunk metadata;
- optionally retrieve candidate spans for each field family;
- keep enough local context for temporality and negation;
- log chunk boundaries, token counts, and retrieval decisions.

Candidate span groups:

| Group | Typical signals |
| --- | --- |
| Seizure frequency | frequency phrases, seizure-free statements, last seizure, clusters, since-last-review phrases |
| Current medications | antiseizure medication names, dose, unit, frequency, planned changes |
| Investigations | EEG, MRI, CT, genetics, bloods, normal/abnormal/pending results |
| Seizure classification | focal/generalized/absence/tonic-clonic/myoclonic terms, semiology phrases |
| Epilepsy classification | epilepsy type, syndrome, diagnostic certainty |

Retrieval must be evaluated as a possible source of recall loss. Direct
full-letter baselines remain necessary.

## Module 2: Field-Specific Extraction

Field extractors read either the full letter, relevant chunks, or retrieved
candidate spans plus local context.

Recommended extractor groups:

| Extractor | Scope |
| --- | --- |
| Seizure frequency extractor | Current/recent seizure frequency, seizure freedom, most recent seizure anchor, ambiguity. |
| Medication extractor | Current anti-seizure medications, dose, unit, frequency, planned changes, rescue medication if supported. |
| Investigation extractor | EEG/MRI/CT/genetics/other investigations, result, status, temporality. |
| Seizure classification extractor | Seizure types, semiology features, pattern modifiers, certainty. |
| Epilepsy classification extractor | Epilepsy type, syndrome, cause if supported, diagnostic certainty. |

Each extractor should:

- emit structured JSON;
- cite evidence spans;
- preserve raw text values alongside normalized labels;
- abstain when unsupported;
- preserve uncertainty rather than forcing normalization;
- record parse validity and repair attempts.

## Module 3: Assertion, Status, And Temporality Enrichment

This module turns extracted mentions into clinical-status objects. It may be
implemented as part of each field extractor or as a separate enrichment pass.

Responsibilities:

- classify current, historical, planned, pending, absent, conditional, possible,
  and uncertain status;
- resolve explicit and relative time anchors where feasible;
- separate current seizure frequency from historical seizure burden;
- distinguish "no tonic-clonic seizures" from global seizure freedom;
- flag inferred dates or ambiguous temporal anchors;
- preserve item-level warnings.

The output should not force every field into a single numeric or categorical
target. It should expose the clinical qualification needed for adjudication.

## Module 4: Normalization And Value Handling

Responsibilities:

- normalize seizure-frequency categories only when source text supports them;
- perform deterministic numeric conversions only under explicit rules;
- normalize medication dose/unit/frequency strings where possible;
- normalize investigation results as normal, abnormal, pending, not stated, or
  uncertain;
- normalize epilepsy and seizure classifications to the chosen schema;
- optionally link concepts to UMLS/ILAE/SNOMED-like identifiers where licensing
  and implementation allow.

For CLINES-inspired UMLS-style normalization, use retrieval or terminology
lookup as an ablation rather than as a hidden assumption. If SapBERT or another
embedding model is used, log model ID, vocabulary source, ranking method, and
candidate list.

## Module 5: Evidence Verification

The verifier checks whether each extracted item is supported by source text. It
must verify support quality rather than checking only for a non-empty evidence
string.

Verifier checks:

- value support;
- status support;
- temporality support;
- normalization support;
- field-family placement;
- known epilepsy edge cases.

Verifier output should include:

- item-level evidence grade;
- warning text;
- error tags;
- suggested downgrade or removal policy;
- confidence adjustment.

Unsupported items should remain inspectable in artifacts even if excluded or
downgraded in the final output.

## Module 6: Aggregation And Schema Adaptation

The aggregator produces the final structured extraction payload.

Responsibilities:

- merge field extractor outputs across chunks;
- deduplicate repeated mentions;
- attach verifier grades and warnings;
- preserve citations;
- resolve conflicts conservatively;
- expose parse validity and field coverage;
- produce result shapes needed by downstream tables.

The aggregator must not invent new clinical facts. It only combines, labels,
downgrades, or excludes outputs from earlier stages.

## Final Payload Shape

Every extraction run should produce:

```json
{
  "pipeline_id": "clines_epilepsy_modular",
  "architecture_family": "clines_inspired_modular",
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
- `seizure_freedom`;
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

The `artifacts` object should include architecture-specific intermediate
outputs where available:

- `normalization`;
- `sections`;
- `chunks`;
- `candidate_spans`;
- `field_extractions`;
- `status_temporality`;
- `normalization_candidates`;
- `verification`;
- `aggregation`.

## Metadata Requirements

Required metadata:

- dataset ID;
- data hash;
- row ID;
- architecture family;
- harness ID;
- model registry entry ID;
- model;
- provider;
- inference backend;
- temperature and decoding settings;
- call budget;
- input tokens;
- output tokens;
- latency;
- estimated cost;
- prompt version;
- schema version;
- code version or commit hash;
- external baseline version or commit hash, where relevant.

## Baseline-Specific Notes

### ExECTv2 External Baseline

ExECTv2 has a public GATE repository and public synthetic validation data, but
the repository currently appears to have no explicit license. Treat it as an
external baseline unless licensing is clarified. Record the source repository,
commit hash, GATE version, input files, output mapping, and validation script
used.

### ExECT-Lite Clean-Room Baseline

If a local rule baseline is needed, implement it from published field
definitions and independently authored rules. Do not copy JAPE rules,
gazetteers, Groovy scripts, or other source logic from ExECTv2 into this repo
without permission.

### CLINES-Inspired Pipeline

Use CLINES as an architectural inspiration, not a replication. Record the paper
version and the public details used: semantic chunking, chunk-level extraction,
normalization, attribute/status/date enrichment, and aggregation.

## Acceptance Criteria

The architecture is implemented well enough when:

1. direct-prompt and modular systems emit the same final schema;
2. baseline outputs can be mapped into the evaluation contract;
3. modular runs expose inspectable artifacts for chunking, spans, extraction,
   status/temporality, normalization, verification, and aggregation;
4. verification grades evidence support beyond quote presence;
5. aggregation preserves warnings rather than hiding uncertainty;
6. run records contain budget, latency, token, cost, and reproducibility
   metadata;
7. evaluation can compare field-level correctness across architecture families,
   model families, and model size tiers.
