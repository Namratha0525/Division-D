# Global Constants for PlasticWise AI

# Resin Identification Codes (RIC) and Polymer Mapping
POLYMER_TYPES = {
    1: "PET (Polyethylene Terephthalate)",
    2: "HDPE (High-Density Polyethylene)",
    3: "PVC (Polyvinyl Chloride)",
    4: "LDPE (Low-Density Polyethylene)",
    5: "PP (Polypropylene)",
    6: "PS (Polystyrene)",
    7: "Other (includes Multi-Layered, Polycarbonate, Acrylic, Nylon, etc.)"
}

# EPR Categories under CPCB Guidelines
EPR_CATEGORIES = {
    "Category I": "Rigid Plastic Packaging",
    "Category II": "Flexible Plastic Packaging (Single layer or multilayer with different types of plastic)",
    "Category III": "Multilayered Plastic Packaging (At least one layer of plastic and at least one layer of other material)",
    "Category IV": "Compostable Plastic Packaging/Carry Bags"
}

# Regulatory Thresholds (PWM Rules 2016 and subsequent updates)
MICRON_LIMIT = 120 # Minimum thickness in microns for carry bags and packaging
BULK_GENERATOR_LIMIT_KG = 100.0 # Limit in kg/day defining a bulk waste generator

# Disposal Pathway Classifications
DISPOSAL_CHANNELS = {
    "RECYCLED": "Recycling / Co-processing",
    "CO_PROCESSED": "Cement Kiln Co-processing",
    "LANDFILLED": "Municipal Landfill",
    "INCINERATED": "Waste-to-Energy Incineration",
    "OPEN_BURNT": "Illegal Open Burning" # Automatically marks compliance breach
}

# Aesthetic Color Palette for Plotly and Streamlit Visualizations
COLOR_PALETTE = {
    "primary": "#1E4620",      # Deep Forest Green
    "secondary": "#5C8D89",    # Sage Green
    "accent": "#F4F7F6",       # Off-white / Muted background
    "highlight": "#D2E5D0",    # Mint Highlight
    "alert_red": "#B23B3B",    # Crimson Alert
    "alert_orange": "#D9822B", # Amber Warning
    "alert_green": "#2B8A3E"   # Forest Safe
}

# Scoring Weights for Sustainability Index
SCORING_WEIGHTS = {
    "recycling_rate": 0.40,
    "sup_proportion": 0.30,
    "compliance_status": 0.20,
    "audit_completeness": 0.10
}
