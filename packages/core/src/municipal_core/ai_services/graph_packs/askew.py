from __future__ import annotations

from typing import Any, Dict
import pandas as pd

from .base import GraphPack


class AskewGraphPack(GraphPack):
    key = "askew"
    label = "Askew data (placeholder)"

    def generate(self, df: pd.DataFrame, compare_mode: bool = False) -> Dict[str, Any]:
        return {}

