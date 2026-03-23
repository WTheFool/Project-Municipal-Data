from municipal_core.ingest.excel_reader import ExcelReader
from municipal_core.standardize.column_map import ColumnMapper
from municipal_core.standardize.typing_engine import TypingEngine
from municipal_core.profile.dataset_profile import DatasetProfiler
from municipal_core.analytics.indicator_engine import IndicatorEngine
from municipal_core.analytics.stats_engine import StatsEngine
from municipal_core.analytics.ml_engine import MLEngine
from municipal_core.ai_services.graph_generator import GraphGenerator
from municipal_core.ai_services.report_generator import ReportGenerator
from municipal_core.exports.excel_exporter import ExcelExporter
from municipal_core.exports.word_exporter import WordExporter

from typing import List, Dict

class UploadHandler:
    """
    Handles the full workflow for uploaded Excel files
    """

    def __init__(self):
        self.reader = ExcelReader()
        self.column_mapper = ColumnMapper()
        self.typing_engine = TypingEngine()
        self.profiler = DatasetProfiler()
        self.indicator_engine = IndicatorEngine()
        self.stats_engine = StatsEngine()
        self.ml_engine = MLEngine()
        self.graph_generator = GraphGenerator()
        self.report_generator = ReportGenerator()
        self.excel_exporter = ExcelExporter()
        self.word_exporter = WordExporter()

    def process_files(self, file_paths: List[str], comparison_mode: bool = False) -> Dict:
        """
        Process 1 or multiple Excel files and return structured results
        """
        # --- 1. Read Excels ---
        dfs = self.reader.read_multiple(file_paths)

        # --- 2. Column mapping & typing ---
        mapped_dfs = []
        for df in dfs:
            df = self.column_mapper.map_columns(df)
            df = self.typing_engine.apply_typing(df)
            mapped_dfs.append(df)

        # --- 3. Profile datasets ---
        profiles = [self.profiler.profile(df) for df in mapped_dfs]

        # --- 4. Indicator generation ---
        indicators = [self.indicator_engine.generate(df) for df in mapped_dfs]

        # --- 5. Statistical analysis ---
        stats = [self.stats_engine.analyze(df) for df in mapped_dfs]

        # --- 6. ML pattern detection ---
        numeric_cols = [col for col in dfs[0].columns if df[col].dtype in ["int64","float64"]]
        ml_results = [self.ml_engine.detect_patterns(df, numeric_cols) for df in mapped_dfs]

        # --- 7. Graph generation ---
        graphs = [self.graph_generator.generate(df, indicators[i], stats[i], ml_results[i])
                  for i, df in enumerate(mapped_dfs)]

        # --- 8. Export results ---
        excel_paths = [self.excel_exporter.export(df, indicators[i], stats[i], ml_results[i])
                       for i, df in enumerate(mapped_dfs)]
        word_paths = [self.word_exporter.export(df, indicators[i], stats[i], ml_results[i])
                      for i, df in enumerate(mapped_dfs)]

        # --- 9. Combine results ---
        combined_results = {
            "profiles": profiles,
            "indicators": indicators,
            "statistics": stats,
            "ml_patterns": ml_results,
            "graphs": graphs,
            "excel_exports": excel_paths,
            "word_exports": word_paths,
            "comparison_mode": comparison_mode
        }

        return combined_results