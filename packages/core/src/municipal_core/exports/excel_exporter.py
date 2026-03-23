import pandas as pd
from typing import Dict, Any
import tempfile
import os

class ExcelExporter:
    """
    Exports a dataframe + stats + indicators to Excel
    Returns the temporary file path.
    """

    def export(self, dataframe: pd.DataFrame, stats: Dict[str, Any], indicators: pd.DataFrame, ml_results: Dict[str, Any]) -> str:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        with pd.ExcelWriter(temp_file.name, engine='xlsxwriter') as writer:
            dataframe.to_excel(writer, sheet_name='Data', index=False)
            indicators.to_excel(writer, sheet_name='Indicators', index=False)

            # Stats sheet
            stats_df = pd.DataFrame.from_dict(stats, orient='index', columns=['Value'])
            stats_df.to_excel(writer, sheet_name='Statistics')

            # ML sheet
            ml_df = pd.DataFrame({k: v for k, v in ml_results.items()})
            ml_df.to_excel(writer, sheet_name='ML')

        return temp_file.name