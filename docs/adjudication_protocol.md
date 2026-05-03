# Clinical Adjudication Protocol

## Purpose

This protocol defines how model outputs should be judged clinically. The guiding
principle is conservative usefulness: reward clinically real, text-supported
information, but penalize unsupported diagnostic upgrades, wrong status, and
over-normalization.

## Scoring Unit

Score at the field-item level, not only at the row level.

For each emitted item, adjudicate:

- value correctness;
- status or temporality correctness;
- normalization correctness;
- evidence support;
- error tags where applicable.

For missing expected items, adjudicate recall when a reference annotation exists.

## Evidence Rule

A model output is fully supported only when its evidence span supports the
specific claimed value and its status or temporality. A non-empty quote is not
enough.

Examples:

- A medication list quote can support a current anti-seizure medication.
- "Previously tried carbamazepine" does not support current carbamazepine.
- "No epileptiform discharges" supports an EEG result, but not a normal EEG
  unless normality is explicitly stated.
- "No tonic-clonic seizures" does not support seizure-free overall if absence
  seizures continue.

## Seizure Frequency

Extract the current or most recent clinically relevant seizure frequency.

Full credit requires:

- correct frequency or seizure-free value;
- correct time window or anchor;
- correct seizure-type specificity where stated;
- no unsupported conversion from vague wording to precise rates;
- decisive evidence span.

Common errors:

- using historical frequency as current;
- collapsing type-specific seizure freedom into global seizure freedom;
- ignoring an explicit seizure-free statement;
- averaging clusters into over-precise monthly rates;
- missing the time anchor.

## Current Anti-Seizure Medications

Extract current maintenance anti-seizure medications, with dose if available and
required by the schema.

Full credit requires:

- correct medication entity;
- current or continued status;
- correct dose/status where schema requires it;
- exclusion of previous, stopped, avoided, allergy-only, and family-member
  medications;
- direct evidence from medication list, plan, or continuation statement.

Rescue medication should be separate when supported by the schema. If the schema
does not support rescue medication yet, mark it out of scope or partial rather
than treating it as current maintenance therapy.

## Investigations

Extract epilepsy-relevant investigations and monitoring:

- EEG, sleep-deprived EEG, ambulatory EEG, and video EEG;
- MRI;
- CT;
- genetic testing;
- blood monitoring, metabolic testing, ECG, and drug levels as `other` when
  relevant to seizure assessment or medication monitoring.

Important rules:

- Bloods, metabolic panels, TFTs, ECG, and drug levels must not normalize to
  `CT`.
- Normal EEG does not imply no epilepsy.
- No epileptiform discharges is not the same as a normal EEG unless stated.
- EEG slowing can be abnormal but non-specific or non-epileptiform.
- Conditional investigation plans are not firm planned investigations.

## Seizure Type, Semiology, And Pattern Modifiers

Separate these concepts:

- canonical seizure type;
- semiology feature;
- pattern modifier;
- epilepsy diagnosis/type.

Use the most specific defensible level:

1. explicit canonical seizure type;
2. strong semiology plus supported onset/awareness;
3. semiology feature without full seizure-type normalization;
4. pattern modifier only;
5. epilepsy diagnosis/type, not seizure type;
6. non-epileptic differential, unless separate epileptic-event wording exists.

Examples:

- "Focal impaired awareness seizures" is a seizure type.
- "Bilateral hand fumbling" is a semiology feature unless awareness/onset are
  supported.
- "Nocturnal clusters" is a pattern or frequency modifier.
- "Temporal lobe epilepsy" is epilepsy type/localization, not seizure type.

## Epilepsy Type And Syndrome

Extract disease-level formulations only when stated:

- focal epilepsy;
- generalized epilepsy;
- combined generalized and focal epilepsy;
- unknown epilepsy type;
- temporal lobe epilepsy or another localization;
- named syndrome, such as juvenile myoclonic epilepsy.

Preserve certainty:

- confirmed;
- probable/likely;
- possible/query;
- differential;
- negated.

Do not infer epilepsy type from medication choice, EEG slowing, MRI abnormality,
or semiology fragments alone.

## Error Tags

Use these tags for adjudication and failure analysis:

- `wrong_temporal_status`
- `unsupported_overclaim`
- `eeg_non_specific`
- `conditional_investigation`
- `investigation_type_confusion`
- `diagnosis_vs_seizure_type`
- `semiology_fragment`
- `pattern_modifier`
- `frequency_anchor_error`
- `medication_status_error`
- `missing_expected_item`
- `unsupported_evidence`
- `schema_valid_but_clinically_wrong`

## Adjudication Sheet Columns

Each adjudication sheet should include:

- row ID;
- harness ID;
- architecture family;
- model registry entry, where applicable;
- model/provider;
- field family;
- emitted value;
- reference value where available;
- value score;
- status/temporality score;
- normalization score;
- evidence grade;
- error tags;
- adjudicator note.

When available, include harness-native context as reviewer-facing metadata:

- manifest ID and manifest hash;
- event-summary counts, especially repairs, verifier passes, and escalation
  decisions;
- verifier-gate failures relevant to the emitted item;
- document-interface locator for the cited evidence;
- workflow-unit version that produced or verified the item.

These fields support auditability and reviewer navigation. They do not replace
human value, status, temporality, normalization, or evidence judgments.
Verifier-gate failures may suggest error tags, but the adjudicator remains
independent from model-generated or deterministic harness claims.

## Minimum Matched Slice

For final reporting, adjudicate a matched slice containing:

- seizure-frequency rows with varied temporal anchors;
- current medication examples with prior, stopped, and planned medication
  distractors;
- investigation examples with EEG, MRI, CT, bloods, ECG, and drug-level edge
  cases;
- seizure semiology and pattern-modifier examples;
- epilepsy type/syndrome examples with uncertainty language.

The same rows should be used across the architecture ladder whenever possible:
clinical NLP baselines, direct LLM baselines, retrieval-field pipelines,
CLINES-inspired modular pipelines, verifier variants, and model-family
sensitivity runs.
