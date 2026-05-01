from epilepsy_extraction.evaluation import parse_label


def test_parse_direct_rate() -> None:
    parsed = parse_label("2 per week")

    assert parsed.pragmatic_class == "frequent"
    assert 8.0 < (parsed.monthly_rate or 0) < 9.0


def test_parse_cluster_rate() -> None:
    parsed = parse_label("2 cluster per month, 6 per cluster")

    assert parsed.monthly_rate == 12.0
    assert parsed.pragmatic_class == "frequent"


def test_parse_seizure_free() -> None:
    parsed = parse_label("seizure free for 12 month")

    assert parsed.monthly_rate == 0.0
    assert parsed.pragmatic_class == "NS"


def test_parse_unknown() -> None:
    parsed = parse_label("unknown, 2 to 3 per cluster")

    assert parsed.monthly_rate == 1000.0
    assert parsed.purist_class == "UNK"


def test_parse_prompt_intervention_labels() -> None:
    labels = [
        "multiple per week",
        "multiple per day",
        "1 per 4 day",
        "1 per 6 week",
        "2 cluster per month, 6 per cluster",
    ]

    for label in labels:
        assert parse_label(label).monthly_rate is not None
