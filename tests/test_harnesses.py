import json
import subprocess
import sys
from pathlib import Path

from epilepsy_extraction.data import compute_file_sha256, load_synthetic_subset, select_fixed_slice
from epilepsy_extraction.harnesses import predict_seizure_frequency, run_deterministic_baseline
from epilepsy_extraction.schemas import DatasetSlice


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "synthetic_subset_fixture.json"


def test_predict_seizure_frequency_uses_letter_text_rules() -> None:
    prediction = predict_seizure_frequency(
        "The diary shows two seizures per month. A historical note mentions one seizure per year."
    )

    assert prediction.label == "2 per month"
    assert prediction.parsed_monthly_rate == 2.0
    assert prediction.evidence[0].quote == "two seizures per month"


def test_deterministic_baseline_run_record_contains_rows_and_validity() -> None:
    records = select_fixed_slice(load_synthetic_subset(FIXTURE_PATH), limit=2)
    dataset = DatasetSlice(
        dataset_id="fixture",
        dataset_path=str(FIXTURE_PATH),
        data_hash=compute_file_sha256(FIXTURE_PATH),
        row_ids=[record.row_id for record in records],
        inclusion_criteria="fixture",
    )

    run = run_deterministic_baseline(records, dataset, "deterministic_fixture", "test")
    data = run.to_dict()

    assert data["harness"] == "deterministic_baseline"
    assert data["budget"]["llm_calls_per_row"] == 0
    assert data["parse_validity"]["seizure_frequency"]["valid_rate"] == 1.0
    assert data["rows"][0]["payload"]["final"]["seizure_frequency"]["value"] == "2 per month"
    assert "exact_label_accuracy" in data["metrics"]


def test_deterministic_baseline_cli_writes_summarizable_run(tmp_path) -> None:
    output = tmp_path / "deterministic.json"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_experiment.py"),
            str(FIXTURE_PATH),
            "--harness",
            "deterministic_baseline",
            "--limit",
            "2",
            "--run-id",
            "deterministic_fixture",
            "--output",
            str(output),
            "--code-version",
            "test-version",
        ],
        check=True,
        cwd=ROOT,
    )

    run_record = json.loads(output.read_text(encoding="utf-8"))
    assert run_record["harness"] == "deterministic_baseline"
    assert len(run_record["rows"]) == 2

    summary = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "summarize_results.py"),
            str(output),
        ],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert json.loads(summary.stdout)["harness"] == "deterministic_baseline"
