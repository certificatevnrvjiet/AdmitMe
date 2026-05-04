import { useContext } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { AuthContext } from "./auth/AuthContext"; // Adjust path as needed

const ProtectedRoute = ({ children, role }) => {
  const { isAuthenticated, isAuthLoading, role: userRole } = useContext(AuthContext);
  const location = useLocation();

  if (isAuthLoading) {
    return (
      <div className="min-h-screen px-4 py-24 text-center text-gray-600">
        Checking your session...
      </div>
    );
  }
 
  if (!isAuthenticated) {
    return <Navigate to="/admin-login" replace state={{ from: location.pathname }} />;
  }
  if (role && userRole !== role) {
    // Optional: you could redirect to a "403 Forbidden"  page or dashboard
    return <Navigate to={userRole === "student" ? "/student-portal/btech-2026" : "/dashboard"} replace />;
  }

  return children;
};

export default ProtectedRoute;
