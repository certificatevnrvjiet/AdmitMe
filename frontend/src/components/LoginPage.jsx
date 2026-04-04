import { useState, useContext , useEffect } from "react";
import { useNavigate } from 'react-router-dom';
import { Link } from "react-router-dom";
import { useTheme } from '../context/ThemeContext';
import API from "../api"; // Adjust the import path as necessary
import { useAuth, AuthContext } from "../auth/AuthContext";
import { FiEye, FiEyeOff } from "react-icons/fi";


const LoginPage = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();
  const { isDarkMode } = useTheme();
  const { login } = useAuth();

  const { isAuthenticated } = useContext(AuthContext);

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard"); // or any other route you want
    }
  }, [isAuthenticated, navigate]);


  const handleSubmit = async (e) => {
    e.preventDefault();
    const form = new URLSearchParams();
    form.append("username", username);
    form.append("password", password);

    try {
      const res = await API.post("/token", form);
      login(res.data.access_token, res.data.role); // Assuming the token contains the role
      navigate("/dashboard");
    } catch (err) {
      alert("Invalid credentials");
    }
  };

  return (
    <div className="h-screen flex items-center justify-center relative"
         style={{
           backgroundImage: 'url(https://vnrvjiet.ac.in/assets/images/Numbers-Image.png)',
           backgroundSize: 'cover',
           backgroundPosition: 'center',
         }}>
      {/* Overlay */}
      <div className={`absolute inset-0 pointer-events-none ${isDarkMode ? 'bg-gradient-to-br from-gray-950/80 to-gray-900/70' : 'bg-gradient-to-br from-blue-50/70 to-indigo-100/70'}`}></div>
      
      {/* Content */}
      <div className={`max-w-md w-full p-8 rounded-xl shadow-2xl relative z-10 mx-4 ${isDarkMode ? 'bg-gray-800' : 'bg-white'} border ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
        <div>
          <h2 className={`mt-6 text-center text-4xl font-extrabold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
            VNRVJIET Login
          </h2>
          <p className={`mt-2 text-center text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
            Please sign in with your department email
          </p>
        </div>
        {error && (
          <div className={`p-3 rounded-md ${isDarkMode ? 'bg-red-900 text-red-200' : 'bg-red-100 text-red-700'}`}>
            {error}
          </div>
        )}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email" className="sr-only">
                Email address
              </label>
              <input
                id="email"
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className={`appearance-none rounded-none relative block w-full px-3 py-2 border ${isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'} rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm`}
                placeholder="Email address"
              />
            </div>
            <div className="relative">
              <label htmlFor="password" className="sr-only mt-2">
                Password
              </label>
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={`appearance-none rounded-none relative block w-full mt-2 px-3 py-2 border ${isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'} rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm`}
                placeholder="Password"
              />
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="absolute inset-y-0 right-0 px-3 flex items-center text-lg text-gray-500 focus:outline-none"
                tabIndex={-1}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <FiEyeOff /> : <FiEye />}
              </button>
            </div>
          </div>

          <div>
            <button
              type="submit"
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors duration-200"
            >
              Sign in
            </button>
            <Link
              to="/student-portal"
              className={`mt-3 inline-flex w-full justify-center rounded-md border px-4 py-2 text-sm font-medium ${
                isDarkMode
                  ? "border-gray-600 text-gray-100 hover:bg-gray-700"
                  : "border-gray-300 text-gray-700 hover:bg-gray-50"
              }`}
            >
              Student Admission Form
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
