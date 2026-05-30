import pytest
import pandas as pd
from utils.validators import validate_audit_row
from modules.epr_checker import EPRCalculator
from modules.sustainability_score import SustainabilityScorer

def test_validate_audit_row_valid():
    """Asserts that a standard, valid record yields True."""
    row = {
        "date": "2026-05-30",
        "resin_code": 1,
        "weight_kg": 10.5,
        "disposal_method": "RECYCLED",
        "thickness_microns": 250
    }
    assert validate_audit_row(row) is True

def test_validate_audit_row_invalid_weight():
    """Asserts that invalid weight_kg triggers ValueError."""
    row = {
        "date": "2026-05-30",
        "resin_code": 1,
        "weight_kg": -2.0, # Violating: must be positive
        "disposal_method": "RECYCLED",
        "thickness_microns": 250
    }
    with pytest.raises(ValueError, match="Weight must be a positive number"):
        validate_audit_row(row)

def test_validate_audit_row_invalid_resin():
    """Asserts that bad resin_code triggers ValueError."""
    row = {
        "date": "2026-05-30",
        "resin_code": 9, # Violating: must be 1-7
        "weight_kg": 5.0,
        "disposal_method": "RECYCLED",
        "thickness_microns": 250
    }
    with pytest.raises(ValueError, match="Must be between 1 and 7"):
        validate_audit_row(row)

def test_epr_bulk_generator():
    """Validates EPR Calculator correctly flags bulk status."""
    calc = EPRCalculator()
    
    # 1. Under limit test
    df_under = pd.DataFrame([
        {"date": pd.Timestamp("2026-05-30"), "resin_code": 1, "weight_kg": 40.0, "disposal_method": "RECYCLED", "thickness_microns": 200}
    ])
    res_under = calc.check_bulk_generator_status(df_under)
    assert res_under["is_bulk"] == False
    
    # 2. Over limit test
    df_over = pd.DataFrame([
        {"date": pd.Timestamp("2026-05-30"), "resin_code": 1, "weight_kg": 150.0, "disposal_method": "RECYCLED", "thickness_microns": 200}
    ])
    res_over = calc.check_bulk_generator_status(df_over)
    assert res_over["is_bulk"] == True

def test_sustainability_scorer():
    """Asserts sustainability scoring metrics are consistent."""
    scorer = SustainabilityScorer()
    
    # Fully recycled, compliant dataset
    df = pd.DataFrame([
        {"date": pd.Timestamp("2026-05-30"), "resin_code": 1, "weight_kg": 10.0, "disposal_method": "RECYCLED", "thickness_microns": 250}
    ])
    res = scorer.calculate_sustainability_index(df, [])
    assert res["score"] >= 85.0
    assert "Gold" in res["grade"]


def test_ai_audit_assistant():
    """Asserts that AIAuditAssistant generates the correct keys."""
    from modules.ai_audit_assistant import AIAuditAssistant
    from modules.dataset_processor import DatasetProcessor
    assistant = AIAuditAssistant()
    
    institution_details = {
        "name": "Test University",
        "state": "Maharashtra",
        "district": "Mumbai City",
        "report_cycle": "Q1"
    }
    df = pd.DataFrame([
        {"date": "2026-05-30", "resin_code": 1, "weight_kg": 10.0, "disposal_method": "RECYCLED", "thickness_microns": 250}
    ])
    cleaned_df = DatasetProcessor().clean_audit_data(df)
    
    compliance_results = {"violations": []}
    epr_results = {
        "bulk_status": {"is_bulk": False, "avg_daily_kg": 0.3, "threshold_kg": 100.0},
        "category_targets": {},
        "overall_epr_liability_kg": 0.0
    }
    score_details = {
        "score": 90.0,
        "grade": "Gold Tier (Exemplary)"
    }
    
    report = assistant.generate_audit_report(
        institution_details=institution_details,
        df=cleaned_df,
        compliance_results=compliance_results,
        epr_results=epr_results,
        score_details=score_details
    )

    
    assert "executive_summary" in report
    assert "key_findings" in report
    assert "compliance_gap_analysis" in report
    assert "epr_assessment" in report
    assert "benchmark_analysis" in report
    assert "environmental_risk_assessment" in report
    assert "sustainability_score_assessment" in report
    assert "waste_reduction_recommendations" in report
    assert "roadmap_12_month" in report
    assert "final_auditor_conclusion" in report
    assert isinstance(report["key_findings"], list)

