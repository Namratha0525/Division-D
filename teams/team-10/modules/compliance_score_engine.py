"""
compliance_score_engine.py
───────────────────────────
Computes three transparent, decomposed compliance scores:

  • PWM Compliance Score  (0-100)  — violation-weighted, severity-penalised
  • EPR Compliance Score  (0-100)  — recycling-target vs actual rate
  • Overall Compliance Score (0-100) — 60% PWM + 40% EPR weighted average

Every number is traceable so judges can follow the arithmetic.
"""
import pandas as pd
from utils.constants import MICRON_LIMIT, BULK_GENERATOR_LIMIT_KG


# ---------------------------------------------------------------------------
# Regulatory constants
# ---------------------------------------------------------------------------
PWM_RULES = {
    "PWM_RULE_4C_MICRONS": {
        "ref": "Rule 4(c) — PWM Rules 2016",
        "title": "Carry-bag / Packaging Sheet Thickness",
        "requirement": "All carry bags and packaging sheets must be ≥ 120 microns thick.",
        "why_it_matters": (
            "Sub-120-micron single-use bags are the primary source of micro-plastic "
            "pollution in urban drains and water bodies. They resist mechanical recycling "
            "and end up in landfills or open environments within weeks of use."
        ),
        "legal_consequence": (
            "Rule 4(c) read with Rule 16: Seizure of non-compliant material, penalty up to "
            "₹1,00,000 for first offence and ₹1,50,000 for repeat, plus facility closure "
            "order from SPCB. (Environment Protection Act, 1986 — Section 15)"
        ),
        "severity": "CRITICAL",
        "severity_weight": 25,          # points deducted from PWM score per critical violation
    },
    "NGT_OPEN_BURNING_BAN": {
        "ref": "Rule 16 + NGT Order — 2016/2019",
        "title": "Open Burning of Plastic Waste",
        "requirement": "Open burning of plastic / municipal solid waste is strictly prohibited.",
        "why_it_matters": (
            "Burning chlorinated plastics (PVC, mixed film) releases dioxins and furans — "
            "carcinogens listed under the Stockholm Convention. One kg of PVC burned can emit "
            "up to 60 g of hydrogen chloride gas affecting a 500-metre radius."
        ),
        "legal_consequence": (
            "NGT Principal Bench Order (2019): Institution liable for ₹25,000/incident. "
            "Repeated non-compliance triggers criminal proceedings under EP Act Section 15 "
            "(up to 5 years imprisonment)."
        ),
        "severity": "CRITICAL",
        "severity_weight": 25,
    },
    "PWM_SUP_BAN_2022": {
        "ref": "Rule 15 — SUP Ban Notification 2022",
        "title": "Single-Use Plastic (Polystyrene) Ban",
        "requirement": "Polystyrene (RIC 6) plates, cups, and cutlery are banned from manufacture, import, stocking, and use.",
        "why_it_matters": (
            "EPS / polystyrene is non-biodegradable and breaks into micro-beads that "
            "contaminate water bodies. It scores zero in recyclability under current Indian "
            "MRF infrastructure and contributes to marine plastic load."
        ),
        "legal_consequence": (
            "SUP Ban Notification 12 Aug 2022: Confiscation of banned items, penalty "
            "₹500–₹50,000 per incident, escalating to ₹1,00,000 for commercial quantities. "
            "SPCB may suspend institutional permits."
        ),
        "severity": "HIGH",
        "severity_weight": 15,
    },
}

EPR_TARGET_PCT = 70.0          # CPCB standard recycling offset target
EPR_BULK_THRESHOLD_KG = BULK_GENERATOR_LIMIT_KG


