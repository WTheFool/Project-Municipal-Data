import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from typing import List, Dict

class MLEngine:
    """
    Performs ML-based pattern detection:
    - Clustering (KMeans)
    - Anomaly detection (IsolationForest)
    """

    def __init__(self, n_clusters: int = 3, contamination: float = 0.05):
        self.n_clusters = n_clusters
        self.contamination = contamination
        self.scaler = StandardScaler()
        self.kmeans_model = None
        self.iforest_model = None

    def detect_patterns(self, df: pd.DataFrame, numeric_columns: List[str]) -> Dict[str, pd.Series]:
        """
        Input: DataFrame and numeric columns to analyze
        Output: dict with clustering labels and anomaly flags
        """
        data = df[numeric_columns].fillna(0)

        # Standardize numeric data
        X_scaled = self.scaler.fit_transform(data)

        # --- KMeans clustering ---
        self.kmeans_model = KMeans(n_clusters=self.n_clusters, random_state=42)
        cluster_labels = self.kmeans_model.fit_predict(X_scaled)
        cluster_series = pd.Series(cluster_labels, index=df.index, name="cluster_label")

        # --- IsolationForest anomaly detection ---
        self.iforest_model = IsolationForest(contamination=self.contamination, random_state=42)
        anomaly_flags = self.iforest_model.fit_predict(X_scaled)
        # IsolationForest: -1 = anomaly, 1 = normal
        anomaly_series = pd.Series(anomaly_flags, index=df.index, name="anomaly_flag")

        return {
            "cluster_labels": cluster_series,
            "anomaly_flags": anomaly_series
        }