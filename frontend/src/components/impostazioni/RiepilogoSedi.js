import React, { useCallback, useEffect, useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Plus, Landmark, ChevronRight } from 'lucide-react';
import { formatCurrency } from '../../lib/utils';
import { NuovaSedeDialog } from './NuovaSedeDialog';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const EMAIL = { nessuna: ['Nessuna', 'bg-gray-100 text-gray-600'], smtp: ['Casella propria', 'bg-green-50 text-green-700'], emergent: ['A pagamento', 'bg-blue-50 text-[#1E4D8C]'] };

export const RiepilogoSedi = () => {
  const [righe, setRighe] = useState([]);
  const [nuova, setNuova] = useState(false);
  const navigate = useNavigate();
  const carica = useCallback(() => { axios.get(`${API}/sedi/riepilogo-impostazioni`).then((r) => setRighe(r.data)); }, []);
  useEffect(() => { carica(); }, [carica]);

  return (
    <div className="space-y-6" data-testid="impostazioni-riepilogo">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 font-['Manrope']">Impostazioni concessionarie</h1>
          <p className="text-gray-600 mt-1">Rimborsi, email e invii automatici di ogni concessionaria. Clicca una riga per modificarla.</p>
        </div>
        <button onClick={() => setNuova(true)} className="inline-flex items-center gap-2 bg-[#1E4D8C] hover:bg-[#163A6A] text-white text-sm font-medium rounded-md px-4 py-2 transition-colors" data-testid="nuova-sede-btn">
          <Plus size={18} /> Nuova concessionaria
        </button>
      </div>
      <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              <th className="px-4 py-3">Concessionaria</th><th className="px-4 py-3">€/km</th><th className="px-4 py-3">Pasti</th>
              <th className="px-4 py-3">Autostrada</th><th className="px-4 py-3">Email</th><th className="px-4 py-3">Invii auto</th><th className="px-4 py-3">Utenti</th><th />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {righe.map((s) => (
              <tr key={s.id} onClick={() => navigate(`/impostazioni/${s.id}`)} className={`cursor-pointer transition-colors hover:bg-blue-50/40 ${s.is_nazionale ? 'bg-amber-50/50' : ''}`} data-testid={`riepilogo-row-${s.id}`}>
                <td className="px-4 py-3">
                  <span className="font-medium text-gray-900">{s.nome}</span> <span className="text-xs text-gray-500">{s.codice}</span>
                  {s.is_nazionale && <span className="ml-2 inline-flex items-center gap-1 bg-amber-100 text-amber-800 text-xs px-2 py-0.5 rounded"><Landmark size={11} /> Nazionale</span>}
                </td>
                <td className="px-4 py-3">{formatCurrency(s.tariffa_km)}</td>
                <td className="px-4 py-3">{formatCurrency(s.rimborso_pasti)}</td>
                <td className="px-4 py-3">{s.rimborso_autostrada ? 'Sì' : 'No'}</td>
                <td className="px-4 py-3"><span className={`text-xs px-2 py-0.5 rounded ${EMAIL[s.email_modalita]?.[1]}`}>{EMAIL[s.email_modalita]?.[0]}</span></td>
                <td className="px-4 py-3">{s.cartelle_con_invio ? `${s.cartelle_con_invio} cartelle` : '—'}</td>
                <td className="px-4 py-3">{s.utenti}</td>
                <td className="px-4 py-3 text-gray-400"><ChevronRight size={16} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <NuovaSedeDialog open={nuova} onOpenChange={setNuova} onCreata={(s) => navigate(`/impostazioni/${s.id}`)} />
    </div>
  );
};
