import streamlit as st
import pandas as pd

# Dark-mode card helpers (same palette as dashboard.py)
_CARD_GREEN  = "rgba(43,138,62,0.18)"
_CARD_RED    = "rgba(178,59,59,0.18)"
_CARD_ORANGE = "rgba(217,130,43,0.18)"
_CARD_GREY   = "rgba(100,100,120,0.22)"
_TXT         = "#E8E8E8"
_TXT_SUB     = "#A0A8B0"
_ACCENT_G    = "#5CDE8C"
_ACCENT_R    = "#FF6B6B"
_ACCENT_O    = "#FFB347"

def _card(border, bg, body):
    return (
        f"<div style='background:{bg}; border-left:5px solid {border}; "
        f"border-radius:10px; padding:16px; margin:4px 0; "
        f"box-shadow:0 2px 10px rgba(0,0,0,0.35);'>{body}</div>"
    )

st.set_page_config(page_title="Compliance Check | PlasticWise AI", layout="wide")

st.markdown("<h1 style='color:#5CDE8C;'>⚖️ PWM Rules 2016 Compliance Checker</h1>",
            unsafe_allow_html=True)
st.markdown(
    f"<p style='color:{_TXT_SUB};'>Statutory audit matching institutional waste streams "
    f"against India's national plastic restrictions.</p>",
    unsafe_allow_html=True,
)

compliance_results = st.session_state.get("compliance_results")

if not compliance_results or "violations" not in compliance_results:
    st.warning("Please upload or input audit records on the Audit Form page to load compliance evaluations.")
