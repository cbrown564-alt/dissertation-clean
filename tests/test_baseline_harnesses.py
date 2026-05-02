from pathlib import Path

from epilepsy_extraction.data import compute_file_sha256, load_synthetic_subset, select_fixed_slice
from epilepsy_extraction.harnesses import (
    run_exect_lite_baseline,
    run_exect_v2_external_baseline,
)
from epilepsy_extraction.schemas import DatasetSlice
from epilepsy_extraction.schemas.contracts import ArchitectureFamily, FieldCoverageStatus


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "synthetic_subset_fixture.json"


def _fixture_dataset(records) -> DatasetSlice:
    return DatasetSlice(
        dataset_id="fixture",
        dataset_path=str(FIXTURE_PATH),
        data_hash=compute_file_sha256(FIXTURE_PATH),
        row_ids=[r.row_id for r in records],
        inclusion_criteria="fixture",
    )


# ── ExECT-lite ────────────────────────────────────────────────────────────────

def test_exect_lite_run_record_has_correct_harness_name() -> None:
    records = select_fixed_slice(load_synthetic_subset(FIXTURE_PATH), limit=2)
    run = run_exect_lite_baseline(records, _fixture_dataset(records), "exect_lite_test", "test")
    assert run.harness == "exect_lite_cleanroom_baseline"


def test_exect_lite_run_record_declares_clinical_nlp_baseline_family() -> None:
    records = select_fixed_slice(load_synthetic_subset(FIXTURE_PATH), limit=2)
    run = run_exect_lite_baseline(records, _fixture_dataset(records), "exect_lite_test", "test")
    assert run.architecture_family == ArchitectureFamily.CLINICAL_NLP_BASELINE.value


def test_exect_lite_run_record_has_mapping_version() -> None:
    records = select_fixed_slice(load_synthetic_subset(FIXTURE_PATH), limit=2)
    run = run_exect_lite_baseline(records, _fixture_dataset(records), "exect_lite_test", "test")
    assert run.mapping_version.startswith("exect_lite")


def test_exect_lite_seizure_frequency_is_implemented_in_coverage() -> None:
    records = select_fixed_slice(load_synthetic_subset(FIXTURE_PATH), limit=2)
    run = run_exect_lite_baseline(records, _fixture_dataset(records), "exect_lite_test", "test")
    assert run.field_coverage["seizure_frequency"] == FieldCoverageStatus.IMPLEMENTED.value


def test_exect_lite_unsupported_fields_are_not_attempted() -> None:
    records = select_fixed_slice(load_synthetic_subset(FIXTURE_PATH), limit=2)
    run = run_exect_lite_baseline(records, _fixture_dataset(records), "exect_lite_test", "test")
    assert run.field_coverage["rescue_medication"] == FieldCoverageStatus.NOT_ATTEMPTED.value
    assert run.field_coverage["comorbidities"] == FieldCoverageStatus.NOT_ATTEMPTED.value


def test_exect_lite_run_has_rows_and_parse_validity() -> None:
    records = select_fixed_slice(load_synthetic_subset(FIXTURE_PATH), limit=2)
    run = run_exect_lite_baseline(records, _fixture_dataset(records), "exect_lite_test", "test")
    assert len(run.rows) == 2
    assert "seizure_frequency" in run.parse_validity


def test_exect_lite_payload_has_required_final_keys() -> None:
    from epilepsy_extraction.schemas import FINAL_EXTRACTION_REQUIRED_KEYS
    records = select_fixed_slice(load_synthetic_subset(FIXTURE_PATH), limit=2)
    run = run_exect_lite_baseline(records, _fixture_dataset(records), "exect_lite_test", "test")
    for row in run.rows:
        final_keys = set(row["payload"]["final"].keys())
        assert set(FINAL_EXTRACTION_REQUIRED_KEYS).issubset(final_keys)


def test_exect_lite_extracts_medication_from_fixture_letter() -> None:
    from epilepsy_extraction.harnesses.exect_lite import _extract_medications
    meds = _extract_medications("Current medication is lamotrigine 100 mg twice daily and levetiracetam 500 mg.")
    names = [m["name"].lower() for m in meds]
    assert "lamotrigine" in names
    assert "levetiracetam" in names


