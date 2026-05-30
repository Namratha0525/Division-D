import pandas as pd
from utils.helpers import calculate_co2_offset

class AuditAnalyzer:
    def __init__(self):
        pass

    def calculate_summary_metrics(self, df: pd.DataFrame) -> dict:
        """
        Computes high-level aggregated metrics from the cleaned waste dataset.
        
        Args:
            df (pd.DataFrame): Cleaned audit dataframe.
            
        Returns:
            dict: Summary metrics for dashboard and reports.
        """
        total_weight = df["weight_kg"].sum()
        
        # Calculate recycling rate
        recycled_df = df[df["disposal_method"].isin(["RECYCLED", "CO_PROCESSED"])]
        recycled_weight = recycled_df["weight_kg"].sum()
        recycling_rate = (recycled_weight / total_weight * 100) if total_weight > 0 else 0.0
        
        # Calculate carbon offsets
        total_co2_offset = 0.0
        for _, row in df.iterrows():
            # Assume any plastic diverted from Landfill / Open Burnt contributes to CO2 offsets
            if row["disposal_method"] in ["RECYCLED", "CO_PROCESSED"]:
                total_co2_offset += calculate_co2_offset(row["weight_kg"], row["resin_code"])
                
        # Determine dominant plastic type
        dominant_polymer = "N/A"
        if not df.empty:
            polymer_sums = df.groupby("polymer_desc")["weight_kg"].sum()
            if not polymer_sums.empty:
                dominant_polymer = polymer_sums.idxmax()

        return {
            "total_weight_kg": total_weight,
            "recycled_weight_kg": recycled_weight,
            "recycling_rate_pct": recycling_rate,
            "total_co2_offset_kg": total_co2_offset,
            "dominant_polymer_type": dominant_polymer,
            "total_records": len(df)
        }

    def aggregate_by_polymer(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregates weights by polymer class for donut graphs."""
        if df.empty:
            return pd.DataFrame()
        return df.groupby(["resin_code", "polymer_desc"])["weight_kg"].sum().reset_index()

    def aggregate_by_disposal(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregates weights by disposal method for bar graphs."""
        if df.empty:
            return pd.DataFrame()
        return df.groupby(["disposal_method", "disposal_desc"])["weight_kg"].sum().reset_index()
