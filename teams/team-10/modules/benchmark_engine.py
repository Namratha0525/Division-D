import pandas as pd
from modules.data_loader import load_cpcb_data, load_swachh_bharat_data, load_epr_data

class BenchmarkEngine:
    def __init__(self):
        self.cpcb_df = load_cpcb_data()
        self.sbm_df = load_swachh_bharat_data()
        self.epr_df = load_epr_data()

    def compare_with_state_average(self, institution_monthly_kg: float, state_name: str) -> dict:
        """
        Compares institution waste against CPCB state average.
        """
        match = self.cpcb_df[self.cpcb_df["state_name"].str.title() == state_name.title()]
        
        # Default fallback average if state is not found
        state_avg = 220.0 
        per_capita = 37.0
        
        if not match.empty:
            # Scale per capita baseline to represent average small institutional monthly waste estimate
            per_capita = float(match.iloc[0]["average_per_capita_g_day"])
            state_avg = per_capita * 6.0 # Arbitrary scaling factor for institution size simulation

        diff_pct = ((institution_monthly_kg - state_avg) / state_avg * 100) if state_avg > 0 else 0.0
        
        return {
            "institution_monthly_kg": institution_monthly_kg,
            "state_average_kg": round(state_avg, 1),
            "difference_pct": round(diff_pct, 1),
            "state_per_capita_g_day": per_capita,
            "status": "ABOVE_AVERAGE" if institution_monthly_kg > state_avg else "BELOW_AVERAGE"
        }

    def compare_with_city_average(self, institution_monthly_kg: float, state_name: str, district_name: str) -> dict:
        """
        Compares institution waste against Swachh Bharat city/district average.
        """
        match = self.sbm_df[
            (self.sbm_df["state_name"].str.title() == state_name.title()) & 
            (self.sbm_df["district_name"].str.title() == district_name.title())
        ]
        
        city_avg = 180.0
        
        if not match.empty:
            city_avg = float(match.iloc[0]["district_monthly_avg_kg_per_institution"])

        diff_pct = ((institution_monthly_kg - city_avg) / city_avg * 100) if city_avg > 0 else 0.0
        
        return {
            "institution_monthly_kg": institution_monthly_kg,
            "city_average_kg": round(city_avg, 1),
            "difference_pct": round(diff_pct, 1),
            "status": "ABOVE_AVERAGE" if institution_monthly_kg > city_avg else "BELOW_AVERAGE"
        }

    def evaluate_epr_compliance(self, category_volumes: dict) -> dict:
        """
        Evaluates EPR compliance risks, target offsets and registration necessity
        based on CPCB EPR Portal thresholds and user volumes.
        
        Args:
            category_volumes (dict): Map of CPCB category name to institutional weight in kg.
            
        Returns:
            dict: EPR compliance assessment.
        """
        risk_elements = []
        overall_risk_level = "LOW"
        total_liability = 0.0
        
        # Check if the institution exceeds registration thresholds
        for cat_name, volume in category_volumes.items():
            # Find matching target percentage in epr_portal_data
            match = self.epr_df[self.epr_df["epr_category"].str.contains(cat_name.split(" (")[0], case=False, na=False)]
            target_pct = 70.0
            if not match.empty:
                target_pct = float(match.iloc[0]["average_recycling_target_pct"])
                
            liability = volume * (target_pct / 100.0)
            total_liability += liability
            
            # If any single category packaging volume exceeds 100 kg, flag high registration alert
            if volume > 100.0:
                risk_elements.append(f"Volume in {cat_name} ({volume:.1f} kg) exceeds CPCB direct monitoring threshold.")
                overall_risk_level = "HIGH"
                
        if total_liability > 150.0:
            overall_risk_level = "HIGH"
        elif total_liability > 50.0:
            overall_risk_level = "MEDIUM"

        return {
            "overall_risk_level": overall_risk_level,
            "total_epr_liability_kg": round(total_liability, 1),
            "risk_flags": risk_elements,
            "epr_portal_benchmarks": self.epr_df.to_dict(orient="records")
        }

def compare_with_state_average(institution_monthly_kg: float, state_name: str) -> dict:
    return BenchmarkEngine().compare_with_state_average(institution_monthly_kg, state_name)

def compare_with_city_average(institution_monthly_kg: float, state_name: str, district_name: str) -> dict:
    return BenchmarkEngine().compare_with_city_average(institution_monthly_kg, state_name, district_name)

def evaluate_epr_compliance(category_volumes: dict) -> dict:
    return BenchmarkEngine().evaluate_epr_compliance(category_volumes)
