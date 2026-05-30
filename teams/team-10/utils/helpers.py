import os
import base64
from datetime import datetime

def format_metric(value: float, suffix: str = "kg") -> str:
    """Formats numeric weights into clean strings (e.g. 1,240 kg or 1.24 tonnes)"""
    if value >= 1000:
        return f"{value / 1000:.2f} Metric Tonnes (MT)"
    return f"{value:,.1f} {suffix}"

def calculate_co2_offset(weight_kg: float, polymer_type_ric: int) -> float:
    """
    Calculates carbon offset metrics of diverting plastic from landfill/burning.
    Approximations are based on average carbon equivalents:
    - ~1 kg plastic diverted from landfill/burned saves ~2.5 kg CO2e.
    """
    co2_factor = 2.52
    if polymer_type_ric == 1: # PET
        co2_factor = 2.15
    elif polymer_type_ric == 6: # Polystyrene (higher lifecycle impact)
        co2_factor = 3.20
    return weight_kg * co2_factor

def get_base64_image(image_path: str) -> str:
    """Encodes standard images into base64 string for embedding inside HTML components or PDF links."""
    if not os.path.exists(image_path):
        return ""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

def generate_report_filename(institution_name: str, format_ext: str = "docx") -> str:
    """Creates a unique timestamped report name for exports."""
    clean_name = "".join([c if c.isalnum() else "_" for c in institution_name]).strip("_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"PlasticWise_Audit_{clean_name}_{timestamp}.{format_ext}"
