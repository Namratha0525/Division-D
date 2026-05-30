import pandas as pd
from utils.constants import SCORING_WEIGHTS
from modules.data_downloader import DataDownloader

class SustainabilityScorer:
    def __init__(self):
        pass

    def calculate_sustainability_index(self, df: pd.DataFrame, violations: list, state_name: str = "Maharashtra", district_name: str = "Mumbai City") -> dict:
        """
        Computes a weighted sustainability performance score (0 to 100) for the institution,
        incorporating comparisons against CPCB & Swachh Bharat regional benchmarks.
        
        Args:
            df (pd.DataFrame): Audit dataset.
            violations (list): Detected rule violations list.
            state_name (str): Selected state for benchmarking comparison.
            district_name (str): Selected district for benchmarking comparison.
            
        Returns:
            dict: Structured index score breakdown, grading labels, and regional benchmarks.
        """
        if df.empty:
            return {
                "score": 0.0,
                "grade": "N/A",
                "color": "#6c757d",
                "breakdown": {},
                "benchmarks": {}
            }

        total_weight = df["weight_kg"].sum()

        # 1. Recycling Rate Score (40% Weight)
        recycled_weight = df[df["disposal_method"].isin(["RECYCLED", "CO_PROCESSED"])]["weight_kg"].sum()
        recycling_rate = (recycled_weight / total_weight) if total_weight > 0 else 0.0
        recycling_score = recycling_rate * 100 * SCORING_WEIGHTS["recycling_rate"]

        # 2. Single-Use Plastic Proportion Score (30% Weight)
        sup_weight = df[(df["resin_code"] == 6) | ((df["thickness_microns"] > 0) & (df["thickness_microns"] < 120))]["weight_kg"].sum()
        sup_proportion = (sup_weight / total_weight) if total_weight > 0 else 0.0
        sup_free_rate = 1.0 - sup_proportion
        sup_score = sup_free_rate * 100 * SCORING_WEIGHTS["sup_proportion"]

        # 3. Compliance & Violations Penalty (20% Weight)
        compliance_penalty = sum(10 for v in violations if v["severity"] in ["CRITICAL", "HIGH"])
        compliance_base = 20.0 - compliance_penalty
        compliance_score = max(0.0, compliance_base)

        # 4. Audit Completeness Score (10% Weight)
        thickness_filled = df["thickness_microns"].notna().sum()
        completeness_rate = thickness_filled / len(df) if len(df) > 0 else 0.0
        completeness_score = completeness_rate * 100 * SCORING_WEIGHTS["audit_completeness"]

        # 5. Load and Compare Benchmarks via BenchmarkEngine and EPRDataProcessor
        from modules.benchmark_engine import BenchmarkEngine
        from modules.epr_data_processor import analyze_epr_compliance, generate_epr_benchmarks
        
        engine = BenchmarkEngine()
        
        # Calculate monthly average institutional waste
        daily_totals = df.groupby(df["date"].dt.date)["weight_kg"].sum()
        avg_daily = daily_totals.mean() if not daily_totals.empty else 0.0
        inst_monthly_avg = avg_daily * 30.0
        
        # Run state and city comparison checks
        state_comparison = engine.compare_with_state_average(inst_monthly_avg, state_name)
        city_comparison = engine.compare_with_city_average(inst_monthly_avg, state_name, district_name)
        
        # Run CPCB EPR Portal compliance and benchmark checks
        epr_analysis_res = analyze_epr_compliance(df)
        epr_bench = generate_epr_benchmarks(state_name)
        
        # Adjust score depending on benchmarking (Bonus for below city average)
        benchmark_bonus = 0.0
        if city_comparison["status"] == "BELOW_AVERAGE":
            benchmark_bonus += 5.0
        else:
            benchmark_bonus -= 5.0
            
        # Penalty for non-compliant EPR status
        if epr_analysis_res["compliance_status"] == "NON_COMPLIANT":
            benchmark_bonus -= 5.0

        # Aggregate final score
        final_score = recycling_score + sup_score + compliance_score + completeness_score + benchmark_bonus
        final_score = max(0.0, min(100.0, final_score))
        
        # Grading assignments
        if final_score >= 85.0:
            grade = "Gold Tier (Exemplary)"
            color = "#2B8A3E" # Safe Green
        elif final_score >= 70.0:
            grade = "Silver Tier (Active Compliance)"
            color = "#5C8D89" # Sage Green
        elif final_score >= 50.0:
            grade = "Bronze Tier (Basic Monitoring)"
            color = "#D9822B" # Orange Warning
        else:
            grade = "Red Tier (Non-Compliant / High Risk)"
            color = "#B23B3B" # Alert Red

        return {
            "score": round(final_score, 1),
            "grade": grade,
            "color": color,
            "breakdown": {
                "recycling_contribution": round(recycling_score, 1),
                "sup_free_contribution": round(sup_score, 1),
                "compliance_contribution": round(compliance_score, 1),
                "completeness_contribution": round(completeness_score, 1),
                "benchmark_adjustment": round(benchmark_bonus, 1)
            },
            "metrics": {
                "recycling_rate_pct": round(recycling_rate * 100, 1),
                "sup_proportion_pct": round(sup_proportion * 100, 1),
                "audit_completeness_pct": round(completeness_rate * 100, 1),
                "active_violations_count": len(violations),
                "institution_monthly_avg_kg": round(inst_monthly_avg, 1)
            },
            "benchmarks": {
                "state_average_kg": state_comparison["state_average_kg"],
                "city_average_kg": city_comparison["city_average_kg"],
                "state_per_capita_g_day": state_comparison["state_per_capita_g_day"],
                "state_comparison_status": state_comparison["status"],
                "city_comparison_status": city_comparison["status"],
                "state_name": state_name,
                "district_name": district_name,
                "epr_analysis": epr_analysis_res,
                "epr_benchmarks": epr_bench
            }
        }
