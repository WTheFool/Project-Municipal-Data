from __future__ import annotations

from typing import Any, Dict
import matplotlib.pyplot as plt
import pandas as pd

from .base import GraphPack, fig_to_base64, num
from .municipal_columns import detect_municipal_columns


class MunicipalTotalsPack(GraphPack):
    key = "municipal_totals"
    label = "Municipal: totals"

    def generate(self, df: pd.DataFrame, compare_mode: bool = False) -> Dict[str, Any]:
        cols = detect_municipal_columns(df)
        crop_col = cols["crop_col"]
        area_col = cols["area_col"]
        water_col = cols["water_col"]
        region_col = cols["region_col"]
        pump_col = cols["pump_col"]

        graphs: Dict[str, str] = {}

        if region_col and area_col:
            try:
                a = num(df, area_col)
                by = df.assign(__a=a).groupby(region_col)["__a"].sum(min_count=1).sort_values(ascending=False).head(20)
                if not by.empty:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    by.plot(kind="bar", ax=ax)
                    ax.set_title(f"Total {area_col} by {region_col}")
                    ax.set_xlabel(region_col)
                    ax.set_ylabel(f"Total {area_col}")
                    fig.tight_layout()
                    graphs["total_area_by_region"] = fig_to_base64(fig)
                    plt.close(fig)
            except Exception:
                pass

        if crop_col and area_col:
            try:
                a = num(df, area_col)
                by = df.assign(__a=a).groupby(crop_col)["__a"].sum(min_count=1).sort_values(ascending=False).head(20)
                if not by.empty:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    by.plot(kind="bar", ax=ax)
                    ax.set_title(f"Total {area_col} by {crop_col}")
                    ax.set_xlabel(crop_col)
                    ax.set_ylabel(f"Total {area_col}")
                    fig.tight_layout()
                    graphs["total_area_by_crop"] = fig_to_base64(fig)
                    plt.close(fig)
            except Exception:
                pass

        if region_col and water_col:
            try:
                w = num(df, water_col)
                by = df.assign(__w=w).groupby(region_col)["__w"].sum(min_count=1).sort_values(ascending=False).head(20)
                if not by.empty:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    by.plot(kind="bar", ax=ax)
                    ax.set_title(f"Total {water_col} by {region_col}")
                    ax.set_xlabel(region_col)
                    ax.set_ylabel(f"Total {water_col}")
                    fig.tight_layout()
                    graphs["total_water_by_region"] = fig_to_base64(fig)
                    plt.close(fig)
            except Exception:
                pass

        if crop_col and water_col:
            try:
                w = num(df, water_col)
                by = df.assign(__w=w).groupby(crop_col)["__w"].sum(min_count=1).sort_values(ascending=False).head(20)
                if not by.empty:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    by.plot(kind="bar", ax=ax)
                    ax.set_title(f"Total {water_col} by {crop_col}")
                    ax.set_xlabel(crop_col)
                    ax.set_ylabel(f"Total {water_col}")
                    fig.tight_layout()
                    graphs["total_water_by_crop"] = fig_to_base64(fig)
                    plt.close(fig)
            except Exception:
                pass

        if pump_col and water_col:
            try:
                w = num(df, water_col)
                by = df.assign(__w=w).groupby(pump_col)["__w"].sum(min_count=1).sort_values(ascending=False).head(20)
                if not by.empty:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    by.plot(kind="bar", ax=ax)
                    ax.set_title(f"Total {water_col} by {pump_col}")
                    ax.set_xlabel(pump_col)
                    ax.set_ylabel(f"Total {water_col}")
                    fig.tight_layout()
                    graphs["total_water_by_pump"] = fig_to_base64(fig)
                    plt.close(fig)
            except Exception:
                pass

        return graphs