else:
    violations    = compliance_results.get("violations", [])
    ai_analysis   = compliance_results.get("ai_analysis", {})
    comp_pct      = compliance_results.get("compliance_percentage", 100.0)
    num_viols     = compliance_results.get("number_of_violations", 0)
    crit_viols    = compliance_results.get("critical_violations", 0)
    overall_rating= compliance_results.get("overall_compliance_rating", "EXCELLENT")

    # Also read the new compliance scores if available
    compliance_scores = st.session_state.get("compliance_scores", {})

    # ── KPI Row ───────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Compliance Percentage", f"{comp_pct:.1f}%")
    c2.metric("Total Violations", str(num_viols))
    c3.metric("Critical Violations", str(crit_viols))
    with c4:
        r_accent = {
            "EXCELLENT": _ACCENT_G, "GOOD": _ACCENT_G,
            "ATTENTION REQUIRED": _ACCENT_O, "NON-COMPLIANT": _ACCENT_R,
        }.get(overall_rating, "#6c757d")
        st.markdown(
            f"<div style='padding:6px 0;'>"
            f"<p style='color:{_TXT_SUB}; font-size:0.8rem; margin:0;'>Overall Rating</p>"
            f"<p style='color:{r_accent}; font-size:1.3rem; font-weight:800; margin:4px 0;'>"
            f"{overall_rating}</p></div>",
            unsafe_allow_html=True,
        )

    # ── Compliance Score Triptych (if available) ──────────────────────────────
    if compliance_scores:
        st.divider()
        st.markdown(
            "<h3 style='color:#5CDE8C;'>⚖️ Compliance Score Engine</h3>"
            "<p style='color:#A0A8B0; font-size:0.83rem; margin-top:-8px;'>"
            "Overall = 60% PWM + 40% EPR. Every point deduction is traceable.</p>",
            unsafe_allow_html=True,
        )
        sc1, sc2, sc3 = st.columns(3)
        for col, title, score, grade, color in [
            (sc1, "PWM COMPLIANCE SCORE",
             compliance_scores.get("pwm_score", 0),
             compliance_scores.get("pwm_grade", "N/A"),
             compliance_scores.get("pwm_color", "#6c757d")),
            (sc2, "EPR COMPLIANCE SCORE",
             compliance_scores.get("epr_score", 0),
             compliance_scores.get("epr_grade", "N/A"),
             compliance_scores.get("epr_color", "#6c757d")),
            (sc3, "OVERALL COMPLIANCE SCORE",
             compliance_scores.get("overall_score", 0),
             compliance_scores.get("overall_grade", "N/A"),
             compliance_scores.get("overall_color", "#6c757d")),
        ]:
            bg = _CARD_GREEN if score >= 75 else (_CARD_ORANGE if score >= 55 else _CARD_RED)
            col.markdown(
                f"<div style='background:{bg}; border-left:6px solid {color}; "
                f"border-radius:12px; padding:20px; text-align:center;'>"
                f"<p style='color:{_TXT_SUB}; font-size:0.75rem; font-weight:700; "
                f"letter-spacing:1px; margin:0;'>{title}</p>"
                f"<h1 style='color:{color}; margin:6px 0; font-size:2.8rem; font-weight:900;'>{score}</h1>"
                f"<p style='color:{_TXT}; font-size:0.82rem; font-weight:600; margin:0;'>{grade}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Compliance Checklist Table ────────────────────────────────────────────
    st.markdown(
        f"<h3 style='color:#5CDE8C;'>📋 Compliance Gaps Checklist</h3>",
        unsafe_allow_html=True,
    )

    rules_definitions = {
        "PWM_RULE_4C_MICRONS": {
            "ref": "Rule 4(c)", "risk": "Critical",
            "req": "Minimum carry bag / packaging sheet thickness of 120 microns",
            "default_ok":  "All carry bags exceed 120 microns threshold",
            "default_gap": "Observed packaging sheets under 120 microns",
            "default_action": "Replace carry bags & sheets immediately with ≥120 microns or certified compostables.",
            "why": "Sub-120 µm bags fragment into micro-plastics contaminating water bodies and resist recycling.",
            "fine": "₹1,00,000 (1st offence) | ₹1,50,000 (repeat) — EP Act S.15",
        },
        "NGT_OPEN_BURNING_BAN": {
            "ref": "Rule 16 / NGT", "risk": "Critical",
            "req": "Strict ban on open burning of plastic & municipal solid waste",
            "default_ok":  "No open burning detected; secure recycling chains active",
            "default_gap": "Incineration via open burning detected in facility",
            "default_action": "Cease open burning immediately; formalise secure recycling collection.",
            "why": "Burning PVC/mixed film releases dioxins and furans (Stockholm Convention carcinogens).",
            "fine": "₹25,000 / incident (NGT 2019) + criminal proceedings under EP Act S.15",
        },
        "PWM_SUP_BAN_2022": {
            "ref": "Rule 15 / SUP Ban", "risk": "High",
            "req": "Prohibition of banned single-use polystyrene items",
            "default_ok":  "Zero polystyrene cutlery or cups detected",
            "default_gap": "Banned polystyrene (RIC 6) found in use",
            "default_action": "Transition cafeteria to wooden, paper, or steel reuse alternatives.",
            "why": "EPS scores zero in recyclability under Indian MRFs and contributes to marine plastic load.",
            "fine": "₹500–₹50,000 / incident | ₹1,00,000 for commercial quantities",
        },
    }

    for rule_id, defs in rules_definitions.items():
        match = [v for v in violations if v["rule_id"] == rule_id]
        is_violated = bool(match)
        accent  = _ACCENT_R if is_violated and defs["risk"] == "Critical" else (
                  _ACCENT_O if is_violated else _ACCENT_G)
        bg      = _CARD_RED if is_violated and defs["risk"] == "Critical" else (
                  _CARD_ORANGE if is_violated else _CARD_GREEN)
        status  = f"⚠️ NON-CONFORMANT" if is_violated else "✅ COMPLIANT"
        gap_txt = defs["default_gap"] if is_violated else "None identified"

        st.markdown(
            _card(
                accent, bg,
                f"<div style='display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap;'>"
                f"<div>"
                f"<p style='color:{_TXT_SUB}; font-size:0.75rem; margin:0; font-weight:700; letter-spacing:0.5px;'>"
                f"{defs['ref']} · {defs['risk'].upper()}</p>"
                f"<h4 style='color:{accent}; margin:4px 0;'>{status}</h4>"
                f"<p style='color:{_TXT}; font-size:0.84rem; margin:2px 0;'>"
                f"<b>Requirement:</b> {defs['req']}</p>"
                f"<p style='color:{_TXT}; font-size:0.84rem; margin:2px 0;'>"
                f"<b>Gap Identified:</b> {gap_txt}</p>"
                f"</div></div>"
                f"<hr style='border-color:rgba(255,255,255,0.1); margin:10px 0;'/>"
                f"<p style='color:{_TXT_SUB}; font-size:0.8rem; margin:3px 0;'>"
                f"<b style='color:{_ACCENT_O};'>Why It Matters:</b> {defs['why']}</p>"
                f"<p style='color:{_TXT_SUB}; font-size:0.8rem; margin:3px 0;'>"
                f"<b style='color:{_ACCENT_R};'>Regulatory Fine:</b> {defs['fine']}</p>"
                f"<p style='color:{_TXT}; font-size:0.82rem; margin:6px 0 0 0;'>"
                f"<b style='color:{_ACCENT_G};'>Corrective Action:</b> {defs['default_action']}</p>"
            ),
            unsafe_allow_html=True,
        )

    st.divider()

    # ── AI Recommendations ────────────────────────────────────────────────────
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(
            f"<h3 style='color:#5CDE8C;'>💡 Strategic Recommendations</h3>",
            unsafe_allow_html=True,
        )
        for rec in ai_analysis.get("general_recommendations", [
            "Focus on increasing source-segregation rates.",
            "Register bulk generator status with SPCB.",
            "Partner with SPCB-registered recycling agents.",
        ]):
            st.markdown(f"- {rec}")

    with col2:
        st.markdown(
            f"<h3 style='color:#5CDE8C;'>🤖 AI Corrective Action Advice</h3>",
            unsafe_allow_html=True,
        )
        if not violations:
            st.success("✔ System fully compliant. No corrective actions currently necessary.")
        else:
            for item in ai_analysis.get("violations_analysis", []):
                rid = item.get("rule_id", "PWM_RULE")
                st.markdown(
                    _card(
                        _ACCENT_O, _CARD_ORANGE,
                        f"<p style='color:{_TXT_SUB}; font-size:0.75rem; margin:0; font-weight:700;'>"
                        f"REGULATION FOCUS</p>"
                        f"<p style='color:{_ACCENT_O}; font-weight:700; font-size:0.9rem; margin:4px 0;'>"
                        f"`{rid}`</p>"
                        f"<p style='color:{_TXT}; font-size:0.83rem; margin:3px 0;'>"
                        f"<b>Citation:</b> {item.get('legal_citation','N/A')}</p>"
                        f"<p style='color:{_ACCENT_R}; font-size:0.83rem; margin:3px 0;'>"
                        f"<b>Legal Implication:</b> {item.get('legal_consequence','N/A')}</p>"
                        f"<ul style='color:{_TXT}; font-size:0.82rem; margin:6px 0 0 16px; padding:0;'>"
                        + "".join(f"<li>{a}</li>" for a in item.get("corrective_actions", []))
                        + "</ul>"
                    ),
                    unsafe_allow_html=True,
                )

    # ── Alternative Materials ─────────────────────────────────────────────────
    st.divider()
    st.markdown(
        f"<h3 style='color:#5CDE8C;'>🔄 Alternative Material Recommendations</h3>",
        unsafe_allow_html=True,
    )
    for item in ai_analysis.get("alt_materials", []):
        st.markdown(f"- **For {item['polymer']}:** {item['alternative']}")
