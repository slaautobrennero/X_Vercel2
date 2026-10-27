import React, { useCallback, useEffect, useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Send, Folder, AlertTriangle } from 'lucide-react';
import { inputCls } from '../SedeEmailConfig';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const OPZ_SEDE = [['no', 'Non inviare email'], ['si', 'Email a tutti gli iscritti della concessionaria']];
const OPZ_COMUNI = [['no', 'Non inviare email'], ['nazionale', 'Email solo agli iscritti del Nazionale'], ['tutte', 'Email agli iscritti di tutte le concessionarie']];

export const InviiAutomaticiCard = ({ sede }) => {
  const [cartelle, setCartelle] = useState([]);
  const [modalita, setModalita] = useState('nessuna');
  const carica = useCallback(() => {
    axios.get(`${API}/cartelle`).then((r) => setCartelle(r.data.filter((c) => c.gestibile && (c.sede_id === sede.id || (c.sede_id === null && sede.is_nazionale)))));
    axios.get(`${API}/sedi/${sede.id}/email-config`).then((r) => setModalita(r.data.modalita));
  }, [sede.id, sede.is_nazionale]);
  useEffect(() => { carica(); }, [carica]);

  const cambia = async (c, valore) => {
    try {
      await axios.put(`${API}/cartelle/${c.id}/invio-email`, { invio_email: valore });
      setCartelle((lista) => lista.map((x) => (x.id === c.id ? { ...x, invio_email: valore } : x)));
      toast.success(`Invio automatico aggiornato per "${c.nome}"`);
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4" data-testid="invii-automatici-card">
      <div>
        <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900"><Send size={18} /> Invii automatici dei documenti</h2>
        <p className="text-sm text-gray-600 mt-1">Scegli per quali cartelle, quando si carica un nuovo file, parte un'email agli iscritti. La notifica nel portale e sul telefono arriva sempre. Ogni iscritto può disattivare queste email dal suo Profilo.</p>
      </div>
      {modalita === 'nessuna' && (
        <p className="flex gap-2 text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-md p-3" data-testid="invii-avviso-email">
          <AlertTriangle size={16} className="shrink-0 mt-0.5" /> Questa concessionaria ha scelto "Nessuna email": le email non partiranno finché non imposti una casella nella scheda Email.
        </p>
      )}
      <ul className="divide-y divide-gray-100 border border-gray-100 rounded-md">
        {cartelle.map((c) => (
          <li key={c.id} className="flex flex-col sm:flex-row sm:items-center gap-2 px-3 py-2.5" data-testid={`invio-row-${c.id}`}>
            <span className="flex-1 flex items-center gap-2 text-sm font-medium text-gray-900">
              <Folder size={15} className="text-[#1E4D8C]" /> {c.nome}
              {c.sede_id === null && <span className="text-xs font-normal px-2 py-0.5 rounded bg-amber-100 text-amber-800">comune a tutte</span>}
              {!c.visibile && <span className="text-xs font-normal text-gray-500">(nascosta: nessun invio)</span>}
            </span>
            <select value={c.invio_email || 'no'} onChange={(e) => cambia(c, e.target.value)} className={`${inputCls} sm:w-80`} data-testid={`invio-select-${c.id}`}>
              {(c.sede_id === null ? OPZ_COMUNI : OPZ_SEDE).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </li>
        ))}
        {!cartelle.length && <li className="px-3 py-4 text-sm text-gray-500">Nessuna cartella: creale dalla pagina Documenti.</li>}
      </ul>
    </div>
  );
};
