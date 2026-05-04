import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./components/LoginPage";
import StudentLoginPage from "./components/StudentLoginPage";
import Dashboard from "./pages/Dashboard";
import UserManagement from "./pages/UserManagement";
import StudentPortal from "./pages/StudentPortal";
import AdminForms from "./pages/AdminForms";
import LandingPage from "./pages/LandingPage";
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
          <div className="flex min-h-screen flex-col bg-white dark:bg-gray-900">
            <Vnrheader />
            <main className="flex-grow bg-gray-50 dark:bg-gray-900">
              <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="/student-form" element={<Navigate to="/student-portal" replace />} />
                <Route path="/admin-login" element={<LoginPage />} />
                <Route path="/student-login" element={<StudentLoginPage />} />
                <Route path="/student-register" element={<StudentLoginPage initialMode="register" />} />
                <Route path="/student-portal" element={<StudentPortal />} />
                <Route path="/student-portal/:slug" element={<StudentPortal />} />
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute>
                      <Dashboard />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/user-management"
                  element={
                    <ProtectedRoute>
                      <UserManagement />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/forms"
                  element={
                    <ProtectedRoute role="admin">
                      <AdminForms />
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
