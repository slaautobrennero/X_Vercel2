import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { RUOLI, formatDate, formatCurrency, STATI_RIMBORSO } from '../lib/utils';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { 
  LayoutDashboard, 
  FileText, 
  Receipt, 
  Megaphone, 
  Bell,
  Clock,
  CheckCircle,
  XCircle,
  ArrowRight
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState({ annunci: 0, documenti: 0, rimborsi: 0, notifiche: 0 });
  const [recentAnnunci, setRecentAnnunci] = useState([]);
  const [recentRimborsi, setRecentRimborsi] = useState([]);
  const [loading, setLoading] = useState(true);

  const canAccessRimborsi = ['delegato', 'segreteria', 'segretario', 'cassiere', 'admin', 'superadmin', 'superuser'].includes(user?.ruolo);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [annunciRes, documentiRes, notificheRes] = await Promise.all([
          axios.get(`${API}/annunci`),
          axios.get(`${API}/documenti`),
          axios.get(`${API}/notifiche`)
        ]);

        setRecentAnnunci(annunciRes.data.slice(0, 3));
        setStats(prev => ({
          ...prev,
          annunci: annunciRes.data.length,
          documenti: documentiRes.data.length,
          notifiche: notificheRes.data.filter(n => !n.letto).length
        }));

        if (canAccessRimborsi) {
          const rimborsiRes = await axios.get(`${API}/rimborsi`);
          setRecentRimborsi(rimborsiRes.data.slice(0, 5));
          setStats(prev => ({ ...prev, rimborsi: rimborsiRes.data.length }));
        }
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [canAccessRimborsi]);

  const StatCard = ({ icon: Icon, label, value, color, to }) => (
    <Link 
      to={to} 
      className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow"
      data-testid={`stat-card-${label.toLowerCase()}`}
    >
      <div className="flex items-center gap-4">
        <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${color}`}>
          <Icon size={24} className="text-white" />
        </div>
        <div>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          <p className="text-sm text-gray-500">{label}</p>
        </div>
      </div>
    </Link>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1E4D8C]"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8" data-testid="dashboard-page">
      {/* Welcome */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 font-['Manrope']">Benvenuto, {user?.nome}!</h1>
        <p className="text-gray-600 mt-1">
          {user?.sede_nome && <span>{user.sede_nome} • </span>}
          {RUOLI[user?.ruolo] || user?.ruolo}
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Megaphone} label="Annunci" value={stats.annunci} color="bg-blue-500" to="/bacheca" />
        <StatCard icon={FileText} label="Documenti" value={stats.documenti} color="bg-green-500" to="/documenti" />
        {canAccessRimborsi && (
          <StatCard icon={Receipt} label="Rimborsi" value={stats.rimborsi} color="bg-purple-500" to="/rimborsi" />
        )}
        <StatCard icon={Bell} label="Notifiche" value={stats.notifiche} color="bg-orange-500" to="/notifiche" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Annunci */}
        <div className="bg-white border border-gray-200 rounded-lg">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Ultimi Annunci</h2>
            <Link to="/bacheca" className="text-sm text-[#1E4D8C] hover:underline flex items-center gap-1">
              Vedi tutti <ArrowRight size={14} />
            </Link>
          </div>
          <div className="divide-y divide-gray-100">
            {recentAnnunci.length === 0 ? (
              <p className="p-6 text-gray-500 text-center">Nessun annuncio</p>
            ) : (
              recentAnnunci.map(annuncio => (
                <div key={annuncio.id} className="p-4 hover:bg-gray-50">
                  <h3 className="font-medium text-gray-900">{annuncio.titolo}</h3>
                  <p className="text-sm text-gray-600 mt-1 line-clamp-2">{annuncio.contenuto}</p>
                  <p className="text-xs text-gray-400 mt-2">{formatDate(annuncio.created_at)}</p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent Rimborsi */}
        {canAccessRimborsi && (
          <div className="bg-white border border-gray-200 rounded-lg">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Ultimi Rimborsi</h2>
              <Link to="/rimborsi" className="text-sm text-[#1E4D8C] hover:underline flex items-center gap-1">
                Vedi tutti <ArrowRight size={14} />
              </Link>
            </div>
            <div className="divide-y divide-gray-100">
              {recentRimborsi.length === 0 ? (
                <p className="p-6 text-gray-500 text-center">Nessun rimborso</p>
              ) : (
                recentRimborsi.map(rimborso => (
                  <div key={rimborso.id} className="p-4 hover:bg-gray-50 flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">{formatDate(rimborso.data)}</p>
                      <p className="text-sm text-gray-600">{rimborso.motivo_nome || 'N/A'}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-gray-900">{formatCurrency(rimborso.importo_totale)}</p>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        rimborso.stato === 'pagato' ? 'bg-green-100 text-green-800' :
                        rimborso.stato === 'approvato' ? 'bg-blue-100 text-blue-800' :
                        rimborso.stato === 'rifiutato' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {STATI_RIMBORSO[rimborso.stato]?.label || rimborso.stato}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
