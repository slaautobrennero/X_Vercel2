import React, { useState } from 'react';
import axios from 'axios';
import { ShieldCheck, ShieldOff, CheckCircle, AlertCircle, X } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function TwoFactorSection({ user, onUpdate }) {
  const isEnabled = !!user?.totp_enabled;

  // Stato setup
  const [showSetup, setShowSetup] = useState(false);
  const [setupData, setSetupData] = useState(null); // {qrcode, secret}
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Stato disable
  const [showDisable, setShowDisable] = useState(false);
  const [disablePassword, setDisablePassword] = useState('');

  const handleStartSetup = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`${API}/auth/2fa/setup`);
      setSetupData(res.data);
      setShowSetup(true);
    } catch (e) {
      setError(e.response?.data?.detail || 'Errore avvio setup');
    } finally {
      setLoading(false);
    }
  };

  const handleEnable = async (e) => {
    e.preventDefault();
    if (code.length !== 6) return;
    setLoading(true);
    setError('');
    try {
      await axios.post(`${API}/auth/2fa/enable`, { code });
      onUpdate({ totp_enabled: true });
      setShowSetup(false);
      setSetupData(null);
      setCode('');
      setSuccess('2FA attivato con successo');
      setTimeout(() => setSuccess(''), 4000);
    } catch (e) {
      setError(e.response?.data?.detail || 'Codice non valido');
    } finally {
      setLoading(false);
    }
  };

  const handleDisable = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await axios.post(`${API}/auth/2fa/disable`, { password: disablePassword });
      onUpdate({ totp_enabled: false });
      setShowDisable(false);
      setDisablePassword('');
      setSuccess('2FA disattivato');
      setTimeout(() => setSuccess(''), 4000);
    } catch (e) {
      setError(e.response?.data?.detail || 'Errore disattivazione');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6" data-testid="2fa-section">
      <div className="flex items-center gap-3 mb-4">
        {isEnabled ? <ShieldCheck className="text-green-600" /> : <ShieldOff className="text-gray-400" />}
        <div className="flex-1">
          <h2 className="text-lg font-semibold text-gray-900">Autenticazione a due fattori</h2>
          <p className="text-sm text-gray-500">
            {isEnabled
              ? 'Attivo: ad ogni accesso verrà richiesto un codice a 6 cifre dall&apos;app autenticatore'
              : 'Aggiungi un livello di sicurezza in più al tuo account'}
          </p>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
          isEnabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-700'
        }`}>
          {isEnabled ? 'Attivo' : 'Non attivo'}
        </span>
      </div>

      {success && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md text-sm text-green-800 flex items-center gap-2">
          <CheckCircle size={16} />
          {success}
        </div>
      )}

      {error && !showSetup && !showDisable && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-800 flex items-center gap-2">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {!isEnabled && !showSetup && (
        <button
          onClick={handleStartSetup}
          disabled={loading}
          className="px-4 py-2 bg-[#1E4D8C] text-white rounded-md hover:bg-[#163A6A] transition-colors disabled:opacity-50"
          data-testid="enable-2fa-btn"
        >
          {loading ? 'Caricamento...' : 'Attiva 2FA'}
        </button>
      )}

      {isEnabled && !showDisable && (
        <button
          onClick={() => setShowDisable(true)}
          className="px-4 py-2 border border-red-300 text-red-700 rounded-md hover:bg-red-50 transition-colors"
          data-testid="disable-2fa-btn"
        >
          Disattiva 2FA
        </button>
      )}

      {/* MODAL SETUP */}
      {showSetup && setupData && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-full max-w-md max-h-[90vh] overflow-auto">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-lg font-semibold">Attiva 2FA</h3>
              <button onClick={() => { setShowSetup(false); setCode(''); setError(''); }} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <ol className="list-decimal list-inside text-sm text-gray-700 space-y-2">
                <li>Installa <strong>Google Authenticator</strong>, <strong>Authy</strong>, <strong>1Password</strong> o un&apos;altra app TOTP.</li>
                <li>Scansiona questo QR code con l&apos;app:</li>
              </ol>

              <div className="flex justify-center bg-gray-50 p-4 rounded-md">
                <img src={setupData.qrcode} alt="QR Code 2FA" className="w-48 h-48" data-testid="2fa-qrcode" />
              </div>

              <details className="text-xs text-gray-600">
                <summary className="cursor-pointer">Non puoi scansionare? Inserisci manualmente</summary>
                <p className="mt-2 font-mono break-all bg-gray-50 p-2 rounded select-all" data-testid="2fa-secret">
                  {setupData.secret}
                </p>
              </details>

              <form onSubmit={handleEnable} className="space-y-3">
                <label className="block text-sm font-medium text-gray-700">
                  3. Inserisci il codice di 6 cifre mostrato dall&apos;app:
                </label>
                <input
                  type="text"
                  inputMode="numeric"
                  pattern="\d{6}"
                  maxLength={6}
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-md text-center text-2xl font-mono tracking-widest focus:ring-2 focus:ring-[#1E4D8C]"
                  placeholder="000000"
                  autoFocus
                  data-testid="2fa-verify-input"
                />
                {error && (
                  <div className="text-sm text-red-700 flex items-center gap-2">
                    <AlertCircle size={14} /> {error}
                  </div>
                )}
                <button
                  type="submit"
                  disabled={loading || code.length !== 6}
                  className="w-full px-4 py-2 bg-[#1E4D8C] text-white rounded-md hover:bg-[#163A6A] transition-colors disabled:opacity-50"
                  data-testid="2fa-verify-btn"
                >
                  {loading ? 'Verifica...' : 'Attiva 2FA'}
                </button>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* MODAL DISABLE */}
      {showDisable && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-full max-w-md">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-lg font-semibold">Disattiva 2FA</h3>
              <button onClick={() => { setShowDisable(false); setDisablePassword(''); setError(''); }} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleDisable} className="p-6 space-y-4">
              <p className="text-sm text-gray-700">
                Per sicurezza, inserisci la tua password per disattivare il 2FA.
              </p>
              <input
                type="password"
                value={disablePassword}
                onChange={(e) => setDisablePassword(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-[#1E4D8C]"
                placeholder="Password attuale"
                required
                autoFocus
                data-testid="2fa-disable-password"
              />
              {error && (
                <div className="text-sm text-red-700 flex items-center gap-2">
                  <AlertCircle size={14} /> {error}
                </div>
              )}
              <button
                type="submit"
                disabled={loading || !disablePassword}
                className="w-full px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors disabled:opacity-50"
                data-testid="2fa-confirm-disable"
              >
                {loading ? 'Disattivazione...' : 'Disattiva 2FA'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
