import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";

import Projects from "./pages/Projects";
import ProjectDetail from "./pages/ProjectDetail";
import RunDetail from "./pages/RunDetail";
import UploadPage from "./pages/UploadPage";

export default function AppRoutes() {
  return (
    <Routes>
      {/* Redirect root to upload */}
      <Route path="/" element={<Navigate to="/upload" replace />} />

      {/* Upload */}
      <Route path="/upload" element={<UploadPage />} />

      {/* Guard against common wrong URLs */}
      <Route path="/projects/upload" element={<Navigate to="/upload" replace />} />

      {/* Projects list */}
      <Route path="/projects" element={<Projects />} />

      {/* Project detail page */}
      <Route path="/projects/:projectId" element={<ProjectDetail />} />

      {/* Run detail page */}
      <Route path="/runs/:runId" element={<RunDetail />} />

      {/* Catch-all 404 route */}
      <Route
        path="*"
        element={
          <div className="p-6 text-center text-red-600">
            404: Page not found
          </div>
        }
      />
    </Routes>
  );
}