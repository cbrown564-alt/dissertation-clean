import json

from epilepsy_extraction.modules.aggregation import aggregate_field_results
from epilepsy_extraction.modules.chunking import chunk_letter, select_chunks_for_family
from epilepsy_extraction.modules.field_extractors import extract_field_family
from epilepsy_extraction.modules.normalization import enrich_seizure_frequency, normalize_frequency
from epilepsy_extraction.modules.status_temporality import infer_status
from epilepsy_extraction.modules.verification import (
    apply_verifier_gate_policy,
    verifier_gate_summary,
    verify_evidence_deterministic,
    verify_field_extraction,
)
from epilepsy_extraction.modules.workflows import (
    aggregator_unit,
    field_extractor_unit,
    modular_workflow_units,
    verifier_unit,
)
from epilepsy_extraction.providers import MockProvider
from epilepsy_extraction.schemas.contracts import EvidenceGrade, FieldFamily


_LETTER = (
    "Seizure Frequency\n"
    "The patient is currently having two seizures per month.\n"
    "Medications\n"
    "She is taking lamotrigine 100 mg bd.\n"
    "Investigations\n"
    "MRI brain was normal. EEG showed generalised spike-wave.\n"
    "Assessment\n"
    "Focal epilepsy with focal to bilateral tonic-clonic seizures.\n"
    "Epilepsy syndrome: juvenile myoclonic epilepsy."
)


# --- Chunking ---

def test_chunk_letter_produces_chunks() -> None:
    chunks = chunk_letter(_LETTER)
    assert len(chunks) >= 1


def test_chunk_letter_section_names_preserved() -> None:
    chunks = chunk_letter(_LETTER)
    names = {c.source_section for c in chunks}
    assert any(n and "seizure" in n.lower() for n in names)


def test_chunk_letter_no_empty_chunks() -> None:
    chunks = chunk_letter(_LETTER)
    assert all(c.text.strip() for c in chunks)


def test_select_chunks_for_seizure_frequency() -> None:
    chunks = chunk_letter(_LETTER)
    selected, warnings = select_chunks_for_family(chunks, FieldFamily.SEIZURE_FREQUENCY)
    assert selected
    assert any("seizure" in c.text.lower() for c in selected)


def test_select_chunks_returns_at_most_max_chunks() -> None:
    chunks = chunk_letter(_LETTER)
    selected, _ = select_chunks_for_family(chunks, FieldFamily.CURRENT_MEDICATIONS, max_chunks=2)
    assert len(selected) <= 2


def test_select_chunks_uses_keyword_scoring_for_unsectioned_body() -> None:
    letter = (
        "This opening paragraph has administrative background only. "
        "There are no target medication terms here. "
        "Later she is taking lamotrigine 100 mg twice daily."
    )
    chunks = chunk_letter(letter, max_chunk_chars=70)

    selected, warnings = select_chunks_for_family(chunks, FieldFamily.CURRENT_MEDICATIONS, max_chunks=1)

    assert warnings == []
    assert len(selected) == 1
    assert "lamotrigine" in selected[0].text.lower()


def test_chunk_token_estimate_positive() -> None:
    chunks = chunk_letter(_LETTER)
    assert all(c.token_estimate > 0 for c in chunks)


# --- Status/temporality ---

def test_infer_status_current() -> None:
    ann = infer_status("The patient is currently seizure-free.")
    assert ann.status == "current"
    assert ann.confidence > 0.5


def test_infer_status_historical() -> None:
    ann = infer_status("She previously had focal seizures but these have resolved.")
    assert ann.status == "historical"


def test_infer_status_unknown() -> None:
    ann = infer_status("Generalised epilepsy.")
    assert ann.status == "unknown"


# --- Normalization ---

def test_normalize_frequency_monthly() -> None:
    result = normalize_frequency("2 times per month")
    assert result.unit == "per_month"
    assert result.monthly_rate == 2.0
    assert result.normalized is True


def test_normalize_frequency_daily() -> None:
    result = normalize_frequency("daily")
    assert result.monthly_rate == 30.0


def test_normalize_frequency_seizure_free() -> None:
    result = normalize_frequency("seizure-free for 12 months")
    assert result.unit == "seizure_free"
    assert result.monthly_rate == 0.0


def test_normalize_frequency_unknown() -> None:
    result = normalize_frequency("occasional")
    assert result.normalized is False
    assert result.monthly_rate is None


def test_enrich_seizure_frequency_adds_monthly_rate() -> None:
    data = {"value": "2 times per week", "confidence": 0.9}
    enriched = enrich_seizure_frequency(data)
    assert "monthly_rate" in enriched
    assert enriched["normalized"] is True


