from __future__ import annotations

from typing import Any, Dict
import matplotlib.pyplot as plt
import pandas as pd

from .base import GraphPack, fig_to_base64, safe_value_counts
from .municipal_columns import detect_municipal_columns


class MunicipalCountsPack(GraphPack):
    key = "municipal_counts"
    label = "Municipal: counts"

    def generate(self, df: pd.DataFrame, compare_mode: bool = False) -> Dict[str, Any]:
        cols = detect_municipal_columns(df)
        crop_col = cols["crop_col"]
        region_col = cols["region_col"]
        pump_col = cols["pump_col"]

        graphs: Dict[str, str] = {}

        if crop_col:
            try:
                by = safe_value_counts(df, crop_col, n=20)
                if not by.empty:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    by.plot(kind="bar", ax=ax)
                    ax.set_title(f"Record count by {crop_col}")
                    ax.set_xlabel(crop_col)
                    ax.set_ylabel("Count")
                    fig.tight_layout()
                    graphs["count_by_crop"] = fig_to_base64(fig)
                    plt.close(fig)
            except Exception:
                pass

        if region_col:
            try:
                by = safe_value_counts(df, region_col, n=20)
                if not by.empty:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    by.plot(kind="bar", ax=ax)
                    ax.set_title(f"Record count by {region_col}")
                    ax.set_xlabel(region_col)
                    ax.set_ylabel("Count")
                    fig.tight_layout()
                    graphs["count_by_region"] = fig_to_base64(fig)
                    plt.close(fig)
            except Exception:
                pass

        if pump_col:
            try:
                by = safe_value_counts(df, pump_col, n=20)
                if not by.empty:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    by.plot(kind="bar", ax=ax)
                    ax.set_title(f"Record count by {pump_col}")
                    ax.set_xlabel(pump_col)
                    ax.set_ylabel("Count")
                    fig.tight_layout()
                    graphs["count_by_pump"] = fig_to_base64(fig)
                    plt.close(fig)
            except Exception:
                pass

        return graphs

