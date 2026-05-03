import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from epilepsy_extraction.data import compute_file_sha256, load_synthetic_subset, select_fixed_slice
from epilepsy_extraction.harnesses import (
    attach_manifest_to_run,
    default_manifest_path,
    load_harness_manifest,
    run_deterministic_baseline,
)
from epilepsy_extraction.schemas import DatasetSlice


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "synthetic_subset_fixture.json"


def test_default_manifest_loads_and_hashes() -> None:
    manifest = load_harness_manifest(default_manifest_path("deterministic_baseline", ROOT))

    assert manifest.manifest_id == "deterministic_baseline.v1"
    assert manifest.harness_id == "deterministic_baseline"
    assert manifest.architecture_family == "clinical_nlp_baseline"
    assert len(manifest.manifest_hash) == 64
    assert manifest.gold_label_isolation["model_visible"] is False


def test_manifest_validation_rejects_gold_label_visibility(tmp_path) -> None:
    source = default_manifest_path("deterministic_baseline", ROOT)
    data = json.loads(source.read_text(encoding="utf-8"))
    data["gold_label_isolation"]["model_visible"] = True
    path = tmp_path / "bad.yaml"
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="model_visible"):
        load_harness_manifest(path)


def test_attach_manifest_to_run_stamps_metadata() -> None:
    records = select_fixed_slice(load_synthetic_subset(FIXTURE_PATH), limit=1)
    dataset = DatasetSlice(
        dataset_id="fixture",
        dataset_path=str(FIXTURE_PATH),
        data_hash=compute_file_sha256(FIXTURE_PATH),
        row_ids=[record.row_id for record in records],
        inclusion_criteria="fixture",
    )
    run = run_deterministic_baseline(records, dataset, "deterministic_fixture", "test")
    manifest = load_harness_manifest(default_manifest_path("deterministic_baseline", ROOT))
    stamped = attach_manifest_to_run(replace(run, architecture_family=""), manifest)

    assert stamped.manifest_id == manifest.manifest_id
    assert stamped.manifest_hash == manifest.manifest_hash
    assert stamped.architecture_family == manifest.architecture_family
    assert stamped.artifact_paths["manifest"].endswith("deterministic_baseline.yaml")
    assert stamped.complexity["manifest"]["harness_id"] == "deterministic_baseline"


def test_run_experiment_writes_manifest_metadata(tmp_path) -> None:
    output = tmp_path / "deterministic.json"
    result = subprocess.run(
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
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 0
    run_record = json.loads(output.read_text(encoding="utf-8"))

    assert run_record["manifest_id"] == "deterministic_baseline.v1"
    assert len(run_record["manifest_hash"]) == 64
    assert run_record["artifact_paths"]["manifest"].endswith("deterministic_baseline.yaml")


def test_run_experiment_rejects_mismatched_manifest(tmp_path) -> None:
    output = tmp_path / "deterministic.json"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_experiment.py"),
            str(FIXTURE_PATH),
            "--harness",
            "deterministic_baseline",
            "--manifest",
            str(default_manifest_path("metadata_smoke", ROOT)),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    assert result.returncode != 0
    assert "not 'deterministic_baseline'" in result.stderr
