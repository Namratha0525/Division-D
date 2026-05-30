import streamlit as st
import pandas as pd
from utils.constants import EPR_CATEGORIES

# Dark-mode card helpers (same palette as dashboard.py)
_CARD_GREEN  = "rgba(43,138,62,0.18)"
_CARD_RED    = "rgba(178,59,59,0.18)"
_CARD_ORANGE = "rgba(217,130,43,0.18)"
_CARD_BLUE   = "rgba(92,141,137,0.18)"
_CARD_GREY   = "rgba(100,100,120,0.22)"
_TXT         = "#E8E8E8"
_TXT_SUB     = "#A0A8B0"
_ACCENT_G    = "#5CDE8C"
_ACCENT_R    = "#FF6B6B"
_ACCENT_O    = "#FFB347"
_ACCENT_T    = "#7ECECA"

def _card(border, bg, body):
    return (
        f"<div style='background:{bg}; border-left:5px solid {border}; "
        f"border-radius:10px; padding:16px; margin:6px 0; "
        f"box-shadow:0 2px 10px rgba(0,0,0,0.35);'>{body}</div>"
    )

def _row(label, value):
    return (
        f"<p style='margin:5px 0; color:{_TXT}; font-size:0.84rem;'>"
        f"<b style='color:{_TXT_SUB};'>{label}</b> "
        f"<span style='color:{_TXT}; font-weight:600;'>{value}</span></p>"
    )

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(page_title="EPR Analysis | PlasticWise AI", layout="wide")

st.markdown(
    "<h1 style='color:#5CDE8C;'>📦 Extended Producer Responsibility (EPR) Target Calculator</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<p style='color:{_TXT_SUB};'>Calculates plastic packaging recycling target obligations "
    f"based on CPCB EPR guidelines and institutional audit data.</p>",
    unsafe_allow_html=True,
)

epr_results   = st.session_state.get("epr_results")
score_details = st.session_state.get("score_details", {})

if not epr_results or "category_targets" not in epr_results:
    st.warning("Please upload or input audit records on the Audit Form page to load the EPR obligation matrices.")
