from __future__ import annotations

from typing import Any, Dict
import matplotlib.pyplot as plt
import pandas as pd

from .base import GraphPack, fig_to_base64
from .municipal_columns import detect_municipal_columns


class MunicipalSpatialPack(GraphPack):
    key = "municipal_spatial"
    label = "Municipal: spatial"

    def generate(self, df: pd.DataFrame, compare_mode: bool = False) -> Dict[str, Any]:
        cols = detect_municipal_columns(df)
        lat_col = cols["lat_col"]
        lon_col = cols["lon_col"]
        water_col = cols["water_col"]

        graphs: Dict[str, str] = {}

        if lat_col and lon_col:
            try:
                lat = pd.to_numeric(df[lat_col], errors="coerce")
                lon = pd.to_numeric(df[lon_col], errors="coerce")
                work = df.assign(__lat=lat, __lon=lon).dropna(subset=["__lat", "__lon"])
                if len(work) >= 5:
                    fig, ax = plt.subplots(figsize=(7, 5))
                    if water_col:
                        w = pd.to_numeric(work[water_col], errors="coerce")
                        sc = ax.scatter(work["__lon"], work["__lat"], c=w, s=20, cmap="viridis", alpha=0.7)
                        cb = fig.colorbar(sc, ax=ax)
                        cb.set_label(water_col)
                    else:
                        ax.scatter(work["__lon"], work["__lat"], s=20, alpha=0.7)
                    ax.set_title("Pump locations (heat view)")
                    ax.set_xlabel(lon_col)
                    ax.set_ylabel(lat_col)
                    fig.tight_layout()
                    graphs["pump_location_heatmap"] = fig_to_base64(fig)
                    plt.close(fig)
            except Exception:
                pass

        return graphs

