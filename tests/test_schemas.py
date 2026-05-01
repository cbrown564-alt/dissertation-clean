import json

from epilepsy_extraction.schemas import (
    CORE_FIELD_FAMILIES,
    BudgetMetadata,
    DatasetSlice,
    EvidenceGrade,
    ExtractionPayload,
    FieldCoverageStatus,
    FinalExtraction,
    RunRecord,
    SupportAssessment,
    write_run_record,
)


def test_support_assessment_full_credit_requires_exact_or_overlapping_span() -> None:
    assert SupportAssessment(EvidenceGrade.EXACT_SPAN).full_credit
    assert SupportAssessment(EvidenceGrade.OVERLAPPING_SPAN).full_credit
    assert not SupportAssessment(EvidenceGrade.SECTION_LEVEL).full_credit


def test_extraction_payload_defaults_to_not_implemented_coverage() -> None:
    payload = ExtractionPayload(
        pipeline_id="deterministic_baseline",
        final=FinalExtraction(),
    )

    assert payload.field_coverage["seizure_frequency"] == FieldCoverageStatus.NOT_IMPLEMENTED
    assert {field.value for field in CORE_FIELD_FAMILIES}.issubset(payload.field_coverage)


def test_write_run_record_creates_json(tmp_path) -> None:
    record = RunRecord(
        run_id="smoke",
        harness="deterministic_baseline",
        schema_version="1.0.0",
        dataset=DatasetSlice(
            dataset_id="synthetic_fixture",
            dataset_path="data/example.json",
            data_hash="abc123",
            row_ids=["1"],
            inclusion_criteria="fixture",
        ),
        model="none",
        provider="deterministic",
        temperature=0.0,
        prompt_version="none",
        code_version="test",
        budget=BudgetMetadata(),
    )

    output = write_run_record(record, tmp_path / "run.json")

    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["dataset"]["n"] == 1
    assert data["harness"] == "deterministic_baseline"
