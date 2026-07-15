import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import Navigation from "./components/Navigation";
import Login from "./pages/Login";
import Register from "./pages/Register";
import RegistrationSuccess from "./pages/RegistrationSuccess";
import Dashboard from "./pages/Dashboard";
import Evaluations from "./pages/Evaluations";
import Profile from "./pages/Profile";
import AdminPanel from "./pages/AdminPanel";
import Performances from "./pages/Performances";
import "./App.css";

function App() {
  return (
    <AuthProvider>
      <Router>
        <Navigation />
        <div className="min-h-screen bg-gray-50">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route
              path="/registration-success"
              element={<RegistrationSuccess />}
            />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Dashboard />
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
            <Route
              path="/performances"
              element={
                <ProtectedRoute>
                  <Performances />
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
              path="/admin"
              element={
                <ProtectedRoute requiredRole="admin">
                  <AdminPanel />
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
