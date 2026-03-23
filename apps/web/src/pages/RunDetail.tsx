import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api, { API_BASE } from "../api/client";
import ChartView from "../components/report/ChartView";

interface RunResult {
  id: string;
  project_id: string;
  status: string;
  error: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  artifacts: { kind: string; storage_key: string; created_at: string }[];
}

const RunDetail: React.FC = () => {
  const { projectId, runId } = useParams<{ projectId: string; runId: string }>();
  const navigate = useNavigate();
  const [run, setRun] = useState<RunResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rerunLoading, setRerunLoading] = useState(false);
  const [graphs, setGraphs] = useState<any>(null);
  const [forecast, setForecast] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [graphTab, setGraphTab] = useState<string>("compare");

  useEffect(() => {
    const fetchRun = async () => {
      setLoading(true);
      try {
        const response = await api.get<RunResult>(`/api/runs/${runId}`);
        setRun(response.data);
      } catch (err: any) {
        console.error(err);
        setError("Failed to load run data.");
      } finally {
        setLoading(false);
      }
    };

    fetchRun();
  }, [projectId, runId]);

  useEffect(() => {
    if (!runId) return;
    let alive = true;
    const fetchArtifacts = async () => {
      try {
        const g = await api.get<any>(`/api/runs/${runId}/artifacts/graphs_json`);
        if (alive) setGraphs(g.data);
      } catch {
        if (alive) setGraphs(null);
      }
      try {
        const f = await api.get<any>(`/api/runs/${runId}/artifacts/forecast_json`);
        if (alive) setForecast(f.data);
      } catch {
        if (alive) setForecast(null);
      }
      try {
        const s = await api.get<any>(`/api/runs/${runId}/artifacts/summary_json`);
        if (alive) setSummary(s.data);
      } catch {
        if (alive) setSummary(null);
      }
    };

    fetchArtifacts();

    // Keep polling artifacts while the run is in progress (graphs often arrive near completion).
    const t = window.setInterval(fetchArtifacts, 1500);
    return () => {
      alive = false;
      window.clearInterval(t);
    };
  }, [runId]);

  useEffect(() => {
    if (!runId) return;
    if (!run) return;
    if (run.status === "completed" || run.status === "failed") return;
    const t = window.setInterval(async () => {
      try {
        const response = await api.get<RunResult>(`/api/runs/${runId}`);
        setRun(response.data);
      } catch {
        // ignore
      }
    }, 1500);
    return () => window.clearInterval(t);
  }, [runId, run]);

  const handleRerun = async () => {
    if (!run) return;
    setRerunLoading(true);
    try {
      setError("Rerun not implemented yet.");
    } catch (err: any) {
      console.error(err);
      setError("Rerun failed.");
    } finally {
      setRerunLoading(false);
    }
  };

  if (loading) return <p>Loading run details...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!run) return <p>No run found.</p>;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <h1 className="text-2xl font-bold">Run</h1>
        <div className="flex gap-2">
          <button
            onClick={() => navigate(`/projects/${run.project_id}`)}
            className="px-4 py-2 rounded border border-gray-300 bg-white hover:bg-gray-50"
          >
            Open project
          </button>
          <button
            onClick={async () => {
              setLoading(true);
              try {
                const response = await api.get<RunResult>(`/api/runs/${runId}`);
                setRun(response.data);
              } finally {
                setLoading(false);
              }
            }}
            className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700"
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="rounded-xl border bg-white p-4 shadow-sm mb-4">
        <div className="font-mono text-xs text-gray-600 break-all">{run.id}</div>
      </div>
      <div className="text-sm text-gray-600 mb-4 space-y-1">
        <div>
          <strong>Status:</strong> {run.status}
        </div>
        <div>
          <strong>Created:</strong> {new Date(run.created_at).toLocaleString()}
        </div>
        {run.started_at && (
          <div>
            <strong>Started:</strong> {new Date(run.started_at).toLocaleString()}
          </div>
        )}
        {run.finished_at && (
          <div>
            <strong>Finished:</strong> {new Date(run.finished_at).toLocaleString()}
          </div>
        )}
        {run.error && (
          <div className="text-red-600">
            <strong>Error:</strong> {run.error}
          </div>
        )}
      </div>

      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-2">Artifacts</h2>
        {run.artifacts?.length ? (
          <ul className="list-disc pl-6">
            {run.artifacts.map((a) => (
              <li key={`${a.kind}-${a.storage_key}`}>
                <span className="font-semibold">{a.kind}</span> <span className="text-gray-600">({a.storage_key})</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-gray-500">No artifacts yet.</p>
        )}
      </div>

      <div className="mb-6 flex flex-wrap gap-3">
        {run.artifacts?.some((a) => a.kind === "excel_export") && (
          <button
            className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700"
            onClick={() => window.open(`${API_BASE}/api/runs/${run.id}/artifacts/excel_export/download`, "_blank")}
          >
            Download Excel
          </button>
        )}
        {run.artifacts?.some((a) => a.kind === "word_export") && (
          <button
            className="px-4 py-2 rounded bg-indigo-600 text-white hover:bg-indigo-700"
            onClick={() => window.open(`${API_BASE}/api/runs/${run.id}/artifacts/word_export/download`, "_blank")}
          >
            Download Word
          </button>
        )}
      </div>

      {summary && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-2">Averages</h2>
          <pre className="bg-gray-100 p-2 rounded overflow-auto text-sm">{JSON.stringify(summary, null, 2)}</pre>
        </div>
      )}

      {forecast && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-2">Forecast</h2>
          <div className="text-sm text-gray-700 mb-2">
            {forecast?.message ? forecast.message : "Predictions are shown below as charts (per metric)."}{" "}
          </div>
          <pre className="bg-gray-100 p-2 rounded overflow-auto text-sm">{JSON.stringify(forecast, null, 2)}</pre>
        </div>
      )}

      {graphs && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-2">Graphs</h2>
          <div className="flex flex-wrap gap-2 mb-3">
            <button
              className={`px-3 py-1 rounded border ${graphTab === "compare" ? "bg-blue-600 text-white border-blue-600" : "border-gray-300"}`}
              onClick={() => setGraphTab("compare")}
            >
              Compare
            </button>
            {graphs?.datasets &&
              Object.keys(graphs.datasets).map((k: string) => (
                <button
                  key={k}
                  className={`px-3 py-1 rounded border ${graphTab === k ? "bg-blue-600 text-white border-blue-600" : "border-gray-300"}`}
                  onClick={() => setGraphTab(k)}
                >
                  {k}
                </button>
              ))}
          </div>

          {(() => {
            const current: Record<string, string> | null =
              graphTab === "compare" ? graphs?.compare ?? null : graphs?.datasets?.[graphTab] ?? null;
            if (!current) return <div className="text-sm text-gray-500">No graphs available for this selection yet.</div>;
            return (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(current).map(([name, b64]) => (
                  <div key={name} className="border rounded bg-white p-3">
                    <div className="font-semibold mb-2">{name}</div>
                    <img alt={name} src={`data:image/png;base64,${b64}`} className="w-full h-auto" />
                  </div>
                ))}
              </div>
            );
          })()}

          {graphs?.forecast && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-2">Prediction charts</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(graphs.forecast).map(([name, b64]: any) => (
                  <div key={name} className="border rounded bg-white p-3">
                    <div className="font-semibold mb-2">{name}</div>
                    <img alt={name} src={`data:image/png;base64,${b64}`} className="w-full h-auto" />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Rerun button */}
      <button
        onClick={handleRerun}
        disabled={rerunLoading}
        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
      >
        {rerunLoading ? "Rerunning..." : "Rerun Analysis"}
      </button>
    </div>
  );
};

export default RunDetail;