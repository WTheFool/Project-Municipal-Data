from __future__ import annotations

from typing import Any, Dict
import matplotlib.pyplot as plt
import pandas as pd

from .base import GraphPack, fig_to_base64


class MunicipalCorrelationPack(GraphPack):
    key = "municipal_correlation"
    label = "Municipal: correlations"

    def generate(self, df: pd.DataFrame, compare_mode: bool = False) -> Dict[str, Any]:
        graphs: Dict[str, str] = {}
        try:
            numeric_cols = df.select_dtypes(include="number").columns.tolist()
            numeric_cols = [c for c in numeric_cols if not str(c).startswith("__")]
            if len(numeric_cols) >= 3:
                corr = df[numeric_cols].corr(numeric_only=True).fillna(0)
                fig, ax = plt.subplots(figsize=(7, 6))
                im = ax.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1)
                ax.set_xticks(range(len(numeric_cols)))
                ax.set_yticks(range(len(numeric_cols)))
                ax.set_xticklabels([str(c)[:12] for c in numeric_cols], rotation=45, ha="right", fontsize=8)
                ax.set_yticklabels([str(c)[:12] for c in numeric_cols], fontsize=8)
                fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
                ax.set_title("Correlation heatmap (numeric fields)")
                fig.tight_layout()
                graphs["corr_heatmap_numeric"] = fig_to_base64(fig)
                plt.close(fig)
        except Exception:
            pass
        return graphs

