from epilepsy_extraction.assets import PROMPT_REGISTRY, SCHEMA_REGISTRY, load_prompt, load_schema
from epilepsy_extraction.schemas import FINAL_EXTRACTION_REQUIRED_KEYS


def test_prompt_registry_assets_are_loadable() -> None:
    for prompt_id in PROMPT_REGISTRY:
        prompt = load_prompt(prompt_id)

        assert prompt.asset_id == prompt_id
        assert prompt.version
        assert prompt.path.startswith("prompts/")
        assert prompt.content.strip()


def test_final_schema_registry_matches_required_payload_keys() -> None:
    schema = load_schema("final_extraction")

    assert schema.asset_id in SCHEMA_REGISTRY
    assert schema.version == "final_extraction_v1"
    assert schema.path == "schemas/final_extraction_v1.json"
    assert schema.content["required"] == list(FINAL_EXTRACTION_REQUIRED_KEYS)
