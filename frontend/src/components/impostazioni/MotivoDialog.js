import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { Campo, inputCls } from '../SedeEmailConfig';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const MotivoDialog = ({ open, onOpenChange, motivo, sedeId, onSalvato }) => {
  const [f, setF] = useState({ nome: '', descrizione: '', richiede_note: false, tutte: false });
  useEffect(() => {
    if (open) setF(motivo
      ? { nome: motivo.nome, descrizione: motivo.descrizione || '', richiede_note: !!motivo.richiede_note, tutte: !motivo.sede_ids?.length }
      : { nome: '', descrizione: '', richiede_note: false, tutte: false });
  }, [open, motivo]);

  const salva = async (e) => {
    e.preventDefault();
    const sede_ids = f.tutte ? [] : (motivo?.sede_ids?.length ? motivo.sede_ids : [sedeId]);
    const body = { nome: f.nome.trim(), descrizione: f.descrizione || null, richiede_note: f.richiede_note, sede_ids };
    try {
      if (motivo) await axios.put(`${API}/motivi-rimborso/${motivo.id}`, body);
      else await axios.post(`${API}/motivi-rimborso`, body);
      toast.success('Motivo salvato');
      onOpenChange(false);
      onSalvato();
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore durante il salvataggio'); }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid="motivo-dialog">
        <DialogHeader><DialogTitle>{motivo ? 'Modifica motivo' : 'Nuovo motivo di rimborso'}</DialogTitle></DialogHeader>
        <form onSubmit={salva} className="space-y-3">
          <Campo label="Nome *"><input required value={f.nome} onChange={(e) => setF({ ...f, nome: e.target.value })} placeholder="es. RSA, Sede, Corso…" className={inputCls} data-testid="motivo-nome-input" /></Campo>
          <Campo label="Descrizione"><input value={f.descrizione} onChange={(e) => setF({ ...f, descrizione: e.target.value })} className={inputCls} data-testid="motivo-descrizione-input" /></Campo>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={f.richiede_note} onChange={(e) => setF({ ...f, richiede_note: e.target.checked })} data-testid="motivo-note-checkbox" /> Note obbligatorie</label>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={f.tutte} onChange={(e) => setF({ ...f, tutte: e.target.checked })} data-testid="motivo-tutte-checkbox" /> Valido per tutte le concessionarie</label>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={() => onOpenChange(false)} className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md">Annulla</button>
            <button type="submit" className="px-4 py-2 text-sm bg-[#1E4D8C] hover:bg-[#163A6A] text-white rounded-md" data-testid="motivo-save-btn">Salva</button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};
