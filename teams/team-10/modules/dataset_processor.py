import pandas as pd
import os
from utils.validators import validate_audit_row, validate_csv_columns
from utils.constants import POLYMER_TYPES, DISPOSAL_CHANNELS

class DatasetProcessor:
    def __init__(self, data_dir: str = "datasets"):
        self.data_dir = data_dir
        
    def clean_audit_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cleans and sanitizes raw audit inputs.
        
        Args:
            df (pd.DataFrame): Dataframe loaded from manual inputs or CSV files.
            
        Returns:
            pd.DataFrame: Cleaned dataframe with standard types and added descriptions.
        """
        # Validate overall columns schema
        validate_csv_columns(df)
        
        cleaned_rows = []
        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            try:
                # Validate individual fields
                validate_audit_row(row_dict)
                cleaned_rows.append(row_dict)
            except ValueError as ve:
                # Log bad rows and skip them or raise, here we skip to be robust but flag in logs
                print(f"Skipping row {idx} due to validation error: {ve}")
                
        if not cleaned_rows:
            raise ValueError("No valid audit rows remaining after validation.")
            
        cleaned_df = pd.DataFrame(cleaned_rows)
        
        # Parse Dates
        cleaned_df["date"] = pd.to_datetime(cleaned_df["date"])
        
        # Map IDs to full descriptive labels
        cleaned_df["polymer_desc"] = cleaned_df["resin_code"].map(POLYMER_TYPES)
        cleaned_df["disposal_desc"] = cleaned_df["disposal_method"].map(DISPOSAL_CHANNELS)
        
        return cleaned_df

    def load_benchmarks(self) -> dict:
        """
        Loads local CPCB or Swachh Bharat benchmarking data if exists.
        Falls back to default settings if CSV files are not generated yet.
        """
        benchmarks = {
            "national_avg_recycling_rate": 60.0, # 60% plastic waste recycled in India (CPCB estimate)
            "target_landfill_diversion": 90.0,   # Swachh Bharat mission target
            "per_capita_plastic_gen_g_day": 37.0  # National daily average per capita
        }
        
        cpcb_path = os.path.join(self.data_dir, "cpcb_data.csv")
        if os.path.exists(cpcb_path):
            try:
                cpcb_df = pd.read_csv(cpcb_path)
                benchmarks["cpcb_rules_count"] = len(cpcb_df)
            except Exception:
                pass
                
        return benchmarks
