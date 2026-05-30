import os
import pandas as pd
import logging

logger = logging.getLogger("DataLoader")

class DataLoader:
    def __init__(self, raw_dir: str = "datasets/raw"):
        self.raw_dir = raw_dir

    def load_cpcb_data(self) -> pd.DataFrame:
        """
        Loads the CPCB Plastic Waste Management raw dataset.
        If missing, returns default benchmark dataframe.
        """
        filepath = os.path.join(self.raw_dir, "cpcb_data.csv")
        if os.path.exists(filepath):
            try:
                return pd.read_csv(filepath)
            except Exception as e:
                logger.error(f"Error loading CPCB data: {e}")
        
        # Return fallback layout
        return pd.DataFrame({
            "state_name": ["Maharashtra", "Tamil Nadu", "Delhi", "Karnataka", "Uttar Pradesh", "West Bengal", "Gujarat"],
            "state_annual_plastic_waste_tonnes": [443724, 401243, 290000, 129600, 244200, 110400, 312000],
            "average_per_capita_g_day": [38.2, 45.1, 42.0, 32.5, 28.1, 30.2, 37.4],
            "recycling_rate_pct": [62.4, 59.1, 65.0, 58.2, 50.5, 48.0, 56.5]
        })

    def load_swachh_bharat_data(self) -> pd.DataFrame:
        """
        Loads Swachh Bharat Mission municipal dataset.
        """
        filepath = os.path.join(self.raw_dir, "swachh_bharat_data.csv")
        if os.path.exists(filepath):
            try:
                return pd.read_csv(filepath)
            except Exception as e:
                logger.error(f"Error loading SBM data: {e}")
                
        return pd.DataFrame({
            "state_name": ["Maharashtra", "Tamil Nadu", "Delhi", "Karnataka", "Uttar Pradesh", "West Bengal", "Gujarat"],
            "district_name": ["Mumbai City", "Chennai", "New Delhi", "Bengaluru Urban", "Lucknow", "Kolkata", "Ahmedabad"],
            "district_monthly_avg_kg_per_institution": [220.0, 210.0, 250.0, 180.0, 150.0, 160.0, 190.0],
            "municipal_collection_rate_pct": [95.0, 91.0, 98.0, 94.0, 80.0, 85.0, 92.0]
        })

    def load_epr_data(self) -> pd.DataFrame:
        """
        Loads the CPCB EPR portal registration and recycling target thresholds.
        """
        filepath = os.path.join(self.raw_dir, "epr_portal_data.csv")
        if os.path.exists(filepath):
            try:
                return pd.read_csv(filepath)
            except Exception as e:
                logger.error(f"Error loading EPR portal data: {e}")
                
        return pd.DataFrame({
            "epr_category": ["Category I (Rigid)", "Category II (Flexible)", "Category III (Multilayered)", "Category IV (Compostable)"],
            "national_registered_brands_count": [1240, 850, 430, 150],
            "average_recycling_target_pct": [70.0, 70.0, 60.0, 80.0],
            "cpcb_industry_offset_tonnes": [25000, 18000, 12000, 2000]
        })

def load_cpcb_data() -> pd.DataFrame:
    return DataLoader().load_cpcb_data()

def load_swachh_bharat_data() -> pd.DataFrame:
    return DataLoader().load_swachh_bharat_data()

def load_epr_data() -> pd.DataFrame:
    return DataLoader().load_epr_data()
