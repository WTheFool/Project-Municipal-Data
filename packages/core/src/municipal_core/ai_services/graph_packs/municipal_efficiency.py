from __future__ import annotations

from typing import Any, Dict
import matplotlib.pyplot as plt
import pandas as pd

from .base import GraphPack, fig_to_base64, num
from .municipal_columns import detect_municipal_columns


class MunicipalEfficiencyPack(GraphPack):
    key = "municipal_efficiency"
    label = "Municipal: efficiency & outliers"

    def generate(self, df: pd.DataFrame, compare_mode: bool = False) -> Dict[str, Any]:
        cols = detect_municipal_columns(df)
        crop_col = cols["crop_col"]
        area_col = cols["area_col"]
        water_col = cols["water_col"]
        region_col = cols["region_col"]

        graphs: Dict[str, str] = {}

        if crop_col and water_col and area_col:
            try:
                w = num(df, water_col)
                a = num(df, area_col).replace(0, pd.NA)
                df2 = df.assign(__wpa=(w / a))
                by = df2.groupby(crop_col)["__wpa"].mean().sort_values(ascending=False).head(20)
                if not by.empty:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    by.plot(kind="bar", ax=ax)
                    ax.set_title(f"Average water per area by {crop_col}")
                    ax.set_xlabel(crop_col)
                    ax.set_ylabel(f"{water_col} / {area_col} (avg)")
                    fig.tight_layout()
                    graphs["avg_water_per_area_by_crop"] = fig_to_base64(fig)
                    plt.close(fig)
            except Exception:
                pass

        if region_col and water_col and area_col:
            try:
                w = num(df, water_col)
                a = num(df, area_col).replace(0, pd.NA)
                df2 = df.assign(__wpa=(w / a))
                by = df2.groupby(region_col)["__wpa"].mean().sort_values(ascending=False).head(20)
                if not by.empty:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    by.plot(kind="bar", ax=ax)
                    ax.set_title(f"Average water per area by {region_col}")
                    ax.set_xlabel(region_col)
                    ax.set_ylabel(f"{water_col} / {area_col} (avg)")
                    fig.tight_layout()
                    graphs["avg_water_per_area_by_region"] = fig_to_base64(fig)
                    plt.close(fig)
            except Exception:
                pass

        if water_col and area_col:
            try:
                w = num(df, water_col)
                a = num(df, area_col).replace(0, pd.NA)
                wpa = (w / a).dropna()
                if not wpa.empty:
                    fig, ax = plt.subplots(figsize=(7, 4))
                    ax.hist(wpa, bins=30)
                    ax.set_title(f"Distribution: {water_col} per {area_col}")
                    ax.set_xlabel(f"{water_col}/{area_col}")
                    ax.set_ylabel("Count")
                    fig.tight_layout()
                    graphs["dist_water_per_area"] = fig_to_base64(fig)
                    plt.close(fig)

                    fig, ax = plt.subplots(figsize=(6, 2.8))
                    ax.boxplot(wpa, vert=False, showfliers=True)
                    ax.set_title(f"Outliers: {water_col} per {area_col}")
                    ax.set_xlabel(f"{water_col}/{area_col}")
                    fig.tight_layout()
                    graphs["box_water_per_area"] = fig_to_base64(fig)
                    plt.close(fig)
            except Exception:
                pass

            try:
                w = num(df, water_col)
                a = num(df, area_col)
                work = df.assign(__w=w, __a=a).dropna(subset=["__w", "__a"])
                if len(work) >= 20:
                    fig, ax = plt.subplots(figsize=(6.5, 4))
                    ax.scatter(work["__a"], work["__w"], s=12, alpha=0.5)
                    ax.set_title(f"{water_col} vs {area_col}")
                    ax.set_xlabel(area_col)
                    ax.set_ylabel(water_col)
                    fig.tight_layout()
                    graphs["scatter_water_vs_area"] = fig_to_base64(fig)
                    plt.close(fig)
            except Exception:
                pass

        return graphs

