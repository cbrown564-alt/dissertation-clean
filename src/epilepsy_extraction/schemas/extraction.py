from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .contracts import SCHEMA_VERSION, SupportAssessment, empty_field_coverage


@dataclass(frozen=True)
class EvidenceSpan:
    quote: str
    section: str | None = None
    span_id: str | None = None
    char_start: int | None = None
    char_end: int | None = None


@dataclass(frozen=True)
class Prediction:
    label: str
    evidence: list[EvidenceSpan] = field(default_factory=list)
    confidence: float = 0.0
    parsed_monthly_rate: float | None = None
    pragmatic_class: str | None = None
    purist_class: str | None = None
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GoldRecord:
    source_row_index: int
    letter: str
    gold_label: str
    gold_evidence: str
    row_ok: bool
    raw: dict[str, Any]

    @property
    def row_id(self) -> str:
        return str(self.source_row_index)


@dataclass(frozen=True)
class ExtractedItem:
    value: str
    normalized_value: str | None = None
    status: str | None = None
    evidence: EvidenceSpan | None = None
    confidence: float = 0.0
    support: SupportAssessment | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class FinalExtraction:
    seizure_frequency: dict[str, Any] = field(default_factory=dict)
    current_medications: list[dict[str, Any]] = field(default_factory=list)
    investigations: list[dict[str, Any]] = field(default_factory=list)
    seizure_types: list[dict[str, Any]] = field(default_factory=list)
    seizure_features: list[dict[str, Any]] = field(default_factory=list)
    seizure_pattern_modifiers: list[dict[str, Any]] = field(default_factory=list)
    epilepsy_type: dict[str, Any] | None = None
    epilepsy_syndrome: dict[str, Any] | None = None
    citations: list[dict[str, Any]] = field(default_factory=list)
    confidence: dict[str, float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ExtractionPayload:
    pipeline_id: str
    final: FinalExtraction
    schema_version: str = SCHEMA_VERSION
    field_coverage: dict[str, str] = field(default_factory=empty_field_coverage)
    artifacts: dict[str, Any] = field(default_factory=dict)
    invalid_output: bool = False
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
