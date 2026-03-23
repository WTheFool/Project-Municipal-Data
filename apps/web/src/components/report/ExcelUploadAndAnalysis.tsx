import React from "react";
import ExcelUploadAndAnalysis from "../components/report/ExcelUploadAndAnalysis";

const ProjectDetail: React.FC = () => {
  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Project Analysis</h1>
      <p className="mb-6 text-gray-700">
        Upload your municipal or generalized Excel datasets to generate dynamic
        indicators, statistical analysis, ML-based insights, graphs, and AI-generated reports.
      </p>

      <ExcelUploadAndAnalysis />

      <div className="mt-10">
        <h2 className="text-xl font-semibold mb-2">Project Info / Metadata</h2>
        <div className="border p-4 bg-gray-50">
          <p><strong>Project Name:</strong> Municipal Irrigation Study</p>
          <p><strong>Description:</strong> Multi-file analysis and indicator generation</p>
          <p><strong>Status:</strong> Active</p>
          <p><strong>Last Updated:</strong> 2026-03-12</p>
        </div>
      </div>
    </div>
  );
};

export default ProjectDetail;