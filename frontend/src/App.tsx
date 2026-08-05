import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import Dashboard from "./pages/Dashboard";
import Assignments from "./pages/Assignments";
import Evaluations from "./pages/Evaluations";
import Profile from "./pages/Profile";
import AdminPanel from "./pages/AdminPanel";
import UploadPerformance from "./pages/UploadPerformance";
import TaskRecommendations from "./pages/TaskRecommendations";
import ReferenceUpload from "./pages/ReferenceUpload";
import MusicianResults from "./pages/MusicianResults";
import "./App.css";

function App() {
  return (
    // AuthProvider makes the current user/session available to every route
    <AuthProvider>
      <Router>
        <div
          className="min-h-screen"
          style={{ backgroundColor: "var(--bg-page)" }}
        >
          <Routes>
            {/* Public routes, accessible without authentication */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            {/* Authenticated routes, wrapped in ProtectedRoute to enforce login (and role, where required) */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <Profile />
                </ProtectedRoute>
              }
            />
            <Route
              path="/assignments"
              element={
                <ProtectedRoute>
                  <Assignments />
                </ProtectedRoute>
              }
            />
            <Route
              path="/performances/upload"
              element={
                <ProtectedRoute>
                  <UploadPerformance />
                </ProtectedRoute>
              }
            />
            <Route
              path="/evaluations"
              element={
                <ProtectedRoute>
                  <Evaluations />
                </ProtectedRoute>
              }
            />
            {/* Admin-only routes */}
            <Route
              path="/admin"
              element={
                <ProtectedRoute requiredRole="admin">
                  <AdminPanel />
                </ProtectedRoute>
              }
            />
            <Route
              path="/recommendations"
              element={
                <ProtectedRoute requiredRole="admin">
                  <TaskRecommendations />
                </ProtectedRoute>
              }
            />
            <Route
              path="/reference-upload"
              element={
                <ProtectedRoute requiredRole="admin">
                  <ReferenceUpload />
                </ProtectedRoute>
              }
            />
            <Route
              path="/musician-results"
              element={
                <ProtectedRoute requiredRole="admin">
                  <MusicianResults />
                </ProtectedRoute>
              }
            />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
