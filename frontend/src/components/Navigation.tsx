import React, { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const Navigation: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  // Don't show navigation on login/register/success pages
  if (
    location.pathname === "/login" ||
    location.pathname === "/register" ||
    location.pathname === "/registration-success"
  ) {
    return null;
  }

  const navLinks = [
    { path: "/", label: "Dashboard" },
    { path: "/performances", label: "Performances" },
    { path: "/evaluations", label: "Evaluations" },
    { path: "/profile", label: "Profile" },
  ];

  // Add admin panel link for admin users
  if (user?.role === "admin") {
    navLinks.push({ path: "/admin", label: "Admin" });
  }

  return (
    <nav className="bg-indigo-600 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo/Brand */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="text-white font-bold text-xl">🎵 MES</div>
          </Link>

          {/* Desktop Navigation Links */}
          <div className="hidden md:flex items-center space-x-1">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  location.pathname === link.path
                    ? "bg-indigo-700 text-white"
                    : "text-indigo-100 hover:bg-indigo-500 hover:text-white"
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* User Info and Logout - Desktop */}
          <div className="hidden md:flex items-center space-x-4">
            <div className="text-indigo-100">
              <p className="text-sm">
                Welcome, <span className="font-semibold">{user?.username}</span>
              </p>
              <p className="text-xs opacity-75">{user?.role}</p>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 rounded-md bg-red-500 text-white text-sm font-medium hover:bg-red-600 transition-colors"
            >
              Logout
            </button>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-indigo-100 hover:bg-indigo-500 hover:text-white focus:outline-none"
            >
              <svg
                className="h-6 w-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d={
                    isOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"
                  }
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {isOpen && (
        <div className="md:hidden bg-indigo-700">
          <div className="px-2 pt-2 pb-3 space-y-1">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={`block px-3 py-2 rounded-md text-base font-medium ${
                  location.pathname === link.path
                    ? "bg-indigo-800 text-white"
                    : "text-indigo-100 hover:bg-indigo-600 hover:text-white"
                }`}
                onClick={() => setIsOpen(false)}
              >
                {link.label}
              </Link>
            ))}
            <div className="px-3 py-2 border-t border-indigo-600 mt-2">
              <p className="text-indigo-100 text-sm mb-3">
                <span className="font-semibold">{user?.username}</span>
                <br />
                <span className="text-xs opacity-75">{user?.role}</span>
              </p>
              <button
                onClick={handleLogout}
                className="w-full px-4 py-2 rounded-md bg-red-500 text-white text-sm font-medium hover:bg-red-600 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navigation;
