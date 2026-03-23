import React from "react";
import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="bg-blue-600 text-white px-6 py-4 shadow-md flex justify-between items-center">
      <div className="text-xl font-bold">
        Municipal Analytics
      </div>
      <div className="space-x-4">
        <Link to="/upload" className="hover:underline">
          Upload
        </Link>
        <Link to="/projects" className="hover:underline">
          Projects
        </Link>
      </div>
    </nav>
  );
}