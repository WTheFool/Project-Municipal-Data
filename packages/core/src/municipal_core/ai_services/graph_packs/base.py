from __future__ import annotations

from typing import Any, Dict
import io
import base64

import pandas as pd


class GraphPack:
    key: str
    label: str

    def generate(self, df: pd.DataFrame, compare_mode: bool = False) -> Dict[str, Any]:
        raise NotImplementedError()


def find_col(df: pd.DataFrame, substrs: list[str]) -> str | None:
    for c in df.columns:
        cl = str(c).lower()
        for s in substrs:
            if s in cl:
                return str(c)
    return None


def num(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce")


def safe_value_counts(df: pd.DataFrame, col: str, n: int = 20) -> pd.Series:
    try:
        return df[col].astype(str).value_counts(dropna=True).head(n)
    except Exception:
        return pd.Series(dtype="int64")


def fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    b = buf.getvalue()
    buf.close()
    return base64.b64encode(b).decode("utf-8")

