import React from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import { Landmark, Trash2 } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const SedeAzioniSuper = ({ sede, onCambio }) => {
  const navigate = useNavigate();
  const nazionale = async () => {
    if (!window.confirm(`Rendere "${sede.nome}" la Sede Nazionale?\n\nLa Sede Nazionale attuale tornerà una concessionaria normale.`)) return;
    try { await axios.post(`${API}/sedi/${sede.id}/marca-nazionale`); toast.success('Sede Nazionale aggiornata'); onCambio(); }
    catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
  };
  const elimina = async () => {
    if (!window.confirm(`Eliminare definitivamente "${sede.nome}"?`)) return;
    try { await axios.delete(`${API}/sedi/${sede.id}`); toast.success('Concessionaria eliminata'); navigate('/impostazioni'); }
    catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
  };
  if (sede.is_nazionale) return null;
  return (
    <div className="flex gap-2">
      <button onClick={nazionale} className="inline-flex items-center gap-1.5 px-3 py-2 text-sm rounded-md border border-amber-300 text-amber-800 hover:bg-amber-50 transition-colors" data-testid="marca-nazionale-btn"><Landmark size={15} /> Rendi Nazionale</button>
      <button onClick={elimina} className="inline-flex items-center gap-1.5 px-3 py-2 text-sm rounded-md border border-red-200 text-red-700 hover:bg-red-50 transition-colors" data-testid="elimina-sede-btn"><Trash2 size={15} /> Elimina</button>
    </div>
  );
};
