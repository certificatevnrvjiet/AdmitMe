import { createContext, useContext, useEffect, useState } from "react";
import API from "../api"; // Adjust the import based on your project structure
// ✅ Create Auth Context
export const AuthContext = createContext();

// ✅ Optional: Custom hook for cleaner context usage
export const useAuth = () => useContext(AuthContext);

// ✅ Helper: Check if token is valid
const verifyToken = async (token) => {
  try {
    const response = await API.get("/api/verify-token", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return {
      isValid: response.data.valid,
      user: response.data.user,
      role: response.data.role,
      expiresAt: response.data.expires
    };
  } catch (error) {
    console.error("Token verification failed:", error.response?.data || error.message);
    return {
      isValid: false,
      user: null,
      role: null,
      expiresAt: null
    };
  }
};

// ✅ Auth Provider Component
export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [role, setRole] = useState(null);
  const [token, setToken] = useState(null);

  // Load auth state from localStorage on app load
  useEffect(() => {
    const savedToken = localStorage.getItem("token");
    const savedRole = localStorage.getItem("role");
    
    const verifyAndSetToken = async () => {
      if (savedToken) {
        const verification = await verifyToken(savedToken);
        if (verification.isValid) {
          setToken(savedToken);
          setRole(verification.role); // Use role from verification
          setIsAuthenticated(true);
        } else {
          logout(); // Clear invalid token
        }
      }
    };

    verifyAndSetToken();
  }, []);

  // ✅ Login function
  const login = (token, userRole) => {
    setIsAuthenticated(true);
    setToken(token);
    setRole(userRole);
    localStorage.setItem("token", token);
    localStorage.setItem("role", userRole);
  };

  // ✅ Logout function
  const logout = () => {
    setIsAuthenticated(false);
    setToken(null);
    setRole(null);
    localStorage.removeItem("token");
    localStorage.removeItem("role");
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, token, login, logout, role }}>
      {children}
    </AuthContext.Provider>
  );
};
