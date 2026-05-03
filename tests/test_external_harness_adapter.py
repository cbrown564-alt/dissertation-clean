from pathlib import Path

from epilepsy_extraction.harnesses import ExternalClinicalAgentAdapter, load_external_adapter_output


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "external_harness_outputs" / "codex_replay_row1.json"


def test_external_adapter_normalizes_replay_fixture() -> None:
    normalized = load_external_adapter_output(FIXTURE)

    assert normalized["adapter"]["runner_name"] == "codex"
    assert normalized["adapter"]["canonical_comparator"] is False
    assert normalized["payload"]["final"]["seizure_frequency"]["value"] == "2 per month"
    assert normalized["event_summary"]["event_count"] == 2


def test_external_adapter_marks_missing_final_invalid() -> None:
    adapter = ExternalClinicalAgentAdapter(
        adapter_id="test_external.v1",
        runner_name="test-runner",
    )

    normalized = adapter.normalize_output({"runner": "x"}, row_id="1", artifact_ref="memory")

    assert normalized["payload"]["invalid_output"] is True
    assert "external_output_missing_final_payload" in normalized["payload"]["warnings"]
