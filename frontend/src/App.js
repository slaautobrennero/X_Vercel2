/**
 * ==============================================
 * SLA PORTALE - Frontend React App
 * ==============================================
 * 
 * Applicazione frontend per il portale rimborsi del Sindacato Lavoratori Autostradali.
 * 
 * Funzionalità principali:
 * - Autenticazione JWT multi-ruolo
 * - Dashboard personalizzata per ogni ruolo
 * - Gestione rimborsi con calcolo KM automatico
 * - Bacheca comunicati e documenti
 * - Notifiche in-app
 * - Export PDF/Excel rendiconti
 * 
 * Ruoli disponibili:
 * - superadmin: Accesso totale multi-sede
 * - superuser: Visualizzazione globale
 * - admin: Gestione propria sede
 * - segretario/segreteria: Gestione sede e documenti
 * - delegato: Richiesta rimborsi
 * - iscritto: Solo bacheca e documenti (sola lettura)
 * 
 * Stack Tecnologico:
 * - React 18 + React Router v6
 * - TailwindCSS per styling
 * - Axios per API calls
 * - Context API per state management
 * 
 * ==============================================
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import './App.css';

// Pages - Pagine dell'applicazione
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

// Layout - Layout principale con sidebar
import MainLayout from './layouts/MainLayout';

/**
 * ProtectedRoute Component
 * Protegge le route che richiedono autenticazione
 * 
 * @param {React.Node} children - Componente da proteggere
 * @param {string[]} allowedRoles - Ruoli autorizzati (opzionale)
 */
function ProtectedRoute({ children, allowedRoles }) {
  const { user, loading } = useAuth();

  // Show loading spinner during auth check
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#1E4D8C]"></div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Check role permissions
  if (allowedRoles && !allowedRoles.includes(user.ruolo)) {
    return <Navigate to="/" replace />;
  }

  return children;
}

/**
 * PublicRoute Component
 * Route accessibili solo agli utenti non autenticati (login/register)
 */
function PublicRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#1E4D8C]"></div>
      </div>
    );
  }

  // Redirect to dashboard if already logged in
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
          <ProtectedRoute allowedRoles={['delegato', 'segreteria', 'segretario', 'cassiere', 'admin', 'superadmin', 'superuser']}>
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
          <ProtectedRoute allowedRoles={['admin', 'cassiere', 'superadmin', 'superuser']}>
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
