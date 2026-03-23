from __future__ import annotations

from typing import Any, Dict
import matplotlib.pyplot as plt
import pandas as pd

from .base import GraphPack, fig_to_base64


class MunicipalFallbackPack(GraphPack):
    key = "municipal_fallback"
    label = "Municipal: fallback"

    def generate(self, df: pd.DataFrame, compare_mode: bool = False) -> Dict[str, Any]:
        graphs: Dict[str, str] = {}

        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        numeric_cols = [c for c in numeric_cols if not str(c).startswith("__")]
        if not numeric_cols:
            return graphs

        if not compare_mode:
            for col in numeric_cols[:8]:
                try:
                    s = pd.to_numeric(df[col], errors="coerce").dropna()
                    if s.empty:
                        continue
                    fig, ax = plt.subplots(figsize=(7, 4))
                    ax.hist(s, bins=25)
                    ax.set_title(f"{col} (mean={s.mean():.2f})")
                    ax.set_xlabel(col)
                    ax.set_ylabel("Count")
                    fig.tight_layout()
                    graphs[f"dist_{col}"] = fig_to_base64(fig)
                    plt.close(fig)
                except Exception:
                    continue
            return graphs

        # Compare: mean by dataset
        work = df
        if "source_file" not in work.columns:
            work = work.copy()
            work["source_file"] = "Dataset"

        for col in numeric_cols[:8]:
            try:
                s = pd.to_numeric(work[col], errors="coerce")
                by = work.assign(__v=s).groupby("source_file")["__v"].mean().sort_index()
                fig, ax = plt.subplots(figsize=(7, 4))
                by.plot(kind="bar", ax=ax)
                ax.set_title(f"Average {col} by dataset")
                ax.set_xlabel("Dataset")
                ax.set_ylabel(f"Average {col}")
                fig.tight_layout()
                graphs[f"avg_{col}_by_dataset"] = fig_to_base64(fig)
                plt.close(fig)
            except Exception:
                continue

        return graphs

