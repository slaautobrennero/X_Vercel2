import React, { useCallback, useEffect, useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { ListChecks, Plus, Edit, Trash2 } from 'lucide-react';
import { MotivoDialog } from './MotivoDialog';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const MotiviSedeCard = ({ sedeId, isSuper }) => {
  const [motivi, setMotivi] = useState([]);
  const [dialog, setDialog] = useState({ open: false, motivo: null });
  const carica = useCallback(() => {
    axios.get(`${API}/motivi-rimborso`, { params: { sede_id: sedeId } }).then((r) => setMotivi(r.data));
  }, [sedeId]);
  useEffect(() => { carica(); }, [carica]);

  const elimina = async (m) => {
    const dove = m.sede_ids?.length ? 'da questa concessionaria' : 'da TUTTE le concessionarie';
    if (!window.confirm(`Eliminare il motivo "${m.nome}" ${dove}?`)) return;
    try { await axios.delete(`${API}/motivi-rimborso/${m.id}`); toast.success('Motivo eliminato'); carica(); }
    catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4" data-testid="motivi-sede-card">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900"><ListChecks size={18} /> Motivi del rimborso</h2>
          <p className="text-sm text-gray-600 mt-1">
            {isSuper ? 'Aggiungi i motivi richiesti dalla concessionaria. I motivi comuni valgono per tutte.' : 'Per aggiungere o cambiare un motivo contatta il SuperAdmin: così i report restano uguali per tutti.'}
          </p>
        </div>
        {isSuper && (
          <button onClick={() => setDialog({ open: true, motivo: null })} className="shrink-0 inline-flex items-center gap-1.5 px-3 py-2 rounded-md bg-[#1E4D8C] hover:bg-[#163A6A] text-white text-sm transition-colors" data-testid="nuovo-motivo-btn">
            <Plus size={16} /> Nuovo motivo
          </button>
        )}
      </div>
      <ul className="divide-y divide-gray-100 border border-gray-100 rounded-md">
        {motivi.map((m) => (
          <li key={m.id} className="flex items-center gap-3 px-3 py-2.5" data-testid={`motivo-row-${m.id}`}>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900">{m.nome}{m.richiede_note && <span className="ml-2 text-xs text-orange-700">note obbligatorie</span>}</p>
              {m.descrizione && <p className="text-xs text-gray-500 truncate">{m.descrizione}</p>}
            </div>
            <span className={`text-xs px-2 py-0.5 rounded ${m.sede_ids?.length ? 'bg-blue-50 text-[#1E4D8C]' : 'bg-gray-100 text-gray-600'}`}>
              {m.sede_ids?.length ? 'Solo questa' : 'Tutte'}
            </span>
            {isSuper && (
              <>
                <button onClick={() => setDialog({ open: true, motivo: m })} className="p-1.5 text-gray-400 hover:text-[#1E4D8C]" aria-label="Modifica" data-testid={`edit-motivo-${m.id}`}><Edit size={15} /></button>
                <button onClick={() => elimina(m)} className="p-1.5 text-gray-400 hover:text-red-600" aria-label="Elimina" data-testid={`delete-motivo-${m.id}`}><Trash2 size={15} /></button>
              </>
            )}
          </li>
        ))}
        {!motivi.length && <li className="px-3 py-4 text-sm text-gray-500">Nessun motivo configurato</li>}
      </ul>
      <MotivoDialog open={dialog.open} motivo={dialog.motivo} sedeId={sedeId} onOpenChange={(o) => setDialog((d) => ({ ...d, open: o }))} onSalvato={carica} />
    </div>
  );
};
