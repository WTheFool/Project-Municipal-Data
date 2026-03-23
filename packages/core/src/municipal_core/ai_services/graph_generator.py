from typing import Any, Dict

import pandas as pd

from municipal_core.ai_services.graph_packs import GraphPack, AskewGraphPack, MunicipalGraphPack

class GraphGenerator:
    """
    Generates graphs for single or multi-file datasets.
    Returns graphs as base64-encoded images for frontend embedding.
    """

    def __init__(self):
        self.packs: dict[str, GraphPack] = {
            MunicipalGraphPack.key: MunicipalGraphPack(),
            AskewGraphPack.key: AskewGraphPack(),
        }

    def generate(self, df: pd.DataFrame, compare_mode: bool = False, mode: str = "municipal") -> Dict[str, Any]:
        """
        Dispatcher: select a graph pack by mode and generate graphs.
        mode: "municipal" | "askew"
        """
        pack = self.packs.get(mode) or self.packs["municipal"]
        return pack.generate(df, compare_mode=compare_mode)