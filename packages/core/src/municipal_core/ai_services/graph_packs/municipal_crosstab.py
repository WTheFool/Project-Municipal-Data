from __future__ import annotations

from typing import Any, Dict
import matplotlib.pyplot as plt
import pandas as pd

from .base import GraphPack, fig_to_base64, num
from .municipal_columns import detect_municipal_columns


class MunicipalCrosstabPack(GraphPack):
    key = "municipal_crosstab"
    label = "Municipal: crosstab"

    def generate(self, df: pd.DataFrame, compare_mode: bool = False) -> Dict[str, Any]:
        cols = detect_municipal_columns(df)
        region_col = cols["region_col"]
        crop_col = cols["crop_col"]
        area_col = cols["area_col"]

        graphs: Dict[str, str] = {}

        if region_col and crop_col and area_col:
            try:
                s = num(df, area_col)
                df2 = df.assign(__area=s)
                pivot = (
                    df2.pivot_table(index=region_col, columns=crop_col, values="__area", aggfunc="sum", observed=False)
                    .fillna(0)
                )
                top_regions = pivot.sum(axis=1).sort_values(ascending=False).head(10).index
                pivot = pivot.loc[top_regions]
                top_crops = pivot.sum(axis=0).sort_values(ascending=False).head(6).index
                pivot = pivot[top_crops]

                fig, ax = plt.subplots(figsize=(9, 5))
                pivot.plot(kind="bar", stacked=True, ax=ax)
                ax.set_title(f"Total {area_col} by {region_col} (stacked by {crop_col})")
                ax.set_xlabel(region_col)
                ax.set_ylabel(f"Total {area_col}")
                ax.legend(title=crop_col, fontsize=8)
                fig.tight_layout()
                graphs["total_area_region_crop_stacked"] = fig_to_base64(fig)
                plt.close(fig)
            except Exception:
                pass

        return graphs

