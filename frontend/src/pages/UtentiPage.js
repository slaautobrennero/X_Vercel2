import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { RUOLI, formatDate } from '../lib/utils';
import axios from 'axios';
import { Users, Search, Edit, Shield } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function UtentiPage() {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);

  const isSuperAdmin = user?.ruolo === 'superadmin';

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const res = await axios.get(`${API}/users`);
      setUsers(res.data);
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateRole = async (userId, newRole) => {
    try {
      const formData = new FormData();
      formData.append('ruolo', newRole);
      await axios.put(`${API}/users/${userId}/ruolo`, formData);
      fetchUsers();
      setSelectedUser(null);
    } catch (error) {
      console.error('Error updating role:', error);
      alert(error.response?.data?.detail || 'Errore durante l\'aggiornamento');
    }
  };

  const filteredUsers = users.filter(u => 
    u.nome?.toLowerCase().includes(search.toLowerCase()) ||
    u.cognome?.toLowerCase().includes(search.toLowerCase()) ||
    u.email?.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1E4D8C]"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="utenti-page">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 font-['Manrope']">Utenti</h1>
        <p className="text-gray-600 mt-1">Gestione degli iscritti</p>
      </div>

      {/* Search */}
      <div className="relative">
        <Search size={20} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Cerca per nome, cognome o email..."
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
          data-testid="search-users-input"
        />
      </div>

      {/* Users Table */}
      {filteredUsers.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
          <Users size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">Nessun utente trovato</p>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <th className="px-4 py-3">Utente</th>
                  <th className="px-4 py-3">Email</th>
                  <th className="px-4 py-3">Ruolo</th>
                  <th className="px-4 py-3">Sede</th>
                  <th className="px-4 py-3">Registrato</th>
                  <th className="px-4 py-3">Azioni</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredUsers.map(u => (
                  <tr key={u.id} className="hover:bg-gray-50" data-testid={`user-row-${u.id}`}>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-[#1E4D8C] flex items-center justify-center text-white text-sm font-medium">
                          {u.nome?.[0]}{u.cognome?.[0]}
                        </div>
                        <span className="font-medium text-gray-900">{u.nome} {u.cognome}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{u.email}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        u.ruolo === 'superadmin' ? 'bg-purple-100 text-purple-800' :
                        u.ruolo === 'admin' ? 'bg-blue-100 text-blue-800' :
                        u.ruolo === 'segretario' ? 'bg-indigo-100 text-indigo-800' :
                        u.ruolo === 'segreteria' ? 'bg-cyan-100 text-cyan-800' :
                        u.ruolo === 'delegato' ? 'bg-green-100 text-green-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {RUOLI[u.ruolo] || u.ruolo}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{u.sede_nome || '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{formatDate(u.created_at)}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => setSelectedUser(u)}
                        className="p-2 text-gray-600 hover:text-[#1E4D8C] hover:bg-blue-50 rounded-md transition-colors"
                        data-testid={`edit-user-${u.id}`}
                      >
                        <Shield size={18} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Role Edit Modal */}
      {selectedUser && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-full max-w-md">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Modifica Ruolo</h2>
            </div>
            <div className="p-6">
              <p className="text-gray-600 mb-4">
                {selectedUser.nome} {selectedUser.cognome} ({selectedUser.email})
              </p>
              <div className="space-y-2">
                {Object.entries(RUOLI).filter(([key]) => 
                  isSuperAdmin || !['superadmin', 'superuser'].includes(key)
                ).map(([key, label]) => (
                  <button
                    key={key}
                    onClick={() => handleUpdateRole(selectedUser.id, key)}
                    className={`w-full text-left px-4 py-3 rounded-md border transition-colors ${
                      selectedUser.ruolo === key 
                        ? 'border-[#1E4D8C] bg-blue-50 text-[#1E4D8C]' 
                        : 'border-gray-200 hover:border-[#1E4D8C] hover:bg-blue-50'
                    }`}
                    data-testid={`role-option-${key}`}
                  >
                    {label}
                  </button>
                ))}
              </div>
              <button
                onClick={() => setSelectedUser(null)}
                className="w-full mt-4 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
              >
                Chiudi
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
