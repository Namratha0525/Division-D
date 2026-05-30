import streamlit as st
import pandas as pd
import datetime

from ai.gemini_client import GeminiClient
from ai.prompts import CHATBOT_SYSTEM_PROMPT
from modules.audit_analyzer import AuditAnalyzer
from modules.data_loader import load_cpcb_data, load_swachh_bharat_data, load_epr_data
from modules.advanced_dataset_analyzer import AdvancedDatasetAnalyzer

# ─────────────────────────────────────────────────────────────────────────────
# Page Configuration
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Chatbot | PlasticWise AI", layout="wide")

st.markdown("<h1 style='color:#1E4620;'>💬 PlasticWise AI Advisor</h1>", unsafe_allow_html=True)
st.markdown(
    "Ask operational or legal questions grounded in India's PWM rules, "
    "CPCB benchmarks, Swachh Bharat data, EPR portal data, and your live audit inventory."
)

# ─────────────────────────────────────────────────────────────────────────────
# Context Packet Builder
# ─────────────────────────────────────────────────────────────────────────────
def build_grounded_context_packet() -> tuple[str, dict]:
    """
    Retrieves all six data sources and assembles a structured context packet.
    Returns (context_string, debug_metadata_dict).
    """
    debug = {}

    # ── 1. Current Audit Data ────────────────────────────────────────────────
    df = st.session_state.get("audit_df")
    audit_section = "**[1] Current Audit Data:** No audit records loaded.\n"
    if df is not None and not df.empty:
        analyzer = AuditAnalyzer()
        summary = analyzer.calculate_summary_metrics(df)
        total_kg      = float(df["weight_kg"].sum())
        recycled_kg   = float(df[df["disposal_method"].isin(["RECYCLED", "CO_PROCESSED"])]["weight_kg"].sum())
        landfilled_kg = float(df[df["disposal_method"] == "LANDFILLED"]["weight_kg"].sum())
        incinerated_kg= float(df[df["disposal_method"] == "INCINERATED"]["weight_kg"].sum())
        burnt_kg      = float(df[df["disposal_method"] == "OPEN_BURNT"]["weight_kg"].sum())

        # Per-category breakdown
        ric_map = {1:"PET (Rigid)", 2:"HDPE (Rigid)", 3:"PVC", 4:"LDPE/LLDPE (Flexible)",
                   5:"PP (Flexible)", 6:"PS/Polystyrene (Single-Use)", 7:"Multi-layer/Other"}
        cat_breakdown = []
        for ric, label in ric_map.items():
            w = float(df[df["resin_code"] == ric]["weight_kg"].sum())
            if w > 0:
                cat_breakdown.append(f"  • {label}: {w:.1f} kg")

        audit_section = (
            f"**[1] Current Audit Data ({len(df)} records):**\n"
            f"  • Total Monitored Waste: {total_kg:.1f} kg\n"
            f"  • Recycled / Co-Processed: {recycled_kg:.1f} kg ({(recycled_kg/total_kg*100 if total_kg else 0):.1f}%)\n"
            f"  • Landfilled: {landfilled_kg:.1f} kg\n"
            f"  • Incinerated: {incinerated_kg:.1f} kg\n"
            f"  • Open Burnt (ILLEGAL): {burnt_kg:.1f} kg\n"
            f"  • Polymer Breakdown:\n" + "\n".join(cat_breakdown) + "\n"
        )
        debug["audit_data"] = {
            "records": len(df),
            "total_kg": round(total_kg, 2),
            "recycled_kg": round(recycled_kg, 2),
            "recycling_rate_pct": round(recycled_kg / total_kg * 100 if total_kg else 0, 1),
            "landfilled_kg": round(landfilled_kg, 2),
            "incinerated_kg": round(incinerated_kg, 2),
            "open_burnt_kg": round(burnt_kg, 2),
            "polymer_categories": {ric_map.get(int(r), "Other"): round(float(df[df["resin_code"] == r]["weight_kg"].sum()), 2)
                                   for r in df["resin_code"].unique()},
        }
    else:
        debug["audit_data"] = {"status": "No audit data loaded"}

    # ── 2. Compliance Results ────────────────────────────────────────────────
    compliance = st.session_state.get("compliance_results", {})
    violations = compliance.get("violations", [])
    comp_pct   = compliance.get("compliance_percentage", 100.0)
    crit_viols = compliance.get("critical_violations", 0)
    rating     = compliance.get("overall_compliance_rating", "N/A")

    compliance_section = (
        f"**[2] Compliance Results:**\n"
        f"  • Compliance Rate: {comp_pct:.1f}%\n"
        f"  • Overall Rating: {rating}\n"
        f"  • Total Violations: {len(violations)}\n"
        f"  • Critical Violations: {crit_viols}\n"
    )
    if violations:
        for v in violations:
            compliance_section += f"  • ⚠ Violation [{v.get('rule_id')}]: {v.get('description')}\n"

    debug["compliance_results"] = {
        "compliance_rate_pct": comp_pct,
        "rating": rating,
        "total_violations": len(violations),
        "critical_violations": crit_viols,
        "violations": [{"rule_id": v.get("rule_id"), "desc": v.get("description")} for v in violations],
    }

    # ── 3. EPR Results ───────────────────────────────────────────────────────
    epr_results      = st.session_state.get("epr_results", {})
    bulk_status      = epr_results.get("bulk_status", {})
    epr_liability_kg = epr_results.get("overall_epr_liability_kg", 0.0)
    cat_targets      = epr_results.get("category_targets", {})
    is_bulk          = bulk_status.get("is_bulk", False)

    epr_section = (
        f"**[3] EPR Obligation Assessment:**\n"
        f"  • Generator Classification: {'BULK GENERATOR (>100 kg/day)' if is_bulk else 'SME GENERATOR'}\n"
        f"  • Total EPR Recycling Liability: {epr_liability_kg:.1f} kg\n"
        f"  • Required Recycling Target Rate: 70%\n"
    )
    for cat, t in cat_targets.items():
        epr_section += (
            f"  • {cat}: Audited {t.get('total_volume_kg', 0.0):.1f} kg | "
            f"Target {t.get('obligation_rate_pct', 0.0):.0f}% | "
            f"Required {t.get('recycling_obligation_kg', 0.0):.1f} kg\n"
        )
    debug["epr_results"] = {
        "is_bulk_generator": is_bulk,
        "epr_liability_kg": round(epr_liability_kg, 2),
        "categories": {k: {"audited_kg": v.get("total_volume_kg"), "target_pct": v.get("obligation_rate_pct")}
                       for k, v in cat_targets.items()},
    }

    # ── 4. Sustainability Score ──────────────────────────────────────────────
    score_details = st.session_state.get("score_details", {})
    score_val   = score_details.get("score", 0.0)
    score_grade = score_details.get("grade", "N/A")
    metrics_d   = score_details.get("metrics", {})

    score_section = (
        f"**[4] Sustainability Score:**\n"
        f"  • Sustainability Index: {score_val}/100 | Grade: {score_grade}\n"
        f"  • Recycling Rate: {metrics_d.get('recycling_rate_pct', 0.0)}%\n"
        f"  • Single-Use Plastic Share: {metrics_d.get('sup_proportion_pct', 0.0)}%\n"
        f"  • Active Violations Count: {metrics_d.get('active_violations_count', 0)}\n"
        f"  • Monthly Avg Generation: {metrics_d.get('institution_monthly_avg_kg', 0.0):.1f} kg\n"
    )
    debug["sustainability_score"] = {
        "score": score_val,
        "grade": score_grade,
        "recycling_rate_pct": metrics_d.get("recycling_rate_pct"),
        "sup_proportion_pct": metrics_d.get("sup_proportion_pct"),
        "active_violations": metrics_d.get("active_violations_count"),
        "monthly_avg_kg": metrics_d.get("institution_monthly_avg_kg"),
    }

    # ── 5. CPCB Benchmark Data ───────────────────────────────────────────────
    state_name    = st.session_state.get("benchmark_state", "Maharashtra")
    district_name = st.session_state.get("benchmark_district", "Mumbai City")
    cpcb_df = load_cpcb_data()
    sbm_df  = load_swachh_bharat_data()

    cpcb_row = cpcb_df[cpcb_df["state_name"].str.lower() == state_name.lower()]
    cpcb_section = ""
    retrieved_cpcb = {}
    if not cpcb_row.empty:
        r = cpcb_row.iloc[0]
        cpcb_section = (
            f"**[5] CPCB Benchmark Data — {state_name}:**\n"
            f"  • Annual Plastic Waste: {r['state_annual_plastic_waste_tonnes']:,.0f} tonnes/year\n"
            f"  • Per Capita Generation: {r['average_per_capita_g_day']} g/day\n"
            f"  • State Recycling Rate: {r['recycling_rate_pct']}%\n"
        )
        retrieved_cpcb = {
            "state": state_name,
            "annual_waste_tonnes": float(r["state_annual_plastic_waste_tonnes"]),
            "per_capita_g_day": float(r["average_per_capita_g_day"]),
            "recycling_rate_pct": float(r["recycling_rate_pct"]),
            "source_rows": 1,
            "total_cpcb_rows": len(cpcb_df),
        }
    else:
        cpcb_section = f"**[5] CPCB Benchmark Data:** State '{state_name}' — national avg 35 g/day, 55% recycling rate.\n"
        retrieved_cpcb = {"status": f"No exact match for '{state_name}' in CPCB dataset", "total_rows": len(cpcb_df)}
    debug["cpcb_benchmark"] = retrieved_cpcb

    # ── 6. Swachh Bharat Benchmark Data ─────────────────────────────────────
    sbm_row = sbm_df[sbm_df["district_name"].str.lower() == district_name.lower()]
    sbm_section = ""
    retrieved_sbm = {}
    if not sbm_row.empty:
        r = sbm_df[sbm_df["state_name"].str.lower() == state_name.lower()]
        r = r.iloc[0] if not r.empty else sbm_row.iloc[0]
        sbm_section = (
            f"**[6] Swachh Bharat Mission Benchmark — {district_name}:**\n"
            f"  • Institutional Monthly Average: {r['district_monthly_avg_kg_per_institution']:.1f} kg/month\n"
            f"  • Municipal Waste Collection Rate: {r['municipal_collection_rate_pct']}%\n"
        )
        retrieved_sbm = {
            "district": district_name,
            "monthly_avg_kg": float(r["district_monthly_avg_kg_per_institution"]),
            "collection_rate_pct": float(r["municipal_collection_rate_pct"]),
            "source_rows": 1,
            "total_sbm_rows": len(sbm_df),
        }
    else:
        sbm_section = f"**[6] Swachh Bharat Benchmark:** District '{district_name}' — avg 180 kg/month, 90% collection rate.\n"
        retrieved_sbm = {"status": f"No match for '{district_name}' in SBM dataset", "total_rows": len(sbm_df)}
    debug["sbm_benchmark"] = retrieved_sbm

    # ── 7. EPR Portal Benchmark (CPCB Registered Brands) ────────────────────
    epr_df  = load_epr_data()
    epr_portal_section = "**[7] CPCB EPR Portal — Industry Benchmarks:**\n"
    epr_portal_records = []
    for _, row in epr_df.iterrows():
        epr_portal_section += (
            f"  • {row['epr_category']}: "
            f"{row['national_registered_brands_count']:,} registered brands nationally, "
            f"avg recycling target {row['average_recycling_target_pct']:.0f}%, "
            f"CPCB sector offset {row['cpcb_industry_offset_tonnes']:,} tonnes.\n"
        )
        epr_portal_records.append({
            "category": row["epr_category"],
            "registered_brands": int(row["national_registered_brands_count"]),
            "recycling_target_pct": float(row["average_recycling_target_pct"]),
            "cpcb_offset_tonnes": float(row["cpcb_industry_offset_tonnes"]),
        })
    debug["epr_portal_benchmark"] = {
        "records_retrieved": len(epr_portal_records),
        "categories": epr_portal_records,
    }

    # ── 8. Rajya Sabha Historical Trends (Large Dataset) ────────────────────
    adv = AdvancedDatasetAnalyzer()
    rs_insights = adv.generate_regulatory_insights(state_name)
    rs_section = ""
    retrieved_rs = {}
    if rs_insights:
        trends = rs_insights.get("trends", {})
        trend_lines = [f"  • {yr}: {val:,.1f} tonnes" if val else f"  • {yr}: N/A"
                       for yr, val in trends.items()]
        rs_section = (
            f"**[8] Rajya Sabha Session 266 — {rs_insights.get('state_name')} Historical Waste Data:**\n"
            + "\n".join(trend_lines) + "\n"
            + f"  • Trend Summary: {rs_insights.get('insights_summary')}\n"
        )
        retrieved_rs = {
            "state": rs_insights.get("state_name"),
            "trend_years": list(trends.keys()),
            "trend_values": {yr: val for yr, val in trends.items() if val},
            "growth_rate_pct": rs_insights.get("growth_rate_pct"),
            "dataset": "RS_Session_266_AU_1159_B_and_C_1.csv (35 states, 5 years)",
        }
    else:
        rs_section = f"**[8] Rajya Sabha Session 266:** No data found for state '{state_name}'.\n"
        retrieved_rs = {"status": "No match"}
    debug["rajya_sabha_trends"] = retrieved_rs

    # ── 9. Polymer Trends (Large Dataset) ───────────────────────────────────
    poly_trends = adv.analyze_polymer_trends(2026)
    poly_section = ""
    retrieved_poly = {}
    if poly_trends:
        top_polys = poly_trends.get("top_polymers", [])
        poly_lines = [f"  • {p[0]}: {p[1]:.1f}% market share ({poly_trends['polymer_volumes'].get(p[0], 0):.1f} MT)"
                      for p in top_polys]
        poly_section = (
            f"**[9] Global Polymer Market (2026) — plastic-use-by-polymer.csv:**\n"
            f"  • Total Volume: {poly_trends.get('total_volume_million_tonnes')} million tonnes\n"
            + "\n".join(poly_lines) + "\n"
        )
        retrieved_poly = {
            "year": poly_trends.get("year"),
            "total_mt": poly_trends.get("total_volume_million_tonnes"),
            "top_5_polymers": [p[0] for p in top_polys],
            "dataset": "plastic-use-by-polymer.csv (42 years, 14 polymer types)",
        }
    else:
        poly_section = "**[9] Polymer Trends:** Data unavailable.\n"
        retrieved_poly = {"status": "Data load failed"}
    debug["polymer_trends"] = retrieved_poly

    # ── 10. Application Usage Trends (Large Dataset) ─────────────────────────
    app_trends = adv.analyze_application_usage(2026)
    app_section = ""
    retrieved_app = {}
    if app_trends:
        top_apps = app_trends.get("top_applications", [])
        app_lines = [f"  • {a[0]}: {a[1]:.1f}% ({app_trends['application_volumes'].get(a[0], 0):.1f} MT)"
                     for a in top_apps]
        app_section = (
            f"**[10] Plastic Application Usage (2026) — plastic-use-by-applicati.csv:**\n"
            f"  • Total Volume: {app_trends.get('total_volume_million_tonnes')} million tonnes\n"
            + "\n".join(app_lines) + "\n"
        )
        retrieved_app = {
            "year": app_trends.get("year"),
            "total_mt": app_trends.get("total_volume_million_tonnes"),
            "top_5_applications": [a[0] for a in top_apps],
            "dataset": "plastic-use-by-applicati.csv (42 years, 13 application sectors)",
        }
    else:
        app_section = "**[10] Application Trends:** Data unavailable.\n"
        retrieved_app = {"status": "Data load failed"}
    debug["application_trends"] = retrieved_app

    # ── Assemble Full Context Packet ─────────────────────────────────────────
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
    context_packet = (
        "╔══════════════════════════════════════════════════════════════════════╗\n"
        "║         PLASTICWISE AI — GROUNDED AUDIT CONTEXT PACKET              ║\n"
        f"║         Generated: {timestamp}                        ║\n"
        "╚══════════════════════════════════════════════════════════════════════╝\n\n"
        f"{audit_section}\n"
        f"{compliance_section}\n"
        f"{epr_section}\n"
        f"{score_section}\n"
        f"{cpcb_section}\n"
        f"{sbm_section}\n"
        f"{epr_portal_section}\n"
        f"{rs_section}\n"
        f"{poly_section}\n"
        f"{app_section}\n"
        "════════════════════════════════════════════════════════════════════════\n"
        "INSTRUCTIONS: Use ALL of the above grounded data when answering. "
        "Always cite specific numbers (tonnages, rates, thresholds). "
        "Reference state benchmarks vs institution metrics. "
        "Align recommendations with PWM Rules 2016 (Rule 4c, Rule 15, Rule 16, Rule 6) and CPCB EPR guidelines.\n"
        "════════════════════════════════════════════════════════════════════════"
    )

    return context_packet, debug


