import React, { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { KeyRound, MailCheck } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const inputCls = 'w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none';
const btnCls = 'w-full bg-[#1E4D8C] hover:bg-[#163A6A] text-white font-medium rounded-md px-4 py-2.5 transition-colors disabled:opacity-50';

const Card = ({ icon: Icon, title, children, testid }) => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50 px-6" data-testid={testid}>
    <div className="bg-white border border-gray-200 rounded-xl p-8 max-w-md w-full">
      <div className="w-12 h-12 rounded-full bg-blue-50 text-[#1E4D8C] flex items-center justify-center mb-4"><Icon size={24} /></div>
      <h1 className="text-2xl font-bold text-gray-900 font-['Manrope'] mb-2">{title}</h1>
      {children}
      <Link to="/login" className="block text-center text-sm text-[#1E4D8C] hover:underline mt-6" data-testid="back-to-login-link">Torna all'accesso</Link>
    </div>
  </div>
);

export function PasswordDimenticataPage() {
  const [email, setEmail] = useState('');
  const [inviata, setInviata] = useState('');
  const [busy, setBusy] = useState(false);
  const [errore, setErrore] = useState('');

  const invia = async (e) => {
    e.preventDefault();
    setBusy(true); setErrore('');
    try {
      const r = await axios.post(`${API}/auth/forgot-password`, { email });
      setInviata(r.data.message);
    } catch (err) {
      setErrore(err.response?.data?.detail || 'Riprova tra qualche minuto');
    } finally { setBusy(false); }
  };

  return (
    <Card icon={inviata ? MailCheck : KeyRound} title="Password dimenticata" testid="forgot-password-page">
      {inviata ? (
        <p className="text-sm text-gray-600" data-testid="forgot-password-sent">{inviata} Controlla anche la cartella spam. Il link vale 30 minuti.</p>
      ) : (
        <form onSubmit={invia} className="space-y-4">
          <p className="text-sm text-gray-600">Scrivi l'email con cui sei registrato: ti mandiamo un link per scegliere una nuova password.</p>
          <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="nome@esempio.it" className={inputCls} data-testid="forgot-password-email-input" />
          {errore && <p className="text-sm text-red-600" data-testid="forgot-password-error">{typeof errore === 'string' ? errore : 'Email non valida'}</p>}
          <button type="submit" disabled={busy} className={btnCls} data-testid="forgot-password-submit">{busy ? 'Invio...' : 'Invia il link'}</button>
        </form>
      )}
    </Card>
  );
}

export function ResetPasswordPage() {
  const [params] = useSearchParams();
  const [pwd, setPwd] = useState('');
  const [pwd2, setPwd2] = useState('');
  const [esito, setEsito] = useState('');
  const [errore, setErrore] = useState('');
  const [busy, setBusy] = useState(false);

  const salva = async (e) => {
    e.preventDefault();
    if (pwd !== pwd2) { setErrore('Le due password non coincidono'); return; }
    setBusy(true); setErrore('');
    try {
      const r = await axios.post(`${API}/auth/reset-password`, { token: params.get('token') || '', new_password: pwd });
      setEsito(r.data.message);
    } catch (err) {
      const d = err.response?.data?.detail;
      setErrore(typeof d === 'string' ? d : 'Password non valida');
    } finally { setBusy(false); }
  };

  return (
    <Card icon={KeyRound} title="Nuova password" testid="reset-password-page">
      {esito ? (
        <p className="text-sm text-green-700" data-testid="reset-password-success">{esito}</p>
      ) : (
        <form onSubmit={salva} className="space-y-4">
          <p className="text-sm text-gray-600">Almeno 8 caratteri, con lettere, numeri e un simbolo.</p>
          <input type="password" required value={pwd} onChange={(e) => setPwd(e.target.value)} placeholder="Nuova password" className={inputCls} data-testid="reset-password-input" />
          <input type="password" required value={pwd2} onChange={(e) => setPwd2(e.target.value)} placeholder="Ripeti la nuova password" className={inputCls} data-testid="reset-password-confirm-input" />
          {errore && <p className="text-sm text-red-600" data-testid="reset-password-error">{errore}</p>}
          <button type="submit" disabled={busy} className={btnCls} data-testid="reset-password-submit">{busy ? 'Salvataggio...' : 'Salva la nuova password'}</button>
        </form>
      )}
    </Card>
  );
}
