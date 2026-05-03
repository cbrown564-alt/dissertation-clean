import json
from pathlib import Path

from epilepsy_extraction.data import compute_file_sha256, load_synthetic_subset, select_fixed_slice
from epilepsy_extraction.harnesses import run_budgeted_escalation_harness
from epilepsy_extraction.providers import MockProvider
from epilepsy_extraction.schemas import DatasetSlice
from epilepsy_extraction.schemas.contracts import ArchitectureFamily, CORE_FIELD_FAMILIES


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "synthetic_subset_fixture.json"

_FIELD_RESPONSE = json.dumps(
    {
        "seizure_frequency": {"value": "2 per month"},
        "current_medications": [],
        "investigations": [],
        "seizure_types": [],
        "seizure_features": [],
        "seizure_pattern_modifiers": [],
        "epilepsy_type": None,
        "epilepsy_syndrome": None,
        "citations": [{"quote": "two seizures per month"}],
        "confidence": {"seizure_frequency": 0.9},
        "warnings": [],
    }
)

_DIRECT_RESPONSE = json.dumps(
    {
        "seizure_frequency": {"value": "2 per month", "label": "2 per month"},
        "current_medications": [],
        "investigations": [],
        "seizure_types": [],
        "seizure_features": [],
        "seizure_pattern_modifiers": [],
        "epilepsy_type": None,
        "epilepsy_syndrome": None,
        "citations": [{"quote": "two seizures per month"}],
        "confidence": {"seizure_frequency": 0.9},
        "warnings": [],
    }
)


def _records():
    return select_fixed_slice(load_synthetic_subset(FIXTURE_PATH), limit=1)


def _dataset(records):
    return DatasetSlice(
        dataset_id="fixture",
        dataset_path=str(FIXTURE_PATH),
        data_hash=compute_file_sha256(FIXTURE_PATH),
        row_ids=[r.row_id for r in records],
        inclusion_criteria="fixture",
    )


def test_budgeted_escalation_stays_separate_from_canonical_baselines() -> None:
    records = _records()
    cheap = MockProvider([_FIELD_RESPONSE] * len(CORE_FIELD_FAMILIES))
    strong = MockProvider([_DIRECT_RESPONSE])

    run = run_budgeted_escalation_harness(records, _dataset(records), "esc", "test", cheap, strong)

    assert run.harness == "budgeted_escalation"
    assert run.architecture_family == ArchitectureFamily.COSTED_RELIABILITY_VARIANT.value
    assert run.event_summary["escalation_decisions"] == 1


def test_budgeted_escalation_uses_stronger_model_on_parse_failure() -> None:
    records = _records()
    cheap = MockProvider(["not json"] * len(CORE_FIELD_FAMILIES))
    strong = MockProvider([_DIRECT_RESPONSE])

    run = run_budgeted_escalation_harness(records, _dataset(records), "esc", "test", cheap, strong)

    assert "escalation_reason:parse_failure" in run.warnings
    assert run.budget.llm_calls_per_row == len(CORE_FIELD_FAMILIES) + 1
    assert len(strong.requests) == 1
