import json
import subprocess
import sys
from pathlib import Path

from epilepsy_extraction.data import compute_file_sha256, load_synthetic_subset, select_fixed_slice
from epilepsy_extraction.harnesses import run_direct_evidence_contract
from epilepsy_extraction.providers import MockProvider
from epilepsy_extraction.schemas import DatasetSlice
from epilepsy_extraction.schemas.contracts import ArchitectureFamily


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "synthetic_subset_fixture.json"

_VALID_RESPONSE = json.dumps(
    {
        "seizure_frequency": {"value": "2 per month", "label": "2 per month"},
        "current_medications": [{"name": "lamotrigine", "dose": "100 mg bd"}],
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


def _records(limit: int = 1):
    return select_fixed_slice(load_synthetic_subset(FIXTURE_PATH), limit=limit)


def _dataset(records):
    return DatasetSlice(
        dataset_id="fixture",
        dataset_path=str(FIXTURE_PATH),
        data_hash=compute_file_sha256(FIXTURE_PATH),
        row_ids=[r.row_id for r in records],
        inclusion_criteria="fixture",
    )


def test_direct_evidence_contract_parses_valid_response() -> None:
    records = _records()
    provider = MockProvider([_VALID_RESPONSE])

    run = run_direct_evidence_contract(records, _dataset(records), "dec", "test", provider)

    assert run.harness == "direct_evidence_contract"
    assert run.budget.llm_calls_per_row == 1
    assert not run.rows[0]["payload"]["invalid_output"]


def test_direct_evidence_contract_architecture_family() -> None:
    records = _records()
    provider = MockProvider([_VALID_RESPONSE])

    run = run_direct_evidence_contract(records, _dataset(records), "dec", "test", provider)

    assert run.architecture_family == ArchitectureFamily.DIRECT_LLM.value


def test_direct_evidence_contract_records_evidence_support_metrics() -> None:
    records = _records()
    provider = MockProvider([_VALID_RESPONSE])

    run = run_direct_evidence_contract(records, _dataset(records), "dec", "test", provider)

    assert "evidence_support" in run.metrics
    support = run.metrics["evidence_support"]
    assert "total_citations" in support
    assert "evidence_supported_rate" in support


def test_direct_evidence_contract_warns_on_unsupported_citation() -> None:
    records = _records()
    response = json.dumps(
        {
            "seizure_frequency": {"value": "2 per month", "label": "2 per month"},
            "current_medications": [],
            "investigations": [],
            "seizure_types": [],
            "seizure_features": [],
            "seizure_pattern_modifiers": [],
            "epilepsy_type": None,
            "epilepsy_syndrome": None,
            "citations": [{"quote": "this quote is not in the letter at all xyz123"}],
            "confidence": {},
            "warnings": [],
        }
    )
    provider = MockProvider([response])

    run = run_direct_evidence_contract(records, _dataset(records), "dec", "test", provider)

    row_support = run.rows[0]["evidence_support"]
    assert row_support["unsupported_citations"] == 1


def test_direct_evidence_contract_invalid_json_marks_invalid_output() -> None:
    records = _records()
    provider = MockProvider(["not json"])

    run = run_direct_evidence_contract(records, _dataset(records), "dec", "test", provider)

    assert run.rows[0]["payload"]["invalid_output"] is True


def test_direct_evidence_contract_cli_from_replay_file(tmp_path) -> None:
    replay = tmp_path / "replay.json"
    replay.write_text(
        json.dumps(
            [{"content": _VALID_RESPONSE, "usage": {"input_tokens": 40, "output_tokens": 12}}]
        ),
        encoding="utf-8",
    )
    output = tmp_path / "dec.json"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_experiment.py"),
            str(FIXTURE_PATH),
            "--harness",
            "direct_evidence_contract",
            "--limit",
            "1",
            "--run-id",
            "dec_test",
            "--output",
            str(output),
            "--replay",
            str(replay),
            "--code-version",
            "test",
        ],
        check=True,
        cwd=ROOT,
    )

    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["harness"] == "direct_evidence_contract"
    assert data["budget"]["total_tokens"] == 52
