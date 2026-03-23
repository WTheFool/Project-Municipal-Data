from typing import Dict, Any

class ReportGenerator:
    """
    Generates a textual report from profiles, statistics, and ML results.
    """

    def generate(self, profile: Dict[str, Any], stats: Dict[str, Any], ml_results: Dict[str, Any]) -> str:
        report_lines = []

        # Profile summary
        report_lines.append("=== Dataset Profile ===")
        for col, summary in profile.items():
            report_lines.append(f"{col}: {summary}")

        # Stats summary
        report_lines.append("\n=== Statistics ===")
        for stat_name, stat_val in stats.items():
            report_lines.append(f"{stat_name}: {stat_val}")

        # ML summary
        report_lines.append("\n=== ML Results ===")
        if 'cluster_labels' in ml_results:
            counts = ml_results['cluster_labels'].value_counts().to_dict()
            report_lines.append(f"Cluster distribution: {counts}")
        if 'anomaly_flags' in ml_results:
            counts = ml_results['anomaly_flags'].value_counts().to_dict()
            report_lines.append(f"Anomalies: {counts}")

        return "\n".join(report_lines)