import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import LoginPage from "./components/LoginPage";
import Dashboard from "./pages/Dashboard";
import Footer from "./components/Footer";
import Vnrheader from "./components/Vnrheader";
import { ThemeProvider } from "./context/ThemeContext";

function App() {
  return (
    <ThemeProvider>
      <Router>
        <div className="flex flex-col min-h-screen bg-white dark:bg-gray-900">
          <Vnrheader />
          <main className="flex-grow mt-16 mb-16 overflow-y-auto">
            <Routes>
              <Route path="/" element={<LoginPage />} />
              <Route path="/dashboard/admin" element={<Dashboard department="admin" />} />
              <Route path="/dashboard/cse" element={<Dashboard department="cse" />} />
              <Route path="/dashboard/ece" element={<Dashboard department="ece" />} />
              <Route path="/dashboard/eee" element={<Dashboard department="eee" />} />
              <Route path="/dashboard/mech" element={<Dashboard department="mech" />} />
              <Route path="/dashboard/civil" element={<Dashboard department="civil" />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;