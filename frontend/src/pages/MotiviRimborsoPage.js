import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Settings, Plus, Edit, Trash2, X, Check } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function MotiviRimborsoPage() {
  const { user } = useAuth();
  const [motivi, setMotivi] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingMotivo, setEditingMotivo] = useState(null);
  const [formData, setFormData] = useState({
    nome: '',
    descrizione: '',
    richiede_note: false
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchMotivi();
  }, []);

  const fetchMotivi = async () => {
    try {
      const res = await axios.get(`${API}/motivi-rimborso`);
      setMotivi(res.data);
    } catch (error) {
      console.error('Error fetching motivi:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (editingMotivo) {
        await axios.put(`${API}/motivi-rimborso/${editingMotivo.id}`, formData);
      } else {
        await axios.post(`${API}/motivi-rimborso`, formData);
      }
      setShowModal(false);
      setEditingMotivo(null);
      resetForm();
      fetchMotivi();
    } catch (error) {
      console.error('Error saving motivo:', error);
      alert(error.response?.data?.detail || 'Errore durante il salvataggio');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (motivo) => {
    setEditingMotivo(motivo);
    setFormData({
      nome: motivo.nome,
      descrizione: motivo.descrizione || '',
      richiede_note: motivo.richiede_note || false
    });
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Sei sicuro di voler eliminare questo motivo?')) return;
    try {
      await axios.delete(`${API}/motivi-rimborso/${id}`);
      fetchMotivi();
    } catch (error) {
      console.error('Error deleting motivo:', error);
      alert(error.response?.data?.detail || 'Errore durante l\'eliminazione');
    }
  };

  const resetForm = () => {
    setFormData({
      nome: '',
      descrizione: '',
      richiede_note: false
    });
  };

  if (user?.ruolo !== 'superadmin') {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Accesso non autorizzato</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1E4D8C]"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="motivi-rimborso-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 font-['Manrope']">Motivi Rimborso</h1>
          <p className="text-gray-600 mt-1">Gestione causali per richieste rimborso</p>
        </div>
        <button
          onClick={() => { resetForm(); setEditingMotivo(null); setShowModal(true); }}
          className="flex items-center gap-2 bg-[#1E4D8C] hover:bg-[#163A6A] text-white font-medium rounded-md px-4 py-2 transition-colors"
          data-testid="new-motivo-btn"
        >
          <Plus size={18} />
          Nuovo Motivo
        </button>
      </div>

      {/* Motivi List */}
      {motivi.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
          <Settings size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">Nessun motivo configurato</p>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <th className="px-6 py-3">Nome</th>
                <th className="px-6 py-3">Descrizione</th>
                <th className="px-6 py-3">Note Obbligatorie</th>
                <th className="px-6 py-3">Azioni</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {motivi.map(motivo => (
                <tr key={motivo.id} className="hover:bg-gray-50" data-testid={`motivo-row-${motivo.id}`}>
                  <td className="px-6 py-4 font-medium text-gray-900">{motivo.nome}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{motivo.descrizione || '-'}</td>
                  <td className="px-6 py-4">
                    {motivo.richiede_note ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                        <Check size={12} className="mr-1" /> Sì
                      </span>
                    ) : (
                      <span className="text-gray-400 text-sm">No</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleEdit(motivo)}
                        className="p-2 text-gray-400 hover:text-[#1E4D8C] hover:bg-blue-50 rounded-md transition-colors"
                        data-testid={`edit-motivo-${motivo.id}`}
                      >
                        <Edit size={16} />
                      </button>
                      <button
                        onClick={() => handleDelete(motivo.id)}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                        data-testid={`delete-motivo-${motivo.id}`}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                {editingMotivo ? 'Modifica Motivo' : 'Nuovo Motivo'}
              </h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nome *</label>
                <input
                  type="text"
                  value={formData.nome}
                  onChange={(e) => setFormData(prev => ({ ...prev, nome: e.target.value }))}
                  required
                  placeholder="es. RSA, Sede, Corso..."
                  className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                  data-testid="motivo-nome-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descrizione</label>
                <textarea
                  value={formData.descrizione}
                  onChange={(e) => setFormData(prev => ({ ...prev, descrizione: e.target.value }))}
                  rows={2}
                  className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none resize-none"
                  data-testid="motivo-descrizione-input"
                />
              </div>
              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.richiede_note}
                    onChange={(e) => setFormData(prev => ({ ...prev, richiede_note: e.target.checked }))}
                    className="rounded text-[#1E4D8C]"
                  />
                  <span className="text-sm font-medium text-gray-700">Note obbligatorie</span>
                </label>
                <p className="text-xs text-gray-500 mt-1 ml-6">
                  Se attivo, l'utente dovrà inserire una nota quando seleziona questo motivo
                </p>
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
                  data-testid="submit-motivo-btn"
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
