from __future__ import annotations

from typing import Any, Dict, Iterable
import pandas as pd

from .base import GraphPack
from .municipal_counts import MunicipalCountsPack
from .municipal_totals import MunicipalTotalsPack
from .municipal_efficiency import MunicipalEfficiencyPack
from .municipal_spatial import MunicipalSpatialPack
from .municipal_trends import MunicipalTrendsPack
from .municipal_correlation import MunicipalCorrelationPack
from .municipal_crosstab import MunicipalCrosstabPack
from .municipal_money import MunicipalMoneyPack
from .municipal_fallback import MunicipalFallbackPack


class MunicipalGraphPack(GraphPack):
    key = "municipal"
    label = "Municipal"

    def __init__(self):
        self.packs: list[GraphPack] = [
            MunicipalTotalsPack(),
            MunicipalCountsPack(),
            MunicipalEfficiencyPack(),
            MunicipalMoneyPack(),
            MunicipalCrosstabPack(),
            MunicipalTrendsPack(),
            MunicipalSpatialPack(),
            MunicipalCorrelationPack(),
            MunicipalFallbackPack(),
        ]

    def generate(self, df: pd.DataFrame, compare_mode: bool = False) -> Dict[str, Any]:
        graphs: Dict[str, Any] = {}
        for p in self.packs:
            try:
                g = p.generate(df, compare_mode=compare_mode)
                if isinstance(g, dict) and g:
                    # last-write wins if duplicates; keep keys stable
                    graphs.update(g)
            except Exception:
                continue
        return graphs

