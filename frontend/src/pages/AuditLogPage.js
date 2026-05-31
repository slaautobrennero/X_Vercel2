import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { formatDateTime, hasAnyRole } from '../lib/utils';
import axios from 'axios';
import { History, Filter, User, FileText, Shield, Power, Trash2, KeyRound, Check, X as XIcon, CreditCard } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Etichette human-readable per le azioni
const ACTION_META = {
  'rimborso.approvato':   { label: 'Approvato',          color: 'bg-yellow-100 text-yellow-800', Icon: Check },
  'rimborso.rifiutato':   { label: 'Rifiutato',          color: 'bg-red-100 text-red-800',       Icon: XIcon },
  'rimborso.pay':         { label: 'Pagato',             color: 'bg-green-100 text-green-800',   Icon: CreditCard },
  'rimborso.pay_direct':  { label: 'Pagato diretto',     color: 'bg-green-100 text-green-800',   Icon: CreditCard },
  'user.reset_password':  { label: 'Reset password',     color: 'bg-orange-100 text-orange-800', Icon: KeyRound },
  'user.disable':         { label: 'Disattivato',        color: 'bg-yellow-100 text-yellow-800', Icon: Power },
  'user.enable':          { label: 'Riattivato',         color: 'bg-green-100 text-green-800',   Icon: Power },
  'user.delete':          { label: 'Cancellato',         color: 'bg-red-100 text-red-800',       Icon: Trash2 },
  'user.change_role':     { label: 'Cambio ruolo',       color: 'bg-blue-100 text-blue-800',     Icon: Shield },
};

const TARGET_FILTERS = [
  { value: '', label: 'Tutti' },
  { value: 'rimborso', label: 'Rimborsi' },
  { value: 'user', label: 'Utenti' },
];

function getActionMeta(action) {
  return ACTION_META[action] || { label: action, color: 'bg-gray-100 text-gray-700', Icon: FileText };
}

export default function AuditLogPage() {
  const { user } = useAuth();
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');

  const fetchLog = useCallback(async () => {
    setLoading(true);
    try {
      const params = filter ? { target_type: filter } : {};
      const res = await axios.get(`${API}/audit-log`, { params });
      setEntries(res.data || []);
    } catch (error) {
      console.error('Error fetching audit log:', error);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchLog();
  }, [fetchLog]);

  return (
    <div className="space-y-6" data-testid="audit-log-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 font-['Manrope']">Audit Log</h1>
          <p className="text-gray-600 mt-1">
            Storico azioni sensibili
            {!hasAnyRole(user, ['superadmin', 'superuser']) && ' (sede di appartenenza)'}
          </p>
        </div>
      </div>

      {/* Filtri */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Filter size={16} />
          <span className="font-medium">Tipo:</span>
        </div>
        {TARGET_FILTERS.map(f => (
          <button
            key={f.value || 'all'}
            onClick={() => setFilter(f.value)}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              filter === f.value
                ? 'bg-[#1E4D8C] text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
            data-testid={`audit-filter-${f.value || 'all'}`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Tabella */}
      {loading ? (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1E4D8C]"></div>
        </div>
      ) : entries.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
          <History size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">Nessuna azione registrata</p>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <th className="px-4 py-3">Quando</th>
                  <th className="px-4 py-3">Chi</th>
                  <th className="px-4 py-3">Azione</th>
                  <th className="px-4 py-3">Target</th>
                  <th className="px-4 py-3">Dettaglio</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {entries.map(e => {
                  const meta = getActionMeta(e.action);
                  const Icon = meta.Icon;
                  return (
                    <tr key={e.id} className="hover:bg-gray-50" data-testid={`audit-row-${e.id}`}>
                      <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">
                        {formatDateTime(e.created_at)}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <div className="flex items-center gap-2">
                          <User size={14} className="text-gray-400" />
                          <span className="font-medium text-gray-900">{e.actor_nome}</span>
                          <span className="text-xs text-gray-500">({e.actor_ruolo})</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${meta.color}`}>
                          <Icon size={12} />
                          {meta.label}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {e.target_label || `${e.target_type}#${(e.target_id || '').slice(-6)}`}
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-600">
                        {e.old_value && e.new_value && (
                          <span><span className="text-gray-500">{e.old_value}</span> → <span className="font-medium">{e.new_value}</span></span>
                        )}
                        {e.note && <div className="text-gray-500 mt-1">{e.note}</div>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// Componente compatto per mostrare lo storico di un singolo rimborso (modale)
export function RimborsoHistoryModal({ rimborsoId, onClose }) {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancel = false;
    async function load() {
      try {
        const res = await axios.get(`${API}/audit-log`, {
          params: { target_type: 'rimborso', target_id: rimborsoId, limit: 50 }
        });
        if (!cancel) setEntries(res.data || []);
      } catch (e) {
        console.error(e);
      } finally {
        if (!cancel) setLoading(false);
      }
    }
    load();
    return () => { cancel = true; };
  }, [rimborsoId]);

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg w-full max-w-lg max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 sticky top-0 bg-white">
          <div className="flex items-center gap-2">
            <History size={20} className="text-[#1E4D8C]" />
            <h2 className="text-lg font-semibold text-gray-900">Storico variazioni</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XIcon size={20} />
          </button>
        </div>
        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[#1E4D8C]"></div>
            </div>
          ) : entries.length === 0 ? (
            <p className="text-sm text-gray-500 italic text-center py-4">Nessuna variazione registrata</p>
          ) : (
            <ul className="space-y-3">
              {entries.map(e => {
                const meta = getActionMeta(e.action);
                const Icon = meta.Icon;
                return (
                  <li key={e.id} className="flex gap-3 pb-3 border-b border-gray-100 last:border-b-0" data-testid={`history-entry-${e.id}`}>
                    <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full flex-shrink-0 ${meta.color}`}>
                      <Icon size={14} />
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">
                        {meta.label}
                        {e.old_value && e.new_value && (
                          <span className="ml-2 text-xs text-gray-500 font-normal">
                            {e.old_value} → {e.new_value}
                          </span>
                        )}
                      </p>
                      <p className="text-xs text-gray-600 mt-0.5">
                        {e.actor_nome} <span className="text-gray-400">({e.actor_ruolo})</span>
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">{formatDateTime(e.created_at)}</p>
                      {e.note && <p className="text-xs text-gray-500 mt-1 italic">{e.note}</p>}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
