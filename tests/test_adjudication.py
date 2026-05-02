import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

from epilepsy_extraction.evaluation.adjudication import (
    ADJUDICATION_COLUMNS,
    build_adjudication_rows,
    read_adjudication_sheet,
    summarize_adjudication,
    write_adjudication_sheet,
)


ROOT = Path(__file__).resolve().parents[1]
RUN_PATH = ROOT / "results" / "runs" / "exect_lite_smoke.json"


def _run_record() -> dict:
    return json.loads(RUN_PATH.read_text(encoding="utf-8"))


def test_build_adjudication_rows_from_run_record_payloads() -> None:
    rows = build_adjudication_rows([_run_record()])

    seizure_frequency = [row for row in rows if row["field_family"] == "seizure_frequency"]
    medications = [row for row in rows if row["field_family"] == "current_medications"]

    assert len(seizure_frequency) == 2
    assert seizure_frequency[0]["emitted_value"] == "2 per month"
    assert seizure_frequency[0]["reference_value"] == "2 per month"
    assert seizure_frequency[0]["evidence"] == "two seizures per month"
    assert medications[0]["emitted_value"] == "lamotrigine"


def test_write_and_read_adjudication_sheet_round_trips(tmp_path) -> None:
    rows = build_adjudication_rows([_run_record()])
    output = write_adjudication_sheet(rows, tmp_path / "sheet.csv")

    imported = read_adjudication_sheet(output)

    assert tuple(imported[0].keys()) == ADJUDICATION_COLUMNS
    assert imported[0]["run_id"] == "exect_lite_smoke"


def test_read_adjudication_sheet_rejects_unknown_error_tags(tmp_path) -> None:
    output = write_adjudication_sheet(build_adjudication_rows([_run_record()]), tmp_path / "sheet.csv")
    rows = list(csv.DictReader(output.open(encoding="utf-8", newline="")))
    rows[0]["error_tags"] = "not_a_real_error"

    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ADJUDICATION_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(ValueError, match="Unknown adjudication error tags"):
        read_adjudication_sheet(output)


def test_summarize_adjudication_counts_completion_and_error_tags() -> None:
    rows = build_adjudication_rows([_run_record()])
    rows[0]["value_score"] = "1"
    rows[0]["evidence_grade"] = "exact_span"
    rows[0]["error_tags"] = "wrong_temporality;unsupported_evidence"

    summary = summarize_adjudication(rows)

    assert summary["rows"] == len(rows)
    assert summary["completed_rows"] == 1
    assert summary["not_adjudicated_rows"] == len(rows) - 1
    assert summary["evidence_grade_counts"]["exact_span"] == 1
    assert summary["error_tag_counts"]["unsupported_evidence"] == 1
    assert summary["error_tag_counts"]["wrong_temporality"] == 1


def test_adjudication_scripts_build_and_summarize_sheet(tmp_path) -> None:
    sheet = tmp_path / "sheet.csv"
    summary_path = tmp_path / "summary.json"

    build = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_adjudication_sheet.py"),
            str(RUN_PATH),
            "--output",
            str(sheet),
        ],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    build_summary = json.loads(build.stdout)
    assert build_summary["rows"] > 0
    assert sheet.exists()

    summarized = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "summarize_adjudication.py"),
            str(sheet),
            "--output",
            str(summary_path),
        ],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    summary = json.loads(summarized.stdout)
    assert summary["not_adjudicated_rows"] == build_summary["rows"]
    assert summary_path.exists()
