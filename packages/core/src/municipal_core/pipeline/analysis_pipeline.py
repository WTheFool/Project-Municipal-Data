from typing import List, Dict, Any
import pandas as pd

from municipal_core.ingest.excel_reader import ExcelReader
from municipal_core.standardize.typing_engine import TypingEngine
from municipal_core.standardize.column_map import ColumnMapper
from municipal_core.profile.dataset_profile import DatasetProfiler
from municipal_core.analytics.indicator_engine import IndicatorEngine
from municipal_core.analytics.stats_engine import StatsEngine
from municipal_core.analytics.ml_engine import MLEngine
from municipal_core.ai_services.graph_generator import GraphGenerator
from municipal_core.ai_services.report_generator import ReportGenerator
from municipal_core.exports.excel_exporter import ExcelExporter
from municipal_core.exports.word_exporter import WordExporter


class AnalysisPipeline:

    def __init__(self):
        self.reader = ExcelReader()
        self.typing_engine = TypingEngine()
        self.column_mapper = ColumnMapper()
        self.profiler = DatasetProfiler()
        self.indicator_engine = IndicatorEngine()
        self.stats_engine = StatsEngine()
        self.ml_engine = MLEngine()
        self.graph_generator = GraphGenerator()
        self.report_generator = ReportGenerator()
        self.excel_exporter = ExcelExporter()
        self.word_exporter = WordExporter()

    def run(self, files: List[str], compare_mode: bool = False) -> Dict[str, Any]:
        """
        Run full pipeline for single or multiple Excel files.
        compare_mode: If True, merges multiple files, tracks source_file, and computes difference indicators.
        """
        dfs = []
        for idx, file in enumerate(files):
            df = self.reader.read(file)
            df["source_file"] = f"Dataset_{idx+1}"  # Track source for graphs
            dfs.append(df)

        if not compare_mode or len(dfs) == 1:
            return self._process_single(dfs[0])

        return self._process_comparison(dfs)

    # --------------------- Internal Methods ---------------------

    def _process_single(self, df: pd.DataFrame) -> Dict[str, Any]:
        df_std = self._standardize(df)
        profile = self._profile(df_std)
        df_features, indicators = self._compute_indicators(df_std)
        stats = self._compute_stats(df_features)
        ml_results = self._run_ml(df_features)
        graphs = self._generate_graphs(df_features)
        report = self._generate_report(profile, stats, ml_results)
        exports = self._export(df_features, stats, indicators, graphs, report)
        return {
            "profile": profile,
            "stats": stats,
            "ml_results": ml_results,
            "graphs": graphs,
            "report": report,
            **exports
        }

    def _process_comparison(self, dfs: List[pd.DataFrame]) -> Dict[str, Any]:
        """
        Merge multiple DataFrames on common columns and compute comparison features.
        Adds difference indicators for numeric columns.
        """
        # Standardize each dataframe individually
        dfs_std = [self._standardize(df) for df in dfs]

        # Find common columns
        common_cols = list(set.intersection(*(set(df.columns) for df in dfs_std)))
        if not common_cols:
            raise ValueError("No common columns found for comparison.")

        # Merge by concatenation
        df_merged = pd.concat([df[common_cols] for df in dfs_std], ignore_index=True)

        # Compute indicators for each row
        df_features, indicators = self._compute_indicators(df_merged)

        # Compute difference indicators (pairwise) for numeric columns
        numeric_cols = df_features.select_dtypes(include="number").columns.tolist()
        for col in numeric_cols:
            if "source_file" in col:
                continue  # Skip non-data columns
            col_diff_name = f"{col}_delta"
            try:
                # Compute difference between datasets if at least 2 datasets
                values_per_dataset = [df[df["source_file"] == f"Dataset_{i+1}"][col].reset_index(drop=True)
                                      for i in range(len(dfs_std))]
                # Only for first two datasets for delta
                if len(values_per_dataset) >= 2:
                    df_features[col_diff_name] = values_per_dataset[0] - values_per_dataset[1]
            except Exception:
                continue  # Ignore if shapes mismatch

        profile = self._profile(df_features)
        stats = self._compute_stats(df_features)
        ml_results = self._run_ml(df_features)
        graphs = self._generate_graphs(df_features, compare_mode=True)
        report = self._generate_report(profile, stats, ml_results)
        exports = self._export(df_features, stats, indicators, graphs, report)

        return {
            "profile": profile,
            "stats": stats,
            "ml_results": ml_results,
            "graphs": graphs,
            "report": report,
            "compare_mode": True,
            "file_count": len(dfs),
            **exports
        }

    # --------------------- Helper Methods ---------------------

    def _standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        typing_result = self.typing_engine.detect(df)
        return self.column_mapper.apply(df, typing_result)

    def _profile(self, df: pd.DataFrame):
        return self.profiler.profile(df)

    def _compute_indicators(self, df: pd.DataFrame):
        indicators = self.indicator_engine.compute(df)
        df_features = pd.concat([df, indicators], axis=1)
        return df_features, indicators

    def _compute_stats(self, df: pd.DataFrame):
        return self.stats_engine.compute(df)

    def _run_ml(self, df: pd.DataFrame):
        return self.ml_engine.analyze(df)

    def _generate_graphs(self, df: pd.DataFrame, compare_mode: bool = False):
        return self.graph_generator.generate(df, compare_mode=compare_mode)

    def _generate_report(self, profile, stats, ml_results):
        return self.report_generator.generate(
            profile=profile,
            stats=stats,
            ml_results=ml_results
        )

    def _export(self, df, stats, indicators, graphs, report):
        excel_file = self.excel_exporter.export(
            dataframe=df,
            stats=stats,
            indicators=indicators,
            graphs=graphs
        )
        word_file = self.word_exporter.export(
            report=report,
            graphs=graphs,
            stats=stats
        )
        return {
            "excel_export": excel_file,
            "word_export": word_file
        }