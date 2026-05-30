import pandas as pd
from utils.constants import BULK_GENERATOR_LIMIT_KG

class EPRCalculator:
    def __init__(self):
        pass

    def check_bulk_generator_status(self, df: pd.DataFrame) -> dict:
        """
        Determines if the institution falls under the 'Bulk Waste Generator' criteria.
        Criteria: Generating more than 100 kg of waste (of all types combined, or specifically plastic)
        per day. In this context, we check if the average daily plastic weight exceeds the limit.
        """
        if df.empty:
            return {"is_bulk": False, "avg_daily_kg": 0.0, "reason": "No data audited."}
            
        # Group by date to find daily totals
        daily_totals = df.groupby(df["date"].dt.date)["weight_kg"].sum()
        avg_daily = daily_totals.mean() if not daily_totals.empty else 0.0
        
        is_bulk = bool(avg_daily >= BULK_GENERATOR_LIMIT_KG)
        
        return {
            "is_bulk": is_bulk,
            "avg_daily_kg": float(avg_daily),
            "threshold_kg": BULK_GENERATOR_LIMIT_KG,
            "reason": (
                f"Average daily generation ({avg_daily:.1f} kg/day) exceeds CPCB threshold "
                f"of {BULK_GENERATOR_LIMIT_KG} kg/day." if is_bulk else 
                f"Daily generation average ({avg_daily:.1f} kg/day) is within legal limits."
            )
        }

    def categorize_epr_packaging(self, df: pd.DataFrame) -> dict:
        """
        Classifies the audit records into official CPCB EPR Categories.
        
        CPCB Categories:
        - Category I: Rigid Plastic (PET bottles, HDPE jars, PP boxes) -> RIC 1, 2, 5
        - Category II: Flexible Packaging -> RIC 4 (LDPE), RIC 7 (Non-multilayer films)
        - Category III: Multilayered (Plastic + non-plastic like tetrapaks, foil laminate) -> RIC 7 (Composites)
        - Category IV: Compostable plastic -> Handled separately (usually custom tagged or composting disposal)
        """
        category_weights = {
            "Category I (Rigid)": 0.0,
            "Category II (Flexible)": 0.0,
            "Category III (Multilayered)": 0.0,
            "Category IV (Compostable)": 0.0
        }
        
        for _, row in df.iterrows():
            ric = row["resin_code"]
            weight = row["weight_kg"]
            disposal = row["disposal_method"]
            
            # Category IV: Compostable check (if disposal method is composting, or custom logic)
            if ric == 7 and "compost" in str(row.get("disposal_desc", "")).lower():
                category_weights["Category IV (Compostable)"] += weight
            elif ric in [1, 2, 5]:
                category_weights["Category I (Rigid)"] += weight
            elif ric in [3, 4, 6]:
                category_weights["Category II (Flexible)"] += weight
            else: # RIC 7
                # Default RIC 7 to Multilayered if not compostable
                category_weights["Category III (Multilayered)"] += weight

        return category_weights

    def calculate_epr_obligations(self, df: pd.DataFrame) -> dict:
        """
        Computes the target recycling obligations based on categorization.
        Under CPCB rules, standard recycling targets for brand owners/bulk users range 
        from 50% to 100% depending on the compliance year. We use a flat 70% obligation rate 
        for calculation demo.
        """
        epr_weights = self.categorize_epr_packaging(df)
        bulk_status = self.check_bulk_generator_status(df)
        
        obligation_rate = 0.70 # 70% legal target
        targets = {}
        
        for cat, weight in epr_weights.items():
            targets[cat] = {
                "total_volume_kg": weight,
                "recycling_obligation_kg": weight * obligation_rate,
                "obligation_rate_pct": obligation_rate * 100
            }
            
        return {
            "bulk_status": bulk_status,
            "category_targets": targets,
            "overall_epr_liability_kg": sum(t["recycling_obligation_kg"] for t in targets.values())
        }
