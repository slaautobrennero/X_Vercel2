import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { formatDate, formatCurrency } from '../lib/utils';
import axios from 'axios';
import { Building2, Plus, Edit, Trash2, X, Settings } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function SediPage() {
  const { user } = useAuth();
  const [sedi, setSedi] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingSede, setEditingSede] = useState(null);
  const [formData, setFormData] = useState({
    nome: '',
    codice: '',
    indirizzo: '',
    tariffa_km: 0.35,
    rimborso_pasti: 15.0,
    rimborso_autostrada: true
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchSedi();
  }, []);

  const fetchSedi = async () => {
    try {
      const res = await axios.get(`${API}/sedi`);
      setSedi(res.data);
    } catch (error) {
      console.error('Error fetching sedi:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (editingSede) {
        await axios.put(`${API}/sedi/${editingSede.id}`, {
          nome: formData.nome,
          indirizzo: formData.indirizzo,
          tariffa_km: formData.tariffa_km,
          rimborso_pasti: formData.rimborso_pasti,
          rimborso_autostrada: formData.rimborso_autostrada
        });
      } else {
        await axios.post(`${API}/sedi`, formData);
      }
      setShowModal(false);
      setEditingSede(null);
      resetForm();
      fetchSedi();
    } catch (error) {
      console.error('Error saving sede:', error);
      alert(error.response?.data?.detail || 'Errore durante il salvataggio');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (sede) => {
    setEditingSede(sede);
    setFormData({
      nome: sede.nome,
      codice: sede.codice,
      indirizzo: sede.indirizzo || '',
      tariffa_km: sede.tariffa_km,
      rimborso_pasti: sede.rimborso_pasti,
      rimborso_autostrada: sede.rimborso_autostrada
    });
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Sei sicuro di voler eliminare questa sede?')) return;
    try {
      await axios.delete(`${API}/sedi/${id}`);
      fetchSedi();
    } catch (error) {
      console.error('Error deleting sede:', error);
      alert(error.response?.data?.detail || 'Errore durante l\'eliminazione');
    }
  };

  const resetForm = () => {
    setFormData({
      nome: '',
      codice: '',
      indirizzo: '',
      tariffa_km: 0.35,
      rimborso_pasti: 15.0,
      rimborso_autostrada: true
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1E4D8C]"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="sedi-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 font-['Manrope']">Sedi</h1>
          <p className="text-gray-600 mt-1">Gestione concessionarie autostradali</p>
        </div>
        <button
          onClick={() => { resetForm(); setEditingSede(null); setShowModal(true); }}
          className="flex items-center gap-2 bg-[#1E4D8C] hover:bg-[#163A6A] text-white font-medium rounded-md px-4 py-2 transition-colors"
          data-testid="new-sede-btn"
        >
          <Plus size={18} />
          Nuova Sede
        </button>
      </div>

      {/* Sedi Grid */}
      {sedi.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
          <Building2 size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">Nessuna sede configurata</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sedi.map(sede => (
            <div key={sede.id} className="bg-white border border-gray-200 rounded-lg p-6" data-testid={`sede-card-${sede.id}`}>
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="font-semibold text-gray-900">{sede.nome}</h3>
                  <p className="text-sm text-[#1E4D8C] font-medium">{sede.codice}</p>
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => handleEdit(sede)}
                    className="p-2 text-gray-400 hover:text-[#1E4D8C] hover:bg-blue-50 rounded-md transition-colors"
                    data-testid={`edit-sede-${sede.id}`}
                  >
                    <Edit size={16} />
                  </button>
                  <button
                    onClick={() => handleDelete(sede.id)}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                    data-testid={`delete-sede-${sede.id}`}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
              
              {sede.indirizzo && (
                <p className="text-sm text-gray-600 mb-4">{sede.indirizzo}</p>
              )}

              <div className="space-y-2 pt-4 border-t border-gray-100">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Tariffa KM</span>
                  <span className="font-medium">{formatCurrency(sede.tariffa_km)}/km</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Rimborso Pasti</span>
                  <span className="font-medium">{formatCurrency(sede.rimborso_pasti)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Autostrada</span>
                  <span className={`font-medium ${sede.rimborso_autostrada ? 'text-green-600' : 'text-gray-400'}`}>
                    {sede.rimborso_autostrada ? 'Sì' : 'No'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                {editingSede ? 'Modifica Sede' : 'Nuova Sede'}
              </h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nome Concessionaria *</label>
                <input
                  type="text"
                  value={formData.nome}
                  onChange={(e) => setFormData(prev => ({ ...prev, nome: e.target.value }))}
                  required
                  className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                  data-testid="sede-nome-input"
                />
              </div>
              {!editingSede && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Codice *</label>
                  <input
                    type="text"
                    value={formData.codice}
                    onChange={(e) => setFormData(prev => ({ ...prev, codice: e.target.value.toUpperCase() }))}
                    required
                    placeholder="es. A22, CAV, ASPI"
                    className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                    data-testid="sede-codice-input"
                  />
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Indirizzo</label>
                <input
                  type="text"
                  value={formData.indirizzo}
                  onChange={(e) => setFormData(prev => ({ ...prev, indirizzo: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                  data-testid="sede-indirizzo-input"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tariffa KM (€)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.tariffa_km}
                    onChange={(e) => setFormData(prev => ({ ...prev, tariffa_km: parseFloat(e.target.value) || 0 }))}
                    className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                    data-testid="sede-tariffa-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Rimborso Pasti (€)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.rimborso_pasti}
                    onChange={(e) => setFormData(prev => ({ ...prev, rimborso_pasti: parseFloat(e.target.value) || 0 }))}
                    className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                    data-testid="sede-pasti-input"
                  />
                </div>
              </div>
              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.rimborso_autostrada}
                    onChange={(e) => setFormData(prev => ({ ...prev, rimborso_autostrada: e.target.checked }))}
                    className="rounded text-[#1E4D8C]"
                  />
                  <span className="text-sm font-medium text-gray-700">Rimborso Autostrada Abilitato</span>
                </label>
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
                >
                  Annulla
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-[#1E4D8C] hover:bg-[#163A6A] text-white rounded-md transition-colors disabled:opacity-50"
                  data-testid="submit-sede-btn"
                >
                  {submitting ? 'Salvataggio...' : 'Salva'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
