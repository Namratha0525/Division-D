import json
import pandas as pd
import logging
from modules.data_loader import load_cpcb_data, load_swachh_bharat_data, load_epr_data
from modules.advanced_dataset_analyzer import AdvancedDatasetAnalyzer

logger = logging.getLogger("ContextBuilder")

class ContextBuilder:
    def __init__(self):
        self.analyzer = AdvancedDatasetAnalyzer()

    def build_grounding_context(self, state: str, district: str, df: pd.DataFrame, epr_results: dict) -> str:
        """
        Gathers matching records across all five datasets and formats them into
        a structured, clear markdown grounding context block for the LLM.
        """
        # 1. State / District CPCB and Swachh Bharat benchmarking context
        cpcb_df = load_cpcb_data()
        sbm_df = load_swachh_bharat_data()
        
        state_match = cpcb_df[cpcb_df['state_name'].str.lower() == state.lower()]
        district_match = sbm_df[sbm_df['district_name'].str.lower() == district.lower()]

        cpcb_context = ""
        if not state_match.empty:
            row = state_match.iloc[0]
            cpcb_context = (
                f"- Regional CPCB Statistics: State of {row['state_name']} generates "
                f"{row['state_annual_plastic_waste_tonnes']:,} tonnes of plastic waste annually, "
                f"with a regional recycling diversion rate of {row['recycling_rate_pct']}% "
                f"and per capita generation of {row['average_per_capita_g_day']} g/day."
            )
        else:
            cpcb_context = f"- Regional CPCB Statistics: Baseline per capita generation of 35 g/day with 50-60% average recycling rate."

        sbm_context = ""
        if not district_match.empty:
            row = district_match.iloc[0]
            sbm_context = (
                f"- Swachh Bharat Municipal Baseline: District of {row['district_name']} has an average "
                f"monthly institutional waste baseline of {row['district_monthly_avg_kg_per_institution']:.1f} kg "
                f"and a municipal waste collection rate of {row['municipal_collection_rate_pct']}%."
            )
        else:
            sbm_context = f"- Swachh Bharat Municipal Baseline: Average institutional generation of 180 kg/month with 90%+ municipal collection rates."

        # 2. Historical Rajya Sabha trends
        rs_trends = self.analyzer.generate_regulatory_insights(state)
        rs_context = ""
        if rs_trends:
            rs_context = f"- Rajya Sabha Session 266 State Historical Trend: {rs_trends.get('insights_summary')}"

        # 3. EPR portal baseline registration counts
        epr_df = load_epr_data()
        epr_details = []
        for _, row in epr_df.iterrows():
            epr_details.append(
                f"  * {row['epr_category']}: {row['national_registered_brands_count']} registered brands nationally, "
                f"average recycling target of {row['average_recycling_target_pct']}%, "
                f"CPCB sector offset of {row['cpcb_industry_offset_tonnes']} tonnes."
            )
        epr_context = "- CPCB EPR Portal Industry Context:\n" + "\n".join(epr_details)

        # 4. Polymer & Application Trends
        poly_trends = self.analyzer.analyze_polymer_trends(2026)
        app_trends = self.analyzer.analyze_application_usage(2026)
        
        poly_context = ""
        if poly_trends:
            top_polys = ", ".join([f"{k} ({v}%)" for k, v in poly_trends.get("top_polymers", [])])
            poly_context = (
                f"- Industry Polymer Consumption (Year {poly_trends.get('year')}): Total volume is "
                f"{poly_trends.get('total_volume_million_tonnes')} million tonnes. "
                f"Top used polymers nationally/globally are: {top_polys}."
            )
            
        app_context = ""
        if app_trends:
            top_apps = ", ".join([f"{k} ({v}%)" for k, v in app_trends.get("top_applications", [])])
            app_context = (
                f"- Industry Application Distribution (Year {app_trends.get('year')}): "
                f"Top plastic applications are: {top_apps}."
            )

        # 5. Institution current audit footprint
        total_kg = float(df["weight_kg"].sum()) if not df.empty else 0.0
        recycling_rate = float(df[df["disposal_method"].isin(["RECYCLED", "CO_PROCESSED"])]["weight_kg"].sum() / total_kg * 100) if total_kg > 0 else 0.0
        
        inst_context = (
            f"- Audited Institution waste profile:\n"
            f"  * Total monitored waste: {total_kg:.1f} kg\n"
            f"  * Current recycling diversion rate: {recycling_rate:.1f}%\n"
            f"  * Calculated EPR packaging liability: {epr_results.get('overall_epr_liability_kg', 0.0):.1f} kg\n"
            f"  * Bulk generator status: {'BULK GENERATOR (Action Required)' if epr_results.get('bulk_status', {}).get('is_bulk') else 'SME GENERATOR (Compliant volume)'}"
        )

        # Combine all grounding namespaces
        unified_context = (
            "=== RETRIEVED REGULATORY & INDUSTRY BENCHMARK CONTEXT ===\n"
            f"{cpcb_context}\n"
            f"{sbm_context}\n"
            f"{rs_context}\n"
            f"{epr_context}\n"
            f"{poly_context}\n"
            f"{app_context}\n"
            f"{inst_context}\n"
            "========================================================="
        )
        
        return unified_context
