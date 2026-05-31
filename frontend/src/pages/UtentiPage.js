import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { RUOLI, RUOLO_BADGE_COLOR, formatDate, hasRole, hasAnyRole, getUserRoles } from '../lib/utils';
import axios from 'axios';
import { Users, Search, Shield, KeyRound, Copy, X, Check, Power, Trash2, AlertTriangle } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function UtentiPage() {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [editingRoles, setEditingRoles] = useState([]);  // ruoli selezionati nel modal
  const [savingRoles, setSavingRoles] = useState(false);
  const [resetUser, setResetUser] = useState(null);
  const [resetResult, setResetResult] = useState(null);
  const [resetLoading, setResetLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  // Stato disattiva/cancella
  const [toggleUser, setToggleUser] = useState(null);
  const [toggleLoading, setToggleLoading] = useState(false);
  const [deleteUser, setDeleteUser] = useState(null);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [deleteLoading, setDeleteLoading] = useState(false);

  const isSuperAdmin = hasRole(user, 'superadmin');
  const canResetPassword = hasAnyRole(user, ['admin', 'segretario', 'superadmin']);
  const canToggleDisabled = hasAnyRole(user, ['admin', 'segretario', 'superadmin']);

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

  const openRoleEditor = (u) => {
    setSelectedUser(u);
    setEditingRoles(getUserRoles(u));
  };

  const toggleEditingRole = (role) => {
    setEditingRoles(prev => {
      const has = prev.includes(role);
      if (role === 'iscritto') {
        // iscritto è esclusivo
        return has ? [] : ['iscritto'];
      }
      // se sto aggiungendo un altro ruolo, rimuovo iscritto
      const cleaned = prev.filter(r => r !== 'iscritto');
      return has ? cleaned.filter(r => r !== role) : [...cleaned, role];
    });
  };

  const handleSaveRoles = async () => {
    if (!selectedUser || editingRoles.length === 0) {
      alert('Seleziona almeno un ruolo');
      return;
    }
    setSavingRoles(true);
    try {
      await axios.put(`${API}/users/${selectedUser.id}/ruolo`, { ruoli: editingRoles });
      await fetchUsers();
      setSelectedUser(null);
      setEditingRoles([]);
    } catch (error) {
      console.error('Error updating roles:', error);
      alert(error.response?.data?.detail || 'Errore durante l\'aggiornamento');
    } finally {
      setSavingRoles(false);
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

  const handleToggleDisabled = async () => {
    if (!toggleUser) return;
    setToggleLoading(true);
    try {
      await axios.put(`${API}/users/${toggleUser.id}/toggle-disabled`, {
        disabled: !toggleUser.disabled
      });
      fetchUsers();
      setToggleUser(null);
    } catch (error) {
      alert(error.response?.data?.detail || 'Errore durante l\'operazione');
    } finally {
      setToggleLoading(false);
    }
  };

  const handleDeleteUser = async () => {
    if (!deleteUser || deleteConfirmText !== 'ELIMINA') return;
    setDeleteLoading(true);
    try {
      await axios.delete(`${API}/users/${deleteUser.id}`);
      fetchUsers();
      setDeleteUser(null);
      setDeleteConfirmText('');
    } catch (error) {
      alert(error.response?.data?.detail || 'Errore durante la cancellazione');
    } finally {
      setDeleteLoading(false);
    }
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
                  <tr key={u.id} className={`hover:bg-gray-50 ${u.disabled ? 'opacity-60 bg-gray-50' : ''}`} data-testid={`user-row-${u.id}`}>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium ${u.disabled ? 'bg-gray-400' : 'bg-[#1E4D8C]'}`}>
                          {u.nome?.[0]}{u.cognome?.[0]}
                        </div>
                        <div>
                          <span className="font-medium text-gray-900">{u.nome} {u.cognome}</span>
                          {u.disabled && (
                            <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
                              Disattivato
                            </span>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{u.email}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {(u.ruoli || [u.ruolo]).filter(Boolean).map(r => (
                          <span
                            key={r}
                            className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${RUOLO_BADGE_COLOR[r] || 'bg-gray-100 text-gray-800'}`}
                          >
                            {RUOLI[r] || r}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{u.sede_nome || '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{formatDate(u.created_at)}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => openRoleEditor(u)}
                          className="p-2 text-gray-600 hover:text-[#1E4D8C] hover:bg-blue-50 rounded-md transition-colors"
                          title="Modifica ruoli"
                          data-testid={`edit-user-${u.id}`}
                        >
                          <Shield size={18} />
                        </button>
                        {canResetPassword && !((u.ruoli || [u.ruolo]).some(r => ['superadmin', 'superuser'].includes(r))) && u.id !== user?.id && (
                          <button
                            onClick={() => setResetUser(u)}
                            className="p-2 text-gray-600 hover:text-orange-600 hover:bg-orange-50 rounded-md transition-colors"
                            title="Reset password"
                            data-testid={`reset-password-${u.id}`}
                          >
                            <KeyRound size={18} />
                          </button>
                        )}
                        {canToggleDisabled && !((u.ruoli || [u.ruolo]).some(r => ['superadmin', 'superuser'].includes(r))) && u.id !== user?.id && (
                          <button
                            onClick={() => setToggleUser(u)}
                            className={`p-2 rounded-md transition-colors ${
                              u.disabled
                                ? 'text-green-600 hover:bg-green-50'
                                : 'text-gray-600 hover:text-yellow-600 hover:bg-yellow-50'
                            }`}
                            title={u.disabled ? 'Riattiva utente' : 'Disattiva utente'}
                            data-testid={`toggle-disabled-${u.id}`}
                          >
                            <Power size={18} />
                          </button>
                        )}
                        {isSuperAdmin && u.id !== user?.id && (
                          <button
                            onClick={() => setDeleteUser(u)}
                            className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                            title="Cancella definitivamente"
                            data-testid={`delete-user-${u.id}`}
                          >
                            <Trash2 size={18} />
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

      {/* Role Edit Modal - MULTI-RUOLO */}
      {selectedUser && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-full max-w-md">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Modifica Ruoli</h2>
              <button
                onClick={() => { setSelectedUser(null); setEditingRoles([]); }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>
            <div className="p-6">
              <p className="text-gray-600 mb-1">
                {selectedUser.nome} {selectedUser.cognome}
              </p>
              <p className="text-sm text-gray-500 mb-4">{selectedUser.email}</p>

              <p className="text-xs text-gray-500 mb-3">
                Seleziona uno o più ruoli. <strong>"Iscritto"</strong> non può essere combinato con altri ruoli.
              </p>

              <div className="space-y-2">
                {Object.entries(RUOLI).filter(([key]) =>
                  isSuperAdmin || !['superadmin', 'superuser'].includes(key)
                ).map(([key, label]) => {
                  const checked = editingRoles.includes(key);
                  const disabled =
                    (key !== 'iscritto' && editingRoles.includes('iscritto')) ||
                    (key === 'iscritto' && editingRoles.length > 0 && !editingRoles.includes('iscritto'));
                  return (
                    <label
                      key={key}
                      className={`flex items-center gap-3 px-4 py-3 rounded-md border transition-colors cursor-pointer ${
                        checked
                          ? 'border-[#1E4D8C] bg-blue-50'
                          : disabled
                            ? 'border-gray-100 bg-gray-50 opacity-50 cursor-not-allowed'
                            : 'border-gray-200 hover:border-[#1E4D8C] hover:bg-blue-50'
                      }`}
                      data-testid={`role-option-${key}`}
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        disabled={disabled}
                        onChange={() => toggleEditingRole(key)}
                        className="w-4 h-4 rounded border-gray-300 text-[#1E4D8C] focus:ring-[#1E4D8C]"
                        data-testid={`role-checkbox-${key}`}
                      />
                      <span className={`flex-1 text-sm font-medium ${RUOLO_BADGE_COLOR[key] || 'text-gray-700'} bg-transparent`}>
                        {label}
                      </span>
                    </label>
                  );
                })}
              </div>

              <div className="flex gap-2 mt-6">
                <button
                  onClick={() => { setSelectedUser(null); setEditingRoles([]); }}
                  className="flex-1 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
                  data-testid="cancel-roles-btn"
                >
                  Annulla
                </button>
                <button
                  onClick={handleSaveRoles}
                  disabled={savingRoles || editingRoles.length === 0}
                  className="flex-1 px-4 py-2 bg-[#1E4D8C] text-white rounded-md hover:bg-[#1A4378] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  data-testid="save-roles-btn"
                >
                  {savingRoles ? 'Salvataggio...' : 'Salva ruoli'}
                </button>
              </div>
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
      {/* Toggle Disable Modal */}
      {toggleUser && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <div className="flex items-center gap-2">
                <Power size={20} className={toggleUser.disabled ? 'text-green-600' : 'text-yellow-600'} />
                <h2 className="text-lg font-semibold text-gray-900">
                  {toggleUser.disabled ? 'Riattiva utente' : 'Disattiva utente'}
                </h2>
              </div>
              <button onClick={() => setToggleUser(null)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <div className="p-6">
              <div className="bg-gray-50 rounded-md p-3 mb-4">
                <p className="font-medium text-gray-900">{toggleUser.nome} {toggleUser.cognome}</p>
                <p className="text-sm text-gray-600">{toggleUser.email}</p>
              </div>
              {toggleUser.disabled ? (
                <p className="text-sm text-gray-700 mb-4">
                  Riattivando l'utente potrà nuovamente effettuare il login e usare il portale.
                </p>
              ) : (
                <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 text-sm text-yellow-800 mb-4">
                  L'utente disattivato non potrà più effettuare il login. I suoi dati e rimborsi storici resteranno intatti. Operazione reversibile.
                </div>
              )}
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setToggleUser(null)}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
                >
                  Annulla
                </button>
                <button
                  onClick={handleToggleDisabled}
                  disabled={toggleLoading}
                  className={`px-4 py-2 text-white rounded-md transition-colors disabled:opacity-50 ${
                    toggleUser.disabled
                      ? 'bg-green-600 hover:bg-green-700'
                      : 'bg-yellow-600 hover:bg-yellow-700'
                  }`}
                  data-testid="confirm-toggle-btn"
                >
                  {toggleLoading ? 'Operazione...' : (toggleUser.disabled ? 'Riattiva' : 'Disattiva')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete User Modal (solo SuperAdmin) */}
      {deleteUser && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <div className="flex items-center gap-2">
                <AlertTriangle size={20} className="text-red-600" />
                <h2 className="text-lg font-semibold text-gray-900">Cancella utente definitivamente</h2>
              </div>
              <button onClick={() => { setDeleteUser(null); setDeleteConfirmText(''); }} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <div className="p-6">
              <div className="bg-gray-50 rounded-md p-3 mb-4">
                <p className="font-medium text-gray-900">{deleteUser.nome} {deleteUser.cognome}</p>
                <p className="text-sm text-gray-600">{deleteUser.email}</p>
              </div>
              <div className="bg-red-50 border border-red-200 rounded-md p-3 text-sm text-red-800 mb-4">
                <p className="font-medium mb-2">⚠️ Operazione irreversibile</p>
                <ul className="list-disc list-inside space-y-1 text-xs">
                  <li>L'utente sarà cancellato definitivamente dal sistema</li>
                  <li>I rimborsi e annunci storici resteranno con dicitura "[utente eliminato]"</li>
                  <li>Le notifiche personali saranno eliminate</li>
                  <li>Per disattivare temporaneamente usa l'icona Power invece</li>
                </ul>
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Per confermare scrivi <code className="bg-gray-100 px-1 rounded font-mono">ELIMINA</code> qui sotto:
                </label>
                <input
                  type="text"
                  value={deleteConfirmText}
                  onChange={(e) => setDeleteConfirmText(e.target.value)}
                  placeholder="ELIMINA"
                  className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-red-500 focus:ring-1 focus:ring-red-500 outline-none"
                  data-testid="delete-confirm-input"
                />
              </div>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => { setDeleteUser(null); setDeleteConfirmText(''); }}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
                >
                  Annulla
                </button>
                <button
                  onClick={handleDeleteUser}
                  disabled={deleteLoading || deleteConfirmText !== 'ELIMINA'}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  data-testid="confirm-delete-btn"
                >
                  {deleteLoading ? 'Cancellazione...' : 'Cancella definitivamente'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
