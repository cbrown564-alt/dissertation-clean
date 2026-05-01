from epilepsy_extraction.evaluation import monthly_rate_match, parse_validity_summary


def test_monthly_rate_match_uses_relative_tolerance_for_infrequent_rates() -> None:
    assert not monthly_rate_match(0.0833333333, 0.2)


def test_monthly_rate_match_accepts_values_inside_relative_tolerance() -> None:
    assert monthly_rate_match(2.0, 2.2)


def test_parse_validity_summary_reports_component_rates() -> None:
    summary = parse_validity_summary(
        [
            ("seizure_frequency", True),
            ("seizure_frequency", False),
            ("current_medications", True),
        ]
    )

    assert summary["seizure_frequency"]["valid"] == 1
    assert summary["seizure_frequency"]["invalid"] == 1
    assert summary["seizure_frequency"]["valid_rate"] == 0.5
    assert summary["current_medications"]["valid_rate"] == 1.0
