import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { UserPlus, Check, X } from 'lucide-react';
import { RUOLI, formatDate } from '../lib/utils';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const RegistrazioniInAttesa = ({ utenti, onChange }) => {
  const [busy, setBusy] = useState(null);
  if (!utenti.length) return null;

  const decidi = async (u, azione) => {
    if (azione === 'rifiuta' && !window.confirm(`Rifiutare la registrazione di ${u.nome} ${u.cognome}? L'account verrà eliminato.`)) return;
    setBusy(u.id);
    try {
      await axios.post(`${API}/users/${u.id}/${azione}`);
      toast.success(azione === 'approva' ? 'Registrazione approvata' : 'Registrazione rifiutata');
      onChange();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Operazione non riuscita');
    } finally {
      setBusy(null);
    }
  };

  return (
    <section className="bg-amber-50 border border-amber-200 rounded-lg p-4" data-testid="registrazioni-in-attesa">
      <h2 className="flex items-center gap-2 font-semibold text-amber-900 mb-3">
        <UserPlus size={18} /> Registrazioni da approvare ({utenti.length})
      </h2>
      <ul className="space-y-2">
        {utenti.map((u) => (
          <li key={u.id} className="bg-white border border-amber-100 rounded-md p-3 flex flex-col sm:flex-row sm:items-center gap-3" data-testid={`registrazione-${u.id}`}>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-gray-900">{u.nome} {u.cognome} <span className="text-xs text-gray-500">· {(u.ruoli || []).map((r) => RUOLI[r] || r).join(', ')}</span></p>
              <p className="text-sm text-gray-600 truncate">{u.email}{u.sede_nome ? ` · ${u.sede_nome}` : ''} · {formatDate(u.created_at)}</p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => decidi(u, 'approva')} disabled={busy === u.id} data-testid={`approva-registrazione-${u.id}`}
                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md bg-green-600 hover:bg-green-700 text-white text-sm font-medium transition-colors disabled:opacity-50">
                <Check size={16} /> Approva
              </button>
              <button onClick={() => decidi(u, 'rifiuta')} disabled={busy === u.id} data-testid={`rifiuta-registrazione-${u.id}`}
                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md border border-red-300 text-red-700 hover:bg-red-50 text-sm font-medium transition-colors disabled:opacity-50">
                <X size={16} /> Rifiuta
              </button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
};
