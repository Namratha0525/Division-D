import streamlit as st
import pandas as pd
from modules.chart_generator import ChartGenerator
from modules.audit_analyzer import AuditAnalyzer

# ── Dark-mode colour palette ───────────────────────────────────────────────
# All card backgrounds use rgba() so they sit on the dark Streamlit canvas.
# Text is always explicitly #E8E8E8 (near-white) so it's always readable.
_CARD_GREEN  = "rgba(43,138,62,0.18)"     # green-tinted dark
_CARD_RED    = "rgba(178,59,59,0.18)"      # red-tinted dark
_CARD_ORANGE = "rgba(217,130,43,0.18)"     # amber-tinted dark
_CARD_BLUE   = "rgba(92,141,137,0.18)"     # teal-tinted dark
_CARD_GREY   = "rgba(100,100,120,0.22)"    # neutral dark
_TXT         = "#E8E8E8"                   # body text
_TXT_SUB     = "#A0A8B0"                   # subdued text
_TXT_HEAD    = "#5CDE8C"                   # bright-green for headings inside cards
_ACCENT_G    = "#5CDE8C"                   # border bright-green
_ACCENT_R    = "#FF6B6B"                   # border bright-red
_ACCENT_O    = "#FFB347"                   # border bright-amber
_ACCENT_T    = "#7ECECA"                   # border teal


def _dm_card(border_color, bg, html_body):
    """Wrap html_body in a dark-mode card div."""
    return (
        f"<div style='background:{bg}; border-left:5px solid {border_color}; "
        f"border-radius:10px; padding:18px; margin:4px 0; "
        f"box-shadow:0 2px 10px rgba(0,0,0,0.35);'>"
        f"{html_body}"
        f"</div>"
    )


def _row(label, value, txt=_TXT, sub=_TXT_SUB):
    return (
        f"<tr>"
        f"<td style='padding:5px 0; color:{sub}; font-size:0.84rem;'><b>{label}</b></td>"
        f"<td style='text-align:right; color:{txt}; font-size:0.84rem; font-weight:600;'>{value}</td>"
        f"</tr>"
    )


# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(page_title="Dashboard | PlasticWise AI", layout="wide")

st.markdown("<h1 style='color:#5CDE8C;'>📊 Analysis Dashboard</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='color:#A0A8B0;'>Institutional plastic waste inventory · Compliance scores · "
    "Carbon impact · Benchmark ranking.</p>",
    unsafe_allow_html=True,
)

df = st.session_state.get("audit_df")

if df is None or df.empty:
    st.warning("Please upload or input audit records on the **Audit Form** page to load the dashboard.")
