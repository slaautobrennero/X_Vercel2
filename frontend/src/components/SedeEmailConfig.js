import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Mail, Send } from 'lucide-react';
import { hasRole } from '../lib/utils';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const inputCls = 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:border-[#1E4D8C] outline-none';
const VUOTA = { modalita: 'nessuna', smtp_host: '', smtp_port: 587, smtp_tls: 'starttls', smtp_user: '', smtp_password: '', smtp_from: '' };

const Campo = ({ label, children }) => (
  <label className="block"><span className="block text-xs font-medium text-gray-700 mb-1">{label}</span>{children}</label>
);

const Opzione = ({ value, cfg, setCfg, titolo, desc, disabled }) => (
  <label className={`flex gap-3 p-3 border rounded-md cursor-pointer ${cfg.modalita === value ? 'border-[#1E4D8C] bg-blue-50/40' : 'border-gray-200'} ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}>
    <input type="radio" name="modalita" value={value} checked={cfg.modalita === value} disabled={disabled}
      onChange={() => setCfg({ ...cfg, modalita: value })} data-testid={`email-modalita-${value}`} />
    <span><span className="block text-sm font-medium text-gray-900">{titolo}</span><span className="block text-xs text-gray-600">{desc}</span></span>
  </label>
);

const SmtpCampi = ({ cfg, setCfg, passwordImpostata }) => {
  const set = (k) => (e) => setCfg({ ...cfg, [k]: e.target.value });
  const gmail = () => setCfg({ ...cfg, smtp_host: 'smtp.gmail.com', smtp_port: 587, smtp_tls: 'starttls' });
  return (
    <div className="space-y-3 border border-gray-200 rounded-md p-3">
      <button type="button" onClick={gmail} className="text-xs text-[#1E4D8C] hover:underline" data-testid="email-preset-gmail">Usa le impostazioni di Gmail</button>
      <div className="grid sm:grid-cols-3 gap-3">
        <div className="sm:col-span-2"><Campo label="Server (SMTP)"><input value={cfg.smtp_host} onChange={set('smtp_host')} placeholder="smtps.aruba.it" className={inputCls} data-testid="email-smtp-host" /></Campo></div>
        <Campo label="Porta"><input type="number" value={cfg.smtp_port} onChange={set('smtp_port')} className={inputCls} data-testid="email-smtp-port" /></Campo>
      </div>
      <Campo label="Sicurezza">
        <select value={cfg.smtp_tls} onChange={set('smtp_tls')} className={inputCls} data-testid="email-smtp-tls">
          <option value="starttls">STARTTLS (di solito porta 587)</option>
          <option value="ssl">SSL (di solito porta 465)</option>
        </select>
      </Campo>
      <div className="grid sm:grid-cols-2 gap-3">
        <Campo label="Utente (indirizzo email)"><input value={cfg.smtp_user} onChange={set('smtp_user')} className={inputCls} data-testid="email-smtp-user" /></Campo>
        <Campo label={passwordImpostata ? 'Password (lascia vuoto per non cambiarla)' : 'Password'}>
          <input type="password" value={cfg.smtp_password} onChange={set('smtp_password')} autoComplete="new-password" className={inputCls} data-testid="email-smtp-password" />
        </Campo>
      </div>
      <Campo label="Mittente (se diverso dall'utente)"><input value={cfg.smtp_from || ''} onChange={set('smtp_from')} className={inputCls} data-testid="email-smtp-from" /></Campo>
      <p className="text-xs text-gray-500">Con Gmail serve una "password per le app" (Account Google → Sicurezza → Verifica in due passaggi → Password per le app), non la password normale.</p>
    </div>
  );
};

export const SedeEmailConfig = ({ user }) => {
  const isSuper = hasRole(user, 'superadmin');
  const [sedi, setSedi] = useState([]);
  const [sedeId, setSedeId] = useState(user?.sede_id || '');
  const [cfg, setCfg] = useState(VUOTA);
  const [info, setInfo] = useState({ password_impostata: false, emergent_disponibile: false });
  const [contatto, setContatto] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    axios.get(`${API}/sedi`).then((r) => { setSedi(r.data); if (!sedeId) setSedeId(r.data[0]?.id || ''); });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!sedeId) return;
    setContatto(sedi.find((s) => s.id === sedeId)?.email_contatto || '');
    axios.get(`${API}/sedi/${sedeId}/email-config`).then((r) => {
      const { password_impostata, emergent_disponibile, ...rest } = r.data;
      setCfg({ ...VUOTA, ...rest, smtp_password: '' });
      setInfo({ password_impostata, emergent_disponibile });
    });
  }, [sedeId, sedi]);

  const errore = (err) => { const d = err.response?.data?.detail; toast.error(typeof d === 'string' ? d : 'Dati non validi'); };

  const salva = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const body = { ...cfg, smtp_port: Number(cfg.smtp_port) || null, smtp_from: cfg.smtp_from || null, smtp_password: cfg.smtp_password || null };
      const r = await axios.put(`${API}/sedi/${sedeId}/email-config`, body);
      await axios.put(`${API}/sedi/${sedeId}/email-contatto`, { email_contatto: contatto.trim() || null });
      setInfo((i) => ({ ...i, password_impostata: r.data.password_impostata }));
      setCfg((c) => ({ ...c, smtp_password: '' }));
      toast.success('Impostazioni email salvate');
    } catch (err) { errore(err); } finally { setBusy(false); }
  };

  const prova = async () => {
    setBusy(true);
    try { const r = await axios.post(`${API}/sedi/${sedeId}/email-config/test`); toast.success(r.data.message); }
    catch (err) { errore(err); } finally { setBusy(false); }
  };

  if (!sedeId) return null;
  return (
    <form onSubmit={salva} className="bg-white border border-gray-200 rounded-lg p-6 space-y-4" data-testid="sede-email-config">
      <div>
        <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900"><Mail size={18} /> Email della concessionaria</h2>
        <p className="text-sm text-gray-600 mt-1">Scegli come la tua concessionaria invia le email (password dimenticata, approvazioni, rimborsi, avvisi di sicurezza).</p>
      </div>
      {isSuper && (
        <select value={sedeId} onChange={(e) => setSedeId(e.target.value)} className={inputCls} data-testid="sede-email-select">
          {sedi.map((s) => <option key={s.id} value={s.id}>{s.nome}</option>)}
        </select>
      )}
      <div className="space-y-2">
        <Opzione value="nessuna" cfg={cfg} setCfg={setCfg} titolo="Nessuna email (gratis)" desc="Avvisi solo nel portale e sul telefono. La password dimenticata la reimposta la segreteria." />
        <Opzione value="smtp" cfg={cfg} setCfg={setCfg} titolo="Casella email propria o Gmail (gratis)" desc="Il portale invia dalla casella del vostro dominio o da un account Gmail." />
        <Opzione value="emergent" cfg={cfg} setCfg={setCfg} disabled={!info.emergent_disponibile} titolo="Servizio email a pagamento" desc={info.emergent_disponibile ? 'Nessuna configurazione, ogni email ha un costo.' : 'Non attivo su questo portale.'} />
      </div>
      {cfg.modalita === 'smtp' && <SmtpCampi cfg={cfg} setCfg={setCfg} passwordImpostata={info.password_impostata} />}
      {cfg.modalita !== 'nessuna' && (
        <Campo label="Email per le risposte (es. segreteria della concessionaria)">
          <input type="email" value={contatto} onChange={(e) => setContatto(e.target.value)} className={inputCls} data-testid="sede-email-input" />
        </Campo>
      )}
      <div className="flex flex-wrap gap-2">
        <button type="submit" disabled={busy} className="px-4 py-2 rounded-md bg-[#1E4D8C] hover:bg-[#163A6A] text-white text-sm font-medium transition-colors disabled:opacity-50" data-testid="sede-email-save-btn">Salva</button>
        {cfg.modalita !== 'nessuna' && (
          <button type="button" onClick={prova} disabled={busy} className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md border border-gray-300 text-sm text-gray-800 hover:bg-gray-50 transition-colors disabled:opacity-50" data-testid="sede-email-test-btn">
            <Send size={14} /> Invia email di prova
          </button>
        )}
      </div>
    </form>
  );
};
