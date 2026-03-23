import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";

interface Project {
  id: string;
  name: string;
  created_at: string;
}

const Projects: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchProjects = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await api.get<Project[]>("/api/projects");
        setProjects(response.data);
      } catch (err: any) {
        console.error(err);
        setError("Failed to load projects.");
      } finally {
        setLoading(false);
      }
    };

    fetchProjects();
  }, []);

  const handleProjectClick = (projectId: string) => {
    navigate(`/projects/${projectId}`);
  };

  if (loading) {
    return <p className="p-6 text-center">Loading projects...</p>;
  }

  if (error) {
    return <p className="p-6 text-center text-red-500">{error}</p>;
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Projects</h1>
        <button
          onClick={() => navigate("/upload")}
          className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700"
        >
          New analysis
        </button>
      </div>
      {projects.length === 0 ? (
        <div className="rounded-xl border bg-white p-6 shadow-sm">
          <div className="font-semibold">No projects yet</div>
          <div className="text-sm text-gray-600 mt-1">Upload an Excel file to create your first project and run.</div>
          <button
            onClick={() => navigate("/upload")}
            className="mt-4 px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700"
          >
            Upload an Excel
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project) => (
            <div
              key={project.id}
              className="border p-4 rounded shadow hover:shadow-lg cursor-pointer transition"
              onClick={() => handleProjectClick(project.id)}
            >
              <h2 className="text-lg font-semibold mb-1">{project.name}</h2>
              <p className="text-sm">
                <strong>Created:</strong> {new Date(project.created_at).toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Projects;