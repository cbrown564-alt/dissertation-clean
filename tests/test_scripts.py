import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "synthetic_subset_fixture.json"


def test_smoke_run_and_summary_work_against_fixture(tmp_path) -> None:
    output = tmp_path / "smoke.json"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_experiment.py"),
            str(FIXTURE_PATH),
            "--limit",
            "2",
            "--run-id",
            "fixture_smoke",
            "--output",
            str(output),
            "--code-version",
            "test-version",
        ],
        check=True,
        cwd=ROOT,
    )

    run_record = json.loads(output.read_text(encoding="utf-8"))
    assert run_record["run_id"] == "fixture_smoke"
    assert run_record["dataset"]["n"] == 2
    assert run_record["dataset"]["row_ids"] == ["1", "2"]
    assert run_record["budget"]["llm_calls_per_row"] == 0
    assert run_record["code_version"] == "test-version"

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
    summary_data = json.loads(summary.stdout)
    assert summary_data["run_id"] == "fixture_smoke"
    assert summary_data["n"] == 2
