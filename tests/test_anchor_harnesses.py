import json
import subprocess
import sys
from pathlib import Path

from epilepsy_extraction.data import compute_file_sha256, load_synthetic_subset, select_fixed_slice
from epilepsy_extraction.harnesses import run_anchor_harness
from epilepsy_extraction.providers import MockProvider
from epilepsy_extraction.schemas import DatasetSlice


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


def test_single_prompt_anchor_parses_provider_json() -> None:
    records = _records()
    provider = MockProvider(['{"label":"2 per month","evidence":"two seizures per month","confidence":0.9}'])

    run = run_anchor_harness(records, _dataset(records), "anchor", "test", provider, harness="single_prompt_anchor")

    assert run.harness == "single_prompt_anchor"
    assert run.budget.llm_calls_per_row == 1
    assert run.rows[0]["prediction"]["label"] == "2 per month"
    assert run.parse_validity["seizure_frequency"]["valid_rate"] == 1.0
    assert run.artifact_paths["prompt"] == "prompts/anchor/single_prompt_v1.md"


def test_single_prompt_anchor_records_invalid_json_as_unknown() -> None:
    records = _records()
    provider = MockProvider(["not json"])

    run = run_anchor_harness(records, _dataset(records), "anchor", "test", provider, harness="single_prompt_anchor")

    assert run.rows[0]["prediction"]["label"] == "unknown"
    assert "invalid_json" in run.rows[0]["prediction"]["warnings"]


def test_anchor_warns_on_abstention_and_unsupported_evidence() -> None:
    records = _records()
    provider = MockProvider(['{"label":"abstain","evidence":"not in letter","confidence":0.1}'])

    run = run_anchor_harness(records, _dataset(records), "anchor", "test", provider, harness="single_prompt_anchor")

    warnings = run.rows[0]["prediction"]["warnings"]
    assert "abstained_or_unknown" in warnings
    assert "unsupported_evidence" in warnings


def test_multi_agent_anchor_uses_extractor_and_verifier_calls() -> None:
    records = _records()
    provider = MockProvider(
        [
            '{"candidates":[{"label":"2 per month"}]}',
            '{"label":"2 per month","evidence":"two seizures per month","confidence":0.8}',
        ]
    )

    run = run_anchor_harness(records, _dataset(records), "anchor", "test", provider, harness="multi_agent_anchor")

    assert run.budget.llm_calls_per_row == 2
    assert len(provider.requests) == 2
    assert provider.requests[1].metadata["prompt_id"] == "anchor_multi_verifier"


def test_self_consistency_anchor_reports_extra_cost_and_votes() -> None:
    records = _records()
    provider = MockProvider(
        [
            '{"label":"2 per month","evidence":"two seizures per month","confidence":0.8}',
            '{"label":"unknown","evidence":"","confidence":0.1}',
            '{"label":"2 per month","evidence":"two seizures per month","confidence":0.6}',
        ]
    )

    run = run_anchor_harness(records, _dataset(records), "anchor", "test", provider, harness="multi_agent_anchor_sc3")

    assert run.budget.llm_calls_per_row == 3
    assert run.rows[0]["prediction"]["label"] == "2 per month"
    assert run.rows[0]["prediction"]["metadata"]["vote_counts"]["2 per month"] == 2


def test_anchor_cli_runs_from_replay_file(tmp_path) -> None:
    replay = tmp_path / "replay.json"
    replay.write_text(
        json.dumps(
            [
                {
                    "content": '{"label":"2 per month","evidence":"two seizures per month","confidence":0.9}',
                    "usage": {"input_tokens": 20, "output_tokens": 6},
                }
            ]
        ),
        encoding="utf-8",
    )
    output = tmp_path / "anchor.json"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_experiment.py"),
            str(FIXTURE_PATH),
            "--harness",
            "single_prompt_anchor",
            "--limit",
            "1",
            "--run-id",
            "anchor_replay",
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
    assert data["harness"] == "single_prompt_anchor"
    assert data["budget"]["total_tokens"] == 26


def test_retrieval_anchor_makes_single_provider_call() -> None:
    records = _records()
    provider = MockProvider(['{"label":"2 per month","evidence":"two seizures per month","confidence":0.9}'])

    run = run_anchor_harness(records, _dataset(records), "anchor", "test", provider, harness="retrieval_anchor")

    assert run.harness == "retrieval_anchor"
    assert run.budget.llm_calls_per_row == 1
    assert len(provider.requests) == 1


def test_retrieval_anchor_records_retrieval_artifacts() -> None:
    records = _records()
    provider = MockProvider(['{"label":"2 per month","evidence":"two seizures per month","confidence":0.9}'])

    run = run_anchor_harness(records, _dataset(records), "anchor", "test", provider, harness="retrieval_anchor")

    assert "retrieval_artifacts" in run.rows[0]
    assert "candidate_spans" in run.rows[0]["retrieval_artifacts"]


def test_retrieval_anchor_warns_on_recall_loss_for_bare_letter() -> None:
    records = _records()
    # Override the letter with something that has no seizure-frequency keywords
    from dataclasses import replace
    no_keyword_records = [replace(records[0], letter="General review. Patient attended clinic.")]
    provider = MockProvider(['{"label":"unknown","evidence":"","confidence":0.0}'])

    run = run_anchor_harness(
        no_keyword_records, _dataset(records), "anchor", "test", provider, harness="retrieval_anchor"
    )

    warnings = run.rows[0]["prediction"]["warnings"]
    assert "retrieval_recall_loss_fallback_full" in warnings


def test_retrieval_anchor_uses_retrieval_prompt_version() -> None:
    records = _records()
    provider = MockProvider(['{"label":"seizure-free","evidence":"no seizures","confidence":1.0}'])

    run = run_anchor_harness(records, _dataset(records), "anchor", "test", provider, harness="retrieval_anchor")

    assert run.prompt_version == "anchor_retrieval_v1"
    assert run.artifact_paths["prompt"] == "prompts/anchor/retrieval_v1.md"
