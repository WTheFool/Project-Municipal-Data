from __future__ import annotations

from typing import Any, Dict
import matplotlib.pyplot as plt
import pandas as pd

from .base import GraphPack, fig_to_base64, num
from .municipal_columns import detect_municipal_columns


class MunicipalMoneyPack(GraphPack):
    key = "municipal_money"
    label = "Municipal: payments"

    def generate(self, df: pd.DataFrame, compare_mode: bool = False) -> Dict[str, Any]:
        cols = detect_municipal_columns(df)
        payment_col = cols["payment_col"]
        area_col = cols["area_col"]

        graphs: Dict[str, str] = {}
        if payment_col and area_col:
            try:
                p = num(df, payment_col)
                a = num(df, area_col).replace(0, pd.NA)
                df2 = df.assign(__ppa=(p / a))
                fig, ax = plt.subplots(figsize=(7, 4))
                ax.hist(df2["__ppa"].dropna(), bins=25)
                ax.set_title(f"Distribution: {payment_col} per {area_col}")
                ax.set_xlabel(f"{payment_col}/{area_col}")
                ax.set_ylabel("Count")
                fig.tight_layout()
                graphs["payment_per_area_distribution"] = fig_to_base64(fig)
                plt.close(fig)
            except Exception:
                pass
        return graphs

