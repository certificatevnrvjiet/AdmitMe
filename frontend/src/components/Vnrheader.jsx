// import './styles.css';
import image from '../assets/image.png';
import React from 'react';
import { useTheme } from '../context/ThemeContext';
import { FiSun, FiMoon, FiMenu, FiX } from 'react-icons/fi';
import { useAuth } from "../auth/AuthContext";
import API from '../api';
import { useEffect, useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';


function Vnrheader() {
    const { isDarkMode, toggleTheme } = useTheme();
    const { token, logout ,role} = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const [user, setUser] = useState(null);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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

      useEffect(() => {
        API.get('/me')
          .then(res =>{ 
            setUser(res.data.User);
          })
          .catch(() => setUser(null));
      }, [role]);

    return (
        <header id="app-header" className={`shadow-lg fixed top-0 left-0 w-full z-50 px-5 py-2 ${
            isDarkMode ? 'bg-gray-800 shadow-gray-900' : 'bg-white shadow-gray-200'
        }`}>
            <div className='flex justify-between items-center max-w-6xl mx-auto'>
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
                <div className="flex items-center gap-4">
                    {/* Desktop Navigation Menu */}
                    {user && (
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
                        {role === 'admin' && (
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
                        )}
                    </div>
                </div>
            )}
        </header>
    );
}

export default Vnrheader;