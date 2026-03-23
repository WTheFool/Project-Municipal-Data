import React, { useEffect, useMemo, useRef, useState } from "react";
import api from "../api/client";
import { useNavigate } from "react-router-dom";

export default function Upload() {
  const [files, setFiles] = useState<File[]>([]);
  const [years, setYears] = useState<Record<string, string>>({});
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // null = hidden, -1 = indeterminate, 0..100 = percent
  const [uploadPct, setUploadPct] = useState<number | null>(null);
  const [autoRun, setAutoRun] = useState(true);
  const [graphMode, setGraphMode] = useState<"municipal" | "askew">("municipal");

  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const [jobProgress, setJobProgress] = useState<number | null>(null);

  const [projectId, setProjectId] = useState<string | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [runStatus, setRunStatus] = useState<string | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [artifacts, setArtifacts] = useState<{ kind: string; storage_key: string; created_at: string }[]>([]);

  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Prevent the browser's default "open file" behavior on drag/drop
  useEffect(() => {
    const stop = (e: DragEvent) => {
      e.preventDefault();
    };
    // Use capture so we beat the browser's default handlers.
    // Important: do NOT globally handle `drop` (it can interfere with our drop-zone).
    window.addEventListener("dragover", stop, { capture: true });
    window.addEventListener("drop", stop, { capture: true });
    return () => {
      window.removeEventListener("dragover", stop, { capture: true } as any);
      window.removeEventListener("drop", stop, { capture: true } as any);
    };
  }, []);

  const acceptExt = useMemo(() => new Set(["xlsx", "xls"]), []);
  const invalidFiles = useMemo(
    () =>
      files.filter((f) => {
        const ext = f.name.split(".").pop()?.toLowerCase() ?? "";
        return !acceptExt.has(ext);
      }),
    [files, acceptExt]
  );

  const mergeFiles = (incoming: File[]) => {
    setFiles((prev) => {
      const key = (f: File) => `${f.name}::${f.size}::${f.lastModified}`;
      const seen = new Set(prev.map(key));
      const merged = [...prev];
      for (const f of incoming) {
        const k = key(f);
        if (seen.has(k)) continue;
        seen.add(k);
        merged.push(f);
      }
      return merged;
    });
    setYears((prev) => {
      const next = { ...prev };
      for (const f of incoming) {
        if (next[f.name]) continue;
        const m = f.name.match(/(19\d{2}|20\d{2})/);
        if (m) next[f.name] = m[1];
      }
      return next;
    });
  };

  const handleFiles = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      mergeFiles(Array.from(event.target.files));
    }
    // allow re-selecting the same file(s)
    event.currentTarget.value = "";
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    const dt = event.dataTransfer;
    if (dt?.files?.length) {
      mergeFiles(Array.from(dt.files));
      return;
    }
    // Fallback for some browsers / drag sources
    const items = Array.from(dt?.items ?? []);
    const files = items
      .filter((i) => i.kind === "file")
      .map((i) => i.getAsFile())
      .filter((f): f is File => !!f);
    if (files.length) mergeFiles(files);
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
  };

  const removeFile = (name: string) => {
    setFiles((xs) => xs.filter((f) => f.name !== name));
    setYears((p) => {
      const n = { ...p };
      delete n[name];
      return n;
    });
  };

  const resetAll = () => {
    setFiles([]);
    setYears({});
    setError(null);
    setUploadPct(null);
    setGraphMode("municipal");
    setJobId(null);
    setJobStatus(null);
    setJobProgress(null);
    setProjectId(null);
    setRunId(null);
    setRunStatus(null);
    setRunError(null);
    setArtifacts([]);
  };

  const clearAll = () => resetAll();

  useEffect(() => {
    if (!jobId) return;
    let alive = true;
    const tick = async () => {
      try {
        const r = await api.get<{ job_id: string; status: string; progress: number; result: any }>(`/api/job/${jobId}`);
        if (!alive) return;
        setJobStatus(r.data.status);
        setJobProgress(typeof r.data.progress === "number" ? r.data.progress : null);
      } catch {
        // ignore
      }
    };
    tick();
    const t = window.setInterval(tick, 1200);
    return () => {
      alive = false;
      window.clearInterval(t);
    };
  }, [jobId]);

  useEffect(() => {
    if (!runId) return;
    let alive = true;
    const tick = async () => {
      try {
        const r = await api.get<{
          id: string;
          status: string;
          error: string | null;
          artifacts: { kind: string; storage_key: string; created_at: string }[];
        }>(`/api/runs/${runId}`);
        if (!alive) return;
        setRunStatus(r.data.status);
        setRunError(r.data.error ?? null);
        setArtifacts(r.data.artifacts ?? []);
      } catch {
        // ignore
      }
    };
    tick();
    const t = window.setInterval(tick, 1500);
    return () => {
      alive = false;
      window.clearInterval(t);
    };
  }, [runId]);

  // Auto-run when files are selected (no "Run" button required).
  useEffect(() => {
    if (!autoRun) return;
    if (!files.length) return;
    if (uploading) return;
    if (runId || jobId) return;

    const t = window.setTimeout(() => {
      uploadFiles();
    }, 250);
    return () => window.clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoRun, files, uploading, runId, jobId]);

  const uploadFiles = async () => {
    if (files.length === 0) return;
    if (invalidFiles.length) {
      setError("Only .xlsx / .xls files are supported.");
      return;
    }

    setUploading(true);
    setError(null);
    setUploadPct(0);
    setJobId(null);
    setJobStatus(null);
    setJobProgress(null);
    setProjectId(null);
    setRunId(null);
    setRunStatus(null);
    setRunError(null);
    setArtifacts([]);

    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));
    // Optional per-file years (aligned with current files order)
    const yearsArr = files.map((f) => {
      const v = years[f.name];
      if (!v) return null;
      const n = Number(v);
      return Number.isFinite(n) ? Math.trunc(n) : null;
    });
    formData.append("years", JSON.stringify(yearsArr));
    formData.append("graph_mode", graphMode);

    try {
      const response = await api.post<{ project_id: string; upload_ids: string[]; run_id: string; job_id: string }>(
        "/api/upload",
        formData,
        {
          onUploadProgress: (evt) => {
            if (!evt.total) {
              // Indeterminate progress when total is unknown.
              setUploadPct(-1);
              return;
            }
            const pct = Math.min(100, Math.round((evt.loaded / evt.total) * 100));
            setUploadPct(pct);
          },
        }
      );

      setProjectId(response.data.project_id);
      setRunId(response.data.run_id);
      setJobId(response.data.job_id);
      setRunStatus("queued");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
      // Leave progress visible briefly; feels less "glitchy" than snapping away.
      window.setTimeout(() => setUploadPct(null), 600);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="rounded-xl border bg-white p-6 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">Upload & Analyze</h1>
            <p className="text-gray-600 mt-1">
              Drop one or more Excel files. We’ll standardize them and generate artifacts (profile + parquet) in the background.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-gray-700 select-none">
              <input type="checkbox" checked={autoRun} onChange={(e) => setAutoRun(e.target.checked)} />
              Auto-run
            </label>
            <button
              onClick={resetAll}
              className="px-4 py-2 rounded border border-gray-300 bg-white hover:bg-gray-50"
            >
              New analysis
            </button>
            <button
              onClick={() => navigate("/projects")}
              className="px-4 py-2 rounded border border-gray-300 bg-white hover:bg-gray-50"
            >
              View projects
            </button>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <div
              className="border-2 border-dashed border-gray-300 p-10 rounded-lg text-center bg-gray-50 hover:bg-gray-100 cursor-pointer"
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="pointer-events-none">
                <p className="font-medium">Drag & drop Excel files</p>
                <p className="text-sm text-gray-600 mt-1">or click to browse</p>
              </div>
              <input
                id="file-input"
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls"
                multiple
                className="hidden"
                onChange={handleFiles}
              />
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-3">
              <div className="text-sm font-semibold text-gray-700">Graph mode</div>
              <div className="inline-flex rounded-lg border overflow-hidden">
                <button
                  type="button"
                  onClick={() => setGraphMode("municipal")}
                  className={`px-3 py-2 text-sm ${graphMode === "municipal" ? "bg-emerald-600 text-white" : "bg-white hover:bg-gray-50"}`}
                >
                  Municipal
                </button>
                <button
                  type="button"
                  onClick={() => setGraphMode("askew")}
                  className={`px-3 py-2 text-sm ${graphMode === "askew" ? "bg-amber-600 text-white" : "bg-white hover:bg-gray-50"}`}
                >
                  Askew data (soon)
                </button>
              </div>
              {graphMode === "askew" && <div className="text-xs text-gray-600">Askew graphs are not implemented yet.</div>}
            </div>
          </div>

          <div className="rounded-lg border bg-white p-4">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold">Selected files</h2>
              <button onClick={clearAll} className="text-sm text-gray-600 hover:text-gray-900" disabled={!files.length}>
                Clear
              </button>
            </div>

            {!files.length ? (
              <p className="text-sm text-gray-500 mt-3">No files selected yet.</p>
            ) : (
              <ul className="mt-3 space-y-2 max-h-64 overflow-auto">
                {files.map((f) => {
                  const ext = f.name.split(".").pop()?.toLowerCase() ?? "";
                  const ok = acceptExt.has(ext);
                  return (
                    <li key={f.name} className="flex items-center justify-between gap-2">
                      <div className="min-w-0">
                        <div className="truncate text-sm font-medium">{f.name}</div>
                        <div className={`text-xs ${ok ? "text-gray-500" : "text-red-600"}`}>
                          {ok ? `${Math.round(f.size / 1024)} KB` : "Unsupported type"}
                        </div>
                        <div className="mt-2 flex items-center gap-2">
                          <label className="text-xs text-gray-600">Year</label>
                          <input
                            value={years[f.name] ?? ""}
                            onChange={(e) => setYears((p) => ({ ...p, [f.name]: e.target.value }))}
                            placeholder="e.g. 2024"
                            className="w-24 text-xs px-2 py-1 border rounded"
                          />
                        </div>
                      </div>
                      <button
                        onClick={() => removeFile(f.name)}
                        className="text-sm px-2 py-1 rounded border border-gray-300 hover:bg-gray-50"
                      >
                        Remove
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}

            {!autoRun && (
              <button
                onClick={uploadFiles}
                disabled={uploading || files.length === 0}
                className="mt-4 w-full px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-700"
              >
                {uploading ? "Uploading..." : "Run analysis"}
              </button>
            )}

            {uploadPct !== null && (
              <div className="mt-3">
                <div className="flex justify-between text-xs text-gray-600">
                  <span>Uploading</span>
                  <span>{uploadPct === -1 ? "…" : `${uploadPct}%`}</span>
                </div>
                <div className="h-2 bg-gray-200 rounded mt-1 overflow-hidden">
                  {uploadPct === -1 ? (
                    <div className="h-2 w-1/3 bg-blue-600 animate-pulse" />
                  ) : (
                    <div className="h-2 bg-blue-600" style={{ width: `${uploadPct}%` }} />
                  )}
                </div>
              </div>
            )}

            {error && <div className="mt-3 text-sm text-red-700 bg-red-50 border border-red-200 p-2 rounded">{error}</div>}
          </div>
        </div>
      </div>

      {(runId || jobId) && (
        <div className="rounded-xl border bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-lg font-semibold">Processing status</h2>
            <div className="flex gap-2">
              {projectId && (
                <button
                  onClick={() => navigate(`/projects/${projectId}`)}
                  className="px-3 py-2 rounded border border-gray-300 hover:bg-gray-50"
                >
                  Open project
                </button>
              )}
              {runId && (
                <button
                  onClick={() => navigate(`/runs/${runId}`)}
                  className="px-3 py-2 rounded bg-blue-600 text-white hover:bg-blue-700"
                >
                  Open run
                </button>
              )}
            </div>
          </div>

          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-lg border p-4">
              <div className="text-sm text-gray-600">Run</div>
              <div className="font-mono text-sm mt-1 break-all">{runId ?? "—"}</div>
              <div className="mt-2 text-sm">
                <span className="text-gray-600">Status: </span>
                <span className="font-semibold">{runStatus ?? "—"}</span>
              </div>
              {runError && <div className="mt-2 text-sm text-red-700">{runError}</div>}
            </div>

            <div className="rounded-lg border p-4">
              <div className="text-sm text-gray-600">Job</div>
              <div className="font-mono text-sm mt-1 break-all">{jobId ?? "—"}</div>
              <div className="mt-2 text-sm">
                <span className="text-gray-600">Status: </span>
                <span className="font-semibold">{jobStatus ?? "—"}</span>
              </div>
              {jobProgress !== null && (
                <div className="mt-2">
                  <div className="flex justify-between text-xs text-gray-600">
                    <span>Progress</span>
                    <span>{jobProgress}%</span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded mt-1 overflow-hidden">
                    <div className="h-2 bg-emerald-600" style={{ width: `${Math.max(0, Math.min(100, jobProgress))}%` }} />
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="mt-4">
            <div className="text-sm font-semibold mb-2">Artifacts</div>
            {!artifacts.length ? (
              <div className="text-sm text-gray-500">Artifacts will appear here when processing completes.</div>
            ) : (
              <ul className="space-y-2">
                {artifacts.map((a) => (
                  <li key={`${a.kind}-${a.storage_key}`} className="rounded border p-3 flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <div className="font-semibold">{a.kind}</div>
                      <div className="text-xs text-gray-600 font-mono break-all">{a.storage_key}</div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}