def test_exect_lite_extracts_tonic_clonic_seizure_type() -> None:
    from epilepsy_extraction.harnesses.exect_lite import _extract_seizure_types
    types = _extract_seizure_types("He has tonic-clonic seizures and absence episodes.")
    labels = [t["type"] for t in types]
    assert "tonic-clonic" in labels
    assert "absence" in labels


def test_exect_lite_budget_has_zero_llm_calls() -> None:
    records = select_fixed_slice(load_synthetic_subset(FIXTURE_PATH), limit=2)
    run = run_exect_lite_baseline(records, _fixture_dataset(records), "exect_lite_test", "test")
    assert run.budget.llm_calls_per_row == 0


# ── ExECTv2 external adapter ──────────────────────────────────────────────────

def _mock_exect_v2_outputs(records) -> dict[str, dict]:
    return {
        record.row_id: {
            "row_id": record.row_id,
            "SeizureFrequency": "2 per month",
            "Medication": [{"name": "lamotrigine"}],
            "Investigation": [{"type": "EEG"}],
            "SeizureType": ["focal"],
            "EpilepsyType": "focal epilepsy",
        }
        for record in records
    }


def test_exect_v2_external_run_has_correct_harness_name() -> None:
    records = select_fixed_slice(load_synthetic_subset(FIXTURE_PATH), limit=2)
    outputs = _mock_exect_v2_outputs(records)
    run = run_exect_v2_external_baseline(
        records, _fixture_dataset(records), "exect_v2_test", "test", outputs
    )
    assert run.harness == "exect_v2_external_baseline"


def test_exect_v2_external_declares_external_baseline_flag() -> None:
    records = select_fixed_slice(load_synthetic_subset(FIXTURE_PATH), limit=2)
    outputs = _mock_exect_v2_outputs(records)
    run = run_exect_v2_external_baseline(
        records, _fixture_dataset(records), "exect_v2_test", "test", outputs
    )
    assert run.external_baseline is True


def test_exect_v2_external_declares_clinical_nlp_baseline_family() -> None:
    records = select_fixed_slice(load_synthetic_subset(FIXTURE_PATH), limit=2)
    outputs = _mock_exect_v2_outputs(records)
    run = run_exect_v2_external_baseline(
        records, _fixture_dataset(records), "exect_v2_test", "test", outputs
    )
    assert run.architecture_family == ArchitectureFamily.CLINICAL_NLP_BASELINE.value


def test_exect_v2_external_maps_seizure_frequency() -> None:
    records = select_fixed_slice(load_synthetic_subset(FIXTURE_PATH), limit=1)
    outputs = {records[0].row_id: {"row_id": records[0].row_id, "SeizureFrequency": "2 per month"}}
    run = run_exect_v2_external_baseline(
        records, _fixture_dataset(records), "exect_v2_test", "test", outputs
    )
    freq = run.rows[0]["payload"]["final"]["seizure_frequency"]
    assert freq["value"] == "2 per month"


def test_exect_v2_external_handles_missing_row_gracefully() -> None:
    records = select_fixed_slice(load_synthetic_subset(FIXTURE_PATH), limit=2)
    run = run_exect_v2_external_baseline(
        records, _fixture_dataset(records), "exect_v2_test", "test", {}
    )
    assert any("exect_v2_missing_row" in w for w in run.warnings)
    assert run.rows[0]["payload"]["invalid_output"] is True


def test_exect_v2_external_payload_has_required_final_keys() -> None:
    from epilepsy_extraction.schemas import FINAL_EXTRACTION_REQUIRED_KEYS
    records = select_fixed_slice(load_synthetic_subset(FIXTURE_PATH), limit=2)
    outputs = _mock_exect_v2_outputs(records)
    run = run_exect_v2_external_baseline(
        records, _fixture_dataset(records), "exect_v2_test", "test", outputs
    )
    for row in run.rows:
        assert set(FINAL_EXTRACTION_REQUIRED_KEYS).issubset(row["payload"]["final"].keys())
