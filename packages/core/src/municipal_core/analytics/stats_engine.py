import pandas as pd
from typing import List, Dict


class StatsEngine:
    """
    Computes descriptive statistics for numeric columns or indicators.
    """
    def __init__(self, numeric_columns: List[str] = None):
        self.numeric_columns = numeric_columns or []

    def compute(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """
        Returns a dict with column -> stats dict
        Example:
        {
            "water_intensity": {"mean": 10.5, "std": 2.3, "min": 5, "max": 15},
            "revenue_per_area": {"mean": 100, "std": 25, "min": 50, "max": 150}
        }
        """
        stats = {}
        cols = self.numeric_columns or df.select_dtypes(include="number").columns.tolist()
        for col in cols:
            s = df[col]
            stats[col] = {
                "mean": float(s.mean()),
                "std": float(s.std()),
                "min": float(s.min()),
                "max": float(s.max())
            }
        return stats