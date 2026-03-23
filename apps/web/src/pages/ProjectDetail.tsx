import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "../api/client";
import { useNavigate } from "react-router-dom";

export default function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [projectData, setProjectData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId || projectId === "upload") {
      navigate("/upload", { replace: true });
      return;
    }
    const fetchProject = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await axios.get(`/api/projects/${projectId}`);
        setProjectData(response.data);
      } catch (err: any) {
        setError(err?.response?.data?.detail || "Failed to fetch project");
      } finally {
        setLoading(false);
      }
    };

    if (projectId) fetchProject();
  }, [projectId, navigate]);

  if (loading) return <div>Loading project details...</div>;
  if (error) return <div className="text-red-600">{error}</div>;
  if (!projectData) return <div>No project data available.</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{projectData.name}</h1>

      <section>
        <h2 className="text-xl font-semibold mb-2">Uploads</h2>
        {projectData.uploads?.length ? (
          <ul className="list-disc pl-6">
            {projectData.uploads.map((u: any) => (
              <li key={u.id}>
                <span className="font-semibold">{u.filename}</span>{" "}
                <span className="text-gray-500">({new Date(u.created_at).toLocaleString()})</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-gray-500">No uploads yet.</p>
        )}
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-2">Runs</h2>
        {projectData.runs?.length ? (
          <ul className="list-disc pl-6">
            {projectData.runs.map((r: any) => (
              <li key={r.id}>
                <a className="text-blue-600 hover:underline" href={`/runs/${r.id}`}>
                  {r.id}
                </a>{" "}
                <span className="text-gray-700">({r.status})</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-gray-500">No runs yet.</p>
        )}
      </section>
    </div>
  );
}