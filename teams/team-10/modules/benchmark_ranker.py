"""
benchmark_ranker.py
────────────────────
Computes rank position and performance tier for the institution
against all states in the CPCB dataset.

Ranks are determined on:
  • Recycling Rate (%)  — higher is better
  • Annual Waste Generation (tonnes/year) — lower is better
  • Per-capita generation (g/day) — lower is better

No ML. Pure pandas sorting + percentile math.
"""
import pandas as pd
from modules.data_loader import load_cpcb_data, load_swachh_bharat_data


# Performance tier thresholds (based on recycling rate rank percentile)
TIER_THRESHOLDS = {
    "Leader":       80,    # top 20% of states by recycling rate
    "On Track":     50,    # top 50%
    "Needs Action": 25,    # top 75%
    # below → Critical
}

TIER_COLORS = {
    "Leader":       ("#2B8A3E", "#EDFAED", "🏆"),
    "On Track":     ("#5C8D89", "#EDF5F5", "✅"),
    "Needs Action": ("#D9822B", "#FFF8F2", "⚠️"),
    "Critical":     ("#B23B3B", "#FFF5F5", "🚨"),
}


class BenchmarkRanker:
    """
    Produces state ranking, district ranking, national comparison,
    and performance tier for the audited institution.
    """

    def __init__(self):
        self.cpcb_df = load_cpcb_data()
        self.sbm_df  = load_swachh_bharat_data()

    def rank(self, state_name: str, district_name: str, institution_monthly_kg: float) -> dict:
        """
        Args:
            state_name              : Selected state (matches cpcb_data.csv)
            district_name           : Selected district (matches swachh_bharat_data.csv)
            institution_monthly_kg  : Institution's monthly average waste (kg)

        Returns:
            dict with full ranking detail
        """
        cpcb = self.cpcb_df.copy()
        sbm  = self.sbm_df.copy()

        total_states   = len(cpcb)
        total_districts = len(sbm)

        # ── State Rank by Recycling Rate ──────────────────────────────────────
        cpcb_sorted_recycling = cpcb.sort_values("recycling_rate_pct", ascending=False).reset_index(drop=True)
        cpcb_sorted_recycling["rank_recycling"] = cpcb_sorted_recycling.index + 1

        state_row = cpcb_sorted_recycling[
            cpcb_sorted_recycling["state_name"].str.lower() == state_name.lower()
        ]
        state_recycling_rank = int(state_row["rank_recycling"].values[0]) if not state_row.empty else total_states
        state_recycling_rate = float(state_row["recycling_rate_pct"].values[0]) if not state_row.empty else 0.0
        state_annual_waste   = float(state_row["state_annual_plastic_waste_tonnes"].values[0]) if not state_row.empty else 0.0
        state_per_capita     = float(state_row["average_per_capita_g_day"].values[0]) if not state_row.empty else 0.0

        # Percentile rank (higher = better)
        state_percentile = round(100.0 * (1 - (state_recycling_rank - 1) / total_states), 0)

        # ── National Average ──────────────────────────────────────────────────
        national_avg_recycling   = round(float(cpcb["recycling_rate_pct"].mean()), 1)
        national_avg_per_capita  = round(float(cpcb["average_per_capita_g_day"].mean()), 1)
        national_avg_monthly_kg  = round(float(sbm["district_monthly_avg_kg_per_institution"].mean()), 1)

        # ── Institution vs District Benchmark ────────────────────────────────
        district_row = sbm[sbm["district_name"].str.lower() == district_name.lower()]
        district_avg = float(district_row["district_monthly_avg_kg_per_institution"].values[0]) if not district_row.empty else 180.0
        collection_rate = float(district_row["municipal_collection_rate_pct"].values[0]) if not district_row.empty else 90.0

        # Rank all districts by monthly avg (lower is better)
        sbm_sorted = sbm.sort_values("district_monthly_avg_kg_per_institution", ascending=True).reset_index(drop=True)
        sbm_sorted["rank_waste"] = sbm_sorted.index + 1
        dist_row_ranked = sbm_sorted[sbm_sorted["district_name"].str.lower() == district_name.lower()]
        district_rank = int(dist_row_ranked["rank_waste"].values[0]) if not dist_row_ranked.empty else total_districts

        # How the institution compares against its own district
        inst_vs_district_pct = round(((institution_monthly_kg - district_avg) / district_avg) * 100, 1) if district_avg > 0 else 0.0
        inst_vs_national_pct = round(((institution_monthly_kg - national_avg_monthly_kg) / national_avg_monthly_kg) * 100, 1) if national_avg_monthly_kg > 0 else 0.0

        # ── Tier Assignment ───────────────────────────────────────────────────
        if state_percentile >= TIER_THRESHOLDS["Leader"]:
            tier = "Leader"
        elif state_percentile >= TIER_THRESHOLDS["On Track"]:
            tier = "On Track"
        elif state_percentile >= TIER_THRESHOLDS["Needs Action"]:
            tier = "Needs Action"
        else:
            tier = "Critical"

        tier_color, tier_bg, tier_icon = TIER_COLORS[tier]

        return {
            # State ranking
            "state_name":                state_name,
            "state_recycling_rank":      state_recycling_rank,
            "state_recycling_rank_of":   total_states,
            "state_recycling_rate_pct":  state_recycling_rate,
            "state_annual_waste_tonnes": round(state_annual_waste, 0),
            "state_per_capita_g_day":    state_per_capita,
            "state_percentile":          state_percentile,

            # National averages
            "national_avg_recycling_pct":    national_avg_recycling,
            "national_avg_per_capita_g_day": national_avg_per_capita,
            "national_avg_monthly_kg":       national_avg_monthly_kg,

            # District ranking
            "district_name":             district_name,
            "district_rank":             district_rank,
            "district_rank_of":          total_districts,
            "district_avg_monthly_kg":   round(district_avg, 1),
            "district_collection_rate_pct": collection_rate,

            # Institution vs benchmarks
            "institution_monthly_kg":    round(institution_monthly_kg, 1),
            "inst_vs_district_pct":      inst_vs_district_pct,
            "inst_vs_national_pct":      inst_vs_national_pct,
            "inst_performance":          "BELOW AVERAGE (Good)" if inst_vs_district_pct < 0 else "ABOVE AVERAGE (Action Required)",

            # Performance tier
            "performance_tier":          tier,
            "tier_color":                tier_color,
            "tier_bg":                   tier_bg,
            "tier_icon":                 tier_icon,

            # All states table for full reference
            "all_states_ranking": cpcb_sorted_recycling[[
                "state_name", "recycling_rate_pct",
                "state_annual_plastic_waste_tonnes", "average_per_capita_g_day",
                "rank_recycling"
            ]].rename(columns={
                "state_name": "State",
                "recycling_rate_pct": "Recycling Rate (%)",
                "state_annual_plastic_waste_tonnes": "Annual Waste (T)",
                "average_per_capita_g_day": "Per Capita (g/day)",
                "rank_recycling": "Rank",
            }).to_dict(orient="records"),
        }
