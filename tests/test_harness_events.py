import json
import subprocess
import sys
from pathlib import Path

from epilepsy_extraction.data import compute_file_sha256, load_synthetic_subset, select_fixed_slice
from epilepsy_extraction.harnesses import run_deterministic_baseline
from epilepsy_extraction.schemas import DatasetSlice, event_dicts, harness_event, summarize_harness_events


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "synthetic_subset_fixture.json"


def test_harness_event_schema_and_summary_are_phi_safe() -> None:
    events = [
        harness_event("context_built", "row-1", 1, component="retrieval"),
        harness_event("provider_call_started", "row-1", 2, component="extractor"),
        harness_event(
            "provider_call_finished",
            "row-1",
            3,
            component="extractor",
            metrics={"input_tokens": 10, "output_tokens": 5},
        ),
        harness_event("parse_repaired", "row-1", 4, component="parser", warnings=["invalid_json"]),
    ]

    data = event_dicts(events)
    summary = summarize_harness_events(events)

    assert data[0]["event_id"] == "row-1:1:context_built"
    assert summary["event_count"] == 4
    assert summary["provider_calls"] == 1
    assert summary["parse_repair_attempts"] == 1
    assert summary["quote_bearing_events"] == 0
    assert "invalid_json" not in json.dumps(summary)


def test_deterministic_harness_emits_row_and_run_events() -> None:
    records = select_fixed_slice(load_synthetic_subset(FIXTURE_PATH), limit=1)
    dataset = DatasetSlice(
        dataset_id="fixture",
        dataset_path=str(FIXTURE_PATH),
        data_hash=compute_file_sha256(FIXTURE_PATH),
        row_ids=[record.row_id for record in records],
        inclusion_criteria="fixture",
    )

    run = run_deterministic_baseline(records, dataset, "deterministic_fixture", "test")
    data = run.to_dict()

    assert data["event_summary"]["event_count"] >= 3
    assert data["event_summary"]["event_type_counts"]["context_built"] == 1
    assert data["rows"][0]["harness_events"]
    assert data["rows"][0]["harness_events"][0]["row_id"] == "1"


def test_run_experiment_writes_event_summary(tmp_path) -> None:
    output = tmp_path / "deterministic.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_experiment.py"),
            str(FIXTURE_PATH),
            "--harness",
            "deterministic_baseline",
            "--limit",
            "1",
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
    assert run_record["event_summary"]["event_count"] >= 3
    assert run_record["harness_events"][0]["event_type"] == "context_built"
