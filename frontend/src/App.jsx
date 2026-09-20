import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ChatPage from './pages/ChatPage';
import AdminKBPage from './pages/AdminKBPage';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* User Protected Routes */}
          <Route element={<ProtectedRoute requireAdmin={false} />}>
            <Route path="/chat" element={<ChatPage />} />
          </Route>

          {/* Admin Protected Routes */}
          <Route element={<ProtectedRoute requireAdmin={true} />}>
            <Route path="/admin" element={<AdminKBPage />} />
            <Route path="/admin/knowledge-base" element={<AdminKBPage />} />
          </Route>

          {/* Default Redirects */}
          <Route path="/" element={<Navigate to="/chat" replace />} />
          <Route path="*" element={<Navigate to="/chat" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