def test_enrich_seizure_frequency_empty_data() -> None:
    result = enrich_seizure_frequency({})
    assert isinstance(result, dict)


# --- Verification ---

def test_verify_exact_span() -> None:
    ctx = "Patient has two seizures per month."
    result = verify_evidence_deterministic("two seizures per month", "two seizures per month", ctx)
    assert result.grade == EvidenceGrade.EXACT_SPAN


def test_verify_overlapping_span() -> None:
    ctx = "She experiences approximately two seizures every month."
    result = verify_evidence_deterministic("two seizures per month", "two seizures per month", ctx)
    assert result.grade in (EvidenceGrade.EXACT_SPAN, EvidenceGrade.OVERLAPPING_SPAN, EvidenceGrade.SECTION_LEVEL)


def test_verify_missing_evidence_when_no_quote() -> None:
    result = verify_evidence_deterministic("two per month", None, "some context")
    assert result.grade == EvidenceGrade.MISSING_EVIDENCE


def test_verify_unsupported_when_not_in_context() -> None:
    result = verify_evidence_deterministic("ten seizures daily", "ten seizures daily", "no seizures here")
    assert result.grade == EvidenceGrade.UNSUPPORTED


def test_verify_field_extraction_returns_grade() -> None:
    field_data = {
        "seizure_frequency": {"value": "2 per month"},
        "citations": [{"quote": "two seizures per month"}],
    }
    ctx = "The patient has two seizures per month."
    artifact, results = verify_field_extraction(field_data, ctx)
    assert "grade" in artifact
    assert "verifier_gates" in artifact
    assert len(results) == 1


def test_verify_field_extraction_no_citations() -> None:
    field_data = {"seizure_frequency": {"value": "2 per month"}}
    artifact, results = verify_field_extraction(field_data, "context")
    assert artifact["grade"] == EvidenceGrade.MISSING_EVIDENCE.value
    assert results == []


def test_verifier_gate_summary_separates_support_dimensions() -> None:
    field_data = {
        "seizure_frequency": {"value": "2 per month", "monthly_rate": 2.0, "status": "current"},
        "citations": [{"field": "seizure_frequency", "quote": "two seizures per month"}],
    }
    summary = verifier_gate_summary(field_data, "The patient is currently having two seizures per month.")

    assert summary["gates"]["value_support"] is True
    assert summary["gates"]["status_support"] is True
    assert summary["gates"]["normalization_support"] is True
    assert summary["passed"] is True


def test_verifier_gate_policy_downgrades_unsupported_overclaim() -> None:
    field_data = {
        "seizure_frequency": {"value": "10 per day"},
        "citations": [{"field": "seizure_frequency", "quote": "not in context"}],
    }
    summary = verifier_gate_summary(field_data, "The patient is currently having two seizures per month.")
    downgraded, warnings = apply_verifier_gate_policy(field_data, summary)

    assert downgraded["unsupported_by_verifier"] is True
    assert any("value_support" in warning for warning in warnings)


# --- Field extraction parsing ---

def test_extract_field_family_promotes_nested_evidence_to_citations() -> None:
    provider = MockProvider([
        json.dumps(
            {
                "seizure_frequency": {
                    "value": "2 per month",
                    "evidence": "two seizures per month",
                    "status": "current",
                }
            }
        )
    ])
    schema = {
        "properties": {
            "seizure_frequency": {"type": "object"},
        }
    }

    result = extract_field_family(
        provider,
        "prompt",
        schema,
        FieldFamily.SEIZURE_FREQUENCY,
        "She has two seizures per month.",
        "mock-model",
        0.0,
    )

    assert result.valid is True
    assert result.data["citations"] == [
        {"field": "seizure_frequency", "quote": "two seizures per month"}
    ]


def test_extract_field_family_uses_schema_properties_for_target_schema() -> None:
    provider = MockProvider([json.dumps({"seizure_frequency": {}})])
    schema = {
        "properties": {
            "seizure_frequency": {"type": "object", "additionalProperties": False},
        }
    }

    extract_field_family(
        provider,
        "prompt",
        schema,
        FieldFamily.SEIZURE_FREQUENCY,
        "context",
        "mock-model",
        0.0,
    )

    content = provider.requests[0].messages[0].content
    assert '"seizure_frequency": {"additionalProperties": false, "type": "object"}' in content


def test_extract_field_family_empty_response_remains_invalid() -> None:
    provider = MockProvider([json.dumps({})])

    result = extract_field_family(
        provider,
        "prompt",
        {"properties": {}},
        FieldFamily.SEIZURE_FREQUENCY,
        "context",
        "mock-model",
        0.0,
    )

    assert result.valid is False


