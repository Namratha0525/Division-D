import streamlit as st
import os
import pandas as pd

from modules.report_generator import ReportGenerator
from app import run_analysis_pipelines

# Configure page
st.set_page_config(page_title="Report Generator | PlasticWise AI", layout="wide")

st.markdown("<h1 style='color:#1E4620;'>📄 Compliance Report Viewer & Exporter</h1>", unsafe_allow_html=True)
st.markdown("Compile official compliance reports aligned with national formats.")

df = st.session_state.get("audit_df")

if df is None or df.empty:
    st.warning("Please upload or input audit records on the Audit Form page before generating documents.")
else:
    st.subheader("Document Export Configurations")
    
    institution_name = st.text_input("Institution Name", value=st.session_state.get("institution_name", "National Institute of Health & Sciences"))
    report_cycle = st.text_input("Reporting Cycle Title", value=st.session_state.get("report_cycle", "Q2 FY 2026-27 Compliance Evaluation"))
    
    # Save input updates back to session state
    st.session_state["institution_name"] = institution_name
    st.session_state["report_cycle"] = report_cycle
    
    st.divider()
    
    # Pack data payload for generator (including audit_df for Annexure A)
    report_data = {
        "institution_name": institution_name,
        "report_cycle": report_cycle,
        "summary_metrics": {
            "total_records": len(df),
            "total_weight_kg": float(df["weight_kg"].sum()),
            "recycling_rate_pct": float(df[df["disposal_method"].isin(["RECYCLED", "CO_PROCESSED"])]["weight_kg"].sum() / df["weight_kg"].sum() * 100) if not df.empty else 0.0,
            "recycled_weight_kg": float(df[df["disposal_method"].isin(["RECYCLED", "CO_PROCESSED"])]["weight_kg"].sum())
        },
        "score_details": st.session_state.get("score_details", {}),
        "compliance_results": st.session_state.get("compliance_results", {}),
        "epr_results": st.session_state.get("epr_results", {}),
        "roadmap": st.session_state.get("roadmap", {}),
        "ai_audit_report": st.session_state.get("ai_audit_report", {}),
        "audit_df": df
    }

    docx_path = os.path.join("reports", "generated_docx", "audit_report_latest.docx")
    pdf_path = os.path.join("reports", "generated_pdf", "audit_report_latest.pdf")

    # =====================================================================
    # ⚡ FINAL PRESENTATION MODE (One-click button)
    # =====================================================================
    st.markdown("### ⚡ Final Presentation Mode")
    st.info("💡 Generate both official Word (DOCX) and PDF reports with updated metrics, compliance checklists, EPR obligation status, and the visual timeline roadmap.")
    
    if st.button("⚡ Generate Full Audit", use_container_width=True):
        with st.spinner("Executing full analysis pipelines & generating reports..."):
            try:
                # Force pipeline rerun to sync any input updates
                run_analysis_pipelines()
                
                # Update report data from updated session state
                report_data["score_details"] = st.session_state.get("score_details", {})
                report_data["compliance_results"] = st.session_state.get("compliance_results", {})
                report_data["epr_results"] = st.session_state.get("epr_results", {})
                report_data["roadmap"] = st.session_state.get("roadmap", {})
                report_data["ai_audit_report"] = st.session_state.get("ai_audit_report", {})
                
                generator = ReportGenerator()
                saved_docx = generator.generate_docx_report(report_data, docx_path)
                saved_pdf = generator.generate_pdf_report(report_data, pdf_path)
                
                st.success("🎉 Official Institutional Plastic Audit Report Compiled!")
                
                c_d1, c_d2 = st.columns(2)
                with c_d1:
                    with open(saved_docx, "rb") as f:
                        st.download_button(
                            label="⬇️ Download Word Audit Report (.docx)",
                            data=f.read(),
                            file_name=f"Official_PlasticWise_Audit_Report_{institution_name.replace(' ', '_')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True
                        )
                with c_d2:
                    with open(saved_pdf, "rb") as f:
                        st.download_button(
                            label="⬇️ Download PDF Audit Report (.pdf)",
                            data=f.read(),
                            file_name=f"Official_PlasticWise_Audit_Report_{institution_name.replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
            except Exception as e:
                st.error(f"Error generating reports: {e}")

    st.divider()

    # Split card builders
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Manual Microsoft Word Export")
        if st.button("Build Microsoft Word (.docx) Document"):
            try:
                generator = ReportGenerator()
                saved_path = generator.generate_docx_report(report_data, docx_path)
                with open(saved_path, "rb") as f:
                    st.download_button(
                        label="⬇️ Download DOCX Report",
                        data=f.read(),
                        file_name=f"PlasticWise_Audit_Report_{institution_name.replace(' ', '_')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                st.success("DOCX generated successfully!")
            except Exception as e:
                st.error(f"Error compiling DOCX: {e}")
                
    with col2:
        st.subheader("Manual PDF Printout Export")
        if st.button("Build Adobe PDF (.pdf) Document"):
            try:
                generator = ReportGenerator()
                saved_path = generator.generate_pdf_report(report_data, pdf_path)
                with open(saved_path, "rb") as f:
                    st.download_button(
                        label="⬇️ Download PDF Report",
                        data=f.read(),
                        file_name=f"PlasticWise_Audit_Report_{institution_name.replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
                st.success("PDF generated successfully!")
            except Exception as e:
                st.error(f"Error compiling PDF: {e}")

    # Preview summary outline
    st.markdown("### Report Content Preview Summary")
    st.markdown(f"**Target Entity:** {institution_name}")
    st.markdown(f"**Period:** {report_cycle}")
    
    # Displays the 12-Month roadmap preview
    st.markdown("#### Preview: AI 12-Month Reduction Roadmap Phases")
    roadmap_phases = report_data.get("roadmap", {}).get("phases", [])
    if roadmap_phases:
        for phase in roadmap_phases:
            with st.expander(f"📅 {phase.get('phase_title')} ({phase.get('months')})"):
                st.write("**Initiatives:**")
                for action in phase.get("action_items", []):
                    st.write(f"- {action}")
                st.write(f"**Target Reduction:** -{phase.get('reduction_target_pct')}%")
