import os
import pytest
import pandas as pd
import datetime
from modules.advanced_dataset_analyzer import AdvancedDatasetAnalyzer
from modules.context_builder import ContextBuilder
from modules.compliance_checker import ComplianceChecker
from modules.report_generator import ReportGenerator

def test_advanced_analyzer():
    """Asserts that Rajya Sabha trends and polymer/application averages parse correctly."""
    analyzer = AdvancedDatasetAnalyzer()
    
    # 1. Rajya Sabha Trend check for Karnataka
    insights = analyzer.generate_regulatory_insights("Karnataka")
    assert insights["state_name"] == "Karnataka"
    assert "trends" in insights
    assert insights["trends"]["2020-21"] == 368080.0
    
    # 2. Polymer Trends check
    poly_trends = analyzer.analyze_polymer_trends(2026)
    assert "total_volume_million_tonnes" in poly_trends
    assert len(poly_trends["top_polymers"]) > 0
    
    # 3. Application Usage check
    app_trends = analyzer.analyze_application_usage(2026)
    assert "total_volume_million_tonnes" in app_trends
    assert len(app_trends["top_applications"]) > 0

def test_context_builder():
    """Asserts that ContextBuilder gathers all 5 namespaces successfully."""
    builder = ContextBuilder()
    df = pd.DataFrame([
        {"date": pd.Timestamp("2026-05-30"), "resin_code": 1, "weight_kg": 10.0, "disposal_method": "RECYCLED", "thickness_microns": 250}
    ])
    epr_res = {"overall_epr_liability_kg": 7.0, "bulk_status": {"is_bulk": False}}
    context = builder.build_grounding_context("Karnataka", "Bengaluru Urban", df, epr_res)
    
    assert "RETRIEVED REGULATORY & INDUSTRY BENCHMARK CONTEXT" in context
    assert "Karnataka" in context
    assert "Rigid" in context
    assert "EPR" in context

def test_upgraded_compliance_metrics():
    """Asserts that ComplianceChecker correctly computes new metrics."""
    checker = ComplianceChecker()
    
    # Dataset with 1 violation (thickness limit breach)
    df = pd.DataFrame([
        {"date": pd.Timestamp("2026-05-30"), "resin_code": 4, "weight_kg": 40.0, "disposal_method": "LANDFILLED", "thickness_microns": 40, "polymer_desc": "LDPE"},
        {"date": pd.Timestamp("2026-05-30"), "resin_code": 1, "weight_kg": 60.0, "disposal_method": "RECYCLED", "thickness_microns": 250, "polymer_desc": "PET"}
    ])
    
    results = checker.get_ai_compliance_report(df, "Karnataka", "Bengaluru Urban")
    
    assert "compliance_percentage" in results
    assert results["compliance_percentage"] == 60.0 # 60kg out of 100kg is compliant
    assert results["number_of_violations"] == 1
    assert results["critical_violations"] == 1
    assert results["overall_compliance_rating"] == "NON-COMPLIANT" # < 75% is non-compliant
    
    # Check alternate recommendations are present
    assert "high_risk_polymers" in results["ai_analysis"]
    assert "alt_materials" in results["ai_analysis"]

