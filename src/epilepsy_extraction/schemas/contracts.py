from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


SCHEMA_VERSION = "1.0.0"


class FieldFamily(str, Enum):
    SEIZURE_FREQUENCY = "seizure_frequency"
    CURRENT_MEDICATIONS = "current_medications"
    INVESTIGATIONS = "investigations"
    SEIZURE_CLASSIFICATION = "seizure_classification"
    EPILEPSY_CLASSIFICATION = "epilepsy_classification"
    RESCUE_MEDICATION = "rescue_medication"
    OTHER_THERAPIES = "other_therapies"
    COMORBIDITIES = "comorbidities"
    ASSOCIATED_SYMPTOMS = "associated_symptoms"


CORE_FIELD_FAMILIES: tuple[FieldFamily, ...] = (
    FieldFamily.SEIZURE_FREQUENCY,
    FieldFamily.CURRENT_MEDICATIONS,
    FieldFamily.INVESTIGATIONS,
    FieldFamily.SEIZURE_CLASSIFICATION,
    FieldFamily.EPILEPSY_CLASSIFICATION,
)


class FieldCoverageStatus(str, Enum):
    IMPLEMENTED = "implemented"
    PARTIAL = "partial"
    NOT_IMPLEMENTED = "not_implemented"
    FAILED = "failed"


class EvidenceGrade(str, Enum):
    EXACT_SPAN = "exact_span"
    OVERLAPPING_SPAN = "overlapping_span"
    SECTION_LEVEL = "section_level"
    WRONG_TEMPORAL_STATUS = "wrong_temporal_status"
    UNSUPPORTED = "unsupported"
    MISSING_EVIDENCE = "missing_evidence"


@dataclass(frozen=True)
class SupportAssessment:
    grade: EvidenceGrade
    warnings: list[str] = field(default_factory=list)

    @property
    def full_credit(self) -> bool:
        return self.grade in {
            EvidenceGrade.EXACT_SPAN,
            EvidenceGrade.OVERLAPPING_SPAN,
        }


def empty_field_coverage() -> dict[str, str]:
    return {
        field.value: FieldCoverageStatus.NOT_IMPLEMENTED.value
        for field in FieldFamily
    }
