import os
import pytest
import pandas as pd
import datetime
from modules.dataset_processor import DatasetProcessor
from modules.compliance_checker import ComplianceChecker
from modules.epr_checker import EPRCalculator
from modules.sustainability_score import SustainabilityScorer
from modules.ai_audit_assistant import AIAuditAssistant
from modules.report_generator import ReportGenerator

def test_end_to_end_demo_workflow():
    """
    Validates the end-to-end execution of the PlasticWise AI analytics and report generation
    pipeline using the demo dataset 'datasets/demo_audit.csv'.
    """
    # 1. Load and parse datasets/demo_audit.csv
    csv_path = "datasets/demo_audit.csv"
    assert os.path.exists(csv_path), "demo_audit.csv does not exist"
    
    raw_df = pd.read_csv(csv_path)
    assert not raw_df.empty, "demo_audit.csv is empty"
    
    # Map raw fields to system format
    mapped_rows = []
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    for _, row in raw_df.iterrows():
        ptype = row["Plastic_Type"]
        disposal = row["Disposal_Method"]
        qty = float(row["Quantity_kg"])
        
        if "PET" in ptype:
            resin_code = 1
            thickness = 250
        elif "LDPE" in ptype:
            resin_code = 4
            thickness = 40
        elif "Multi-layer" in ptype:
            resin_code = 7
            thickness = 80
        else:
            resin_code = 7
            thickness = 150
            
        disp_upper = disposal.upper()
        if "RECYCLE" in disp_upper:
            disposal_method = "RECYCLED"
        elif "CO_PROCESS" in disp_upper or "CO-PROCESS" in disp_upper:
            disposal_method = "CO_PROCESSED"
        elif "LANDFILL" in disp_upper:
            disposal_method = "LANDFILLED"
        elif "INCINERATE" in disp_upper:
            disposal_method = "INCINERATED"
        elif "BURN" in disp_upper:
            disposal_method = "OPEN_BURNT"
        else:
            disposal_method = "LANDFILLED"
            
        mapped_rows.append({
            "date": today_str,
            "resin_code": resin_code,
            "weight_kg": qty,
            "disposal_method": disposal_method,
            "thickness_microns": thickness
        })
        
    mapped_df = pd.DataFrame(mapped_rows)
    
    # 2. Clean data
    processor = DatasetProcessor()
    cleaned_df = processor.clean_audit_data(mapped_df)
    assert len(cleaned_df) == 3
    
    # Get metadata
    inst_name = raw_df.iloc[0]["Institution"]
    state_name = raw_df.iloc[0]["State"]
    district_name = "Bengaluru Urban" # Karnataka default
    
    # 3. Compliance Checker
    compliance_checker = ComplianceChecker()
    compliance_results = compliance_checker.get_ai_compliance_report(
        cleaned_df, state_name=state_name, district_name=district_name
    )
    assert "violations" in compliance_results
    assert "ai_analysis" in compliance_results
    
    # 4. EPR Analysis
    epr_calculator = EPRCalculator()
    epr_results = epr_calculator.calculate_epr_obligations(cleaned_df)
    assert "bulk_status" in epr_results
    assert "category_targets" in epr_results
    assert epr_results["overall_epr_liability_kg"] > 0.0
    
    # 5. Sustainability Score
    scorer = SustainabilityScorer()
    violations = compliance_results.get("violations", [])
    score_details = scorer.calculate_sustainability_index(
        cleaned_df, violations, state_name=state_name, district_name=district_name
    )
    assert "score" in score_details
    assert "grade" in score_details
    assert "benchmarks" in score_details
    
    # 6. AI Audit Assistant
    assistant = AIAuditAssistant()
    institution_details = {
        "name": inst_name,
        "report_cycle": "Demo Verification Run",
        "state": state_name,
        "district": district_name
    }
    ai_audit_report = assistant.generate_audit_report(
        institution_details=institution_details,
        df=cleaned_df,
        compliance_results=compliance_results,
        epr_results=epr_results,
        score_details=score_details
    )
    assert "executive_summary" in ai_audit_report
    assert "roadmap_12_month" in ai_audit_report
    
    # 7. Generate DOCX and PDF Reports
    report_data = {
        "institution_name": inst_name,
        "report_cycle": "Demo Verification Run",
        "summary_metrics": {
            "total_records": len(cleaned_df),
            "total_weight_kg": float(cleaned_df["weight_kg"].sum()),
            "recycling_rate_pct": float(cleaned_df[cleaned_df["disposal_method"].isin(["RECYCLED", "CO_PROCESSED"])]["weight_kg"].sum() / cleaned_df["weight_kg"].sum() * 100),
            "recycled_weight_kg": float(cleaned_df[cleaned_df["disposal_method"].isin(["RECYCLED", "CO_PROCESSED"])]["weight_kg"].sum())
        },
        "score_details": score_details,
        "compliance_results": compliance_results,
        "epr_results": epr_results,
        "ai_audit_report": ai_audit_report
    }
    
    os.makedirs("reports/test_output", exist_ok=True)
    docx_path = "reports/test_output/demo_audit_test.docx"
    pdf_path = "reports/test_output/demo_audit_test.pdf"
    
    if os.path.exists(docx_path):
        os.remove(docx_path)
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
        
    report_generator = ReportGenerator()
    
    # Generate DOCX
    saved_docx = report_generator.generate_docx_report(report_data, docx_path)
    assert os.path.exists(saved_docx), "Failed to generate DOCX report"
    
    # Generate PDF
    saved_pdf = report_generator.generate_pdf_report(report_data, pdf_path)
    assert os.path.exists(saved_pdf), "Failed to generate PDF report"
    
    # Clean up outputs after verification
    if os.path.exists(docx_path):
        os.remove(docx_path)
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
