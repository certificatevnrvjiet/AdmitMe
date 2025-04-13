import React, { useState } from "react";
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { isDarkMode } = useTheme();

  const handleLogin = (e) => {
    e.preventDefault();
    setError("");

    // Check if email and password are provided
    if (!email || !password) {
      setError("Please enter both email and password");
      return;
    }

    // Check if it's a valid email
    if (!email.includes('@')) {
      setError("Please enter a valid email address");
      return;
    }

    // Check if it's admin
    if (email === "admin@vnrvjiet.in" && password === "admin123") {
      navigate('/dashboard/admin');
      return;
    }

    // Extract domain from email
    const domain = email.split('@')[1];
    
    // Check if it's a valid VNRVJIET email
    if (domain !== 'vnrvjiet.in') {
      setError("Please use your VNRVJIET email");
      return;
    }

    // Extract department from email
    const username = email.split('@')[0];
    let department = '';

    if (username.includes('cse')) {
      department = 'cse';
    } else if (username.includes('ece')) {
      department = 'ece';
    } else if (username.includes('eee')) {
      department = 'eee';
    } else if (username.includes('mech')) {
      department = 'mech';
    } else if (username.includes('civil')) {
      department = 'civil';
    }

    if (!department) {
      setError("Invalid department email");
      return;
    }

    // For demo purposes, using a simple password check
    if (password === "password123") {
      navigate(`/dashboard/${department}`);
    } else {
      setError("Invalid credentials");
    }
  };

  return (
    <div className={`min-h-screen flex items-center justify-center ${isDarkMode ? 'bg-gray-900' : 'bg-gradient-to-br from-blue-50 to-indigo-100'} py-12 px-4 sm:px-6 lg:px-8`}>
      <div className={`max-w-md w-full space-y-8 p-10 rounded-xl shadow-2xl ${isDarkMode ? 'bg-gray-800' : 'bg-white'}`}>
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
        <form className="mt-8 space-y-6" onSubmit={handleLogin}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email" className="sr-only">
                Email address
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={`appearance-none rounded-none relative block w-full px-3 py-2 border ${isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'} rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm`}
                placeholder="Email address"
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only mt-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={`appearance-none rounded-none relative block w-full mt-2 px-3 py-2 border ${isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'} rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm`}
                placeholder="Password"
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors duration-200"
            >
              Sign in
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;