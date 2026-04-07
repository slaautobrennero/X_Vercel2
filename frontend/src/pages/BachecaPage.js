import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { formatDateTime } from '../lib/utils';
import axios from 'axios';
import { Megaphone, Plus, Trash2, Link as LinkIcon, X } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function BachecaPage() {
  const { user } = useAuth();
  const [annunci, setAnnunci] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ titolo: '', contenuto: '', link_documento: '' });
  const [submitting, setSubmitting] = useState(false);

  const canPost = ['segreteria', 'segretario', 'admin', 'superadmin'].includes(user?.ruolo);

  useEffect(() => {
    fetchAnnunci();
  }, []);

  const fetchAnnunci = async () => {
    try {
      const res = await axios.get(`${API}/annunci`);
      setAnnunci(res.data);
    } catch (error) {
      console.error('Error fetching annunci:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await axios.post(`${API}/annunci`, formData);
      setShowModal(false);
      setFormData({ titolo: '', contenuto: '', link_documento: '' });
      fetchAnnunci();
    } catch (error) {
      console.error('Error creating annuncio:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Sei sicuro di voler eliminare questo annuncio?')) return;
    try {
      await axios.delete(`${API}/annunci/${id}`);
      fetchAnnunci();
    } catch (error) {
      console.error('Error deleting annuncio:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1E4D8C]"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="bacheca-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 font-['Manrope']">Bacheca</h1>
          <p className="text-gray-600 mt-1">Comunicati e annunci</p>
        </div>
        {canPost && (
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 bg-[#1E4D8C] hover:bg-[#163A6A] text-white font-medium rounded-md px-4 py-2 transition-colors"
            data-testid="new-annuncio-btn"
          >
            <Plus size={18} />
            Nuovo Annuncio
          </button>
        )}
      </div>

      {/* Annunci List */}
      <div className="space-y-4">
        {annunci.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
            <Megaphone size={48} className="mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">Nessun annuncio pubblicato</p>
          </div>
        ) : (
          annunci.map(annuncio => (
            <div key={annuncio.id} className="bg-white border border-gray-200 rounded-lg p-6" data-testid={`annuncio-${annuncio.id}`}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h2 className="text-lg font-semibold text-gray-900">{annuncio.titolo}</h2>
                  <p className="text-gray-600 mt-2 whitespace-pre-wrap">{annuncio.contenuto}</p>
                  {annuncio.link_documento && (
                    <a 
                      href={annuncio.link_documento} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 mt-3 text-[#1E4D8C] hover:underline text-sm"
                    >
                      <LinkIcon size={14} />
                      Documento allegato
                    </a>
                  )}
                  <div className="mt-4 text-sm text-gray-500">
                    <span>{annuncio.autore_nome}</span>
                    <span className="mx-2">•</span>
                    <span>{formatDateTime(annuncio.created_at)}</span>
                  </div>
                </div>
                {canPost && (
                  <button
                    onClick={() => handleDelete(annuncio.id)}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                    data-testid={`delete-annuncio-${annuncio.id}`}
                  >
                    <Trash2 size={18} />
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-full max-w-lg">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Nuovo Annuncio</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Titolo *</label>
                <input
                  type="text"
                  value={formData.titolo}
                  onChange={(e) => setFormData(prev => ({ ...prev, titolo: e.target.value }))}
                  required
                  className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                  data-testid="annuncio-titolo-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Contenuto *</label>
                <textarea
                  value={formData.contenuto}
                  onChange={(e) => setFormData(prev => ({ ...prev, contenuto: e.target.value }))}
                  required
                  rows={5}
                  className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none resize-none"
                  data-testid="annuncio-contenuto-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Link Documento (opzionale)</label>
                <input
                  type="url"
                  value={formData.link_documento}
                  onChange={(e) => setFormData(prev => ({ ...prev, link_documento: e.target.value }))}
                  placeholder="https://..."
                  className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                  data-testid="annuncio-link-input"
                />
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
                  data-testid="submit-annuncio-btn"
                >
                  {submitting ? 'Pubblicazione...' : 'Pubblica'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
