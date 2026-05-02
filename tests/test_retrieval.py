from epilepsy_extraction.retrieval.candidates import (
    build_retrieval_context,
    retrieve_candidate_spans,
    _split_sentences,
    _deduplicate,
    CandidateSpan,
)
from epilepsy_extraction.schemas.contracts import FieldFamily


LETTER = (
    "Clinic letter. Present seizure frequency: two seizures per month. "
    "Current medication is lamotrigine 100 mg twice daily. "
    "MRI was normal. EEG showed generalised spike-wave."
)


def test_retrieve_candidate_spans_finds_seizure_freq_keywords() -> None:
    spans = retrieve_candidate_spans(LETTER, FieldFamily.SEIZURE_FREQUENCY)

    assert spans
    assert any("seizure" in s.text.lower() or "per month" in s.text.lower() for s in spans)


def test_retrieve_candidate_spans_empty_for_no_matches() -> None:
    spans = retrieve_candidate_spans("No relevant content here.", FieldFamily.INVESTIGATIONS)

    assert spans == []


def test_retrieve_candidate_spans_returns_scored_spans() -> None:
    spans = retrieve_candidate_spans(LETTER, FieldFamily.SEIZURE_FREQUENCY)

    assert all(s.score >= 1 for s in spans)
    assert all(s.field_family == FieldFamily.SEIZURE_FREQUENCY.value for s in spans)


def test_retrieve_candidate_spans_respects_max_spans() -> None:
    long_letter = (LETTER + " ") * 20
    spans = retrieve_candidate_spans(long_letter, FieldFamily.SEIZURE_FREQUENCY, max_spans=2)

    assert len(spans) <= 2


def test_retrieve_candidate_spans_medications() -> None:
    spans = retrieve_candidate_spans(LETTER, FieldFamily.CURRENT_MEDICATIONS)

    assert spans
    assert any("lamotrigine" in s.text.lower() for s in spans)


def test_retrieve_candidate_spans_investigations() -> None:
    spans = retrieve_candidate_spans(LETTER, FieldFamily.INVESTIGATIONS)

    assert spans
    assert any("MRI" in s.text or "EEG" in s.text for s in spans)


def test_build_retrieval_context_returns_context_artifacts_warnings() -> None:
    context, artifacts, warnings = build_retrieval_context(LETTER, FieldFamily.SEIZURE_FREQUENCY)

    assert context
    assert isinstance(artifacts, list)
    assert isinstance(warnings, list)


def test_build_retrieval_context_artifacts_have_required_keys() -> None:
    _, artifacts, _ = build_retrieval_context(LETTER, FieldFamily.SEIZURE_FREQUENCY)

    if artifacts:
        for art in artifacts:
            assert "text" in art
            assert "field_family" in art
            assert "score" in art


def test_build_retrieval_context_fallback_on_no_match() -> None:
    no_match = "Patient is doing well. No relevant keywords present."
    context, artifacts, warnings = build_retrieval_context(no_match, FieldFamily.INVESTIGATIONS)

    assert "retrieval_recall_loss_fallback_full" in warnings
    assert context == no_match
    assert artifacts == []


def test_split_sentences_handles_periods() -> None:
    text = "First sentence. Second sentence. Third sentence."
    result = _split_sentences(text)

    assert len(result) == 3
    assert result[0][1] == "First sentence."


def test_split_sentences_handles_newlines() -> None:
    text = "First line\nSecond line\nThird line"
    result = _split_sentences(text)

    assert len(result) == 3


def test_deduplicate_removes_contained_span() -> None:
    outer = CandidateSpan(text="outer text here", field_family="x", score=5, span_start=0, span_end=100)
    inner = CandidateSpan(text="inner", field_family="x", score=3, span_start=10, span_end=50)
    result = _deduplicate([outer, inner])

    assert len(result) == 1
    assert result[0].score == 5


def test_deduplicate_keeps_non_overlapping_spans() -> None:
    a = CandidateSpan(text="a", field_family="x", score=2, span_start=0, span_end=50)
    b = CandidateSpan(text="b", field_family="x", score=2, span_start=60, span_end=100)
    result = _deduplicate([a, b])

    assert len(result) == 2
