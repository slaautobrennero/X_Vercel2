import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { formatApiErrorDetail } from '../lib/utils';
import { Eye, EyeOff, LogIn, ShieldCheck } from 'lucide-react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [requires2FA, setRequires2FA] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password, requires2FA ? totpCode : undefined);
      navigate('/');
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (detail === '2FA_REQUIRED') {
        // Server ci dice che serve il codice 2FA
        setRequires2FA(true);
        setError('');
      } else {
        setError(formatApiErrorDetail(detail) || err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 px-4" data-testid="login-page">
      {/* Login Form - Centrato (SENZA sfondo logo) */}
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="mb-8 text-center">
            <img 
              src="https://customer-assets.emergentagent.com/job_portale-rimborsi/artifacts/vtzwwkoa_SfondoSLA.png" 
              alt="SLA Logo" 
              className="h-20 mx-auto mb-6"
            />
            <h1 className="text-3xl font-bold text-gray-900 font-['Manrope']">Accedi</h1>
            <p className="text-gray-600 mt-2">Portale Sindacato Lavoratori Autostradali</p>
          </div>

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm" data-testid="login-error">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full border border-gray-300 rounded-md shadow-sm px-4 py-2.5 focus:border-[#1E4D8C] focus:ring-[#1E4D8C] focus:ring-1 outline-none transition-colors"
                placeholder="nome@email.com"
                data-testid="login-email-input"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full border border-gray-300 rounded-md shadow-sm px-4 py-2.5 pr-10 focus:border-[#1E4D8C] focus:ring-[#1E4D8C] focus:ring-1 outline-none transition-colors"
                  placeholder="••••••••"
                  data-testid="login-password-input"
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

            {requires2FA && (
              <div>
                <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-md flex items-start gap-2">
                  <ShieldCheck className="text-[#1E4D8C] flex-shrink-0 mt-0.5" size={18} />
                  <p className="text-sm text-gray-700">
                    Inserisci il codice a 6 cifre dell&apos;app autenticatore (Google Authenticator, Authy, ecc.)
                  </p>
                </div>
                <label htmlFor="totp" className="block text-sm font-medium text-gray-700 mb-1">
                  Codice 2FA
                </label>
                <input
                  id="totp"
                  type="text"
                  inputMode="numeric"
                  pattern="\d{6}"
                  maxLength={6}
                  value={totpCode}
                  onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, ''))}
                  required
                  autoFocus
                  className="w-full border border-gray-300 rounded-md shadow-sm px-4 py-2.5 text-center text-2xl font-mono tracking-widest focus:border-[#1E4D8C] focus:ring-[#1E4D8C] focus:ring-1 outline-none transition-colors"
                  placeholder="000000"
                  data-testid="login-totp-input"
                />
              </div>
            )}

            <button
              type="submit"
              disabled={loading || (requires2FA && totpCode.length !== 6)}
              className="w-full bg-[#1E4D8C] hover:bg-[#163A6A] text-white font-medium rounded-md px-4 py-2.5 transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              data-testid="login-submit-btn"
            >
              {loading ? (
                <span>Accesso in corso...</span>
              ) : (
                <>
                  <LogIn size={18} />
                  <span>{requires2FA ? 'Verifica codice' : 'Accedi'}</span>
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-600 text-sm">
              Non hai un account?{' '}
              <Link to="/register" className="text-[#1E4D8C] hover:underline font-medium" data-testid="register-link">
                Registrati
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
