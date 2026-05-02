import json
import subprocess
import sys
from pathlib import Path

from epilepsy_extraction.data import compute_file_sha256, load_synthetic_subset, select_fixed_slice
from epilepsy_extraction.harnesses import run_direct_full_contract, run_single_prompt_full_contract
from epilepsy_extraction.providers import MockProvider
from epilepsy_extraction.schemas import DatasetSlice
from epilepsy_extraction.schemas.contracts import ArchitectureFamily


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "synthetic_subset_fixture.json"


def _records(limit: int = 1):
    return select_fixed_slice(load_synthetic_subset(FIXTURE_PATH), limit=limit)


def _dataset(records):
    return DatasetSlice(
        dataset_id="fixture",
        dataset_path=str(FIXTURE_PATH),
        data_hash=compute_file_sha256(FIXTURE_PATH),
        row_ids=[record.row_id for record in records],
        inclusion_criteria="fixture",
    )


def _final_payload(value: str = "2 per month") -> dict:
    return {
        "seizure_frequency": {"value": value, "evidence": "two seizures per month"},
        "current_medications": [{"value": "lamotrigine 100 mg twice daily"}],
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


def test_single_prompt_full_contract_parses_final_schema() -> None:
    records = _records()
    provider = MockProvider([json.dumps({"final": _final_payload()})])

    run = run_direct_full_contract(records, _dataset(records), "full", "test", provider)

    assert run.harness == "direct_full_contract"
    assert run.architecture_family == ArchitectureFamily.DIRECT_LLM.value
    assert run.schema_version == "final_extraction_v1"
    assert run.budget.llm_calls_per_row == 1
    assert run.rows[0]["payload"]["final"]["seizure_frequency"]["value"] == "2 per month"
    assert run.rows[0]["payload"]["invalid_output"] is False
    assert run.parse_validity["seizure_frequency"]["valid_rate"] == 1.0
    assert run.artifact_paths["schema"] == "schemas/final_extraction_v1.json"


def test_single_prompt_full_contract_invalid_json_is_component_measurable() -> None:
    records = _records()
    provider = MockProvider(["not json"])

    run = run_single_prompt_full_contract(records, _dataset(records), "full", "test", provider)

    assert run.rows[0]["payload"]["invalid_output"] is True
    assert "invalid_json" in run.rows[0]["payload"]["warnings"]
    assert run.parse_validity["final_output"]["valid_rate"] == 0.0
    assert run.parse_validity["current_medications"]["valid_rate"] == 0.0


def test_direct_full_contract_flags_malformed_component_shape() -> None:
    records = _records()
    malformed = _final_payload()
    malformed["current_medications"] = {"value": "lamotrigine"}
    provider = MockProvider([json.dumps({"final": malformed})])

    run = run_direct_full_contract(records, _dataset(records), "full", "test", provider)

    assert run.rows[0]["payload"]["invalid_output"] is True
    assert run.parse_validity["current_medications"]["valid_rate"] == 0.0


def test_single_prompt_full_contract_missing_key_fails_payload() -> None:
    records = _records()
    incomplete = _final_payload()
    del incomplete["current_medications"]
    provider = MockProvider([json.dumps(incomplete)])

    run = run_single_prompt_full_contract(records, _dataset(records), "full", "test", provider)

    assert run.rows[0]["payload"]["invalid_output"] is True
    assert "current_medications" in run.rows[0]["payload"]["warnings"][0]


def test_single_prompt_full_contract_cli_runs_from_replay(tmp_path) -> None:
    replay = tmp_path / "replay.json"
    replay.write_text(
        json.dumps(
            [
                {
                    "content": json.dumps({"final": _final_payload()}),
                    "usage": {"input_tokens": 30, "output_tokens": 20},
                }
            ]
        ),
        encoding="utf-8",
    )
    output = tmp_path / "full.json"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_experiment.py"),
            str(FIXTURE_PATH),
            "--harness",
            "direct_full_contract",
            "--limit",
            "1",
            "--run-id",
            "full_replay",
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
    assert data["harness"] == "direct_full_contract"
    assert data["budget"]["total_tokens"] == 50
    assert data["rows"][0]["payload"]["invalid_output"] is False
