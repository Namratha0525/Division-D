import streamlit as st
import pandas as pd
import os

from modules.dataset_processor import DatasetProcessor
from modules.audit_analyzer import AuditAnalyzer
from modules.compliance_checker import ComplianceChecker
from modules.epr_checker import EPRCalculator
from modules.sustainability_score import SustainabilityScorer
from modules.roadmap_generator import RoadmapGenerator
from modules.compliance_score_engine import ComplianceScoreEngine
from modules.carbon_impact import CarbonImpactAnalyzer
from modules.benchmark_ranker import BenchmarkRanker

# Set Streamlit Page Styling configurations
st.set_page_config(
    page_title="PlasticWise AI",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom css injected for enterprise green branding
st.markdown("""
<style>
    .main-title {
        color: #1E4620;
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: 0.1rem;
    }
    .sub-title {
        color: #5C8D89;
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #F4F7F6;
        color: #222222 !important;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1E4620;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .metric-card h4, .metric-card p, .metric-card li, .metric-card span {
        color: #222222 !important;
    }
    .legal-alert {
        background-color: #FFF5F5;
        color: #222222 !important;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #B23B3B;
        margin-bottom: 10px;
    }
    .legal-alert h4, .legal-alert p {
        color: #222222 !important;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initializes standard audit values across tabs."""
    if "data_processed" not in st.session_state:
        st.session_state["data_processed"] = False
        
    if "benchmark_state" not in st.session_state:
        st.session_state["benchmark_state"] = "Maharashtra"
        
    if "benchmark_district" not in st.session_state:
        st.session_state["benchmark_district"] = "Mumbai City"

    if "institution_name" not in st.session_state:
        st.session_state["institution_name"] = "National Institute of Health & Sciences"

    if "report_cycle" not in st.session_state:
        st.session_state["report_cycle"] = "Q2 FY 2026-27 Compliance Evaluation"
        
    if "audit_df" not in st.session_state:
        # Load sample data automatically for clean hackathon demo on start
        sample_path = os.path.join("datasets", "processed_data.csv")
        if os.path.exists(sample_path):
            try:
                raw_df = pd.read_csv(sample_path)
                proc = DatasetProcessor()
                st.session_state["audit_df"] = proc.clean_audit_data(raw_df)
                st.session_state["data_processed"] = True
            except Exception:
                st.session_state["audit_df"] = pd.DataFrame()
        else:
            st.session_state["audit_df"] = pd.DataFrame()

    if "compliance_results" not in st.session_state:
        st.session_state["compliance_results"] = {}
        
    if "epr_results" not in st.session_state:
        st.session_state["epr_results"] = {}
        
    if "score_details" not in st.session_state:
        st.session_state["score_details"] = {}
        
    if "roadmap" not in st.session_state:
        st.session_state["roadmap"] = {}

    if "ai_audit_report" not in st.session_state:
        st.session_state["ai_audit_report"] = {}

    # New engines
    if "compliance_scores" not in st.session_state:
        st.session_state["compliance_scores"] = {}

    if "carbon_impact" not in st.session_state:
        st.session_state["carbon_impact"] = {}

    if "benchmark_ranking" not in st.session_state:
        st.session_state["benchmark_ranking"] = {}

def run_analysis_pipelines():
    """Triggers all analytical engines on the loaded dataset."""
    df = st.session_state["audit_df"]
    if df.empty:
        return

    state_name = st.session_state.get("benchmark_state", "Maharashtra")
    district_name = st.session_state.get("benchmark_district", "Mumbai City")

    # 1. Run compliance checker with regional parameters
    checker = ComplianceChecker()
    st.session_state["compliance_results"] = checker.get_ai_compliance_report(df, state_name=state_name, district_name=district_name)

    # 2. Run EPR analysis
    epr_calc = EPRCalculator()
    st.session_state["epr_results"] = epr_calc.calculate_epr_obligations(df)

    # 3. Calculate Sustainability Index with benchmark inputs
    scorer = SustainabilityScorer()
    violations = st.session_state["compliance_results"].get("violations", [])
    st.session_state["score_details"] = scorer.calculate_sustainability_index(
        df, violations, state_name=state_name, district_name=district_name
    )

    # 4. Generate 12-Month roadmap targets
    roadmap_gen = RoadmapGenerator()
    analyzer = AuditAnalyzer()
    summary = analyzer.calculate_summary_metrics(df)
    st.session_state["roadmap"] = roadmap_gen.generate_12_month_roadmap(summary, st.session_state["score_details"])

    # 5. Run AI Audit Assistant
    from modules.ai_audit_assistant import AIAuditAssistant
    assistant = AIAuditAssistant()
    institution_details = {
        "name": st.session_state.get("institution_name", "National Institute of Health & Sciences"),
        "report_cycle": st.session_state.get("report_cycle", "Q2 FY 2026-27 Compliance Evaluation"),
        "state": state_name,
        "district": district_name
    }
    st.session_state["ai_audit_report"] = assistant.generate_audit_report(
        institution_details=institution_details,
        df=df,
        compliance_results=st.session_state["compliance_results"],
        epr_results=st.session_state["epr_results"],
        score_details=st.session_state["score_details"]
    )

    # 6. Compliance Score Engine — three transparent scores
    violations = st.session_state["compliance_results"].get("violations", [])
    score_engine = ComplianceScoreEngine()
    st.session_state["compliance_scores"] = score_engine.compute(df, violations)

    # 7. Carbon Impact Analysis
    carbon_analyzer = CarbonImpactAnalyzer()
    st.session_state["carbon_impact"] = carbon_analyzer.analyze(df)

    # 8. Benchmark Ranking
    metrics_d = st.session_state["score_details"].get("metrics", {})
    inst_monthly = metrics_d.get("institution_monthly_avg_kg", 0.0)
    ranker = BenchmarkRanker()
    st.session_state["benchmark_ranking"] = ranker.rank(state_name, district_name, inst_monthly)

def main():
    init_session_state()
    
    # Process initial analysis if df was preloaded
    if st.session_state["data_processed"] and not st.session_state["score_details"]:
        run_analysis_pipelines()


    # Sidebar branding & controls
    st.sidebar.markdown("<h2 style='color:#1E4620; text-align:center;'>♻️ PlasticWise AI</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("<p style='text-align:center; font-style:italic;'>India PWM & EPR Compliance Hub</p>", unsafe_allow_html=True)
    st.sidebar.divider()
    
    # Regional selector controls for Benchmarking comparisons
    st.sidebar.subheader("Benchmark Settings")
    state_options = ["Maharashtra", "Tamil Nadu", "Delhi", "Karnataka", "Uttar Pradesh", "West Bengal", "Gujarat"]
    district_map = {
        "Maharashtra": "Mumbai City",
        "Tamil Nadu": "Chennai",
        "Delhi": "New Delhi",
        "Karnataka": "Bengaluru Urban",
        "Uttar Pradesh": "Lucknow",
        "West Bengal": "Kolkata",
        "Gujarat": "Ahmedabad"
    }
    
    selected_state = st.sidebar.selectbox(
        "Regional Benchmark State",
        options=state_options,
        index=state_options.index(st.session_state["benchmark_state"])
    )
    
    selected_district = district_map[selected_state]
    st.sidebar.caption(f"Mapped District: **{selected_district}**")
    
    # Handle state/district changes
    if (selected_state != st.session_state["benchmark_state"] or 
        selected_district != st.session_state["benchmark_district"]):
        st.session_state["benchmark_state"] = selected_state
        st.session_state["benchmark_district"] = selected_district
        run_analysis_pipelines()
        st.sidebar.success("Recalculating regional comparison stats...")

    st.sidebar.divider()
    
    # Main Header
    st.markdown("<h1 class='main-title'>PlasticWise AI</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Institutional Plastic Audit Report Generator & Compliance Officer Dashboard</p>", unsafe_allow_html=True)

    # Layout overview
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Welcome to the Compliance Dashboard")
        st.markdown(
            "PlasticWise AI assists universities, campuses, and healthcare networks "
            "in monitoring plastic packaging volumes, validating disposal processes, and "
            "complying with the Ministry of Environment, Forest & Climate Change (MoEFCC) updates. "
        )
        
        st.info(
            "💡 **How to proceed:**\n"
            "1. Access the **Audit Form** page from the sidebar to upload audit sheets or input details.\n"
            "2. View charts and KPIs on the **Dashboard** page.\n"
            "3. Assess legal violations and EPR recycling offsets in the **Compliance** and **EPR Analysis** tabs.\n"
            "4. Compile and download audit reports on the **Report Viewer** page."
        )

        st.markdown("#### Primary Indian Regulatory References Tracked")
        st.markdown(
            "- **Rule 4(c) Micron Limit**: Restriction on carry bags of thickness less than 120 microns.\n"
            "- **Rule 15 Single-Use Ban**: Prohibition of standard polystyrene plates, cutlery, and wraps.\n"
            "- **EPR Targets Schedule**: Categorization and recycling offset target weights for Categories I, II, III, and IV."
        )

    with col2:
        st.markdown("### Institutional Summary")
        if not st.session_state["audit_df"].empty:
            score_data = st.session_state["score_details"]
            metrics = score_data.get("metrics", {})
            
            st.markdown(
                f"<div class='metric-card'>"
                f"<h4>Sustainability Performance</h4>"
                f"<h2 style='color:{score_data.get('color')};'>{score_data.get('score', 0.0)}/100</h2>"
                f"<p><b>Grade:</b> {score_data.get('grade')}</p>"
                f"<hr>"
                f"<ul>"
                f"<li><b>Recycling Rate:</b> {metrics.get('recycling_rate_pct')}%</li>"
                f"<li><b>Single-Use Share:</b> {metrics.get('sup_proportion_pct')}%</li>"
                f"<li><b>Active Violations:</b> {metrics.get('active_violations_count')}</li>"
                f"</ul>"
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            st.warning("No audit records loaded yet. Use the Audit Form page to ingest data.")

if __name__ == "__main__":
    main()
