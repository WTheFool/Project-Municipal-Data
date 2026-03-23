from __future__ import annotations

from typing import Any, Dict
import matplotlib.pyplot as plt
import pandas as pd

from .base import GraphPack, fig_to_base64
from .municipal_columns import detect_municipal_columns


class MunicipalTrendsPack(GraphPack):
    key = "municipal_trends"
    label = "Municipal: trends"

    def generate(self, df: pd.DataFrame, compare_mode: bool = False) -> Dict[str, Any]:
        cols = detect_municipal_columns(df)
        year_col = cols["year_col"]
        area_col = cols["area_col"]
        water_col = cols["water_col"]

        graphs: Dict[str, str] = {}
        if not year_col:
            return graphs

        try:
            y = pd.to_numeric(df[year_col], errors="coerce").astype("Int64")
            work = df.copy()
            work["__year"] = y
            work = work.dropna(subset=["__year"])
            if work.empty:
                return graphs

            if area_col:
                a = pd.to_numeric(work[area_col], errors="coerce")
                by = work.assign(__a=a).groupby("__year")["__a"].sum(min_count=1).sort_index()
                if len(by.index) >= 2:
                    fig, ax = plt.subplots(figsize=(7, 4))
                    ax.plot(by.index.astype(int).tolist(), by.values.tolist(), marker="o")
                    ax.set_title(f"Total {area_col} over time")
                    ax.set_xlabel("Year")
                    ax.set_ylabel(f"Total {area_col}")
                    fig.tight_layout()
                    graphs["trend_total_area"] = fig_to_base64(fig)
                    plt.close(fig)

            if water_col:
                w = pd.to_numeric(work[water_col], errors="coerce")
                by = work.assign(__w=w).groupby("__year")["__w"].sum(min_count=1).sort_index()
                if len(by.index) >= 2:
                    fig, ax = plt.subplots(figsize=(7, 4))
                    ax.plot(by.index.astype(int).tolist(), by.values.tolist(), marker="o")
                    ax.set_title(f"Total {water_col} over time")
                    ax.set_xlabel("Year")
                    ax.set_ylabel(f"Total {water_col}")
                    fig.tight_layout()
                    graphs["trend_total_water"] = fig_to_base64(fig)
                    plt.close(fig)
        except Exception:
            pass

        return graphs

