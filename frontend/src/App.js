import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import './App.css';

// Pages
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import BachecaPage from './pages/BachecaPage';
import DocumentiPage from './pages/DocumentiPage';
import RimborsiPage from './pages/RimborsiPage';
import NotifichePage from './pages/NotifichePage';
import UtentiPage from './pages/UtentiPage';
import SediPage from './pages/SediPage';
import ProfiloPage from './pages/ProfiloPage';
import MotiviRimborsoPage from './pages/MotiviRimborsoPage';
import ReportPage from './pages/ReportPage';

// Layout
import MainLayout from './layouts/MainLayout';

function ProtectedRoute({ children, allowedRoles }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#1E4D8C]"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.ruolo)) {
    return <Navigate to="/" replace />;
  }

  return children;
}

function PublicRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#1E4D8C]"></div>
      </div>
    );
  }

  if (user) {
    return <Navigate to="/" replace />;
  }

  return children;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={
        <PublicRoute>
          <LoginPage />
        </PublicRoute>
      } />
      <Route path="/register" element={
        <PublicRoute>
          <RegisterPage />
        </PublicRoute>
      } />

      {/* Protected Routes */}
      <Route path="/" element={
        <ProtectedRoute>
          <MainLayout />
        </ProtectedRoute>
      }>
        <Route index element={<DashboardPage />} />
        <Route path="bacheca" element={<BachecaPage />} />
        <Route path="documenti" element={<DocumentiPage />} />
        <Route path="rimborsi" element={
          <ProtectedRoute allowedRoles={['delegato', 'segreteria', 'segretario', 'admin', 'superadmin', 'superuser']}>
            <RimborsiPage />
          </ProtectedRoute>
        } />
        <Route path="notifiche" element={<NotifichePage />} />
        <Route path="utenti" element={
          <ProtectedRoute allowedRoles={['segretario', 'admin', 'superadmin', 'superuser']}>
            <UtentiPage />
          </ProtectedRoute>
        } />
        <Route path="sedi" element={
          <ProtectedRoute allowedRoles={['superadmin']}>
            <SediPage />
          </ProtectedRoute>
        } />
        <Route path="motivi-rimborso" element={
          <ProtectedRoute allowedRoles={['superadmin']}>
            <MotiviRimborsoPage />
          </ProtectedRoute>
        } />
        <Route path="report" element={
          <ProtectedRoute allowedRoles={['admin', 'superadmin', 'superuser']}>
            <ReportPage />
          </ProtectedRoute>
        } />
        <Route path="profilo" element={<ProfiloPage />} />
      </Route>

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
