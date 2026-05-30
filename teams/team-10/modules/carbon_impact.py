"""
carbon_impact.py
─────────────────
Detailed CO₂ emission and savings analysis per disposal pathway and polymer type.
Uses IPCC/EPA emission factors referenced against Indian waste composition data.

No ML — pure arithmetic, fully auditable.
"""
import pandas as pd


# ---------------------------------------------------------------------------
# Emission factors (kg CO₂e per kg of plastic)
# Sources: IPCC 2006 Guidelines, EPA AP-42, CPCB India 2019 waste report
# ---------------------------------------------------------------------------
CO2_FACTORS = {
    # Recycling: saves manufacturing emissions vs virgin production
    "RECYCLED": {
        1: -1.50,   # PET  — saves ~1.5 kg CO2e per kg recycled vs virgin
        2: -1.80,   # HDPE — saves ~1.8 kg CO2e per kg
        3: -2.00,   # PVC  — saves ~2.0 kg CO2e per kg
        4: -1.75,   # LDPE — saves ~1.75 kg CO2e per kg
        5: -1.90,   # PP   — saves ~1.9 kg CO2e per kg
        6: -2.50,   # PS   — saves ~2.5 kg CO2e per kg
        7: -1.60,   # Mixed/Other
    },
    # Co-processing in cement kilns
    "CO_PROCESSED": {
        1: -0.90, 2: -0.95, 3: -0.85, 4: -0.90, 5: -0.92, 6: -1.00, 7: -0.88,
    },
    # Landfill: emits CH4 over decades, converted to CO2e
    "LANDFILLED": {
        1: 0.80, 2: 0.70, 3: 0.60, 4: 0.90, 5: 0.75, 6: 0.95, 7: 0.80,
    },
    # WTE incineration — controlled, counts as partial emission
    "INCINERATED": {
        1: 2.00, 2: 1.80, 3: 2.80, 4: 2.10, 5: 1.95, 6: 3.10, 7: 2.20,
    },
    # Open burning — worst case: uncontrolled combustion
    "OPEN_BURNT": {
        1: 3.20, 2: 2.90, 3: 4.50, 4: 3.40, 5: 3.10, 6: 5.00, 7: 3.50,
    },
}

# CO2 equivalences for report narrative
KG_CO2_PER_TREE_PER_YEAR     = 21.77   # Average tropical tree sequesters 21.77 kg CO2/year
KG_CO2_PER_KM_CAR            = 0.171   # Average Indian petrol car (ARAI 2023)
KG_CO2_PER_KWH_ELECTRICITY   = 0.82    # CEA India grid emission factor 2022

POLYMER_NAMES = {
    1: "PET", 2: "HDPE", 3: "PVC",
    4: "LDPE", 5: "PP", 6: "PS (Polystyrene)", 7: "Multi-layer/Other"
}


class CarbonImpactAnalyzer:
    """
    Calculates full CO₂ impact profile: savings from good pathways,
    emissions from bad pathways, and net environmental footprint.
    """

    def analyze(self, df: pd.DataFrame) -> dict:
        if df.empty:
            return self._empty_result()

        rows = []
        total_saved_kg = 0.0
        total_emitted_kg = 0.0

        for _, row in df.iterrows():
            ric    = int(row["resin_code"])
            weight = float(row["weight_kg"])
            method = str(row["disposal_method"]).upper()

            factors = CO2_FACTORS.get(method, {})
            factor  = factors.get(ric, factors.get(7, 0.0))
            co2_kg  = round(weight * factor, 3)

            if co2_kg < 0:
                total_saved_kg += abs(co2_kg)
            else:
                total_emitted_kg += co2_kg

            rows.append({
                "polymer":       POLYMER_NAMES.get(ric, "Other"),
                "weight_kg":     weight,
                "pathway":       method,
                "co2_factor":    factor,
                "co2_impact_kg": co2_kg,
                "impact_type":   "SAVINGS" if co2_kg < 0 else "EMISSION",
            })

        detail_df = pd.DataFrame(rows)
        net_co2_kg = round(total_emitted_kg - total_saved_kg, 2)

        # Equivalences
        trees_saved_equivalent   = round(total_saved_kg / KG_CO2_PER_TREE_PER_YEAR, 1)
        car_km_avoided           = round(total_saved_kg / KG_CO2_PER_KM_CAR, 0)
        kwh_electricity_saved    = round(total_saved_kg / KG_CO2_PER_KWH_ELECTRICITY, 1)

        # Per-pathway summary
        pathway_summary = {}
        for method in detail_df["pathway"].unique():
            sub = detail_df[detail_df["pathway"] == method]
            pathway_summary[method] = {
                "total_weight_kg": round(sub["weight_kg"].sum(), 2),
                "total_co2_kg":    round(sub["co2_impact_kg"].sum(), 2),
                "impact_type":     "SAVINGS" if sub["co2_impact_kg"].sum() < 0 else "EMISSION",
            }

        # Per-polymer summary
        polymer_summary = (
            detail_df.groupby("polymer")
            .agg(weight_kg=("weight_kg", "sum"), co2_kg=("co2_impact_kg", "sum"))
            .round(2)
            .reset_index()
            .to_dict(orient="records")
        )

        return {
            "total_saved_co2_kg":       round(total_saved_kg, 2),
            "total_emitted_co2_kg":     round(total_emitted_kg, 2),
            "net_co2_kg":               net_co2_kg,
            "net_direction":            "NET SAVINGS" if net_co2_kg < 0 else "NET EMISSION",
            "trees_equivalent":         trees_saved_equivalent,
            "car_km_avoided":           int(car_km_avoided),
            "kwh_electricity_saved":    kwh_electricity_saved,
            "pathway_breakdown":        pathway_summary,
            "polymer_breakdown":        polymer_summary,
            "methodology_note": (
                "CO₂ factors sourced from IPCC 2006 Guidelines Vol. 5, "
                "US EPA AP-42, and CPCB India Plastic Waste Management Report 2019. "
                "Recycling and co-processing values represent avoided virgin-production emissions. "
                "Open burning factors include uncontrolled combustion of chlorinated compounds."
            ),
        }

    # ── Empty Result ──────────────────────────────────────────────────────────
    @staticmethod
    def _empty_result():
        return {
            "total_saved_co2_kg": 0.0, "total_emitted_co2_kg": 0.0,
            "net_co2_kg": 0.0, "net_direction": "N/A",
            "trees_equivalent": 0.0, "car_km_avoided": 0,
            "kwh_electricity_saved": 0.0,
            "pathway_breakdown": {}, "polymer_breakdown": [],
            "methodology_note": "No audit data.",
        }
