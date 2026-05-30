import pandas as pd
from utils.constants import POLYMER_TYPES, DISPOSAL_CHANNELS

def validate_audit_row(row: dict) -> bool:
    """
    Validates a single waste audit record row.
    
    Args:
        row (dict): A dictionary representing a single record.
        
    Returns:
        bool: True if valid, raises ValueError or returns False if invalid.
    """
    # 1. Check weight is numeric and positive
    weight = row.get("weight_kg")
    if weight is None or not isinstance(weight, (int, float)) or weight <= 0:
        raise ValueError(f"Invalid weight_kg: {weight}. Weight must be a positive number.")
        
    # 2. Check polymer type code is standard (1-7)
    ric = row.get("resin_code")
    if ric not in POLYMER_TYPES.keys():
        raise ValueError(f"Invalid resin_code: {ric}. Must be between 1 and 7.")
        
    # 3. Check disposal method is mapped
    disposal = row.get("disposal_method")
    if disposal not in DISPOSAL_CHANNELS.keys():
        raise ValueError(f"Invalid disposal_method: {disposal}. Must be one of {list(DISPOSAL_CHANNELS.keys())}.")
        
    # 4. Check thickness if provided (must be positive)
    thickness = row.get("thickness_microns")
    if thickness is not None:
        if not isinstance(thickness, (int, float)) or thickness <= 0:
            raise ValueError(f"Invalid thickness_microns: {thickness}. Must be a positive number.")
            
    return True

def validate_csv_columns(df: pd.DataFrame) -> bool:
    """
    Asserts whether the uploaded CSV contains required header columns.
    
    Args:
        df (pd.DataFrame): Input dataframe.
        
    Returns:
        bool: True if valid, raises ValueError otherwise.
    """
    required_cols = ["date", "resin_code", "weight_kg", "disposal_method", "thickness_microns"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}. Required: {required_cols}")
    return True
