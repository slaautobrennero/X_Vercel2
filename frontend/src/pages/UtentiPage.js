import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { RUOLI, formatDate } from '../lib/utils';
import axios from 'axios';
import { Users, Search, Shield, KeyRound, Copy, X, Check } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function UtentiPage() {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [resetUser, setResetUser] = useState(null);
  const [resetResult, setResetResult] = useState(null);
  const [resetLoading, setResetLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const isSuperAdmin = user?.ruolo === 'superadmin';
  const canResetPassword = ['admin', 'segretario', 'superadmin'].includes(user?.ruolo);

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

  const handleResetPassword = async () => {
    if (!resetUser) return;
    setResetLoading(true);
    try {
      const res = await axios.post(`${API}/users/${resetUser.id}/reset-password`);
      setResetResult(res.data);
    } catch (error) {
      alert(error.response?.data?.detail || 'Errore durante il reset password');
      setResetUser(null);
    } finally {
      setResetLoading(false);
    }
  };

  const closeResetModal = () => {
    setResetUser(null);
    setResetResult(null);
    setCopied(false);
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      // Fallback per browser senza clipboard API
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
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
                        u.ruolo === 'cassiere' ? 'bg-emerald-100 text-emerald-800' :
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
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => setSelectedUser(u)}
                          className="p-2 text-gray-600 hover:text-[#1E4D8C] hover:bg-blue-50 rounded-md transition-colors"
                          title="Modifica ruolo"
                          data-testid={`edit-user-${u.id}`}
                        >
                          <Shield size={18} />
                        </button>
                        {canResetPassword && !['superadmin', 'superuser'].includes(u.ruolo) && u.id !== user?.id && (
                          <button
                            onClick={() => setResetUser(u)}
                            className="p-2 text-gray-600 hover:text-orange-600 hover:bg-orange-50 rounded-md transition-colors"
                            title="Reset password"
                            data-testid={`reset-password-${u.id}`}
                          >
                            <KeyRound size={18} />
                          </button>
                        )}
                      </div>
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
      {/* Reset Password Modal */}
      {resetUser && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <div className="flex items-center gap-2">
                <KeyRound size={20} className="text-orange-600" />
                <h2 className="text-lg font-semibold text-gray-900">Reset Password</h2>
              </div>
              <button onClick={closeResetModal} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <div className="p-6">
              {!resetResult ? (
                <>
                  <p className="text-gray-700 mb-2">
                    Sei sicuro di voler reimpostare la password di:
                  </p>
                  <div className="bg-gray-50 rounded-md p-3 mb-4">
                    <p className="font-medium text-gray-900">{resetUser.nome} {resetUser.cognome}</p>
                    <p className="text-sm text-gray-600">{resetUser.email}</p>
                  </div>
                  <div className="bg-orange-50 border border-orange-200 rounded-md p-3 text-sm text-orange-800 mb-4">
                    Verrà generata una password temporanea che dovrai comunicare all'utente. L'utente sarà obbligato a cambiarla al primo accesso.
                  </div>
                  <div className="flex justify-end gap-3">
                    <button
                      onClick={closeResetModal}
                      className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
                    >
                      Annulla
                    </button>
                    <button
                      onClick={handleResetPassword}
                      disabled={resetLoading}
                      className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-md transition-colors disabled:opacity-50"
                      data-testid="confirm-reset-btn"
                    >
                      {resetLoading ? 'Reset in corso...' : 'Conferma Reset'}
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <div className="bg-green-50 border border-green-200 rounded-md p-3 mb-4 text-sm text-green-800">
                    ✓ Password reimpostata con successo!
                  </div>
                  <p className="text-sm text-gray-700 mb-2">
                    <strong>Comunica questa password all'utente:</strong>
                  </p>
                  <div className="bg-gray-900 text-green-400 font-mono text-lg p-4 rounded-md mb-2 text-center select-all" data-testid="temp-password-display">
                    {resetResult.temporary_password}
                  </div>
                  <div className="flex gap-2 mb-4">
                    <button
                      onClick={() => copyToClipboard(resetResult.temporary_password)}
                      className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-[#1E4D8C] hover:bg-[#163A6A] text-white rounded-md text-sm transition-colors"
                      data-testid="copy-password-btn"
                    >
                      {copied ? <><Check size={16} /> Copiata!</> : <><Copy size={16} /> Copia password</>}
                    </button>
                  </div>
                  <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 text-xs text-yellow-800 mb-4">
                    ⚠️ Questa password è mostrata <strong>una sola volta</strong>. Salvala o copiala adesso. L'utente dovrà cambiarla al primo accesso.
                  </div>
                  <button
                    onClick={closeResetModal}
                    className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-800 text-white rounded-md transition-colors"
                  >
                    Chiudi
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
