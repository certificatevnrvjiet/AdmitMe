import { useContext } from "react";
import { Navigate } from "react-router-dom";
import { AuthContext } from "./auth/AuthContext"; // Adjust path as needed

const ProtectedRoute = ({ children, role }) => {
  const { isAuthenticated, role: userRole } = useContext(AuthContext);
 
  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }
  if (role && userRole !== role) {
    // Optional: you could redirect to a "403 Forbidden"  page or dashboard
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

export default ProtectedRoute;
