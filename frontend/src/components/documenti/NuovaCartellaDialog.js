import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { X } from 'lucide-react';
import { hasRole } from '../../lib/utils';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const NuovaCartellaDialog = ({ user, onClose, onCreated }) => {
  const isSuper = hasRole(user, 'superadmin');
  const isNazAdmin = !isSuper && !!user?.is_nazionale_member;
  const [nome, setNome] = useState('');
  const [ambito, setAmbito] = useState(isSuper ? 'tutte' : 'sede');
  const [sedi, setSedi] = useState([]);
  const [errore, setErrore] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (isSuper) axios.get(`${API}/sedi`).then((r) => setSedi(r.data));
  }, [isSuper]);

  const crea = async (e) => {
    e.preventDefault();
    setBusy(true); setErrore('');
    const payload = ambito === 'tutte' ? { nome, ambito: 'tutte' } : isSuper ? { nome, ambito: 'sede', sede_id: ambito } : { nome, ambito: 'sede' };
    try {
      await axios.post(`${API}/cartelle`, payload);
      onCreated();
    } catch (err) {
      const d = err.response?.data?.detail;
      setErrore(typeof d === 'string' ? d : 'Nome non valido');
    } finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" data-testid="nuova-cartella-dialog">
      <form onSubmit={crea} className="bg-white rounded-lg w-full max-w-md">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Nuova cartella</h2>
          <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nome cartella *</label>
            <input value={nome} onChange={(e) => setNome(e.target.value)} required maxLength={60}
              className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] outline-none" data-testid="nuova-cartella-nome-input" />
          </div>
          {(isSuper || isNazAdmin) && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Per chi è</label>
              <select value={ambito} onChange={(e) => setAmbito(e.target.value)} className="w-full border border-gray-300 rounded-md px-4 py-2" data-testid="nuova-cartella-ambito-select">
                <option value="tutte">Tutte le concessionarie</option>
                {isNazAdmin && <option value="sede">Solo Sede Nazionale</option>}
                {isSuper && sedi.map((s) => <option key={s.id} value={s.id}>Solo {s.nome}</option>)}
              </select>
            </div>
          )}
          {errore && <p className="text-sm text-red-600" data-testid="nuova-cartella-error">{errore}</p>}
        </div>
        <div className="flex justify-end gap-3 px-6 pb-6">
          <button type="button" onClick={onClose} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition-colors">Annulla</button>
          <button type="submit" disabled={busy} className="px-4 py-2 bg-[#1E4D8C] hover:bg-[#163A6A] text-white rounded-md transition-colors disabled:opacity-50" data-testid="nuova-cartella-submit">Crea</button>
        </div>
      </form>
    </div>
  );
};