else:
    bulk_status      = epr_results.get("bulk_status", {})
    category_targets = epr_results.get("category_targets", {})
    overall_liability= epr_results.get("overall_epr_liability_kg", 0.0)

    df       = st.session_state.get("audit_df")
    total_kg = float(df["weight_kg"].sum()) if df is not None and not df.empty else 0.0

    avg_daily_kg        = bulk_status.get("avg_daily_kg", 0.0)
    annual_generation_kg= avg_daily_kg * 365.0
    is_bulk             = bulk_status.get("is_bulk", False)
    inst_category       = ("Bulk Commercial/Educational Generator" if is_bulk
                           else "Small-Medium Institutional Generator")
    bulk_gen_text       = ("BULK WASTE GENERATOR" if is_bulk
                           else "SME GENERATOR (Below Threshold)")
    required_target_pct = 70.0
    recycling_rate_pct  = (
        float(df[df["disposal_method"].isin(["RECYCLED","CO_PROCESSED"])]["weight_kg"].sum()
              / total_kg * 100)
        if total_kg > 0 else 0.0
    )

    # Compliance traffic-light decision
    if recycling_rate_pct >= required_target_pct and not is_bulk:
        compliance_status = "COMPLIANT"
        traffic_accent    = _ACCENT_G
        traffic_bg        = _CARD_GREEN
        traffic_text      = "🟢 COMPLIANT — Meets recycling targets & SME volume status"
    elif is_bulk and recycling_rate_pct < required_target_pct:
        compliance_status = "NON-COMPLIANT"
        traffic_accent    = _ACCENT_R
        traffic_bg        = _CARD_RED
        traffic_text      = "🔴 NON-COMPLIANT — EPR obligations not met & classified as Bulk Generator"
    else:
        compliance_status = "ATTENTION NEEDED"
        traffic_accent    = _ACCENT_O
        traffic_bg        = _CARD_ORANGE
        traffic_text      = "🟡 ATTENTION NEEDED — Minor gaps in target recyclability or registration"

    # ── Traffic Light Banner ──────────────────────────────────────────────────
    st.markdown(
        _card(
            traffic_accent, traffic_bg,
            f"<p style='color:{traffic_accent}; font-size:1.15rem; font-weight:800; margin:0;'>"
            f"{traffic_text}</p>"
        ),
        unsafe_allow_html=True,
    )

    # ── EPR Obligation Assessment Grid ────────────────────────────────────────
    st.markdown(
        f"<h3 style='color:#5CDE8C; margin-top:20px;'>📋 EPR Obligation Assessment</h3>",
        unsafe_allow_html=True,
    )

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown(
            _card(
                _ACCENT_G, _CARD_GREEN,
                _row("Institution Category:", inst_category)
                + _row("Bulk Generator Status:", bulk_gen_text)
                + _row("Annual Plastic Generation (Projected):", f"{annual_generation_kg:,.1f} kg/year")
            ),
            unsafe_allow_html=True,
        )
    with col_c2:
        st.markdown(
            _card(
                _ACCENT_T, _CARD_BLUE,
                _row("EPR Audited Liability:", f"{overall_liability:.1f} kg")
                + _row("Required Recycling Target Rate:", f"{required_target_pct:.1f}%")
                + _row("EPR Compliance Status:", compliance_status)
            ),
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Category-wise Target Matrix ───────────────────────────────────────────
    st.markdown(
        f"<h3 style='color:#5CDE8C;'>CPCB Category-wise Target Matrix</h3>",
        unsafe_allow_html=True,
    )
    for cat_name, targets in category_targets.items():
        desc = EPR_CATEGORIES.get(cat_name.split(" (")[0], "Other packaging types")
        with st.expander(f"📋 {cat_name} — {desc}"):
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Total Audited Volume",     f"{targets['total_volume_kg']:.1f} kg")
            col_b.metric("Required Offset Rate",     f"{targets['obligation_rate_pct']:.0f}%")
            col_c.metric("Recycling Obligation",     f"{targets['recycling_obligation_kg']:.1f} kg")

    st.divider()

    # ── EPR Benchmark Comparison ──────────────────────────────────────────────
    st.markdown(
        f"<h3 style='color:#5CDE8C;'>📊 Dataset Grounded EPR Benchmark Comparison</h3>",
        unsafe_allow_html=True,
    )

    benchmarks      = score_details.get("benchmarks", {})
    epr_bench       = benchmarks.get("epr_benchmarks", {})
    epr_analysis_res= benchmarks.get("epr_analysis", {})

    if epr_bench and epr_analysis_res:
        state_name  = benchmarks.get("state_name", "Maharashtra")
        status_text = "Action Required" if epr_analysis_res.get("registration_required") else "Fully Compliant"

        col_b1, col_b2, col_b3 = st.columns(3)

        col_b1.markdown(
            _card(
                _ACCENT_G, _CARD_GREEN,
                f"<p style='color:{_TXT_SUB}; font-size:0.75rem; font-weight:700; "
                f"letter-spacing:1px; margin:0;'>INSTITUTION STATUS</p>"
                f"<h4 style='color:{_ACCENT_G}; margin:6px 0;'>Institution Status</h4>"
                + _row("Audited Liability:", f"{overall_liability:.1f} kg")
                + _row("Compliance Status:", compliance_status)
                + _row("Action Required:", status_text)
            ),
            unsafe_allow_html=True,
        )
        col_b2.markdown(
            _card(
                _ACCENT_T, _CARD_BLUE,
                f"<p style='color:{_TXT_SUB}; font-size:0.75rem; font-weight:700; "
                f"letter-spacing:1px; margin:0;'>REGISTERED ORGANIZATIONS</p>"
                f"<h4 style='color:{_ACCENT_T}; margin:6px 0;'>Registered Organizations</h4>"
                + _row(f"Registered Brands in {state_name}:",
                       str(epr_bench.get("state_registered_brands", "N/A")))
                + _row("Target Threshold:", ">100 kg/day")
                + f"<small style='color:{_TXT_SUB};'>Source: CPCB EPR Registry</small>"
            ),
            unsafe_allow_html=True,
        )
        col_b3.markdown(
            _card(
                _ACCENT_O, _CARD_ORANGE,
                f"<p style='color:{_TXT_SUB}; font-size:0.75rem; font-weight:700; "
                f"letter-spacing:1px; margin:0;'>INDUSTRY AVERAGES</p>"
                f"<h4 style='color:{_ACCENT_O}; margin:6px 0;'>Industry Averages</h4>"
                + _row("Compliance Rate:",
                       f"{epr_bench.get('industry_compliance_rate_pct','N/A')}%")
                + _row("Avg Brand Tonnage:",
                       f"{epr_bench.get('average_brand_liability_tonnes','N/A')} MT/yr")
                + f"<small style='color:{_TXT_SUB};'>Source: National Average Index</small>"
            ),
            unsafe_allow_html=True,
        )
    else:
        st.info("EPR benchmark data not yet computed. Run the full analysis pipeline first.")
