import pandas as pd
from typing import List, Dict
from municipal_core.standardize.typing_engine import VariableType

# Simulated AI model for demo purposes
AI_COLUMN_TYPE_MAP = {
    "area": "AREA",
    "water": "RESOURCE",
    "volume": "RESOURCE",
    "payment": "ECONOMIC",
    "price": "ECONOMIC",
    "crop": "CATEGORICAL",
    "community": "CATEGORICAL",
    "pump": "CATEGORICAL",
    "date": "TEMPORAL",
    "time": "TEMPORAL"
}

import random

def map_columns_ai(dfs: List[pd.DataFrame]) -> (List[pd.DataFrame], List[Dict]):
    """
    Simulate AI-based column typing across multiple DataFrames with confidence scores.
    Returns:
      - typed DataFrames (columns renamed to standard names if mapping exists)
      - list of column mappings with confidence per file
    """
    typed_dfs = []
    column_confidence_list = []

    for df in dfs:
        col_mapping = []
        df_copy = df.copy()
        for col in df.columns:
            lower_col = col.lower()
            # Find best match in AI_COLUMN_TYPE_MAP
            matched_type = "OTHER"
            for keyword, vtype in AI_COLUMN_TYPE_MAP.items():
                if keyword in lower_col:
                    matched_type = vtype
                    break
            confidence = round(random.uniform(0.8, 1.0) if matched_type != "OTHER" else random.uniform(0.4, 0.7), 2)
            mapped_name = matched_type.lower() if matched_type != "OTHER" else col
            col_mapping.append({
                "original_name": col,
                "mapped_name": mapped_name,
                "type": matched_type,
                "confidence": confidence
            })
            # Optionally rename columns to standardized mapped_name
            df_copy.rename(columns={col: mapped_name}, inplace=True)
        typed_dfs.append(df_copy)
        column_confidence_list.append(col_mapping)

    return typed_dfs, column_confidence_list