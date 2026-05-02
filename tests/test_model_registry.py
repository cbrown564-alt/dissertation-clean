from pathlib import Path

import pytest

from epilepsy_extraction.models import ModelRegistryEntry, get_registry_entry, load_registry, validate_registry


REGISTRY_PATH = Path(__file__).resolve().parents[1] / "config" / "model_registry.candidate.yaml"


def test_load_candidate_registry_returns_entries() -> None:
    entries = load_registry(REGISTRY_PATH)
    assert len(entries) > 0
    assert all(isinstance(e, ModelRegistryEntry) for e in entries)


def test_candidate_registry_has_no_validation_errors() -> None:
    entries = load_registry(REGISTRY_PATH)
    errors = validate_registry(entries)
    assert errors == [], f"Registry validation errors: {errors}"


def test_candidate_registry_model_ids_are_non_empty() -> None:
    for entry in load_registry(REGISTRY_PATH):
        assert entry.model_id.strip(), f"Empty model_id in entry: {entry}"


def test_candidate_registry_covers_anthropic_and_openai() -> None:
    providers = {e.provider for e in load_registry(REGISTRY_PATH)}
    assert "anthropic" in providers
    assert "openai" in providers


def test_candidate_registry_has_frontier_and_small_tiers() -> None:
    tiers = {e.tier for e in load_registry(REGISTRY_PATH)}
    assert "frontier" in tiers
    assert any("small" in t for t in tiers)


def test_get_registry_entry_returns_known_model() -> None:
    entry = get_registry_entry("claude-3-5-sonnet-20241022", REGISTRY_PATH)
    assert entry is not None
    assert entry.provider == "anthropic"
    assert entry.tier == "frontier"
    assert entry.context_window > 0


def test_get_registry_entry_returns_none_for_unknown_model() -> None:
    entry = get_registry_entry("nonexistent-model-xyz", REGISTRY_PATH)
    assert entry is None


def test_model_registry_entry_to_dict_is_serialisable() -> None:
    import json
    entry = get_registry_entry("claude-3-5-sonnet-20241022", REGISTRY_PATH)
    assert entry is not None
    data = entry.to_dict()
    json.dumps(data)  # must not raise


def test_validate_registry_detects_duplicate_model_ids() -> None:
    entry = ModelRegistryEntry(
        model_id="duplicate-id",
        display_name="Dup A",
        provider="test",
        family="test",
        tier="small",
        context_window=4096,
    )
    errors = validate_registry([entry, entry])
    assert any("duplicate" in e.lower() or "Duplicate" in e for e in errors)


def test_validate_registry_detects_unknown_tier() -> None:
    entry = ModelRegistryEntry(
        model_id="bad-tier",
        display_name="Bad",
        provider="test",
        family="test",
        tier="giant",
        context_window=4096,
    )
    errors = validate_registry([entry])
    assert any("tier" in e.lower() for e in errors)


def test_load_registry_raises_on_missing_required_key(tmp_path) -> None:
    bad_yaml = "models:\n  - model_id: missing-keys\n    display_name: X\n"
    path = tmp_path / "bad.yaml"
    path.write_text(bad_yaml, encoding="utf-8")
    with pytest.raises(ValueError, match="missing required keys"):
        load_registry(path)
