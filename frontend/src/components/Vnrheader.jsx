// import './styles.css';
import image from '../assets/icon.png';
import React from 'react';
import { useTheme } from '../context/ThemeContext';
import { FiSun, FiMoon, FiMenu, FiX, FiArrowLeft } from 'react-icons/fi';
import { useAuth } from "../auth/AuthContext";
import API from '../api';
import { useEffect, useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';


function Vnrheader() {
    const { isDarkMode, toggleTheme } = useTheme();
    const { token, logout, role, isAuthenticated } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const [user, setUser] = useState(null);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const isStaffSession = isAuthenticated && role !== "student";

    const handleThemeToggle = () => {
        toggleTheme();
        // Force a re-render of the document
        document.documentElement.classList.toggle('dark', !isDarkMode);
    };

    const handleLogout = () => {
        setUser(null);
        logout();
        navigate("/");
      };

    const showBackButton = location.pathname !== "/";

    const getBackTarget = () => {
        const pathname = location.pathname;

        if (pathname.startsWith("/student-portal/")) {
            return "/student-portal";
        }
        if (pathname === "/student-register") {
            return "/student-login";
        }
        if (pathname === "/student-login" || pathname === "/admin-login") {
            return "/";
        }
        if (pathname === "/forms" || pathname === "/user-management") {
            return "/dashboard";
        }
        if (pathname === "/dashboard") {
            return "/";
        }
        if (pathname === "/student-portal") {
            return "/student-login";
        }
        if (role === "student") {
            return "/student-portal";
        }
        if (isAuthenticated) {
            return "/dashboard";
        }
        return "/";
    };

    const handleBack = () => {
        setMobileMenuOpen(false);
        navigate(getBackTarget());
    };

    const handleAdminNavigation = () => {
        setMobileMenuOpen(false);
        navigate(isStaffSession ? "/dashboard" : "/admin-login");
    };

      useEffect(() => {
        if (!isAuthenticated || !token) {
          setUser(null);
          return;
        }

        API.get('/me')
          .then(res => { 
            setUser(res.data.User);
          })
          .catch((err) => {
            setUser(null);
            if (err?.response?.status === 401) {
              logout();
              navigate("/");
            }
          });
      }, [isAuthenticated, token, role, logout, navigate]);

    return (
        <header id="app-header" className={`sticky top-0 left-0 w-full z-50 border-b px-5 py-2 ${
            isDarkMode ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-white'
        }`}>
            <div className='flex justify-between items-center max-w-6xl mx-auto'>
                {showBackButton && (
                    <button
                        type="button"
                        onClick={handleBack}
                        className={`mr-2 inline-flex shrink-0 items-center gap-2 rounded-md border px-3 py-2 text-sm font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                            isDarkMode
                                ? 'border-gray-600 text-gray-100 hover:bg-gray-700'
                                : 'border-gray-200 text-gray-700 hover:bg-gray-100'
                        }`}
                        aria-label="Go back"
                    >
                        <FiArrowLeft size={18} />
                        <span className="hidden sm:inline">Back</span>
                    </button>
                )}
                <div className='lg:flex md:flex items-center justify-center flex-1'>
                    <img className="w-12 h-12 mx-3" src={image} alt="VNR Logo" />
                    <div className="text-center">
                        <p className={`lg:text-xl font-bold tracking-wide hidden sm:block ${
                        isDarkMode ? 'text-red-400' : 'text-red-600'
                    }`}>VNR Vignana Jyothi Institute of Engineering & Technology - VJEC</p>
                        <h5 className={`text-sm hidden md:block ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                            Vignana Jyothi Nagar, Pragathi Nagar, Nizampet (S.O), Hyderabad, Telangana, India - 500 090
                        </h5>
                    </div> 
                </div>
                <div className="flex items-center gap-2 sm:gap-4">
                    {/* Desktop Navigation Menu */}
                    {user && role === 'student' && (
                        <nav className="hidden md:flex items-center gap-4">
                            <Link
                                to="/student-portal"
                                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                                    location.pathname === '/student-portal'
                                        ? 'bg-blue-600 text-white'
                                        : isDarkMode
                                        ? 'text-gray-300 hover:text-white hover:bg-gray-700'
                                        : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                                }`}
                            >
                                Student Portal
                            </Link>
                        </nav>
                    )}

                    {user && role !== 'student' && (
                        <nav className="hidden md:flex items-center gap-4">
                            <Link
                                to="/dashboard"
                                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                                    location.pathname === '/dashboard'
                                        ? 'bg-blue-600 text-white'
                                        : isDarkMode
                                        ? 'text-gray-300 hover:text-white hover:bg-gray-700'
                                        : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                                }`}
                            >
                                Dashboard
                            </Link>
                            {role === 'admin' && (
                                <>
                                    <Link
                                        to="/forms"
                                        className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                                            location.pathname === '/forms'
                                                ? 'bg-blue-600 text-white'
                                                : isDarkMode
                                                ? 'text-gray-300 hover:text-white hover:bg-gray-700'
                                                : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                                        }`}
                                    >
                                        Forms
                                    </Link>
                                    <Link
                                        to="/user-management"
                                        className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                                            location.pathname === '/user-management'
                                                ? 'bg-blue-600 text-white'
                                                : isDarkMode
                                                ? 'text-gray-300 hover:text-white hover:bg-gray-700'
                                                : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                                        }`}
                                    >
                                        User Management
                                    </Link>
                                </>
                            )}
                        </nav>
                    )}
                    
                    {/* Mobile menu button */}
                    {user && (
                        <button
                            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                            className="md:hidden p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
                        >
                            {mobileMenuOpen ? <FiX size={24} /> : <FiMenu size={24} />}
                        </button>
                    )}
                    
                    <button
                        onClick={handleThemeToggle}
                        className={`p-2 rounded-full transition-colors duration-200 ${
                            isDarkMode 
                                ? 'bg-gray-700 text-yellow-300 hover:bg-gray-600' 
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                        aria-label="Toggle theme"
                    >
                        {isDarkMode ? <FiSun size={24} /> : <FiMoon size={24} />}
                    </button>

                    {role !== "student" && location.pathname !== "/admin-login" && (
                        <button
                            type="button"
                            onClick={handleAdminNavigation}
                            className={`inline-flex rounded-md px-3 py-2 text-sm font-bold transition-colors sm:px-4 ${
                                isStaffSession
                                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                                    : 'bg-red-600 text-white hover:bg-red-700'
                            }`}
                        >
                            <span className="sm:hidden">{isStaffSession ? "Admin" : "Admin"}</span>
                            <span className="hidden sm:inline">{isStaffSession ? "Admin Dashboard" : "Admin Login"}</span>
                        </button>
                    )}
                    
                    {user && (
                        <button
                            onClick={handleLogout}
                            className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
                        >
                            Logout
                        </button>
                    )}
                </div>
            </div>
            
            {/* Mobile Navigation Menu */}
            {mobileMenuOpen && user && (
                <div className={`md:hidden absolute top-full left-0 w-full ${isDarkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
                    <div className="px-2 pt-2 pb-3 space-y-1">
                        {role === 'student' ? (
                            <Link
                                to="/student-portal"
                                onClick={() => setMobileMenuOpen(false)}
                                className={`block px-3 py-2 rounded-md text-base font-medium ${
                                    location.pathname === '/student-portal'
                                        ? 'bg-blue-600 text-white'
                                        : isDarkMode
                                        ? 'text-gray-300 hover:text-white hover:bg-gray-700'
                                        : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                                }`}
                            >
                                Student Portal
                            </Link>
                        ) : (
                            <Link
                                to="/dashboard"
                                onClick={() => setMobileMenuOpen(false)}
                                className={`block px-3 py-2 rounded-md text-base font-medium ${
                                    location.pathname === '/dashboard'
                                        ? 'bg-blue-600 text-white'
                                        : isDarkMode
                                        ? 'text-gray-300 hover:text-white hover:bg-gray-700'
                                        : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                                }`}
                            >
                                Dashboard
                            </Link>
                        )}
                        {role === 'admin' && (
                            <>
                                <Link
                                    to="/forms"
                                    onClick={() => setMobileMenuOpen(false)}
                                    className={`block px-3 py-2 rounded-md text-base font-medium ${
                                        location.pathname === '/forms'
                                            ? 'bg-blue-600 text-white'
                                            : isDarkMode
                                            ? 'text-gray-300 hover:text-white hover:bg-gray-700'
                                            : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                                    }`}
                                >
                                    Forms
                                </Link>
                                <Link
                                    to="/user-management"
                                    onClick={() => setMobileMenuOpen(false)}
                                    className={`block px-3 py-2 rounded-md text-base font-medium ${
                                        location.pathname === '/user-management'
                                            ? 'bg-blue-600 text-white'
                                            : isDarkMode
                                            ? 'text-gray-300 hover:text-white hover:bg-gray-700'
                                            : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                                    }`}
                                >
                                    User Management
                                </Link>
                            </>
                        )}
                        {role !== 'student' && location.pathname !== '/admin-login' && (
                            <button
                                type="button"
                                onClick={handleAdminNavigation}
                                className={`block w-full rounded-md px-3 py-2 text-left text-base font-medium ${
                                    isStaffSession
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-red-600 text-white'
                                }`}
                            >
                                {isStaffSession ? 'Admin Dashboard' : 'Admin Login'}
                            </button>
                        )}
                    </div>
                </div>
            )}
        </header>
    );
}

export default Vnrheader;