def test_docx_pdf_redesign():
    """Asserts that the redesigned report generator compiles files with visual tables & annexures successfully."""
    generator = ReportGenerator()
    
    df = pd.DataFrame([
        {"date": "2026-05-30", "resin_code": 1, "weight_kg": 150.0, "disposal_method": "RECYCLED", "thickness_microns": 250, "polymer_desc": "PET"},
        {"date": "2026-05-30", "resin_code": 4, "weight_kg": 60.0, "disposal_method": "LANDFILLED", "thickness_microns": 40, "polymer_desc": "LDPE"},
        {"date": "2026-05-30", "resin_code": 7, "weight_kg": 40.0, "disposal_method": "INCINERATED", "thickness_microns": 80, "polymer_desc": "Other"}
    ])
    
    report_data = {
        "institution_name": "ABC Engineering College",
        "report_cycle": "Verification Run",
        "summary_metrics": {
            "total_records": 3,
            "total_weight_kg": 250.0,
            "recycling_rate_pct": 60.0,
            "recycled_weight_kg": 150.0
        },
        "score_details": {
            "score": 60.0,
            "grade": "Bronze",
            "explanation": "Weighted performance indices.",
            "benchmarks": {
                "state_name": "Karnataka",
                "district_name": "Bengaluru Urban",
                "state_average_kg": 220.0,
                "city_average_kg": 180.0,
                "city_comparison_status": "Attention Needed",
                "epr_benchmarks": {
                    "state_registered_brands": 2670,
                    "industry_compliance_rate_pct": 74.5,
                    "average_brand_liability_tonnes": 15.4
                },
                "epr_analysis": {
                    "overall_liability_kg": 171.0,
                    "compliance_status": "NON_COMPLIANT",
                    "registration_required": True
                }
            }
        },
        "compliance_results": {
            "violations": [
                {"rule_id": "PWM_RULE_4C_MICRONS", "severity": "CRITICAL", "description": "Thickness under 120 microns", "affected_weight_kg": 100.0}
            ]
        },
        "epr_results": {
            "bulk_status": {"is_bulk": True, "avg_daily_kg": 150.0},
            "overall_epr_liability_kg": 171.0,
            "category_targets": {
                "Category I (Rigid)": {"total_volume_kg": 150.0, "obligation_rate_pct": 70.0, "recycling_obligation_kg": 105.0},
                "Category II (Flexible)": {"total_volume_kg": 60.0, "obligation_rate_pct": 70.0, "recycling_obligation_kg": 42.0},
                "Category III (Multilayered)": {"total_volume_kg": 40.0, "obligation_rate_pct": 60.0, "recycling_obligation_kg": 24.0}
            }
        },
        "ai_audit_report": {
            "executive_summary": "Overall compliance review.",
            "key_findings": ["Monitored total waste generates 250 kg."],
            "compliance_gap_analysis": [
                {"violation": "Thickness Breach", "severity": "CRITICAL", "corrective_action": "Replace bags"}
            ],
            "epr_assessment": {"obligations": "EPR is active.", "registration_status": "Required", "recommended_actions": "Sign MoUs"},
            "benchmark_analysis": {"state_comparison": "Avg", "city_comparison": "Avg", "national_comparison": "Avg", "industry_comparison": "Avg"},
            "environmental_risk_assessment": {"risk_level": "HIGH", "justification": "Violations found"},
            "sustainability_score_assessment": {"score": 60.0, "grade": "Bronze", "explanation": "Detailed explanation"},
            "waste_reduction_recommendations": [
                {"recommendation": "Shift packaging", "expected_impact": "Save 15%"}
            ],
            "roadmap_12_month": [
                {"month": "Month 1-3", "target": "Policy", "activities": ["Draft MoUs"], "expected_outcome": "Policy active", "compliance_improvement": "Resolves Rule 15"}
            ],
            "final_auditor_conclusion": "Auditor final signs."
        },
        "audit_df": df
    }
    
    os.makedirs("reports/test_output", exist_ok=True)
    docx_path = "reports/test_output/refocused_docx_test.docx"
    pdf_path = "reports/test_output/refocused_pdf_test.pdf"
    
    if os.path.exists(docx_path):
        os.remove(docx_path)
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
        
    saved_docx = generator.generate_docx_report(report_data, docx_path)
    assert os.path.exists(saved_docx)
    
    saved_pdf = generator.generate_pdf_report(report_data, pdf_path)
    assert os.path.exists(saved_pdf)
    
    # Cleanup after test validation
    if os.path.exists(docx_path):
        os.remove(docx_path)
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
