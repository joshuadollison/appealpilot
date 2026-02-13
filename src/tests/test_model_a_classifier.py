from smallbizpulse.models.model_a_classifier import classify_denial_reason


def test_classifier_detects_medical_necessity() -> None:
    result = classify_denial_reason(
        "Denial reason: not medically necessary and insufficient clinical justification."
    )
    assert result.category == "medical_necessity"
    assert result.confidence > 0.3
    assert "medically necessary" in " ".join(result.matched_terms).lower()


def test_classifier_falls_back_to_other() -> None:
    result = classify_denial_reason("Reason: generic denial with no category cues.")
    assert result.category == "other"
    assert result.confidence == 0.3
