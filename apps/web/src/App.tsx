import React from "react";
import AppRoutes from "./routes";
import "./index.css";

// Optional: layout components
import Navbar from "./components/layout/Navbar";
import PageContainer from "./components/layout/PageContainer";
import { BrowserRouter } from "react-router-dom";

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <PageContainer>
          <AppRoutes />
        </PageContainer>
      </div>
    </BrowserRouter>
  );
}

export default App;