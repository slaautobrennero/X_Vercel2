import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { formatDateTime } from '../lib/utils';
import axios from 'axios';
import { Bell, Check, CheckCheck, Trash2 } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function NotifichePage() {
  const [notifiche, setNotifiche] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNotifiche();
  }, []);

  const fetchNotifiche = async () => {
    try {
      const res = await axios.get(`${API}/notifiche`);
      setNotifiche(res.data);
    } catch (error) {
      console.error('Error fetching notifiche:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (id) => {
    try {
      await axios.put(`${API}/notifiche/${id}/letto`);
      setNotifiche(prev => prev.map(n => n.id === id ? { ...n, letto: true } : n));
    } catch (error) {
      console.error('Error marking notifica as read:', error);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await axios.put(`${API}/notifiche/letto-tutte`);
      setNotifiche(prev => prev.map(n => ({ ...n, letto: true })));
    } catch (error) {
      console.error('Error marking all notifiche as read:', error);
    }
  };

  const unreadCount = notifiche.filter(n => !n.letto).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1E4D8C]"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="notifiche-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 font-['Manrope']">Notifiche</h1>
          <p className="text-gray-600 mt-1">
            {unreadCount > 0 ? `${unreadCount} non lette` : 'Tutte lette'}
          </p>
        </div>
        {unreadCount > 0 && (
          <button
            onClick={handleMarkAllAsRead}
            className="flex items-center gap-2 text-[#1E4D8C] hover:bg-blue-50 px-4 py-2 rounded-md transition-colors"
            data-testid="mark-all-read-btn"
          >
            <CheckCheck size={18} />
            Segna tutte come lette
          </button>
        )}
      </div>

      {notifiche.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
          <Bell size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">Nessuna notifica</p>
        </div>
      ) : (
        <div className="space-y-2">
          {notifiche.map(notifica => (
            <div
              key={notifica.id}
              className={`bg-white border rounded-lg p-4 transition-colors ${
                notifica.letto ? 'border-gray-200' : 'border-[#1E4D8C] bg-blue-50/30'
              }`}
              data-testid={`notifica-${notifica.id}`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                    notifica.letto ? 'bg-gray-300' : 'bg-[#1E4D8C]'
                  }`} />
                  <div>
                    <h3 className={`font-medium ${
                      notifica.letto ? 'text-gray-700' : 'text-gray-900'
                    }`}>{notifica.titolo}</h3>
                    <p className="text-sm text-gray-600 mt-1">{notifica.messaggio}</p>
                    <p className="text-xs text-gray-400 mt-2">{formatDateTime(notifica.created_at)}</p>
                  </div>
                </div>
                {!notifica.letto && (
                  <button
                    onClick={() => handleMarkAsRead(notifica.id)}
                    className="p-2 text-gray-400 hover:text-[#1E4D8C] hover:bg-blue-50 rounded-md transition-colors"
                    data-testid={`mark-read-${notifica.id}`}
                  >
                    <Check size={18} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
