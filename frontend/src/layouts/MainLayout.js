import React, { useState } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { RUOLI } from '../lib/utils';
import { 
  LayoutDashboard, 
  FileText, 
  Receipt, 
  Megaphone, 
  Bell, 
  Users, 
  Building2, 
  LogOut, 
  Menu, 
  ChevronDown,
  User,
  Settings,
  BarChart3
} from 'lucide-react';

export default function MainLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const canAccessRimborsi = ['delegato', 'segreteria', 'segretario', 'admin', 'superadmin', 'superuser'].includes(user?.ruolo);
  const canManageUsers = ['segretario', 'admin', 'superadmin', 'superuser'].includes(user?.ruolo);
  const canManageSedi = ['superadmin'].includes(user?.ruolo);
  const canManageMotivi = ['superadmin'].includes(user?.ruolo);
  const canViewReports = ['admin', 'superadmin', 'superuser'].includes(user?.ruolo);

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard, show: true },
    { path: '/bacheca', label: 'Bacheca', icon: Megaphone, show: true },
    { path: '/documenti', label: 'Documenti', icon: FileText, show: true },
    { path: '/rimborsi', label: 'Rimborsi', icon: Receipt, show: canAccessRimborsi },
    { path: '/report', label: 'Report', icon: BarChart3, show: canViewReports },
    { path: '/notifiche', label: 'Notifiche', icon: Bell, show: true },
    { path: '/utenti', label: 'Utenti', icon: Users, show: canManageUsers },
    { path: '/sedi', label: 'Sedi', icon: Building2, show: canManageSedi },
    { path: '/motivi-rimborso', label: 'Motivi Rimborso', icon: Settings, show: canManageMotivi },
  ];

  return (
    <div className="min-h-screen bg-gray-50 relative" data-testid="main-layout">
      {/* Background watermark logo SLA - Fisso in tutte le pagine interne */}
      <div 
        className="fixed inset-0 flex items-center justify-center opacity-[0.05] pointer-events-none z-0"
        style={{
          backgroundImage: 'url(https://customer-assets.emergentagent.com/job_portale-rimborsi/artifacts/jf6zpv8y_SfondoSLA.png)',
          backgroundSize: '70%',
          backgroundPosition: 'center center',
          backgroundRepeat: 'no-repeat'
        }}
      />

      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden" 
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`fixed top-0 left-0 h-full w-64 bg-white border-r border-gray-200 z-50 transform transition-transform duration-200 lg:translate-x-0 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-4 border-b border-gray-200">
            <Link to="/" className="flex items-center gap-3">
              <img 
                src="https://customer-assets.emergentagent.com/job_portale-rimborsi/artifacts/vtzwwkoa_SfondoSLA.png" 
                alt="SLA" 
                className="h-10"
              />
              <span className="font-bold text-[#1E4D8C] font-['Manrope']">SLA</span>
            </Link>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            {navItems.filter(item => item.show).map(item => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center gap-3 px-4 py-2.5 rounded-md text-sm font-medium transition-colors ${
                    isActive 
                      ? 'bg-blue-50 text-[#1E4D8C]' 
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                  data-testid={`nav-${item.path.slice(1) || 'dashboard'}`}
                >
                  <Icon size={20} />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* User info */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-full bg-[#1E4D8C] flex items-center justify-center text-white font-medium">
                {user?.nome?.[0]}{user?.cognome?.[0]}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{user?.nome} {user?.cognome}</p>
                <p className="text-xs text-gray-500">{RUOLI[user?.ruolo] || user?.ruolo}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-md transition-colors"
              data-testid="logout-btn"
            >
              <LogOut size={18} />
              Esci
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:ml-64">
        {/* Header */}
        <header className="sticky top-0 z-30 bg-white border-b border-gray-200">
          <div className="flex items-center justify-between px-4 py-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 text-gray-600 hover:bg-gray-100 rounded-md"
              data-testid="mobile-menu-btn"
            >
              <Menu size={24} />
            </button>

            <div className="flex-1 lg:flex-none" />

            <div className="flex items-center gap-4">
              {/* Notifications */}
              <Link to="/notifiche" className="p-2 text-gray-600 hover:bg-gray-100 rounded-md relative" data-testid="header-notifications-btn">
                <Bell size={20} />
              </Link>

              {/* User menu */}
              <div className="relative">
                <button 
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center gap-2 p-2 hover:bg-gray-100 rounded-md"
                  data-testid="user-menu-btn"
                >
                  <div className="w-8 h-8 rounded-full bg-[#1E4D8C] flex items-center justify-center text-white text-sm font-medium">
                    {user?.nome?.[0]}{user?.cognome?.[0]}
                  </div>
                  <ChevronDown size={16} className="text-gray-500 hidden sm:block" />
                </button>

                {userMenuOpen && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setUserMenuOpen(false)} />
                    <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                      <div className="p-3 border-b border-gray-100">
                        <p className="text-sm font-medium text-gray-900">{user?.nome} {user?.cognome}</p>
                        <p className="text-xs text-gray-500">{user?.email}</p>
                      </div>
                      <div className="p-2">
                        <Link
                          to="/profilo"
                          onClick={() => setUserMenuOpen(false)}
                          className="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-md"
                          data-testid="profile-link"
                        >
                          <User size={16} />
                          Profilo
                        </Link>
                        <button
                          onClick={handleLogout}
                          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-md"
                        >
                          <LogOut size={16} />
                          Esci
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