# ─────────────────────────────────────────────────────────────────────────────
# Render Debug Panel
# ─────────────────────────────────────────────────────────────────────────────
def render_debug_panel(debug: dict, question: str):
    """Renders a collapsible styled debug panel after the AI response."""
    with st.expander("🔬 Grounding Debug Panel — Retrieved Records", expanded=False):
        st.markdown(
            "<div style='background:#0E1117; border:1px solid #1E4620; border-radius:8px; padding:16px;'>",
            unsafe_allow_html=True
        )

        st.markdown(
            "<p style='color:#5CDE8C; font-family:monospace; font-size:0.85rem; margin:0;'>"
            f"▶ Query: <b>{question[:120]}...</b>" if len(question) > 120 else f"▶ Query: <b>{question}</b>"
            "</p>",
            unsafe_allow_html=True
        )
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            # Audit Data block
            audit_d = debug.get("audit_data", {})
            if "records" in audit_d:
                st.markdown("**📂 [1] Audit Data**")
                st.markdown(
                    f"<div style='background:#111; border-left:3px solid #1E4620; padding:8px; border-radius:4px; font-size:0.8rem; color:#AAFFAA;'>"
                    f"Records: <b>{audit_d.get('records')}</b><br/>"
                    f"Total: <b>{audit_d.get('total_kg')} kg</b><br/>"
                    f"Recycled: <b>{audit_d.get('recycled_kg')} kg</b><br/>"
                    f"Recycling Rate: <b>{audit_d.get('recycling_rate_pct')}%</b><br/>"
                    f"Landfilled: <b>{audit_d.get('landfilled_kg')} kg</b><br/>"
                    f"Open Burnt: <b>{audit_d.get('open_burnt_kg')} kg</b>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown("**📂 [1] Audit Data** — ⚠ No data loaded")

            st.markdown("")

            # Compliance Results
            comp_d = debug.get("compliance_results", {})
            st.markdown("**⚖️ [2] Compliance Results**")
            st.markdown(
                f"<div style='background:#111; border-left:3px solid #D9822B; padding:8px; border-radius:4px; font-size:0.8rem; color:#FFDDAA;'>"
                f"Compliance: <b>{comp_d.get('compliance_rate_pct', 'N/A')}%</b><br/>"
                f"Rating: <b>{comp_d.get('rating', 'N/A')}</b><br/>"
                f"Violations: <b>{comp_d.get('total_violations', 0)}</b><br/>"
                f"Critical: <b>{comp_d.get('critical_violations', 0)}</b>"
                f"</div>",
                unsafe_allow_html=True
            )

            st.markdown("")

            # EPR Results
            epr_d = debug.get("epr_results", {})
            st.markdown("**📦 [3] EPR Results**")
            st.markdown(
                f"<div style='background:#111; border-left:3px solid #5C8D89; padding:8px; border-radius:4px; font-size:0.8rem; color:#AADDFF;'>"
                f"Bulk Generator: <b>{'YES' if epr_d.get('is_bulk_generator') else 'NO'}</b><br/>"
                f"EPR Liability: <b>{epr_d.get('epr_liability_kg', 0)} kg</b><br/>"
                f"Categories: <b>{len(epr_d.get('categories', {}))}</b>"
                f"</div>",
                unsafe_allow_html=True
            )

            st.markdown("")

            # Sustainability Score
            sc_d = debug.get("sustainability_score", {})
            st.markdown("**🏆 [4] Sustainability Score**")
            st.markdown(
                f"<div style='background:#111; border-left:3px solid #8FBC8F; padding:8px; border-radius:4px; font-size:0.8rem; color:#CCFFCC;'>"
                f"Score: <b>{sc_d.get('score', 'N/A')}/100</b><br/>"
                f"Grade: <b>{sc_d.get('grade', 'N/A')}</b><br/>"
                f"Recycling Rate: <b>{sc_d.get('recycling_rate_pct', 'N/A')}%</b><br/>"
                f"Active Violations: <b>{sc_d.get('active_violations', 'N/A')}</b>"
                f"</div>",
                unsafe_allow_html=True
            )

        with col2:
            # CPCB Benchmark
            cpcb_d = debug.get("cpcb_benchmark", {})
            st.markdown("**📊 [5] CPCB Benchmark**")
            st.markdown(
                f"<div style='background:#111; border-left:3px solid #4A90D9; padding:8px; border-radius:4px; font-size:0.8rem; color:#AACCFF;'>"
                f"State: <b>{cpcb_d.get('state', 'N/A')}</b><br/>"
                f"Annual Waste: <b>{cpcb_d.get('annual_waste_tonnes', 'N/A'):,} tonnes</b><br/>"
                f"Per Capita: <b>{cpcb_d.get('per_capita_g_day', 'N/A')} g/day</b><br/>"
                f"Recycling: <b>{cpcb_d.get('recycling_rate_pct', 'N/A')}%</b><br/>"
                f"Total CPCB Rows: <b>{cpcb_d.get('total_cpcb_rows', 'N/A')}</b>"
                f"</div>",
                unsafe_allow_html=True
            ) if "state" in cpcb_d else st.markdown(f"<div style='color:#FF9999;'>{cpcb_d.get('status', 'N/A')}</div>", unsafe_allow_html=True)

            st.markdown("")

            # SBM Benchmark
            sbm_d = debug.get("sbm_benchmark", {})
            st.markdown("**🏙️ [6] Swachh Bharat Benchmark**")
            st.markdown(
                f"<div style='background:#111; border-left:3px solid #9B59B6; padding:8px; border-radius:4px; font-size:0.8rem; color:#DDAAFF;'>"
                f"District: <b>{sbm_d.get('district', 'N/A')}</b><br/>"
                f"Monthly Avg: <b>{sbm_d.get('monthly_avg_kg', 'N/A')} kg/month</b><br/>"
                f"Collection Rate: <b>{sbm_d.get('collection_rate_pct', 'N/A')}%</b><br/>"
                f"Total SBM Rows: <b>{sbm_d.get('total_sbm_rows', 'N/A')}</b>"
                f"</div>",
                unsafe_allow_html=True
            ) if "district" in sbm_d else st.markdown(f"<div style='color:#FF9999;'>{sbm_d.get('status', 'N/A')}</div>", unsafe_allow_html=True)

            st.markdown("")

            # EPR Portal
            epr_portal_d = debug.get("epr_portal_benchmark", {})
            st.markdown("**🏭 [7] EPR Portal Benchmarks**")
            st.markdown(
                f"<div style='background:#111; border-left:3px solid #E67E22; padding:8px; border-radius:4px; font-size:0.8rem; color:#FFDDAA;'>"
                f"Categories Retrieved: <b>{epr_portal_d.get('records_retrieved', 0)}</b><br/>"
                + "".join([
                    f"{c['category']}: <b>{c['registered_brands']:,} brands</b><br/>"
                    for c in epr_portal_d.get("categories", [])
                ])
                + "</div>",
                unsafe_allow_html=True
            )

            st.markdown("")

            # Rajya Sabha
            rs_d = debug.get("rajya_sabha_trends", {})
            st.markdown("**📜 [8] Rajya Sabha Session 266**")
            st.markdown(
                f"<div style='background:#111; border-left:3px solid #1ABC9C; padding:8px; border-radius:4px; font-size:0.8rem; color:#AAFFEE;'>"
                f"State: <b>{rs_d.get('state', 'N/A')}</b><br/>"
                f"Dataset: <b>{rs_d.get('dataset', 'N/A')}</b><br/>"
                f"Growth Rate: <b>{rs_d.get('growth_rate_pct', 'N/A')}%</b><br/>"
                f"Years Available: <b>{', '.join(rs_d.get('trend_years', []))}</b>"
                f"</div>",
                unsafe_allow_html=True
            ) if "state" in rs_d else st.markdown(f"<div style='color:#FF9999;'>{rs_d.get('status', 'N/A')}</div>", unsafe_allow_html=True)

        st.markdown("---")

        # Polymer & Application Datasets (full width)
        poly_d = debug.get("polymer_trends", {})
        app_d  = debug.get("application_trends", {})

        col3, col4 = st.columns(2)
        with col3:
            st.markdown("**🧪 [9] Polymer Market Trends**")
            st.markdown(
                f"<div style='background:#111; border-left:3px solid #F39C12; padding:8px; border-radius:4px; font-size:0.8rem; color:#FFEEAA;'>"
                f"Year: <b>{poly_d.get('year', 'N/A')}</b><br/>"
                f"Total Volume: <b>{poly_d.get('total_mt', 'N/A')} MT</b><br/>"
                f"Dataset: <b>{poly_d.get('dataset', 'N/A')}</b><br/>"
                f"Top Polymers: <b>{', '.join(poly_d.get('top_5_polymers', []))}</b>"
                f"</div>",
                unsafe_allow_html=True
            )
        with col4:
            st.markdown("**🏗️ [10] Application Usage Trends**")
            st.markdown(
                f"<div style='background:#111; border-left:3px solid #2ECC71; padding:8px; border-radius:4px; font-size:0.8rem; color:#AAFFCC;'>"
                f"Year: <b>{app_d.get('year', 'N/A')}</b><br/>"
                f"Total Volume: <b>{app_d.get('total_mt', 'N/A')} MT</b><br/>"
                f"Dataset: <b>{app_d.get('dataset', 'N/A')}</b><br/>"
                f"Top Sectors: <b>{', '.join(app_d.get('top_5_applications', []))}</b>"
                f"</div>",
                unsafe_allow_html=True
            )

        st.markdown(
            "<p style='color:#555; font-size:0.75rem; margin-top:8px;'>All data retrieved live from session state "
            "and on-disk datasets: cpcb_data.csv | swachh_bharat_data.csv | EPR portal | "
            "RS_Session_266 | plastic-use-by-polymer.csv | plastic-use-by-applicati.csv</p>",
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Grounding Badge
# ─────────────────────────────────────────────────────────────────────────────
def render_grounding_badge():
    st.markdown(
        "<div style='"
        "background: linear-gradient(135deg, #0D2B0E 0%, #1E4620 100%); "
        "color: #5CDE8C; "
        "border: 1px solid #2E6B30; "
        "border-radius: 8px; "
        "padding: 10px 16px; "
        "margin-bottom: 12px; "
        "display: flex; "
        "align-items: center; "
        "font-size: 0.85rem; "
        "font-family: monospace;'>"
        "🛡️ &nbsp;<b>Response grounded using audit data, CPCB dataset, "
        "Swachh Bharat dataset and EPR benchmark data.</b> &nbsp;"
        "| Sources: 10 data streams | Datasets: RS_Session_266 · polymer trends · application usage"
        "</div>",
        unsafe_allow_html=True
    )


# ─────────────────────────────────────────────────────────────────────────────
# Chat Session Initialization
# ─────────────────────────────────────────────────────────────────────────────
if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = [
        {
            "role": "assistant",
            "content": (
                "Namaste! I am **PlasticWise Advisor** — your grounded AI assistant for India's Plastic Waste "
                "Management ecosystem.\n\n"
                "Every response I provide is grounded using:\n"
                "- 📂 Your live institutional audit data\n"
                "- 📊 CPCB State Benchmark Dataset\n"
                "- 🏙️ Swachh Bharat Mission District Benchmarks\n"
                "- 📦 CPCB EPR Portal Registration Data\n"
                "- 📜 Rajya Sabha Session 266 — State-wise Plastic Waste Trends (35 states, 5 years)\n"
                "- 🧪 Global Polymer Market Trends (42 years, 14 polymers)\n"
                "- 🏗️ Plastic Application Usage Data (42 years, 13 sectors)\n\n"
                "Ask me about **compliance violations, EPR targets, recycling strategies, "
                "benchmark comparisons, or roadmap planning**!"
            )
        }
    ]

if "debug_data" not in st.session_state:
    st.session_state["debug_data"] = {}

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — Grounding Status Panel
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛡️ Grounding Status")
    df_check = st.session_state.get("audit_df")
    comp_check = st.session_state.get("compliance_results", {})
    epr_check = st.session_state.get("epr_results", {})
    score_check = st.session_state.get("score_details", {})

    status_items = [
        ("📂 Audit Data", df_check is not None and not (hasattr(df_check, 'empty') and df_check.empty)),
        ("⚖️ Compliance Results", bool(comp_check)),
        ("📦 EPR Results", bool(epr_check)),
        ("🏆 Sustainability Score", bool(score_check)),
        ("📊 CPCB Dataset", True),      # Always available (fallback)
        ("🏙️ Swachh Bharat Data", True), # Always available (fallback)
        ("📦 EPR Portal Data", True),    # Always available (fallback)
        ("📜 RS Session 266 CSV", True), # Large dataset
        ("🧪 Polymer Trends CSV", True), # Large dataset
        ("🏗️ Application CSV", True),    # Large dataset
    ]
    for label, loaded in status_items:
        color = "#5CDE8C" if loaded else "#FF6B6B"
        icon  = "✅" if loaded else "⚠️"
        st.markdown(
            f"<div style='font-size:0.82rem; padding:3px 0; color:{color};'>{icon} {label}</div>",
            unsafe_allow_html=True
        )

    st.markdown("---")
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state["chat_messages"] = [st.session_state["chat_messages"][0]]
        st.session_state["debug_data"] = {}
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Display Chat History
# ─────────────────────────────────────────────────────────────────────────────
for i, msg in enumerate(st.session_state["chat_messages"]):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # Show debug panel for assistant responses (except the welcome message)
        if msg["role"] == "assistant" and i > 0:
            dbg = st.session_state["debug_data"].get(i)
            question = st.session_state["chat_messages"][i - 1].get("content", "") if i > 0 else ""
            if dbg:
                render_debug_panel(dbg, question)


# ─────────────────────────────────────────────────────────────────────────────
# Handle New User Input
# ─────────────────────────────────────────────────────────────────────────────
user_input = st.chat_input("Ask about compliance, EPR targets, recycling, benchmarks...")

if user_input:
    # Append and display user message
    st.session_state["chat_messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        # Build grounding context packet
        with st.spinner("🔍 Retrieving data from all 10 grounding streams..."):
            context_packet, debug_meta = build_grounded_context_packet()

        # Display grounding badge
        render_grounding_badge()

        # Compose the final grounded prompt
        grounded_prompt = (
            f"{context_packet}\n\n"
            f"USER QUESTION: {user_input}\n\n"
            "RESPONSE INSTRUCTIONS:\n"
            "1. Answer the user question directly and professionally.\n"
            "2. Cite specific numbers from the grounding context above (waste volumes, rates, benchmarks).\n"
            "3. Compare the institution's metrics against state and national averages where relevant.\n"
            "4. Reference the applicable PWM Rule number(s) for any compliance guidance.\n"
            "5. Format your response with clear bullet points or numbered steps for actionability.\n"
            "6. End with one specific, actionable next step the institution should take.\n"
        )

        with st.spinner("🤖 Generating grounded response..."):
            client = GeminiClient()
            ai_response = client.query_gemini(
                system_instruction=CHATBOT_SYSTEM_PROMPT,
                prompt=grounded_prompt
            )

        st.markdown(ai_response)

        # Show debug panel immediately after response
        response_index = len(st.session_state["chat_messages"]) + 1
        render_debug_panel(debug_meta, user_input)

    # Store response and debug metadata
    st.session_state["chat_messages"].append({"role": "assistant", "content": ai_response})
    st.session_state["debug_data"][len(st.session_state["chat_messages"]) - 1] = debug_meta
