import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Mail } from 'lucide-react';
import { hasRole } from '../lib/utils';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const SedeEmailContatto = ({ user }) => {
  const isSuper = hasRole(user, 'superadmin');
  const [sedi, setSedi] = useState([]);
  const [sedeId, setSedeId] = useState(user?.sede_id || '');
  const [email, setEmail] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    axios.get(`${API}/sedi`).then((r) => {
      setSedi(r.data);
      const id = user?.sede_id || r.data[0]?.id || '';
      setSedeId(id);
      setEmail(r.data.find((s) => s.id === id)?.email_contatto || '');
    });
  }, [user]);

  const cambiaSede = (id) => {
    setSedeId(id);
    setEmail(sedi.find((s) => s.id === id)?.email_contatto || '');
  };

  const salva = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await axios.put(`${API}/sedi/${sedeId}/email-contatto`, { email_contatto: email.trim() || null });
      setSedi((prev) => prev.map((s) => (s.id === sedeId ? { ...s, email_contatto: email.trim() || null } : s)));
      toast.success('Email della concessionaria salvata');
    } catch (err) {
      const d = err.response?.data?.detail;
      toast.error(typeof d === 'string' ? d : 'Email non valida');
    } finally { setBusy(false); }
  };

  if (!sedeId) return null;
  return (
    <form onSubmit={salva} className="bg-white border border-gray-200 rounded-lg p-6 space-y-3" data-testid="sede-email-contatto">
      <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900"><Mail size={18} /> Email della concessionaria</h2>
      <p className="text-sm text-gray-600">Se un utente risponde a un'email del portale, la risposta arriva a questo indirizzo.</p>
      {isSuper && (
        <select value={sedeId} onChange={(e) => cambiaSede(e.target.value)} className="w-full border border-gray-300 rounded-md px-4 py-2" data-testid="sede-email-select">
          {sedi.map((s) => <option key={s.id} value={s.id}>{s.nome}</option>)}
        </select>
      )}
      <div className="flex flex-col sm:flex-row gap-2">
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="segreteria@esempio.it"
          className="flex-1 border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] outline-none" data-testid="sede-email-input" />
        <button type="submit" disabled={busy} className="px-4 py-2 rounded-md bg-[#1E4D8C] hover:bg-[#163A6A] text-white font-medium transition-colors disabled:opacity-50" data-testid="sede-email-save-btn">Salva</button>
      </div>
    </form>
  );
};