else:
    analyzer  = AuditAnalyzer()
    chart_gen = ChartGenerator()
    metrics   = analyzer.calculate_summary_metrics(df)
    score_details = st.session_state.get("score_details", {})
    carbon    = st.session_state.get("carbon_impact", {})

    # ── KPI Row ───────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("📦 Total Audited Volume",
              f"{metrics['total_weight_kg']:.1f} kg",
              delta=f"{metrics['total_records']} Records")
    k2.metric("♻️ Recycling Diversion Rate",
              f"{metrics['recycling_rate_pct']:.1f}%",
              delta="Target: 70%")
    k3.metric("🌿 CO₂ Saved",
              f"{carbon.get('total_saved_co2_kg', metrics['total_co2_offset_kg']):.1f} kg CO₂e",
              delta="Estimated")
    k4.metric("🔬 Dominant Polymer",
              metrics['dominant_polymer_type'].split(" (")[0],
              delta="Reduction Target")

    st.divider()

    # =========================================================================
    # SECTION A: COMPLIANCE SCORE TRIPTYCH
    # =========================================================================
    compliance_scores = st.session_state.get("compliance_scores", {})
    if compliance_scores:
        st.markdown(
            "<h3 style='color:#5CDE8C;'>⚖️ Compliance Score Engine</h3>"
            "<p style='color:#A0A8B0; font-size:0.85rem; margin-top:-10px;'>"
            "Overall = <b>60% PWM Score + 40% EPR Score</b>. "
            "Every deduction is traceable to a specific rule and waste volume.</p>",
            unsafe_allow_html=True,
        )

        cs1, cs2, cs3 = st.columns(3)

        def _score_card(col, title, score, grade, accent):
            if score >= 75:
                bg, glow = _CARD_GREEN, _ACCENT_G
            elif score >= 55:
                bg, glow = _CARD_ORANGE, _ACCENT_O
            else:
                bg, glow = _CARD_RED, _ACCENT_R
            col.markdown(
                f"<div style='background:{bg}; border:1px solid {glow}33; border-left:6px solid {glow}; "
                f"border-radius:12px; padding:22px; text-align:center; "
                f"box-shadow:0 0 18px {glow}22;'>"
                f"<p style='color:{_TXT_SUB}; font-size:0.75rem; font-weight:700; "
                f"letter-spacing:1px; margin:0;'>{title}</p>"
                f"<h1 style='color:{accent}; margin:8px 0 4px; font-size:3.2rem; font-weight:900;'>{score}</h1>"
                f"<p style='color:{_TXT}; font-size:0.82rem; font-weight:600; margin:0;'>{grade}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

        _score_card(cs1, "PWM COMPLIANCE SCORE",
                    compliance_scores.get("pwm_score", 0),
                    compliance_scores.get("pwm_grade", "N/A"),
                    compliance_scores.get("pwm_color", "#6c757d"))
        _score_card(cs2, "EPR COMPLIANCE SCORE",
                    compliance_scores.get("epr_score", 0),
                    compliance_scores.get("epr_grade", "N/A"),
                    compliance_scores.get("epr_color", "#6c757d"))
        _score_card(cs3, "OVERALL COMPLIANCE SCORE",
                    compliance_scores.get("overall_score", 0),
                    compliance_scores.get("overall_grade", "N/A"),
                    compliance_scores.get("overall_color", "#6c757d"))

        st.markdown(
            f"<p style='color:{_TXT_SUB}; font-size:0.76rem; margin-top:6px;'>"
            f"📐 {compliance_scores.get('formula_note', '')}</p>",
            unsafe_allow_html=True,
        )

        col_bd1, col_bd2 = st.columns(2)
        with col_bd1:
            pwm_bd = compliance_scores.get("pwm_breakdown", {})
            if pwm_bd.get("penalty_components"):
                with st.expander("🔍 PWM Score — Penalty Breakdown", expanded=False):
                    st.markdown(
                        f"Base: **100 pts** | Penalty: **-{pwm_bd.get('total_penalty', 0)} pts**"
                    )
                    for comp in pwm_bd["penalty_components"]:
                        sc = _ACCENT_R if comp["severity"] == "CRITICAL" else _ACCENT_O
                        st.markdown(
                            f"<div style='border-left:3px solid {sc}; padding:6px 12px; margin:4px 0; "
                            f"background:{_CARD_GREY}; border-radius:4px; font-size:0.82rem; color:{_TXT};'>"
                            f"<b style='color:{sc};'>{comp['rule_id']}</b> — {comp['severity']}<br/>"
                            f"Base −{comp['base_deduction_pts']} pts × vol.factor {comp['volume_factor']:.2f} "
                            f"= <b>−{comp['actual_deduction_pts']} pts</b><br/>"
                            f"<span style='color:{_TXT_SUB};'>"
                            f"Affected: {comp['affected_kg']:.1f} kg ({comp['affected_pct_of_total']:.1f}%)</span>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
            else:
                with st.expander("🔍 PWM Score — No Violations", expanded=False):
                    st.success("No penalties applied. Full 100 pts base maintained.")

        with col_bd2:
            epr_bd = compliance_scores.get("epr_breakdown", {})
            if epr_bd:
                with st.expander("🔍 EPR Score — Formula Detail", expanded=False):
                    st.markdown(
                        f"| Component | Value |\n|---|---|\n"
                        f"| Actual Recycling Rate | **{epr_bd.get('actual_recycling_pct',0):.1f}%** |\n"
                        f"| CPCB Target | **{epr_bd.get('target_recycling_pct',70):.0f}%** |\n"
                        f"| Achievement Ratio | **{epr_bd.get('achievement_ratio_pct',0):.1f}%** |\n"
                        f"| Recycling Component | **{epr_bd.get('recycling_component_pts',0):.1f} / 85 pts** |\n"
                        f"| Bulk Generator | **{'YES (No bonus)' if epr_bd.get('bulk_generator') else 'NO (+10 pts)'}** |\n"
                        f"| No-Burning Bonus | **+{epr_bd.get('no_open_burning_bonus_pts',0):.0f} pts** |"
                    )

        st.divider()

    # =========================================================================
    # SECTION B: CARBON IMPACT PANEL
    # =========================================================================
    if carbon:
        st.markdown(
            "<h3 style='color:#5CDE8C;'>🌿 Carbon Impact Analysis</h3>",
            unsafe_allow_html=True,
        )
        net_co2   = carbon.get("net_co2_kg", 0.0)
        net_dir   = carbon.get("net_direction", "N/A")
        net_accent = _ACCENT_G if net_co2 <= 0 else _ACCENT_R
        net_bg     = _CARD_GREEN if net_co2 <= 0 else _CARD_RED

        ci1, ci2, ci3, ci4 = st.columns(4)
        ci1.metric("🟢 CO₂ Saved (Recycling)",
                   f"{carbon.get('total_saved_co2_kg',0):.2f} kg CO₂e",
                   delta="Benefit")
        ci2.metric("🔴 CO₂ Emitted (Landfill/Burn)",
                   f"{carbon.get('total_emitted_co2_kg',0):.2f} kg CO₂e",
                   delta="Impact", delta_color="inverse")
        ci3.metric("🌳 Trees Equivalent (1 yr)",
                   f"{carbon.get('trees_equivalent',0):.1f}")
        ci4.metric("🚗 Car Travel Avoided",
                   f"{carbon.get('car_km_avoided',0):,} km")

        st.markdown(
            _dm_card(
                net_accent, net_bg,
                f"<b style='color:{net_accent}; font-size:1rem;'>"
                f"Net Carbon Position: {net_dir} — {abs(net_co2):.2f} kg CO₂e</b>"
                f"<br/><small style='color:{_TXT_SUB};'>"
                f"{carbon.get('methodology_note','')}</small>"
            ),
            unsafe_allow_html=True,
        )

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            with st.expander("📊 Carbon by Disposal Pathway", expanded=False):
                rows = [
                    {"Pathway": k,
                     "Weight (kg)": v["total_weight_kg"],
                     "CO₂ Impact (kg)": v["total_co2_kg"],
                     "Type": v["impact_type"]}
                    for k, v in carbon.get("pathway_breakdown", {}).items()
                ]
                if rows:
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        with col_c2:
            with st.expander("🧪 Carbon by Polymer Type", expanded=False):
                poly_rows = carbon.get("polymer_breakdown", [])
                if poly_rows:
                    st.dataframe(pd.DataFrame(poly_rows), use_container_width=True, hide_index=True)

        st.divider()

    # =========================================================================
    # SECTION C: BENCHMARK RANK BADGE
    # =========================================================================
    ranking = st.session_state.get("benchmark_ranking", {})
    if ranking:
        st.markdown(
            "<h3 style='color:#5CDE8C;'>🏅 Benchmark Ranking & Performance Tier</h3>",
            unsafe_allow_html=True,
        )
        tier        = ranking.get("performance_tier", "N/A")
        tier_accent = ranking.get("tier_color", "#6c757d")
        tier_icon   = ranking.get("tier_icon", "")

        # Map tier → dark bg
        tier_bg_map = {
            "Leader":       _CARD_GREEN,
            "On Track":     _CARD_BLUE,
            "Needs Action": _CARD_ORANGE,
            "Critical":     _CARD_RED,
        }
        tier_bg = tier_bg_map.get(tier, _CARD_GREY)

        bk1, bk2, bk3 = st.columns(3)
        bk1.markdown(
            _dm_card(
                tier_accent, tier_bg,
                f"<p style='color:{_TXT_SUB}; font-size:0.75rem; font-weight:700; "
                f"letter-spacing:1px; margin:0;'>STATE RECYCLING RANK</p>"
                f"<h2 style='color:{tier_accent}; margin:6px 0;'>"
                f"#{ranking.get('state_recycling_rank','?')} "
                f"<small style='font-size:1rem; color:{_TXT_SUB};'>"
                f"of {ranking.get('state_recycling_rank_of','?')}</small></h2>"
                f"<p style='color:{_TXT}; font-size:0.82rem; margin:0;'>"
                f"{ranking.get('state_name','N/A')}<br/>"
                f"Recycling: <b style='color:{_ACCENT_G};'>{ranking.get('state_recycling_rate_pct','N/A')}%</b>"
                f" vs National Avg: <b style='color:{_TXT};'>{ranking.get('national_avg_recycling_pct','N/A')}%</b></p>"
            ),
            unsafe_allow_html=True,
        )
        bk2.markdown(
            _dm_card(
                tier_accent, tier_bg,
                f"<p style='color:{_TXT_SUB}; font-size:0.75rem; font-weight:700; "
                f"letter-spacing:1px; margin:0;'>DISTRICT WASTE RANK</p>"
                f"<h2 style='color:{tier_accent}; margin:6px 0;'>"
                f"#{ranking.get('district_rank','?')} "
                f"<small style='font-size:1rem; color:{_TXT_SUB};'>"
                f"of {ranking.get('district_rank_of','?')}</small></h2>"
                f"<p style='color:{_TXT}; font-size:0.82rem; margin:0;'>"
                f"{ranking.get('district_name','N/A')}<br/>"
                f"District Avg: <b style='color:{_TXT};'>{ranking.get('district_avg_monthly_kg','N/A')} kg/mo</b><br/>"
                f"Institution: <b style='color:{_ACCENT_G};'>{ranking.get('institution_monthly_kg','N/A')} kg/mo</b></p>"
            ),
            unsafe_allow_html=True,
        )
        bk3.markdown(
            _dm_card(
                tier_accent, tier_bg,
                f"<p style='color:{_TXT_SUB}; font-size:0.75rem; font-weight:700; "
                f"letter-spacing:1px; margin:0; text-align:center;'>PERFORMANCE TIER</p>"
                f"<h2 style='color:{tier_accent}; margin:8px 0; text-align:center;'>{tier_icon} {tier}</h2>"
                f"<p style='color:{_TXT}; font-size:0.82rem; margin:0; text-align:center;'>"
                f"National Percentile: <b style='color:{_ACCENT_G};'>{ranking.get('state_percentile','N/A')}%</b><br/>"
                f"vs District: <b style='color:{_TXT};'>{ranking.get('inst_vs_district_pct',0):+.1f}%</b> "
                f"({'Below' if ranking.get('inst_vs_district_pct',0) < 0 else 'Above'} avg)</p>"
            ),
            unsafe_allow_html=True,
        )

        with st.expander("📋 Full State Ranking Table (CPCB Dataset)", expanded=False):
            all_states = ranking.get("all_states_ranking", [])
            if all_states:
                rank_df = pd.DataFrame(all_states)
                target  = ranking.get("state_name", "").lower()
                def _hl(row):
                    if row["State"].lower() == target:
                        return ["background-color:rgba(43,138,62,0.35); font-weight:bold"] * len(row)
                    return [""] * len(row)
                st.dataframe(
                    rank_df.style.apply(_hl, axis=1),
                    use_container_width=True, hide_index=True,
                )

        st.divider()

    # =========================================================================
    # SECTION D: CHARTS & GAUGES
    # =========================================================================
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.plotly_chart(chart_gen.plot_waste_composition_donut(df), use_container_width=True)
        st.plotly_chart(chart_gen.plot_monthly_trends(df), use_container_width=True)

    with col_right:
        if score_details:
            st.markdown(
                "<h3 style='color:#5CDE8C;'>Sustainability Performance Score</h3>",
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                chart_gen.plot_sustainability_gauge(
                    score_details.get("score", 0.0),
                    score_details.get("color", "#6c757d"),
                ),
                use_container_width=True,
            )
            st.info(f"🏆 Grading Tier: **{score_details.get('grade')}**")

            # ── Benchmark comparison card ──────────────────────────────────
            st.markdown(
                "<h3 style='color:#5CDE8C; margin-top:16px;'>📊 Dataset Benchmark Analysis</h3>",
                unsafe_allow_html=True,
            )
            bench         = score_details.get("benchmarks", {})
            metrics_d     = score_details.get("metrics", {})
            inst_monthly  = metrics_d.get("institution_monthly_avg_kg", 0.0)
            state_avg     = bench.get("state_average_kg", 220.0)
            national_avg  = 200.0
            state_name    = bench.get("state_name", "Maharashtra")
            district_name = bench.get("district_name", "Mumbai City")
            city_avg      = bench.get("city_average_kg", 180.0)

            if inst_monthly > max(state_avg, national_avg):
                perf_text, perf_accent, perf_bg = "Above Average Waste Generation", _ACCENT_R, _CARD_RED
            elif inst_monthly < min(state_avg, national_avg):
                perf_text, perf_accent, perf_bg = "Below Average Waste Generation", _ACCENT_G, _CARD_GREEN
            else:
                perf_text, perf_accent, perf_bg = "Average Waste Generation", _ACCENT_O, _CARD_ORANGE

            st.markdown(
                _dm_card(
                    perf_accent, perf_bg,
                    f"<h4 style='margin-top:0; color:{perf_accent};'><b>Performance: {perf_text}</b></h4>"
                    f"<table style='width:100%; border-collapse:collapse;'>"
                    + _row("Institution Waste:", f"{inst_monthly:.1f} kg/month", _ACCENT_G)
                    + _row(f"State Average ({state_name}):", f"{state_avg:.1f} kg/month")
                    + _row("National Average:", f"{national_avg:.1f} kg/month")
                    + _row(f"City Average ({district_name}):", f"{city_avg:.1f} kg/month")
                    + f"</table>"
                    f"<small style='color:{_TXT_SUB}; display:block; margin-top:10px;'>"
                    f"Source: CPCB & Swachh Bharat Datasets 2026</small>"
                ),
                unsafe_allow_html=True,
            )
            st.markdown("<br/>", unsafe_allow_html=True)

            # ── EPR Risk Indicator ─────────────────────────────────────────
            st.markdown(
                "<h3 style='color:#5CDE8C;'>📦 EPR Risk Indicator & Benchmarks</h3>",
                unsafe_allow_html=True,
            )
            epr_comp  = bench.get("epr_analysis", {})
            epr_bench_d = bench.get("epr_benchmarks", {})
            risk_level = "HIGH" if epr_comp.get("registration_required") else "LOW"
            risk_map = {
                "HIGH":   (_ACCENT_R, _CARD_RED,    "High Registration Necessity & Packaging Target Liability"),
                "MEDIUM": (_ACCENT_O, _CARD_ORANGE, "Moderate Liability — Monitoring Required"),
                "LOW":    (_ACCENT_G, _CARD_GREEN,  "Low Liability — Compliant Volume Thresholds"),
            }
            ra, rb_bg, rd = risk_map[risk_level]
            st.markdown(
                _dm_card(
                    ra, rb_bg,
                    f"<h4 style='margin:0; color:{ra};'>⚠️ Risk Level: {risk_level}</h4>"
                    f"<p style='margin:6px 0; color:{_TXT}; font-size:0.9rem;'>{rd}</p>"
                    f"<table style='width:100%; border-collapse:collapse;'>"
                    + _row("Institution Status:",
                           f"{epr_comp.get('compliance_status','N/A')} "
                           f"({epr_comp.get('overall_liability_kg', 0.0):.1f} kg liability)")
                    + _row(f"Registered Orgs ({state_name}):",
                           f"{epr_bench_d.get('state_registered_brands', 2670)} Brands")
                    + _row("Industry Compliance Avg:",
                           f"{epr_bench_d.get('industry_compliance_rate_pct', 74.5)}%")
                    + f"</table>"
                    f"<small style='display:block; color:{_TXT_SUB}; margin-top:8px;'>"
                    f"Source: eprplastic.cpcb.gov.in</small>"
                ),
                unsafe_allow_html=True,
            )
            st.markdown("<br/>", unsafe_allow_html=True)

        st.plotly_chart(chart_gen.plot_disposal_bar(df), use_container_width=True)

    # =========================================================================
    # SECTION E: AI AUDIT ASSISTANT INSIGHTS
    # =========================================================================
    st.divider()
    st.markdown(
        "<h2 style='color:#5CDE8C;'>🤖 AI Audit Assistant Insights</h2>"
        "<p style='color:#5CDE8C; font-size:0.82rem;'>"
        "🟢 AI Response Grounded Using CPCB, Swachh Bharat Mission and EPR Benchmark Datasets.</p>",
        unsafe_allow_html=True,
    )

    report = st.session_state.get("ai_audit_report")
    if not report:
        st.info("No AI Audit Report generated. Please run the analysis pipeline first.")
    else:
        # Executive Summary card
        st.markdown(
            _dm_card(
                _ACCENT_G, _CARD_GREEN,
                f"<h3 style='margin-top:0; color:{_ACCENT_G};'><b>Executive Performance Summary</b></h3>"
                f"<p style='font-size:1rem; line-height:1.7; color:{_TXT};'>"
                f"{report.get('executive_summary')}</p>"
            ),
            unsafe_allow_html=True,
        )

        tab_findings, tab_gaps, tab_epr, tab_bench, tab_risks, tab_recs, tab_roadmap = st.tabs([
            "🔍 Key Findings", "⚖️ Compliance Gaps", "📦 EPR Assessment",
            "📊 Benchmarks", "⚠️ Risk & Score", "💡 Recommendations", "📅 Roadmap",
        ])

        with tab_findings:
            st.markdown(f"<h4 style='color:{_ACCENT_G};'>Grounded Key Findings</h4>",
                        unsafe_allow_html=True)
            for f in report.get("key_findings", []):
                st.markdown(f"- {f}")

        with tab_gaps:
            st.markdown(f"<h4 style='color:{_ACCENT_G};'>Statutory Compliance Gap Analysis</h4>",
                        unsafe_allow_html=True)
            gaps = report.get("compliance_gap_analysis", [])
            if not gaps:
                st.success("✔ No legal non-conformances identified.")
            else:
                for gap in gaps:
                    sev = gap.get("severity", "HIGH")
                    ga  = _ACCENT_R if sev in ["CRITICAL", "HIGH"] else _ACCENT_O
                    gb  = _CARD_RED if sev in ["CRITICAL", "HIGH"] else _CARD_ORANGE
                    st.markdown(
                        _dm_card(
                            ga, gb,
                            f"<h4 style='color:{ga}; margin-top:0;'>⚠️ {gap.get('violation')} ({sev})</h4>"
                            f"<p style='color:{_TXT}; margin:4px 0 0 0;'>"
                            f"<b>Corrective Action:</b> {gap.get('corrective_action')}</p>"
                        ),
                        unsafe_allow_html=True,
                    )

        with tab_epr:
            st.markdown(f"<h4 style='color:{_ACCENT_G};'>EPR Obligation Assessment</h4>",
                        unsafe_allow_html=True)
            epr_data = report.get("epr_assessment", {})
            st.markdown(f"**Obligations:** {epr_data.get('obligations')}")
            st.info(f"**Registration Status:** {epr_data.get('registration_status')}")
            st.markdown(f"**Recommended Action:** {epr_data.get('recommended_actions')}")

        with tab_bench:
            st.markdown(f"<h4 style='color:{_ACCENT_G};'>Dataset-Grounded Benchmark Analysis</h4>",
                        unsafe_allow_html=True)
            bd = report.get("benchmark_analysis", {})
            for label, key in [
                ("State comparison", "state_comparison"),
                ("City comparison",  "city_comparison"),
                ("National baseline","national_comparison"),
                ("CPCB Industry avg","industry_comparison"),
            ]:
                st.markdown(f"- **{label}:** {bd.get(key)}")

        with tab_risks:
            st.markdown(f"<h4 style='color:{_ACCENT_G};'>Environmental Risk & Score</h4>",
                        unsafe_allow_html=True)
            risk_data = report.get("environmental_risk_assessment", {})
            lvl = risk_data.get("risk_level", "MEDIUM")
            ra2 = _ACCENT_R if lvl in ["CRITICAL","HIGH"] else (_ACCENT_O if lvl == "MEDIUM" else _ACCENT_G)
            rb2 = _CARD_RED  if lvl in ["CRITICAL","HIGH"] else (_CARD_ORANGE if lvl == "MEDIUM" else _CARD_GREEN)
            st.markdown(
                _dm_card(
                    ra2, rb2,
                    f"<h4 style='color:{ra2}; margin-top:0;'>🔥 Risk Level: {lvl}</h4>"
                    f"<p style='color:{_TXT}; margin:4px 0 0 0;'>{risk_data.get('justification')}</p>"
                ),
                unsafe_allow_html=True,
            )
            sd = report.get("sustainability_score_assessment", {})
            st.metric(f"Sustainability Grade: {sd.get('grade')}",
                      f"{sd.get('score')}/100", help=sd.get("explanation"))
            st.write(sd.get("explanation"))

        with tab_recs:
            st.markdown(f"<h4 style='color:{_ACCENT_G};'>Waste Reduction Recommendations</h4>",
                        unsafe_allow_html=True)
            for rec in report.get("waste_reduction_recommendations", []):
                st.markdown(f"- **{rec.get('recommendation')}**")
                st.markdown(f"  *Expected Impact:* {rec.get('expected_impact')}")

        with tab_roadmap:
            st.markdown(f"<h4 style='color:{_ACCENT_G};'>12-Month Transition Roadmap</h4>",
                        unsafe_allow_html=True)
            st.plotly_chart(chart_gen.plot_roadmap_flowchart(), use_container_width=True)
            for phase in report.get("roadmap_12_month", []):
                with st.expander(f"📅 {phase.get('month')} — {phase.get('target')}"):
                    st.write(f"**Expected Outcome:** {phase.get('expected_outcome')}")
                    st.write(f"**Compliance Improvement:** {phase.get('compliance_improvement')}")
                    for act in phase.get("activities", []):
                        st.write(f"- {act}")

        # Final Auditor Conclusion
        st.markdown(
            _dm_card(
                _ACCENT_G, _CARD_GREEN,
                f"<h4 style='color:{_ACCENT_G}; margin-top:0;'><b>Final Auditor Conclusion</b></h4>"
                f"<p style='font-style:italic; line-height:1.7; color:{_TXT};'>"
                f"{report.get('final_auditor_conclusion')}</p>"
            ),
            unsafe_allow_html=True,
        )