# --- Aggregation ---

def test_aggregate_field_results_produces_final_extraction() -> None:
    field_results = {
        FieldFamily.SEIZURE_FREQUENCY: {
            "seizure_frequency": {"value": "2 per month"},
            "citations": [{"quote": "two per month"}],
            "confidence": {"seizure_frequency": 0.9},
            "warnings": [],
        },
        FieldFamily.CURRENT_MEDICATIONS: {
            "current_medications": [{"name": "lamotrigine", "dose": "100 mg bd"}],
            "citations": [],
            "confidence": {},
            "warnings": [],
        },
        FieldFamily.INVESTIGATIONS: {"investigations": [], "citations": [], "confidence": {}, "warnings": []},
        FieldFamily.SEIZURE_CLASSIFICATION: {
            "seizure_types": [],
            "seizure_features": [],
            "seizure_pattern_modifiers": [],
            "citations": [],
            "confidence": {},
            "warnings": [],
        },
        FieldFamily.EPILEPSY_CLASSIFICATION: {
            "epilepsy_type": None,
            "epilepsy_syndrome": None,
            "citations": [],
            "confidence": {},
            "warnings": [],
        },
    }
    result = aggregate_field_results(field_results)
    assert result.final.seizure_frequency == {"value": "2 per month"}
    assert result.final.current_medications[0]["name"] == "lamotrigine"
    assert not result.any_invalid


def test_aggregate_marks_invalid_when_family_empty() -> None:
    field_results = {
        FieldFamily.SEIZURE_FREQUENCY: {},
        FieldFamily.CURRENT_MEDICATIONS: {"current_medications": [], "citations": [], "confidence": {}, "warnings": []},
        FieldFamily.INVESTIGATIONS: {"investigations": [], "citations": [], "confidence": {}, "warnings": []},
        FieldFamily.SEIZURE_CLASSIFICATION: {
            "seizure_types": [], "seizure_features": [], "seizure_pattern_modifiers": [],
            "citations": [], "confidence": {}, "warnings": [],
        },
        FieldFamily.EPILEPSY_CLASSIFICATION: {
            "epilepsy_type": None, "epilepsy_syndrome": None,
            "citations": [], "confidence": {}, "warnings": [],
        },
    }
    result = aggregate_field_results(field_results)
    assert result.any_invalid is True


def test_aggregate_citations_merged_across_families() -> None:
    field_results = {
        FieldFamily.SEIZURE_FREQUENCY: {
            "seizure_frequency": {"value": "2"},
            "citations": [{"quote": "A"}],
            "confidence": {}, "warnings": [],
        },
        FieldFamily.CURRENT_MEDICATIONS: {
            "current_medications": [],
            "citations": [{"quote": "B"}],
            "confidence": {}, "warnings": [],
        },
        FieldFamily.INVESTIGATIONS: {"investigations": [], "citations": [], "confidence": {}, "warnings": []},
        FieldFamily.SEIZURE_CLASSIFICATION: {
            "seizure_types": [], "seizure_features": [], "seizure_pattern_modifiers": [],
            "citations": [], "confidence": {}, "warnings": [],
        },
        FieldFamily.EPILEPSY_CLASSIFICATION: {
            "epilepsy_type": None, "epilepsy_syndrome": None,
            "citations": [], "confidence": {}, "warnings": [],
        },
    }
    result = aggregate_field_results(field_results)
    assert len(result.final.citations) == 2


# --- Workflow units ---

def test_field_extractor_workflow_unit_declares_contract() -> None:
    unit = field_extractor_unit(FieldFamily.SEIZURE_FREQUENCY)

    assert unit.unit_id.startswith("field_extractor.seizure_frequency@")
    assert "candidate_context" in unit.contract.inputs
    assert "field_payload" in unit.contract.outputs
    assert "may not read gold labels" in unit.contract.invariants


def test_modular_workflow_units_include_verifier_and_aggregator() -> None:
    units = modular_workflow_units(provider_verifier=True)
    names = {unit.name for unit in units}

    assert "provider_verifier" in names
    assert "schema_aggregator" in names
    assert len([unit for unit in units if unit.name == "field_extractor"]) >= 5


def test_aggregator_workflow_unit_bans_new_claims() -> None:
    unit = aggregator_unit()
    assert "aggregator must not invent missing clinical claims" in unit.contract.invariants


def test_verifier_workflow_unit_distinguishes_provider_backed() -> None:
    assert verifier_unit(provider_backed=False).name == "deterministic_verifier"
    assert verifier_unit(provider_backed=True).name == "provider_verifier"
