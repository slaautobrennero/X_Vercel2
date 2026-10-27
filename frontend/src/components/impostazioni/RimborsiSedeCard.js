import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Receipt } from 'lucide-react';
import { Campo, inputCls } from '../SedeEmailConfig';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const RimborsiSedeCard = ({ sede, onSalvato }) => {
  const [f, setF] = useState({});
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    setF({ nome: sede.nome, indirizzo: sede.indirizzo || '', tariffa_km: sede.tariffa_km ?? 0.35, rimborso_pasti: sede.rimborso_pasti ?? 15, rimborso_autostrada: !!sede.rimborso_autostrada });
  }, [sede]);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value });

  const salva = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await axios.put(`${API}/sedi/${sede.id}`, { ...f, tariffa_km: Number(f.tariffa_km) || 0, rimborso_pasti: Number(f.rimborso_pasti) || 0 });
      toast.success('Impostazioni salvate');
      onSalvato?.();
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore durante il salvataggio'); } finally { setBusy(false); }
  };

  return (
    <form onSubmit={salva} className="bg-white border border-gray-200 rounded-lg p-6 space-y-4" data-testid="rimborsi-sede-card">
      <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900"><Receipt size={18} /> Dati e tariffe rimborsi</h2>
      <div className="grid sm:grid-cols-2 gap-3">
        <Campo label="Nome concessionaria"><input required value={f.nome || ''} onChange={set('nome')} className={inputCls} data-testid="sede-nome-input" /></Campo>
        <Campo label="Indirizzo"><input value={f.indirizzo || ''} onChange={set('indirizzo')} className={inputCls} data-testid="sede-indirizzo-input" /></Campo>
        <Campo label="Tariffa al km (€)"><input type="number" step="0.01" min="0" value={f.tariffa_km ?? ''} onChange={set('tariffa_km')} className={inputCls} data-testid="sede-tariffa-input" /></Campo>
        <Campo label="Rimborso pasti massimo (€)"><input type="number" step="0.01" min="0" value={f.rimborso_pasti ?? ''} onChange={set('rimborso_pasti')} className={inputCls} data-testid="sede-pasti-input" /></Campo>
      </div>
      <label className="flex items-center gap-2 text-sm text-gray-800">
        <input type="checkbox" checked={!!f.rimborso_autostrada} onChange={set('rimborso_autostrada')} data-testid="sede-autostrada-checkbox" />
        Rimborso del pedaggio autostradale
      </label>
      <button type="submit" disabled={busy} className="px-4 py-2 rounded-md bg-[#1E4D8C] hover:bg-[#163A6A] text-white text-sm font-medium transition-colors disabled:opacity-50" data-testid="sede-rimborsi-save-btn">Salva</button>
    </form>
  );
};
