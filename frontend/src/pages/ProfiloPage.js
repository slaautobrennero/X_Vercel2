import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { RUOLI } from '../lib/utils';
import axios from 'axios';
import { User, Mail, Phone, MapPin, CreditCard, Save } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function ProfiloPage() {
  const { user, updateUser } = useAuth();
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

  return (
    <div className="max-w-2xl mx-auto space-y-6" data-testid="profilo-page">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 font-['Manrope']">Profilo</h1>
        <p className="text-gray-600 mt-1">Gestisci le tue informazioni personali</p>
      </div>

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
      </div>
    </div>
  );
}
