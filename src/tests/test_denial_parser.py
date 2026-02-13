from smallbizpulse.ingest.denial_parser import parse_denial_text


def test_parse_denial_text_extracts_core_fields() -> None:
    denial_text = """
    Payer: UnitedHealthcare
    Denial Reason: Not medically necessary based on submitted records.
    CPT Code: 72148
    HCPCS: A9279
    Please submit appeal within 60 days.
    """

    parsed = parse_denial_text(denial_text)

    assert parsed.payer == "UnitedHealthcare"
    assert "72148" in parsed.cpt_hcpcs_codes
    assert "A9279" in parsed.cpt_hcpcs_codes
    assert "medically necessary" in parsed.denial_reason_text.lower()
    assert any("within 60 days" in hint.lower() for hint in parsed.deadline_hints)
