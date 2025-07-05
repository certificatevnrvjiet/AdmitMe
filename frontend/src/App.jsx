import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import LoginPage from "./components/LoginPage";
import Dashboard from "./pages/Dashboard";
import Footer from "./components/Footer";
import Vnrheader from "./components/Vnrheader";
import { ThemeProvider } from "./context/ThemeContext";
import ProtectedRoute from "./ProtectedRoute";
import { AuthProvider } from "./auth/AuthContext";
import "./App.css"; // Import your global styles


function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <Router>
          <div className="flex flex-col min-h-screen overflow-auto scrollbar-hide h-64 bg-white dark:bg-gray-900">
            <Vnrheader />
            <main className="flex-grow mt-16 mb-16 overflow-y-auto">
              <Routes>
                <Route path="/" element={<LoginPage />} />
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute>
                      <Dashboard />
                    </ProtectedRoute>
                  }
                />
               </Routes>
            </main>
            <Footer />
          </div>
        </Router>
      </ThemeProvider>
    </AuthProvider>
  );
}

export default App;
