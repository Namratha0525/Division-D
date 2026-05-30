import os
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger("AdvancedDatasetAnalyzer")

class AdvancedDatasetAnalyzer:
    def __init__(self, data_dir: str = "datasets"):
        self.data_dir = data_dir
        self.rs_path = os.path.join(data_dir, "RS_Session_266_AU_1159_B_and_C_1.csv")
        self.polymer_path = os.path.join(data_dir, "plastic-use-by-polymer.csv")
        self.application_path = os.path.join(data_dir, "plastic-use-by-applicati.csv")

    def _load_csv(self, filepath: str) -> pd.DataFrame:
        if os.path.exists(filepath):
            try:
                return pd.read_csv(filepath)
            except Exception as e:
                logger.error(f"Error loading {filepath}: {e}")
        return pd.DataFrame()

    def analyze_polymer_trends(self, current_year: int = 2026) -> dict:
        """
        Loads polymer trends, finds the row matching current_year, and returns
        summary metrics of the top polymers nationally/globally.
        """
        df = self._load_csv(self.polymer_path)
        if df.empty:
            return {}

        # The 'Category' column represents the year
        # Note: Category might be stored as integer or quoted string, so we clean it.
        df['Category_clean'] = df['Category'].astype(str).str.replace('"', '').str.strip()
        row = df[df['Category_clean'] == str(current_year)]
        if row.empty:
            # Fallback to the closest year
            row = df.tail(1)
            year_val = row['Category_clean'].values[0]
        else:
            year_val = str(current_year)

        # Columns representing polymers
        cols = [c for c in df.columns if c not in ['Category', 'Category_clean']]
        
        polymer_shares = {}
        total_vol = 0.0
        for col in cols:
            val = row[col].values[0]
            try:
                # Handle potential string format
                val = float(str(val).replace('"', '').strip())
            except ValueError:
                val = 0.0
            polymer_shares[col] = val
            total_vol += val

        # Calculate percentages
        polymer_pct = {}
        if total_vol > 0:
            for k, v in polymer_shares.items():
                polymer_pct[k] = round((v / total_vol) * 100, 1)

        sorted_pct = sorted(polymer_pct.items(), key=lambda x: x[1], reverse=True)

        return {
            "year": year_val,
            "total_volume_million_tonnes": round(total_vol, 1),
            "polymer_volumes": polymer_shares,
            "polymer_shares_pct": polymer_pct,
            "top_polymers": sorted_pct[:5]
        }

    def analyze_application_usage(self, current_year: int = 2026) -> dict:
        """
        Loads application usage trends, finds the row matching current_year,
        and returns the top applications.
        """
        df = self._load_csv(self.application_path)
        if df.empty:
            return {}

        df['Category_clean'] = df['Category'].astype(str).str.replace('"', '').str.strip()
        row = df[df['Category_clean'] == str(current_year)]
        if row.empty:
            row = df.tail(1)
            year_val = row['Category_clean'].values[0]
        else:
            year_val = str(current_year)

        cols = [c for c in df.columns if c not in ['Category', 'Category_clean']]
        
        app_shares = {}
        total_vol = 0.0
        for col in cols:
            val = row[col].values[0]
            try:
                val = float(str(val).replace('"', '').strip())
            except ValueError:
                val = 0.0
            app_shares[col] = val
            total_vol += val

        app_pct = {}
        if total_vol > 0:
            for k, v in app_shares.items():
                app_pct[k] = round((v / total_vol) * 100, 1)

        sorted_pct = sorted(app_pct.items(), key=lambda x: x[1], reverse=True)

        return {
            "year": year_val,
            "total_volume_million_tonnes": round(total_vol, 1),
            "application_volumes": app_shares,
            "application_shares_pct": app_pct,
            "top_applications": sorted_pct[:5]
        }

    def generate_industry_benchmarks(self, inst_df: pd.DataFrame, current_year: int = 2026) -> dict:
        """
        Correlates the audited institution's polymer distribution against
        national/global industry averages.
        """
        poly_trends = self.analyze_polymer_trends(current_year)
        if not poly_trends or inst_df.empty:
            return {}

        # Map RIC to polymer columns in dataset
        # RIC mapping:
        # 1 -> PET
        # 2 -> HDPE
        # 3 -> PVC
        # 4 -> LDPE, LLDPE
        # 5 -> PP
        # 6 -> PS
        # 7 -> Other (combining ABS, ASA, SAN, Fibres, Bioplastics, PUR, etc.)
        ric_to_col = {
            1: "PET",
            2: "HDPE",
            3: "PVC",
            4: "LDPE, LLDPE",
            5: "PP",
            6: "PS",
            7: "Other"
        }

        # Calculate institution volumes & shares
        inst_total_weight = inst_df["weight_kg"].sum()
        inst_shares = {}
        
        # Initalize all keys
        for key in ric_to_col.values():
            inst_shares[key] = 0.0

        if inst_total_weight > 0:
            for ric, col in ric_to_col.items():
                weight = inst_df[inst_df["resin_code"] == ric]["weight_kg"].sum()
                inst_shares[col] = round((weight / inst_total_weight) * 100, 1)

        # Get national/industry shares
        industry_shares = poly_trends.get("polymer_shares_pct", {})
        
        # Build comparison structure
        comparisons = []
        for col in ric_to_col.values():
            inst_pct = inst_shares.get(col, 0.0)
            ind_pct = industry_shares.get(col, 0.0)
            if col == "Other":
                # For "Other", sum up ABS, Fibres, etc. in national dataset
                other_cols = ["ABS, ASA, SAN", "Bioplastics", "Elastomers (tyres)", "Fibres", "Marine coatings", "Other", "PUR", "Road marking coatings"]
                ind_pct = round(sum(industry_shares.get(oc, 0.0) for oc in other_cols), 1)

            comparisons.append({
                "polymer": col,
                "institution_pct": inst_pct,
                "industry_pct": ind_pct,
                "difference": round(inst_pct - ind_pct, 1)
            })

        return {
            "year": poly_trends.get("year"),
            "comparisons": comparisons
        }

    def generate_regulatory_insights(self, state_name: str) -> dict:
        """
        Analyzes Rajya Sabha Session 266 historical state-wise plastic waste trends.
        """
        df = self._load_csv(self.rs_path)
        if df.empty:
            return {}

        # Normalize state names for comparison
        df['State_clean'] = df['State/UT-wise'].astype(str).str.strip().str.lower()
        target_state = state_name.strip().lower()

        # Find matching row
        row = df[df['State_clean'].str.contains(target_state, na=False)]
        if row.empty:
            # Try fuzzy check or fallback to Karnataka
            row = df[df['State_clean'].str.contains('karnataka', na=False)]
            if row.empty:
                return {}

        state_official_name = row['State/UT-wise'].values[0]

        # Extract values for available years
        years = ['2016-17', '2017-18', '2018-19', '2019-20', '2020-21']
        trends = {}
        for y in years:
            val = row[y].values[0]
            if pd.isna(val) or str(val).strip().upper() == 'NA':
                trends[y] = None
            else:
                try:
                    trends[y] = float(str(val).replace('"', '').strip())
                except ValueError:
                    trends[y] = None

        # Calculate growth rate between first non-None year and 2020-21
        valid_vals = [(y, v) for y, v in trends.items() if v is not None]
        growth_pct = 0.0
        insights = ""
        
        if len(valid_vals) >= 2:
            first_year, first_val = valid_vals[0]
            last_year, last_val = valid_vals[-1]
            if first_val > 0:
                growth_pct = round(((last_val - first_val) / first_val) * 100, 1)
            insights = f"Historical state records show plastic waste in {state_official_name} went from {first_val:,.1f} tonnes in {first_year} to {last_val:,.1f} tonnes in {last_year}, a growth of {growth_pct}%."
        else:
            insights = f"Historical state records for {state_official_name} show active plastic waste generation monitoring under the Ministry of Environment, Forest & Climate Change."

        return {
            "state_name": state_official_name,
            "trends": trends,
            "growth_rate_pct": growth_pct,
            "insights_summary": insights
        }
