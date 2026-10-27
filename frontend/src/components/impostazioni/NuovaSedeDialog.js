import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { Campo, inputCls } from '../SedeEmailConfig';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const VUOTA = { nome: '', codice: '', indirizzo: '', tariffa_km: 0.35, rimborso_pasti: 15, rimborso_autostrada: true };

export const NuovaSedeDialog = ({ open, onOpenChange, onCreata }) => {
  const [f, setF] = useState(VUOTA);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value });

  const salva = async (e) => {
    e.preventDefault();
    try {
      const r = await axios.post(`${API}/sedi`, { ...f, codice: f.codice.toUpperCase().trim(), tariffa_km: Number(f.tariffa_km) || 0, rimborso_pasti: Number(f.rimborso_pasti) || 0 });
      toast.success('Concessionaria creata');
      setF(VUOTA);
      onOpenChange(false);
      onCreata(r.data);
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore durante il salvataggio'); }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid="nuova-sede-dialog">
        <DialogHeader><DialogTitle>Nuova concessionaria</DialogTitle></DialogHeader>
        <form onSubmit={salva} className="space-y-3">
          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-2"><Campo label="Nome *"><input required value={f.nome} onChange={set('nome')} className={inputCls} data-testid="nuova-sede-nome" /></Campo></div>
            <Campo label="Codice *"><input required value={f.codice} onChange={set('codice')} placeholder="A22" className={inputCls} data-testid="nuova-sede-codice" /></Campo>
          </div>
          <Campo label="Indirizzo"><input value={f.indirizzo} onChange={set('indirizzo')} className={inputCls} data-testid="nuova-sede-indirizzo" /></Campo>
          <div className="grid grid-cols-2 gap-3">
            <Campo label="Tariffa al km (€)"><input type="number" step="0.01" min="0" value={f.tariffa_km} onChange={set('tariffa_km')} className={inputCls} data-testid="nuova-sede-tariffa" /></Campo>
            <Campo label="Rimborso pasti (€)"><input type="number" step="0.01" min="0" value={f.rimborso_pasti} onChange={set('rimborso_pasti')} className={inputCls} data-testid="nuova-sede-pasti" /></Campo>
          </div>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={f.rimborso_autostrada} onChange={set('rimborso_autostrada')} /> Rimborso pedaggio autostradale</label>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={() => onOpenChange(false)} className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md">Annulla</button>
            <button type="submit" className="px-4 py-2 text-sm bg-[#1E4D8C] hover:bg-[#163A6A] text-white rounded-md" data-testid="nuova-sede-save-btn">Crea</button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};
