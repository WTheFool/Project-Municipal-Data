class DatasetProfiler:

    def profile(self, df):

        return {
            "rows": len(df),
            "columns": list(df.columns),
            "missing": df.isnull().sum().to_dict()
        }