import pytest

from epilepsy_extraction.document import ClinicalDocumentInterface
from epilepsy_extraction.schemas.contracts import FieldFamily


LETTER = (
    "Assessment:\n"
    "The patient has two seizures per month.\n"
    "Current Medications:\n"
    "Lamotrigine 100 mg twice daily.\n"
    "Investigations:\n"
    "MRI brain was normal."
)


def test_document_interface_returns_sections() -> None:
    interface = ClinicalDocumentInterface(LETTER)
    sections = interface.get_sections()

    assert sections
    assert any("assessment" in section["name"] for section in sections)


def test_search_spans_returns_stable_locator() -> None:
    interface = ClinicalDocumentInterface(LETTER)
    spans = interface.search_spans(FieldFamily.SEIZURE_FREQUENCY)

    assert spans
    span = interface.get_span(spans[0]["locator"])
    assert span["text"] == spans[0]["text"]


def test_get_span_rejects_locator_when_text_hash_does_not_match() -> None:
    interface = ClinicalDocumentInterface(LETTER)
    locator = interface.search_spans(FieldFamily.SEIZURE_FREQUENCY)[0]["locator"]
    bad_locator = locator.rsplit(":", 1)[0] + ":badbadbadbad"

    with pytest.raises(ValueError, match="hash"):
        interface.get_span(bad_locator)


def test_quote_evidence_returns_locator_for_exact_quote() -> None:
    interface = ClinicalDocumentInterface(LETTER)
    result = interface.quote_evidence("two seizures per month")

    assert result["supported"] is True
    assert result["locator"].startswith("char:")


def test_validate_payload_reports_missing_final_keys() -> None:
    interface = ClinicalDocumentInterface(LETTER)
    result = interface.validate_payload({"final": {"seizure_frequency": {"value": "2 per month"}}})

    assert result["valid"] is False
    assert "missing required keys" in result["error"]


def test_compare_evidence_to_claim_returns_grade_and_locator() -> None:
    interface = ClinicalDocumentInterface(LETTER)
    result = interface.compare_evidence_to_claim(
        "2 per month",
        "two seizures per month",
    )

    assert result["full_credit"] is True
    assert result["locator"].startswith("char:")