# ---------------------------------------------------------------------------
# Core Engine
# ---------------------------------------------------------------------------
class ComplianceScoreEngine:
    """
    Transparent, rule-based compliance scoring engine.
    No ML. Every score component is documented and auditable.
    """

    def compute(self, df: pd.DataFrame, violations: list) -> dict:
        """
        Args:
            df         : Cleaned audit DataFrame
            violations : Output of ComplianceChecker.check_violations()

        Returns:
            Structured dict with three scores + full breakdown + enriched violations
        """
        if df.empty:
            return self._empty_result()

        total_kg = float(df["weight_kg"].sum())

        # ── 1.  PWM Score ────────────────────────────────────────────────────
        pwm_score, pwm_breakdown = self._compute_pwm_score(df, violations, total_kg)

        # ── 2.  EPR Score ────────────────────────────────────────────────────
        epr_score, epr_breakdown = self._compute_epr_score(df, total_kg)

        # ── 3.  Overall Score ────────────────────────────────────────────────
        overall_score = round(0.60 * pwm_score + 0.40 * epr_score, 1)
        overall_grade, overall_color, overall_badge = self._grade(overall_score)

        # ── 4.  Enriched violations with "why it matters" + legal consequence
        enriched_violations = self._enrich_violations(violations)

        return {
            "pwm_score": pwm_score,
            "pwm_grade": self._grade(pwm_score)[0],
            "pwm_color": self._grade(pwm_score)[1],
            "pwm_breakdown": pwm_breakdown,

            "epr_score": epr_score,
            "epr_grade": self._grade(epr_score)[0],
            "epr_color": self._grade(epr_score)[1],
            "epr_breakdown": epr_breakdown,

            "overall_score": overall_score,
            "overall_grade": overall_grade,
            "overall_color": overall_color,
            "overall_badge": overall_badge,

            "formula_note": (
                "Overall = 0.60 × PWM Score + 0.40 × EPR Score. "
                "PWM Score starts at 100 and deducts severity-weighted penalty per active violation. "
                "EPR Score is computed from recycling rate vs 70% target, adjusted for bulk generator status."
            ),
            "enriched_violations": enriched_violations,
        }

    # ── PWM Score ─────────────────────────────────────────────────────────────
    def _compute_pwm_score(self, df: pd.DataFrame, violations: list, total_kg: float):
        base = 100.0
        penalty = 0.0
        components = []

        for v in violations:
            rule_meta = PWM_RULES.get(v["rule_id"], {})
            sev_weight = rule_meta.get("severity_weight", 10)

            # Volume-weighted penalty: heavier the affected weight, larger the penalty
            affected_pct = (v.get("affected_weight_kg", 0.0) / total_kg * 100) if total_kg > 0 else 0.0
            volume_factor = min(1.0, affected_pct / 20.0)  # caps at 100% penalty at 20%+ volume
            this_penalty = round(sev_weight * (0.5 + 0.5 * volume_factor), 1)

            penalty += this_penalty
            components.append({
                "rule_id": v["rule_id"],
                "severity": v.get("severity", "HIGH"),
                "base_deduction_pts": sev_weight,
                "volume_factor": round(volume_factor, 2),
                "actual_deduction_pts": this_penalty,
                "affected_kg": round(v.get("affected_weight_kg", 0.0), 1),
                "affected_pct_of_total": round(affected_pct, 1),
            })

        pwm_score = round(max(0.0, base - penalty), 1)
        return pwm_score, {
            "base_score": base,
            "total_penalty": round(penalty, 1),
            "penalty_components": components,
        }

    # ── EPR Score ─────────────────────────────────────────────────────────────
    def _compute_epr_score(self, df: pd.DataFrame, total_kg: float):
        recycled_kg = float(
            df[df["disposal_method"].isin(["RECYCLED", "CO_PROCESSED"])]["weight_kg"].sum()
        )
        actual_recycling_pct = (recycled_kg / total_kg * 100) if total_kg > 0 else 0.0

        # Achievement ratio vs target (70%)
        achievement_ratio = min(1.0, actual_recycling_pct / EPR_TARGET_PCT)
        raw_score = achievement_ratio * 85.0   # max 85 points from recycling

        # Bonus: 10 pts if NOT a bulk generator
        daily_totals = df.groupby(df["date"].dt.date)["weight_kg"].sum()
        avg_daily = float(daily_totals.mean()) if not daily_totals.empty else 0.0
        is_bulk = avg_daily >= EPR_BULK_THRESHOLD_KG
        bulk_bonus = 0.0 if is_bulk else 10.0

        # Bonus: 5 pts for zero open burning
        open_burnt = float(df[df["disposal_method"] == "OPEN_BURNT"]["weight_kg"].sum())
        burn_bonus = 0.0 if open_burnt > 0 else 5.0

        epr_score = round(min(100.0, raw_score + bulk_bonus + burn_bonus), 1)

        return epr_score, {
            "actual_recycling_pct": round(actual_recycling_pct, 1),
            "target_recycling_pct": EPR_TARGET_PCT,
            "achievement_ratio_pct": round(achievement_ratio * 100, 1),
            "recycling_component_pts": round(raw_score, 1),
            "bulk_generator": is_bulk,
            "avg_daily_kg": round(avg_daily, 1),
            "bulk_status_bonus_pts": bulk_bonus,
            "no_open_burning_bonus_pts": burn_bonus,
        }

    # ── Enriched Violations ────────────────────────────────────────────────────
    def _enrich_violations(self, violations: list) -> list:
        enriched = []
        for v in violations:
            meta = PWM_RULES.get(v["rule_id"], {})
            enriched.append({
                **v,
                "rule_reference": meta.get("ref", v["rule_id"]),
                "requirement": meta.get("requirement", ""),
                "why_it_matters": meta.get("why_it_matters", ""),
                "legal_consequence": meta.get("legal_consequence", ""),
                "corrective_priority": "IMMEDIATE" if v.get("severity") == "CRITICAL" else "URGENT",
            })
        return enriched

    # ── Grade Bands ───────────────────────────────────────────────────────────
    @staticmethod
    def _grade(score: float):
        if score >= 90:
            return "Excellent", "#2B8A3E", "🏆 EXCELLENT"
        elif score >= 75:
            return "Good", "#5C8D89", "✅ GOOD"
        elif score >= 55:
            return "Attention Required", "#D9822B", "⚠️ ATTENTION REQUIRED"
        else:
            return "Non-Compliant", "#B23B3B", "🚨 NON-COMPLIANT"

    # ── Empty Result ──────────────────────────────────────────────────────────
    @staticmethod
    def _empty_result():
        return {
            "pwm_score": 0.0, "pwm_grade": "N/A", "pwm_color": "#6c757d", "pwm_breakdown": {},
            "epr_score": 0.0, "epr_grade": "N/A", "epr_color": "#6c757d", "epr_breakdown": {},
            "overall_score": 0.0, "overall_grade": "N/A", "overall_color": "#6c757d",
            "overall_badge": "N/A", "formula_note": "", "enriched_violations": [],
        }
