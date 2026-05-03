import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "synthetic_subset_fixture.json"
FROZEN_REGISTRY = ROOT / "config" / "model_registry.2026-05-02.yaml"
SCRIPT = ROOT / "scripts" / "run_model_matrix.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("run_model_matrix", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _mini_registry(tmp_path: Path, frozen: bool = True) -> Path:
    frozen_at = '"2026-05-02"' if frozen else '""'
    text = f"""\
registry_version: "0.1"
created: "2026-05-02"
frozen_at: {frozen_at}

models:
  - model_id: test-frontier
    display_name: Test Frontier
    provider: test
    family: test-family
    tier: frontier
    context_window: 128000
  - model_id: test-small
    display_name: Test Small
    provider: test
    family: test-family
    tier: small
    context_window: 128000
"""
    path = tmp_path / "test_registry.yaml"
    path.write_text(text, encoding="utf-8")
    return path


# --- unit tests for build_plan logic ---


def test_build_plan_one_entry_per_model_per_provider_harness(tmp_path) -> None:
    mod = _load_script()
    from epilepsy_extraction.models.registry import load_registry

    registry = _mini_registry(tmp_path)
    entries = load_registry(registry)
    plan = mod.build_plan(entries, ["single_prompt_anchor"], None, None)

    assert len(plan) == 2
    assert all(harness == "single_prompt_anchor" for _, harness in plan)
    model_ids = [e.model_id for e, _ in plan]
    assert "test-frontier" in model_ids
    assert "test-small" in model_ids


def test_build_plan_deterministic_harness_runs_once(tmp_path) -> None:
    mod = _load_script()
    from epilepsy_extraction.models.registry import load_registry

    registry = _mini_registry(tmp_path)
    entries = load_registry(registry)
    plan = mod.build_plan(entries, ["deterministic_baseline"], None, None)

    assert len(plan) == 1
    entry, harness = plan[0]
    assert entry is None
    assert harness == "deterministic_baseline"


def test_build_plan_tier_filter_excludes_unmatched(tmp_path) -> None:
    mod = _load_script()
    from epilepsy_extraction.models.registry import load_registry

    registry = _mini_registry(tmp_path)
    entries = load_registry(registry)
    plan = mod.build_plan(entries, ["single_prompt_anchor"], {"frontier"}, None)

    assert len(plan) == 1
    assert plan[0][0].model_id == "test-frontier"


def test_build_plan_model_id_filter(tmp_path) -> None:
    mod = _load_script()
    from epilepsy_extraction.models.registry import load_registry

    registry = _mini_registry(tmp_path)
    entries = load_registry(registry)
    plan = mod.build_plan(entries, ["single_prompt_anchor"], None, {"test-small"})

    assert len(plan) == 1
    assert plan[0][0].model_id == "test-small"


def test_build_plan_mixed_harnesses(tmp_path) -> None:
    mod = _load_script()
    from epilepsy_extraction.models.registry import load_registry

    registry = _mini_registry(tmp_path)
    entries = load_registry(registry)
    plan = mod.build_plan(entries, ["deterministic_baseline", "single_prompt_anchor"], None, None)

    # 1 deterministic + 2 provider-backed (one per model entry)
    assert len(plan) == 3
    harnesses = [h for _, h in plan]
    assert harnesses.count("deterministic_baseline") == 1
    assert harnesses.count("single_prompt_anchor") == 2


# --- subprocess integration tests ---


def test_dry_run_outputs_valid_json_plan(tmp_path) -> None:
    registry = _mini_registry(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--registry", str(registry),
            "--dataset", str(FIXTURE_PATH),
            "--harnesses", "single_prompt_anchor",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["total_runs"] == 2
    assert all(item["harness"] == "single_prompt_anchor" for item in data["plan"])


def test_dry_run_tier_filter_reduces_plan(tmp_path) -> None:
    registry = _mini_registry(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--registry", str(registry),
            "--dataset", str(FIXTURE_PATH),
            "--harnesses", "single_prompt_anchor",
            "--tiers", "frontier",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["total_runs"] == 1
    assert data["plan"][0]["tier"] == "frontier"


def test_unfrozen_registry_blocked_without_flag(tmp_path) -> None:
    registry = _mini_registry(tmp_path, frozen=False)
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--registry", str(registry),
            "--dataset", str(FIXTURE_PATH),
            "--harnesses", "deterministic_baseline",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode != 0


def test_unfrozen_registry_allowed_with_flag(tmp_path) -> None:
    registry = _mini_registry(tmp_path, frozen=False)
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--registry", str(registry),
            "--dataset", str(FIXTURE_PATH),
            "--harnesses", "deterministic_baseline",
            "--dry-run",
            "--allow-unfrozen",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 0, result.stderr


def test_deterministic_harness_writes_run_record(tmp_path) -> None:
    registry = _mini_registry(tmp_path)
    output_dir = tmp_path / "runs"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--registry", str(registry),
            "--dataset", str(FIXTURE_PATH),
            "--harnesses", "deterministic_baseline",
            "--limit", "2",
            "--output-dir", str(output_dir),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["runs"] == 1
    run_path = Path(summary["results"][0]["output"])
    assert run_path.exists()
    record = json.loads(run_path.read_text(encoding="utf-8"))
    assert record["harness"] == "deterministic_baseline"


def test_anchor_harness_writes_records_with_registry_entry(tmp_path) -> None:
    registry = _mini_registry(tmp_path)
    output_dir = tmp_path / "runs"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--registry", str(registry),
            "--dataset", str(FIXTURE_PATH),
            "--harnesses", "single_prompt_anchor",
            "--limit", "1",
            "--output-dir", str(output_dir),
            "--provider", "mock",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["runs"] == 2

    for item in summary["results"]:
        record = json.loads(Path(item["output"]).read_text(encoding="utf-8"))
        assert record["model_registry_entry"] in ("test-frontier", "test-small")
        assert record["harness"] == "single_prompt_anchor"


def test_frozen_registry_used_for_canonical_runs() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--registry", str(FROZEN_REGISTRY),
            "--dataset", str(FIXTURE_PATH),
            "--harnesses", "deterministic_baseline",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["total_runs"] >= 1


def test_unknown_harness_exits_with_error(tmp_path) -> None:
    registry = _mini_registry(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--registry", str(registry),
            "--dataset", str(FIXTURE_PATH),
            "--harnesses", "not_a_real_harness",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode != 0
