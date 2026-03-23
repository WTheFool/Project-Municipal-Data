import pandas as pd
from pathlib import Path
from io import BytesIO


class ExcelReader:

    def read(self, source, filename: str | None = None) -> pd.DataFrame:
        """
        Reads tabular data from:
        - file path
        - uploaded buffer (BytesIO)

        Supports:
        - Excel (.xls, .xlsx)
        - CSV (.csv)
        """

        # Case 1: reading from uploaded buffer
        if isinstance(source, BytesIO):

            if filename and filename.endswith(".csv"):
                return pd.read_csv(source)

            return pd.read_excel(source)

        # Case 2: reading from file path
        if isinstance(source, str) or isinstance(source, Path):

            path = Path(source)

            if not path.exists():
                raise FileNotFoundError(f"File not found: {source}")

            if path.suffix == ".csv":
                return pd.read_csv(path)

            if path.suffix in [".xls", ".xlsx"]:
                return pd.read_excel(path)

            raise ValueError(f"Unsupported file type: {path.suffix}")

        raise ValueError("Unsupported input type for ExcelReader")

    def read_multiple(self, sources: list, filenames: list | None = None):

        dfs = []

        for i, src in enumerate(sources):

            filename = None
            if filenames:
                filename = filenames[i]

            dfs.append(self.read(src, filename))

        return dfs