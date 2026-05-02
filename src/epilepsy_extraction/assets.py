from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class VersionedTextAsset:
    asset_id: str
    version: str
    path: str
    content: str


@dataclass(frozen=True)
class VersionedJsonAsset:
    asset_id: str
    version: str
    path: str
    content: dict[str, Any]


PROMPT_REGISTRY = {
    "anchor_single": ("anchor/single_prompt_v1.md", "anchor_single_prompt_v1"),
    "anchor_multi_extractor": ("anchor/multi_agent_v1/extractor.md", "anchor_multi_agent_v1"),
    "anchor_multi_verifier": ("anchor/multi_agent_v1/verifier.md", "anchor_multi_agent_v1"),
    "full_contract_single": ("full_contract/single_prompt_v1.md", "full_contract_single_prompt_v1"),
    "full_contract_multi_section_timeline": (
        "full_contract/multi_agent_v1/section_timeline.md",
        "full_contract_multi_agent_v1",
    ),
    "full_contract_multi_field_extractor": (
        "full_contract/multi_agent_v1/field_extractor.md",
        "full_contract_multi_agent_v1",
    ),
    "full_contract_multi_verification": (
        "full_contract/multi_agent_v1/verification.md",
        "full_contract_multi_agent_v1",
    ),
    "full_contract_multi_aggregation": (
        "full_contract/multi_agent_v1/aggregation.md",
        "full_contract_multi_agent_v1",
    ),
}

SCHEMA_REGISTRY = {
    "final_extraction": ("final_extraction_v1.json", "final_extraction_v1"),
}

MAPPING_REGISTRY = {
    "exect_lite": ("exect_lite_mapping_v1.yaml", "exect_lite_v1"),
    "exect_v2": ("exect_v2_mapping_v1.yaml", "exect_v2_v1"),
}


def load_prompt(prompt_id: str) -> VersionedTextAsset:
    relative_path, version = PROMPT_REGISTRY[prompt_id]
    path = REPO_ROOT / "prompts" / relative_path
    return VersionedTextAsset(
        asset_id=prompt_id,
        version=version,
        path=path.relative_to(REPO_ROOT).as_posix(),
        content=path.read_text(encoding="utf-8"),
    )


def load_mapping(mapping_id: str) -> VersionedTextAsset:
    relative_path, version = MAPPING_REGISTRY[mapping_id]
    path = REPO_ROOT / "mappings" / relative_path
    return VersionedTextAsset(
        asset_id=mapping_id,
        version=version,
        path=path.relative_to(REPO_ROOT).as_posix(),
        content=path.read_text(encoding="utf-8"),
    )


def load_schema(schema_id: str) -> VersionedJsonAsset:
    relative_path, version = SCHEMA_REGISTRY[schema_id]
    path = REPO_ROOT / "schemas" / relative_path
    return VersionedJsonAsset(
        asset_id=schema_id,
        version=version,
        path=path.relative_to(REPO_ROOT).as_posix(),
        content=json.loads(path.read_text(encoding="utf-8")),
    )
