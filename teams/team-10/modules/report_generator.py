import os
from datetime import datetime
import pandas as pd
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from modules.data_loader import load_epr_data

class ReportGenerator:
    def __init__(self):
        pass

    def _set_cell_background(self, cell, fill_color: str):
        """Sets XML cell background tint in docx tables."""
        tcPr = cell._tc.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_color}"/>')
        tcPr.append(shd)

    def generate_docx_report(self, report_data: dict, output_path: str) -> str:
        """
        Creates an executive Word Document report mapping institutional waste metrics.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc = Document()
        
        # Configure standard document margins
        for section in doc.sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)

        # Style normal font
        doc.styles['Normal'].font.name = 'Arial'
        doc.styles['Normal'].font.size = Pt(11)

        # =====================================================================
        # 1. COVER PAGE
        # =====================================================================
        title_p = doc.add_paragraph()
        title_p.paragraph_format.space_before = Pt(80)
        title_run = title_p.add_run("PLASTIC WASTE AUDIT & REGULATORY\nCOMPLIANCE REPORT")
        title_run.bold = True
        title_run.font.size = Pt(24)
        title_run.font.color.rgb = RGBColor(30, 70, 32)
        title_p.alignment = 1

        subtitle_p = doc.add_paragraph()
        sub_run = subtitle_p.add_run("Extended Producer Responsibility (EPR) & PWM Rules 2016 Evaluation")
        sub_run.font.size = Pt(12)
        sub_run.italic = True
        subtitle_p.alignment = 1

        doc.add_paragraph().paragraph_format.space_after = Pt(100)

        meta_p = doc.add_paragraph()
        m_run1 = meta_p.add_run(f"AUDITED INSTITUTION: ")
        m_run1.bold = True
        meta_p.add_run(f"{report_data.get('institution_name', 'National Institute of Health & Sciences')}\n")
        m_run2 = meta_p.add_run(f"REPORT CYCLE: ")
        m_run2.bold = True
        meta_p.add_run(f"{report_data.get('report_cycle', 'Q2 FY 2026-27')}\n")
        m_run3 = meta_p.add_run(f"DATE GENERATED: ")
        m_run3.bold = True
        meta_p.add_run(f"{datetime.now().strftime('%d %B, %Y')}\n")
        m_run4 = meta_p.add_run(f"COMPLIANCE STANDARDS: ")
        m_run4.bold = True
        meta_p.add_run(f"Ministry of Environment, Forest & Climate Change (MoEFCC), India")
        meta_p.alignment = 1

        doc.add_page_break()

        # =====================================================================
        # 2. EXECUTIVE SUMMARY
        # =====================================================================
        h1 = doc.add_paragraph()
        h1_run = h1.add_run("1. Executive Summary")
        h1_run.bold = True
        h1_run.font.size = Pt(14)
        h1_run.font.color.rgb = RGBColor(30, 70, 32)

        summary_metrics = report_data.get("summary_metrics", {})
        score_details = report_data.get("score_details", {})
        ai_report = report_data.get("ai_audit_report", {})

        doc.add_paragraph(
            f"This audit report analyzes institutional plastic waste generation and compliance profiles. "
            f"During the current audit cycle, the system registered {summary_metrics.get('total_records', 0)} waste audits, "
            f"tracking a total quantity of {summary_metrics.get('total_weight_kg', 0.0):,.1f} kg of plastic packaging materials. "
            f"Overall Sustainability Rating Index is calculated at {score_details.get('score', 0.0)}/100 ({score_details.get('grade', 'N/A')})."
        )
        if ai_report and "executive_summary" in ai_report:
            doc.add_paragraph(ai_report.get("executive_summary"))

        doc.add_paragraph()

        # =====================================================================
        # 3. INSTITUTION PROFILE
        # =====================================================================
        h_prof = doc.add_paragraph()
        hp_run = h_prof.add_run("2. Institution Profile")
        hp_run.bold = True
        hp_run.font.size = Pt(14)
        hp_run.font.color.rgb = RGBColor(30, 70, 32)

        bench = score_details.get("benchmarks", {})
        state_name = bench.get("state_name", "Maharashtra")
        district_name = bench.get("district_name", "Mumbai City")

        prof_table = doc.add_table(rows=4, cols=2)
        prof_table.style = 'Light Shading Accent 1'
        profile_data = [
            ("Institution Name", report_data.get('institution_name')),
            ("State Pollution Control Board State", state_name),
            ("Municipal Corporation / District", district_name),
            ("Evaluation Cycle", report_data.get('report_cycle'))
        ]
        for idx, (k, v) in enumerate(profile_data):
            row = prof_table.rows[idx]
            row.cells[0].text = k
            row.cells[1].text = str(v)
            row.cells[0].paragraphs[0].runs[0].bold = True

        doc.add_paragraph()

        # =====================================================================
        # 4. WASTE INVENTORY SUMMARY
        # =====================================================================
        h_inv = doc.add_paragraph()
        hi_run = h_inv.add_run("3. Waste Inventory Summary")
        hi_run.bold = True
        hi_run.font.size = Pt(14)
        hi_run.font.color.rgb = RGBColor(30, 70, 32)

        doc.add_paragraph("The table below compiles active audit values categorised under plastic packaging types:")
        
        # Pull category weights
        epr_results = report_data.get("epr_results", {})
        category_targets = epr_results.get("category_targets", {})
        
        inv_table = doc.add_table(rows=len(category_targets) + 1, cols=3)
        inv_table.style = 'Light Shading Accent 1'
        
        inv_table.rows[0].cells[0].text = "EPR Category"
        inv_table.rows[0].cells[1].text = "Audited Volume (kg)"
        inv_table.rows[0].cells[2].text = "Disposal Target Rate (%)"
        for cell in inv_table.rows[0].cells:
            self._set_cell_background(cell, "1E4620")
            cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
            cell.paragraphs[0].runs[0].bold = True

        for idx, (cat_name, targets) in enumerate(category_targets.items(), 1):
            row = inv_table.rows[idx]
            row.cells[0].text = cat_name
            row.cells[1].text = f"{targets['total_volume_kg']:.1f} kg"
            row.cells[2].text = f"{targets['obligation_rate_pct']:.0f}%"

        doc.add_paragraph()

        # =====================================================================
        # 5. COMPLIANCE GAP ANALYSIS
        # =====================================================================
        h_gap = doc.add_paragraph()
        hg_run = h_gap.add_run("4. Statutory Compliance Gap Analysis (PWM Rules 2016)")
        hg_run.bold = True
        hg_run.font.size = Pt(14)
        hg_run.font.color.rgb = RGBColor(30, 70, 32)

        violations = report_data.get("compliance_results", {}).get("violations", [])
        
        # Structured Gaps Table
        doc.add_paragraph("The rule engine executed checks against India's national plastic guidelines:")
        
        rules_defs = {
            "PWM_RULE_4C_MICRONS": ("Rule 4(c)", "Min carry bag thickness of 120 microns", "Critical", "Replace carry bags and sheets immediately with >120 microns or certified compostables."),
            "NGT_OPEN_BURNING_BAN": ("Rule 16 / NGT", "Strict ban on open burning of plastic waste", "Critical", "Cease open waste burning immediately; formalize secure recycling collections."),
            "PWM_SUP_BAN_2022": ("Rule 15 / SUP Ban", "Prohibition of banned single-use polystyrene cutlery/plates", "High", "Transition cafeteria cups/cutlery to wooden, paper, or steel reuse alternatives.")
        }
        
        gap_table = doc.add_table(rows=len(rules_defs) + 1, cols=6)
        gap_table.style = 'Light Shading Accent 1'
        headers = ["Rule Ref", "Requirement", "Current Status", "Gap Identified", "Risk", "Corrective Action"]
        for c_idx, h_text in enumerate(headers):
            gap_table.rows[0].cells[c_idx].text = h_text
            self._set_cell_background(gap_table.rows[0].cells[c_idx], "1E4620")
            gap_table.rows[0].cells[c_idx].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
            gap_table.rows[0].cells[c_idx].paragraphs[0].runs[0].bold = True

        for r_idx, (rule_id, (ref, req, risk, action)) in enumerate(rules_defs.items(), 1):
            match = [v for v in violations if v["rule_id"] == rule_id]
            row = gap_table.rows[r_idx]
            row.cells[0].text = ref
            row.cells[1].text = req
            row.cells[4].text = risk
            row.cells[5].text = action
            
            if match:
                viol = match[0]
                row.cells[2].text = f"⚠️ NON-CONFORMANT"
                row.cells[3].text = viol["description"]
            else:
                row.cells[2].text = "✅ Compliant"
                row.cells[3].text = "None"
                row.cells[4].text = "Low"
                row.cells[5].text = "Maintain segregation checklists."

        doc.add_paragraph()

        # =====================================================================
        # 6. EPR ASSESSMENT
        # =====================================================================
        h_epr = doc.add_paragraph()
        he_run = h_epr.add_run("5. Extended Producer Responsibility (EPR) Assessment")
        he_run.bold = True
        he_run.font.size = Pt(14)
        he_run.font.color.rgb = RGBColor(30, 70, 32)

        bulk_status = epr_results.get("bulk_status", {})
        overall_liability = epr_results.get("overall_epr_liability_kg", 0.0)
        
        doc.add_paragraph(
            f"Under CPCB guidelines, the institution is classified as: "
            f"{'BULK WASTE GENERATOR' if bulk_status.get('is_bulk') else 'SME GENERATOR'}. "
            f"Audit calculations register a total required recycling offset target weight of {overall_liability:.1f} kg."
        )
        
        epr_table = doc.add_table(rows=len(category_targets) + 1, cols=4)
        epr_table.style = 'Light Shading Accent 1'
        epr_headers = ["Category", "Audited Qty (kg)", "Target Offset (%)", "Target Weight (kg)"]
        for c_idx, h_text in enumerate(epr_headers):
            epr_table.rows[0].cells[c_idx].text = h_text
            self._set_cell_background(epr_table.rows[0].cells[c_idx], "1E4620")
            epr_table.rows[0].cells[c_idx].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
            epr_table.rows[0].cells[c_idx].paragraphs[0].runs[0].bold = True

        for idx, (cat_name, targets) in enumerate(category_targets.items(), 1):
            row = epr_table.rows[idx]
            row.cells[0].text = cat_name
            row.cells[1].text = f"{targets['total_volume_kg']:.1f}"
            row.cells[2].text = f"{targets['obligation_rate_pct']:.0f}%"
            row.cells[3].text = f"{targets['recycling_obligation_kg']:.1f}"

        doc.add_paragraph()

        # =====================================================================
        # 7. BENCHMARK ANALYSIS
        # =====================================================================
        h_ben = doc.add_paragraph()
        hbe_run = h_ben.add_run("6. Dataset Driven Benchmark Analysis")
        hbe_run.bold = True
        hbe_run.font.size = Pt(14)
        hbe_run.font.color.rgb = RGBColor(30, 70, 32)

        inst_monthly = score_details.get("metrics", {}).get("institution_monthly_avg_kg", 0.0)
        state_avg = bench.get("state_average_kg", 220.0)
        city_avg = bench.get("city_average_kg", 180.0)

        doc.add_paragraph(
            f"• Current Institutional average: {inst_monthly:.1f} kg/month.\n"
            f"• SPCB Regional average for {state_name}: {state_avg:.1f} kg/month.\n"
            f"• Municipal baseline for {district_name}: {city_avg:.1f} kg/month.\n"
            f"The institution waste footprint rating is '{bench.get('city_comparison_status', 'N/A')}' compared to local municipal averages."
        )

        doc.add_paragraph()

        # =====================================================================
        # 8. SUSTAINABILITY SCORE
        # =====================================================================
        h_sc = doc.add_paragraph()
        hsc_run = h_sc.add_run("7. Sustainability Score")
        hsc_run.bold = True
        hsc_run.font.size = Pt(14)
        hsc_run.font.color.rgb = RGBColor(30, 70, 32)

        doc.add_paragraph(
            f"Sustainability Index: {score_details.get('score', 0.0)}/100 | Grade: {score_details.get('grade', 'N/A')}\n"
            f"Details: {score_details.get('explanation')}"
        )

        doc.add_paragraph()

        # =====================================================================
        # 9. 12-MONTH ROADMAP (NATIVE FLOWCHART IN DOCX)
        # =====================================================================
        h_road = doc.add_paragraph()
        hro_run = h_road.add_run("8. 12-Month Action Roadmap")
        hro_run.bold = True
        hro_run.font.size = Pt(14)
        hro_run.font.color.rgb = RGBColor(30, 70, 32)

        doc.add_paragraph("A structured transition schedule is plotted horizontally as a milestone flowchart below:")

        # Draw a beautiful horizontal flowchart table in Word
        flow_table = doc.add_table(rows=1, cols=7)
        flow_table.style = 'Table Grid'
        
        # Steps
        steps = [
            ("Months 1-3", "Policy & Setup\n\n• Policy Setup\n• SUP Ban\n• Vendor Reg", "1E4620"),
            ("➔", "Next Phase", "ffffff"),
            ("Months 4-6", "Segregation Infra\n\n• Bins Setup\n• Staff Training\n• Logging", "5C8D89"),
            ("➔", "Next Phase", "ffffff"),
            ("Months 7-9", "Partnerships\n\n• Recycler MoUs\n• Tracking logs\n• EPR Target", "8FBC8F"),
            ("➔", "Next Phase", "ffffff"),
            ("Months 10-12", "Certification\n\n• Final Audit\n• Green Campus\n• 100% Target", "D9822B")
        ]
        
        for c_idx, (title, details, bg_col) in enumerate(steps):
            cell = flow_table.rows[0].cells[c_idx]
            if title == "➔":
                cell.text = "\n\n  ➔"
                cell.paragraphs[0].runs[0].font.size = Pt(20)
                cell.paragraphs[0].runs[0].bold = True
                cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(92, 141, 137)
            else:
                cell.text = f"{title}\n{details}"
                self._set_cell_background(cell, bg_col)
                cell.paragraphs[0].runs[0].bold = True
                cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
                # Apply light color to the details
                for run in cell.paragraphs[0].runs[1:]:
                    run.font.color.rgb = RGBColor(245, 245, 245)
                    run.font.size = Pt(9.5)

        doc.add_paragraph()

        # =====================================================================
        # 10. RECOMMENDATIONS
        # =====================================================================
        h_rec = doc.add_paragraph()
        hrc_run = h_rec.add_run("9. Strategic Waste Reduction Recommendations")
        hrc_run.bold = True
        hrc_run.font.size = Pt(14)
        hrc_run.font.color.rgb = RGBColor(30, 70, 32)

        recs_list = ai_report.get("waste_reduction_recommendations", [])
        if recs_list:
            for r in recs_list:
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Inches(0.25)
                p.add_run(f"• {r.get('recommendation', '')} ").bold = True
                p.add_run(f"(Expected Impact: {r.get('expected_impact', '')})")
        else:
            doc.add_paragraph("• Shift food service vendors to non-plastic packaging.")
            doc.add_paragraph("• Implement source segregation color-coded waste bins.")

        doc.add_paragraph()

        # =====================================================================
        # 11. FINAL CONCLUSION
        # =====================================================================
        h_con = doc.add_paragraph()
        hco_run = h_con.add_run("10. Final Auditor Conclusion")
        hco_run.bold = True
        hco_run.font.size = Pt(14)
        hco_run.font.color.rgb = RGBColor(30, 70, 32)

        doc.add_paragraph(ai_report.get("final_auditor_conclusion", "The audited institution is recommended to execute the 12-month transition roadmap to achieve full CPCB and SPCB regulatory compliance."))

        doc.add_page_break()

        # =====================================================================
        # 12. ANNEXURES
        # =====================================================================
        h_ann = doc.add_paragraph()
        han_run = h_ann.add_run("Annexures Section")
        han_run.bold = True
        han_run.font.size = Pt(16)
        han_run.font.color.rgb = RGBColor(30, 70, 32)

        # Annexure A: Raw Audit Dataset
        p_ana = doc.add_paragraph()
        paa_run = p_ana.add_run("Annexure A: Raw Monitored Audit Dataset")
        paa_run.bold = True
        paa_run.font.size = Pt(12)
        
        # Display first 15 records in table
        df = report_data.get("audit_df", pd.DataFrame())
        raw_table = doc.add_table(rows=min(15, len(df)) + 1, cols=5)
        raw_table.style = 'Light Shading Accent 1'
        raw_hdrs = ["Date Logged", "Resin Code", "Weight (kg)", "Pathway", "Thickness"]
        for c_idx, h_text in enumerate(raw_hdrs):
            raw_table.rows[0].cells[c_idx].text = h_text
            self._set_cell_background(raw_table.rows[0].cells[c_idx], "1E4620")
            raw_table.rows[0].cells[c_idx].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
            raw_table.rows[0].cells[c_idx].paragraphs[0].runs[0].bold = True

        for idx, row in df.head(15).iterrows():
            r_idx = idx + 1
            raw_table.rows[r_idx].cells[0].text = str(row.get("date", ""))[:10]
            raw_table.rows[r_idx].cells[1].text = str(row.get("resin_code", ""))
            raw_table.rows[r_idx].cells[2].text = f"{row.get('weight_kg', 0.0):.1f}"
            raw_table.rows[r_idx].cells[3].text = str(row.get("disposal_method", ""))
            raw_table.rows[r_idx].cells[4].text = f"{row.get('thickness_microns', 0.0):.0f}" if pd.notna(row.get("thickness_microns")) else "N/A"

        doc.add_paragraph()

        # Annexure B: Compliance Checklist
        p_anb = doc.add_paragraph()
        pab_run = p_anb.add_run("Annexure B: Statutory Checklist Registry")
        pab_run.bold = True
        pab_run.font.size = Pt(12)
        doc.add_paragraph(
            "1. Rule 4(c) carry bag thickness >= 120 microns: Evaluated.\n"
            "2. Rule 15 single-use plastic ban compliance: Evaluated.\n"
            "3. Rule 16 ban on open facility waste incineration: Evaluated."
        )

        doc.add_paragraph()

        # Annexure C: EPR Benchmark Tables
        p_anc = doc.add_paragraph()
        pac_run = p_anc.add_run("Annexure C: CPCB EPR Benchmark Tables")
        pac_run.bold = True
        pac_run.font.size = Pt(12)
        
        epr_df = load_epr_data()
        epr_bench_table = doc.add_table(rows=len(epr_df) + 1, cols=4)
        epr_bench_table.style = 'Light Shading Accent 1'
        epr_b_hdrs = ["Category Name", "Registered Brands", "Recycling Target", "CPCB Sector Offset"]
        for c_idx, h_text in enumerate(epr_b_hdrs):
            epr_bench_table.rows[0].cells[c_idx].text = h_text
            self._set_cell_background(epr_bench_table.rows[0].cells[c_idx], "1E4620")
            epr_bench_table.rows[0].cells[c_idx].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
            epr_bench_table.rows[0].cells[c_idx].paragraphs[0].runs[0].bold = True

        for idx, row in epr_df.iterrows():
            r_idx = idx + 1
            epr_bench_table.rows[r_idx].cells[0].text = str(row.get("epr_category", ""))
            epr_bench_table.rows[r_idx].cells[1].text = f"{row.get('national_registered_brands_count', 0):,}"
            epr_bench_table.rows[r_idx].cells[2].text = f"{row.get('average_recycling_target_pct', 0.0):.0f}%"
            epr_bench_table.rows[r_idx].cells[3].text = f"{row.get('cpcb_industry_offset_tonnes', 0.0):,} tonnes"

        doc.add_paragraph()

        # Annexure D: Dataset References
        p_and = doc.add_paragraph()
        pad_run = p_and.add_run("Annexure D: Regulatory Dataset References")
        pad_run.bold = True
        pad_run.font.size = Pt(12)
        doc.add_paragraph(
            "• Dataset 1: CPCB Plastic Waste Management State statistics (https://cpcb.nic.in/plastic-waste-management/)\n"
            "• Dataset 2: Swachh Bharat Mission (Urban) Municipal waste records (https://sbmurban.org/)\n"
            "• Dataset 3: CPCB Extended Producer Responsibility portal registry (https://eprplastic.cpcb.gov.in/)"
        )

        doc.save(output_path)
        return output_path

    def generate_pdf_report(self, report_data: dict, output_path: str) -> str:
        """
        Creates an executive PDF report using ReportLab Flowables.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc = SimpleDocTemplate(output_path, pagesize=letter,
                                rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            name="TitleStyle",
            parent=styles["Title"],
            textColor=colors.HexColor("#1E4620"),
            fontSize=18,
            leading=22,
            spaceAfter=15
        )
        
        h1_style = ParagraphStyle(
            name="H1Style",
            parent=styles["Heading1"],
            textColor=colors.HexColor("#1E4620"),
            fontSize=12,
            leading=16,
            spaceBefore=12,
            spaceAfter=8
        )
        
        body_style = styles["Normal"]
        story = []
        
        # Cover details
        story.append(Paragraph("<b>PLASTIC AUDIT & COMPLIANCE EVALUATION REPORT</b>", title_style))
        story.append(Paragraph(f"<b>Institution:</b> {report_data.get('institution_name')}", body_style))
        story.append(Paragraph(f"<b>Cycle:</b> {report_data.get('report_cycle')}", body_style))
        story.append(Paragraph(f"<b>Date Generated:</b> {datetime.now().strftime('%d %B, %Y')}", body_style))
        story.append(Spacer(1, 15))
        
        # 1. Executive Summary
        story.append(Paragraph("<b>1. Executive Performance Summary</b>", h1_style))
        summary = report_data.get("summary_metrics", {})
        score = report_data.get("score_details", {})
        ai_report = report_data.get("ai_audit_report", {})
        
        exec_text = (
            f"Monitored waste audits: {summary.get('total_records', 0)} logged entries. "
            f"Total monitored weight is {summary.get('total_weight_kg', 0.0):.1f} kg. "
            f"Overall Sustainability Rating Index is: <b>{score.get('score', 0.0)}/100 ({score.get('grade', 'N/A')})</b>."
        )
        story.append(Paragraph(exec_text, body_style))
        if ai_report and "executive_summary" in ai_report:
            story.append(Spacer(1, 5))
            story.append(Paragraph(ai_report.get("executive_summary"), body_style))
        story.append(Spacer(1, 10))

        # 2. Compliance Gap Analysis
        story.append(Paragraph("<b>2. Statutory Gaps Analysis (PWM Rules 2016)</b>", h1_style))
        violations = report_data.get("compliance_results", {}).get("violations", [])
        
        rules_defs = {
            "PWM_RULE_4C_MICRONS": ("Rule 4(c)", "Min carry bag thickness of 120 microns", "Critical", "Replace carry bags and sheets immediately with >120 microns or certified compostables."),
            "NGT_OPEN_BURNING_BAN": ("Rule 16 / NGT", "Strict ban on open burning of plastic waste", "Critical", "Cease open waste burning immediately; formalize secure recycling collections."),
            "PWM_SUP_BAN_2022": ("Rule 15 / SUP Ban", "Prohibition of banned single-use polystyrene cutlery/plates", "High", "Transition cafeteria cups/cutlery to wooden, paper, or steel reuse alternatives.")
        }
        
        gap_table_data = [[
            Paragraph("<b>Rule</b>", body_style),
            Paragraph("<b>Req</b>", body_style),
            Paragraph("<b>Status</b>", body_style),
            Paragraph("<b>Gap</b>", body_style)
        ]]
        
        for rule_id, (ref, req, risk, action) in rules_defs.items():
            match = [v for v in violations if v["rule_id"] == rule_id]
            if match:
                gap_table_data.append([
                    Paragraph(ref, body_style),
                    Paragraph(req, body_style),
                    Paragraph("⚠️ NON-CONFORM", body_style),
                    Paragraph(match[0]["description"], body_style)
                ])
            else:
                gap_table_data.append([
                    Paragraph(ref, body_style),
                    Paragraph(req, body_style),
                    Paragraph("✅ Compliant", body_style),
                    Paragraph("None", body_style)
                ])
        gt = Table(gap_table_data, colWidths=[60, 150, 80, 210])
        gt.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#D2E5D0")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(gt)
        story.append(Spacer(1, 10))

        # 3. EPR Assessment
        story.append(Paragraph("<b>3. EPR Target Obligation Assessment</b>", h1_style))
        epr_results = report_data.get("epr_results", {})
        overall_liability = epr_results.get("overall_epr_liability_kg", 0.0)
        category_targets = epr_results.get("category_targets", {})
        
        epr_text = (
            f"CPCB Bulk Generator Status: <b>{'Classified as Bulk Generator' if epr_results.get('bulk_status', {}).get('is_bulk') else 'Compliant SME Generator'}</b>. "
            f"Monitored packaging EPR target weight: <b>{overall_liability:.1f} kg</b>."
        )
        story.append(Paragraph(epr_text, body_style))
        story.append(Spacer(1, 5))
        
        epr_table_data = [[
            Paragraph("<b>EPR Category</b>", body_style),
            Paragraph("<b>Audited (kg)</b>", body_style),
            Paragraph("<b>Target Rate (%)</b>", body_style),
            Paragraph("<b>Required (kg)</b>", body_style)
        ]]
        for cat_name, targets in category_targets.items():
            epr_table_data.append([
                Paragraph(cat_name, body_style),
                f"{targets['total_volume_kg']:.1f}",
                f"{targets['obligation_rate_pct']:.0f}%",
                f"{targets['recycling_obligation_kg']:.1f}"
            ])
        et = Table(epr_table_data, colWidths=[200, 100, 100, 100])
        et.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#D2E5D0")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(et)
        story.append(Spacer(1, 10))

        # 4. Roadmap (Plotly horizontal milestones representation in text flowchart block)
        story.append(Paragraph("<b>4. 12-Month Action Roadmap</b>", h1_style))
        roadmap_list = ai_report.get("roadmap_12_month", [])
        
        road_table_data = [[
            Paragraph("<b>Month</b>", body_style),
            Paragraph("<b>Activities & substitution paths</b>", body_style),
            Paragraph("<b>Compliance Outcomes</b>", body_style)
        ]]
        for phase in roadmap_list:
            act_str = "<br/>".join([f"- {a}" for a in phase.get("activities", [])])
            out_str = f"Outcome: {phase.get('expected_outcome')}<br/>Compliance: {phase.get('compliance_improvement')}"
            road_table_data.append([
                Paragraph(f"<b>{phase.get('month')}</b><br/>{phase.get('target')}", body_style),
                Paragraph(act_str, body_style),
                Paragraph(out_str, body_style)
            ])
        rot = Table(road_table_data, colWidths=[100, 220, 180])
        rot.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#D2E5D0")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(rot)
        story.append(Spacer(1, 10))

        # PageBreak for Annexures
        story.append(PageBreak())

        # Annexures Title
        story.append(Paragraph("<b>Report Annexures Section</b>", title_style))
        story.append(Spacer(1, 10))

        # Annexure A
        story.append(Paragraph("<b>Annexure A: Raw Monitored Audit Dataset</b>", h1_style))
        df = report_data.get("audit_df", pd.DataFrame())
        raw_table_data = [[
            Paragraph("<b>Date</b>", body_style),
            Paragraph("<b>Resin</b>", body_style),
            Paragraph("<b>Weight (kg)</b>", body_style),
            Paragraph("<b>Disposal</b>", body_style)
        ]]
        for idx, row in df.head(10).iterrows():
            raw_table_data.append([
                str(row.get("date", ""))[:10],
                str(row.get("resin_code", "")),
                f"{row.get('weight_kg', 0.0):.1f}",
                str(row.get("disposal_method", ""))
            ])
        rt = Table(raw_table_data, colWidths=[120, 80, 100, 200])
        rt.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#D2E5D0")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(rt)
        story.append(Spacer(1, 10))

        # Annexure D References
        story.append(Paragraph("<b>Annexure D: Regulatory Dataset References</b>", h1_style))
        ref_text = (
            "• Dataset 1: Central Pollution Control Board PWM guidelines (https://cpcb.nic.in/plastic-waste-management/)<br/>"
            "• Dataset 2: Swachh Bharat Mission (Urban) Local Body benchmarks (https://sbmurban.org/)<br/>"
            "• Dataset 3: CPCB EPR Portal online registry indexes (https://eprplastic.cpcb.gov.in/)"
        )
        story.append(Paragraph(ref_text, body_style))

        doc.build(story)
        return output_path
