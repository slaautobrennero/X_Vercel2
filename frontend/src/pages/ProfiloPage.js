import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { RUOLI } from '../lib/utils';
import axios from 'axios';
import { User, Mail, Phone, MapPin, CreditCard, Save, Lock, Eye, EyeOff, AlertCircle, CheckCircle } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Validazione password lato client (specchia regole backend)
function validatePassword(pwd) {
  if (pwd.length < 8) return 'La password deve avere almeno 8 caratteri';
  if (!/[A-Za-z]/.test(pwd)) return 'La password deve contenere almeno una lettera';
  if (!/\d/.test(pwd)) return 'La password deve contenere almeno un numero';
  if (!/[^A-Za-z0-9]/.test(pwd)) return 'La password deve contenere almeno un carattere speciale';
  return null;
}

export default function ProfiloPage() {
  const { user, updateUser, logout } = useAuth();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    nome: user?.nome || '',
    cognome: user?.cognome || '',
    telefono: user?.telefono || '',
    indirizzo: user?.indirizzo || '',
    citta: user?.citta || '',
    cap: user?.cap || '',
    iban: user?.iban || ''
  });
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  // Stato cambio password
  const [pwdData, setPwdData] = useState({ current: '', next: '', confirm: '' });
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNext, setShowNext] = useState(false);
  const [pwdError, setPwdError] = useState('');
  const [pwdSubmitting, setPwdSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSuccess(false);
    try {
      await axios.put(`${API}/users/${user.id}`, formData);
      updateUser(formData);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (error) {
      console.error('Error updating profile:', error);
      alert(error.response?.data?.detail || 'Errore durante il salvataggio');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPwdError('');

    if (pwdData.next !== pwdData.confirm) {
      setPwdError('Le nuove password non coincidono');
      return;
    }

    const validationErr = validatePassword(pwdData.next);
    if (validationErr) {
      setPwdError(validationErr);
      return;
    }

    if (pwdData.current === pwdData.next) {
      setPwdError('La nuova password deve essere diversa dall\'attuale');
      return;
    }

    setPwdSubmitting(true);
    try {
      await axios.post(`${API}/auth/change-password`, {
        current_password: pwdData.current,
        new_password: pwdData.next
      });
      alert('Password aggiornata con successo. Effettua nuovamente il login.');
      try { await logout(); } catch (_) {}
      navigate('/login');
    } catch (error) {
      setPwdError(error.response?.data?.detail || 'Errore durante il cambio password');
    } finally {
      setPwdSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6" data-testid="profilo-page">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 font-['Manrope']">Profilo</h1>
        <p className="text-gray-600 mt-1">Gestisci le tue informazioni personali</p>
      </div>

      {user?.must_change_password && (
        <div className="bg-orange-50 border border-orange-300 rounded-lg p-4 flex items-start gap-3" data-testid="must-change-password-banner">
          <Lock size={20} className="text-orange-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-orange-900">Cambio password obbligatorio</p>
            <p className="text-sm text-orange-800 mt-1">
              La tua password è stata reimpostata da un amministratore. Per sicurezza, cambiala subito qui sotto.
            </p>
          </div>
        </div>
      )}

      {/* User Card */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-16 h-16 rounded-full bg-[#1E4D8C] flex items-center justify-center text-white text-xl font-bold">
            {user?.nome?.[0]}{user?.cognome?.[0]}
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900">{user?.nome} {user?.cognome}</h2>
            <p className="text-gray-600">{user?.email}</p>
            <div className="flex items-center gap-2 mt-1">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                user?.ruolo === 'superadmin' ? 'bg-purple-100 text-purple-800' :
                user?.ruolo === 'admin' ? 'bg-blue-100 text-blue-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {RUOLI[user?.ruolo] || user?.ruolo}
              </span>
              {user?.sede_nome && (
                <span className="text-sm text-gray-500">• {user.sede_nome}</span>
              )}
            </div>
          </div>
        </div>

        {success && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
            Profilo aggiornato con successo!
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <User size={14} className="inline mr-1" />
                Nome
              </label>
              <input
                type="text"
                value={formData.nome}
                onChange={(e) => setFormData(prev => ({ ...prev, nome: e.target.value }))}
                className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                data-testid="profilo-nome-input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <User size={14} className="inline mr-1" />
                Cognome
              </label>
              <input
                type="text"
                value={formData.cognome}
                onChange={(e) => setFormData(prev => ({ ...prev, cognome: e.target.value }))}
                className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                data-testid="profilo-cognome-input"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Phone size={14} className="inline mr-1" />
              Telefono
            </label>
            <input
              type="tel"
              value={formData.telefono}
              onChange={(e) => setFormData(prev => ({ ...prev, telefono: e.target.value }))}
              className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
              data-testid="profilo-telefono-input"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <MapPin size={14} className="inline mr-1" />
              Indirizzo
            </label>
            <input
              type="text"
              value={formData.indirizzo}
              onChange={(e) => setFormData(prev => ({ ...prev, indirizzo: e.target.value }))}
              className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
              data-testid="profilo-indirizzo-input"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Città</label>
              <input
                type="text"
                value={formData.citta}
                onChange={(e) => setFormData(prev => ({ ...prev, citta: e.target.value }))}
                className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                data-testid="profilo-citta-input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">CAP</label>
              <input
                type="text"
                value={formData.cap}
                onChange={(e) => setFormData(prev => ({ ...prev, cap: e.target.value }))}
                className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                data-testid="profilo-cap-input"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <CreditCard size={14} className="inline mr-1" />
              IBAN
            </label>
            <input
              type="text"
              value={formData.iban}
              onChange={(e) => setFormData(prev => ({ ...prev, iban: e.target.value }))}
              placeholder="IT..."
              className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
              data-testid="profilo-iban-input"
            />
          </div>

          <div className="pt-4">
            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-2 bg-[#1E4D8C] hover:bg-[#163A6A] text-white font-medium rounded-md px-6 py-2 transition-colors disabled:opacity-50"
              data-testid="save-profilo-btn"
            >
              <Save size={18} />
              {saving ? 'Salvataggio...' : 'Salva Modifiche'}
            </button>
          </div>
        </form>
      </div>      {/* Card Cambio Password */}
      <div className="bg-white border border-gray-200 rounded-lg p-6" data-testid="change-password-card">
        <div className="flex items-center gap-2 mb-2">
          <Lock size={18} className="text-[#1E4D8C]" />
          <h2 className="text-lg font-semibold text-gray-900">Cambia password</h2>
        </div>
        <p className="text-sm text-gray-500 mb-4">
          Per sicurezza, dopo il cambio dovrai effettuare nuovamente il login.
        </p>

        {pwdError && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm flex items-start gap-2">
            <AlertCircle size={16} className="flex-shrink-0 mt-0.5" />
            <span>{pwdError}</span>
          </div>
        )}

        <form onSubmit={handleChangePassword} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password attuale *</label>
            <div className="relative">
              <input
                type={showCurrent ? 'text' : 'password'}
                value={pwdData.current}
                onChange={(e) => setPwdData(prev => ({ ...prev, current: e.target.value }))}
                required
                autoComplete="current-password"
                className="w-full border border-gray-300 rounded-md px-4 py-2 pr-10 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                data-testid="current-password-input"
              />
              <button
                type="button"
                onClick={() => setShowCurrent(!showCurrent)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                tabIndex={-1}
              >
                {showCurrent ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nuova password *</label>
              <div className="relative">
                <input
                  type={showNext ? 'text' : 'password'}
                  value={pwdData.next}
                  onChange={(e) => setPwdData(prev => ({ ...prev, next: e.target.value }))}
                  required
                  autoComplete="new-password"
                  className="w-full border border-gray-300 rounded-md px-4 py-2 pr-10 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                  data-testid="new-password-input"
                />
                <button
                  type="button"
                  onClick={() => setShowNext(!showNext)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  tabIndex={-1}
                >
                  {showNext ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Conferma nuova password *</label>
              <input
                type={showNext ? 'text' : 'password'}
                value={pwdData.confirm}
                onChange={(e) => setPwdData(prev => ({ ...prev, confirm: e.target.value }))}
                required
                autoComplete="new-password"
                className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                data-testid="confirm-password-input"
              />
            </div>
          </div>

          {/* Indicatori requisiti password */}
          <PasswordRequirements password={pwdData.next} />

          <div className="pt-2">
            <button
              type="submit"
              disabled={pwdSubmitting}
              className="flex items-center gap-2 bg-[#1E4D8C] hover:bg-[#163A6A] text-white font-medium rounded-md px-6 py-2 transition-colors disabled:opacity-50"
              data-testid="submit-change-password-btn"
            >
              <Lock size={18} />
              {pwdSubmitting ? 'Salvataggio...' : 'Cambia password'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Componente helper per visualizzare requisiti password con check verde/rosso
function PasswordRequirements({ password }) {
  const checks = [
    { test: password.length >= 8, label: 'Almeno 8 caratteri' },
    { test: /[A-Za-z]/.test(password), label: 'Almeno una lettera' },
    { test: /\d/.test(password), label: 'Almeno un numero' },
    { test: /[^A-Za-z0-9]/.test(password), label: 'Almeno un carattere speciale (!@#$%...)' },
  ];

  if (!password) return null;

  return (
    <ul className="text-xs space-y-1 mt-1" data-testid="password-requirements">
      {checks.map((c, i) => (
        <li key={i} className={`flex items-center gap-1.5 ${c.test ? 'text-green-700' : 'text-gray-500'}`}>
          {c.test ? <CheckCircle size={12} /> : <AlertCircle size={12} />}
          {c.label}
        </li>
      ))}
    </ul>
  );
}
