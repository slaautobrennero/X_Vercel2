import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { formatApiErrorDetail } from '../lib/utils';
import { Eye, EyeOff, UserPlus } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    nome: '',
    cognome: '',
    telefono: '',
    indirizzo: '',
    citta: '',
    cap: '',
    iban: '',
    sede_id: '',
    ruolo: 'iscritto'
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [sedi, setSedi] = useState([]);
  const { register } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // Fetch sedi for dropdown
    axios.get(`${API}/sedi`)
      .then(res => setSedi(res.data))
      .catch(() => {});
  }, []);

  const handleChange = (e) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Le password non coincidono');
      return;
    }

    if (formData.password.length < 6) {
      setError('La password deve essere di almeno 6 caratteri');
      return;
    }

    setLoading(true);

    try {
      const { confirmPassword, ...registerData } = formData;
      await register(registerData);
      navigate('/');
    } catch (err) {
      setError(formatApiErrorDetail(err.response?.data?.detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex" data-testid="register-page">
      {/* Left side - Background */}
      <div 
        className="hidden lg:block lg:w-2/5 bg-cover bg-center"
        style={{ 
          backgroundImage: 'url(https://customer-assets.emergentagent.com/job_portale-rimborsi/artifacts/9qoxl0rw_Full%20logo.png)',
          backgroundColor: '#1E4D8C'
        }}
      />

      {/* Right side - Form */}
      <div className="flex-1 flex items-center justify-center bg-white px-8 py-12 overflow-y-auto">
        <div className="w-full max-w-xl">
          <div className="mb-8 text-center">
            <img 
              src="https://customer-assets.emergentagent.com/job_portale-rimborsi/artifacts/vtzwwkoa_SfondoSLA.png" 
              alt="SLA Logo" 
              className="h-16 mx-auto mb-4"
            />
            <h1 className="text-3xl font-bold text-gray-900 font-['Manrope']">Registrazione</h1>
            <p className="text-gray-600 mt-2">Crea il tuo account SLA</p>
          </div>

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm" data-testid="register-error">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nome *</label>
                <input
                  type="text"
                  name="nome"
                  value={formData.nome}
                  onChange={handleChange}
                  required
                  className="w-full border border-gray-300 rounded-md shadow-sm px-4 py-2.5 focus:border-[#1E4D8C] focus:ring-[#1E4D8C] focus:ring-1 outline-none"
                  data-testid="register-nome-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Cognome *</label>
                <input
                  type="text"
                  name="cognome"
                  value={formData.cognome}
                  onChange={handleChange}
                  required
                  className="w-full border border-gray-300 rounded-md shadow-sm px-4 py-2.5 focus:border-[#1E4D8C] focus:ring-[#1E4D8C] focus:ring-1 outline-none"
                  data-testid="register-cognome-input"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="w-full border border-gray-300 rounded-md shadow-sm px-4 py-2.5 focus:border-[#1E4D8C] focus:ring-[#1E4D8C] focus:ring-1 outline-none"
                placeholder="nome@email.com"
                data-testid="register-email-input"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password *</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    className="w-full border border-gray-300 rounded-md shadow-sm px-4 py-2.5 pr-10 focus:border-[#1E4D8C] focus:ring-[#1E4D8C] focus:ring-1 outline-none"
                    data-testid="register-password-input"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Conferma Password *</label>
                <input
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  required
                  className="w-full border border-gray-300 rounded-md shadow-sm px-4 py-2.5 focus:border-[#1E4D8C] focus:ring-[#1E4D8C] focus:ring-1 outline-none"
                  data-testid="register-confirm-password-input"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Concessionaria *</label>
              <select
                name="sede_id"
                value={formData.sede_id}
                onChange={handleChange}
                required
                className="w-full border border-gray-300 rounded-md shadow-sm px-4 py-2.5 focus:border-[#1E4D8C] focus:ring-[#1E4D8C] focus:ring-1 outline-none"
                data-testid="register-sede-select"
              >
                <option value="">Seleziona la tua sede</option>
                {sedi.map(sede => (
                  <option key={sede.id} value={sede.id}>{sede.nome}</option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Ruolo</label>
                <select
                  name="ruolo"
                  value={formData.ruolo}
                  onChange={handleChange}
                  className="w-full border border-gray-300 rounded-md shadow-sm px-4 py-2.5 focus:border-[#1E4D8C] focus:ring-[#1E4D8C] focus:ring-1 outline-none"
                  data-testid="register-ruolo-select"
                >
                  <option value="iscritto">Iscritto</option>
                  <option value="delegato">Delegato</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Telefono</label>
                <input
                  type="tel"
                  name="telefono"
                  value={formData.telefono}
                  onChange={handleChange}
                  className="w-full border border-gray-300 rounded-md shadow-sm px-4 py-2.5 focus:border-[#1E4D8C] focus:ring-[#1E4D8C] focus:ring-1 outline-none"
                  data-testid="register-telefono-input"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Indirizzo</label>
              <input
                type="text"
                name="indirizzo"
                value={formData.indirizzo}
                onChange={handleChange}
                className="w-full border border-gray-300 rounded-md shadow-sm px-4 py-2.5 focus:border-[#1E4D8C] focus:ring-[#1E4D8C] focus:ring-1 outline-none"
                placeholder="Via/Piazza"
                data-testid="register-indirizzo-input"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Città</label>
                <input
                  type="text"
                  name="citta"
                  value={formData.citta}
                  onChange={handleChange}
                  className="w-full border border-gray-300 rounded-md shadow-sm px-4 py-2.5 focus:border-[#1E4D8C] focus:ring-[#1E4D8C] focus:ring-1 outline-none"
                  data-testid="register-citta-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">CAP</label>
                <input
                  type="text"
                  name="cap"
                  value={formData.cap}
                  onChange={handleChange}
                  className="w-full border border-gray-300 rounded-md shadow-sm px-4 py-2.5 focus:border-[#1E4D8C] focus:ring-[#1E4D8C] focus:ring-1 outline-none"
                  data-testid="register-cap-input"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">IBAN</label>
              <input
                type="text"
                name="iban"
                value={formData.iban}
                onChange={handleChange}
                className="w-full border border-gray-300 rounded-md shadow-sm px-4 py-2.5 focus:border-[#1E4D8C] focus:ring-[#1E4D8C] focus:ring-1 outline-none"
                placeholder="IT..."
                data-testid="register-iban-input"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#1E4D8C] hover:bg-[#163A6A] text-white font-medium rounded-md px-4 py-2.5 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
              data-testid="register-submit-btn"
            >
              {loading ? 'Registrazione in corso...' : (
                <>
                  <UserPlus size={18} />
                  <span>Registrati</span>
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-600 text-sm">
              Hai già un account?{' '}
              <Link to="/login" className="text-[#1E4D8C] hover:underline font-medium" data-testid="login-link">
                Accedi
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
