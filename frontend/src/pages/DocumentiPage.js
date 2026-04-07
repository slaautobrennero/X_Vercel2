import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { formatDateTime } from '../lib/utils';
import axios from 'axios';
import { FileText, Plus, Download, Trash2, Upload, X, FolderOpen } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function DocumentiPage() {
  const { user } = useAuth();
  const [documenti, setDocumenti] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedCategoria, setSelectedCategoria] = useState('');
  const [formData, setFormData] = useState({ nome: '', categoria: 'modulistica', descrizione: '' });
  const [file, setFile] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const canUpload = ['segreteria', 'segretario', 'admin', 'superadmin'].includes(user?.ruolo);

  const categorie = [
    { value: 'modulistica', label: 'Modulistica' },
    { value: 'documento', label: 'Documenti' },
    { value: 'altro', label: 'Altro' }
  ];

  useEffect(() => {
    fetchDocumenti();
  }, [selectedCategoria]);

  const fetchDocumenti = async () => {
    try {
      const url = selectedCategoria 
        ? `${API}/documenti?categoria=${selectedCategoria}` 
        : `${API}/documenti`;
      const res = await axios.get(url);
      setDocumenti(res.data);
    } catch (error) {
      console.error('Error fetching documenti:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;
    
    setSubmitting(true);
    try {
      const data = new FormData();
      data.append('file', file);
      data.append('nome', formData.nome);
      data.append('categoria', formData.categoria);
      data.append('descrizione', formData.descrizione || '');
      
      await axios.post(`${API}/documenti`, data, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setShowModal(false);
      setFormData({ nome: '', categoria: 'modulistica', descrizione: '' });
      setFile(null);
      fetchDocumenti();
    } catch (error) {
      console.error('Error uploading documento:', error);
      alert(error.response?.data?.detail || 'Errore durante il caricamento');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDownload = async (doc) => {
    try {
      const response = await axios.get(`${API}/documenti/${doc.id}/download`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', doc.filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error downloading documento:', error);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Sei sicuro di voler eliminare questo documento?')) return;
    try {
      await axios.delete(`${API}/documenti/${id}`);
      fetchDocumenti();
    } catch (error) {
      console.error('Error deleting documento:', error);
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
    <div className="space-y-6" data-testid="documenti-page">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 font-['Manrope']">Documenti</h1>
          <p className="text-gray-600 mt-1">Modulistica e documenti condivisi</p>
        </div>
        {canUpload && (
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 bg-[#1E4D8C] hover:bg-[#163A6A] text-white font-medium rounded-md px-4 py-2 transition-colors"
            data-testid="upload-documento-btn"
          >
            <Upload size={18} />
            Carica Documento
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setSelectedCategoria('')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            selectedCategoria === '' 
              ? 'bg-[#1E4D8C] text-white' 
              : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
          }`}
          data-testid="filter-all"
        >
          Tutti
        </button>
        {categorie.map(cat => (
          <button
            key={cat.value}
            onClick={() => setSelectedCategoria(cat.value)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedCategoria === cat.value 
                ? 'bg-[#1E4D8C] text-white' 
                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
            data-testid={`filter-${cat.value}`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Documents Grid */}
      {documenti.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
          <FolderOpen size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">Nessun documento trovato</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {documenti.map(doc => (
            <div key={doc.id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow" data-testid={`documento-${doc.id}`}>
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
                  <FileText size={20} className="text-[#1E4D8C]" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-gray-900 truncate">{doc.nome}</h3>
                  <p className="text-sm text-gray-500 capitalize">{doc.categoria}</p>
                  {doc.descrizione && (
                    <p className="text-sm text-gray-600 mt-1 line-clamp-2">{doc.descrizione}</p>
                  )}
                  <p className="text-xs text-gray-400 mt-2">{formatDateTime(doc.created_at)}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 mt-4 pt-4 border-t border-gray-100">
                <button
                  onClick={() => handleDownload(doc)}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm text-[#1E4D8C] hover:bg-blue-50 rounded-md transition-colors"
                  data-testid={`download-${doc.id}`}
                >
                  <Download size={16} />
                  Scarica
                </button>
                {canUpload && (
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                    data-testid={`delete-${doc.id}`}
                  >
                    <Trash2 size={16} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-full max-w-lg">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Carica Documento</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nome Documento *</label>
                <input
                  type="text"
                  value={formData.nome}
                  onChange={(e) => setFormData(prev => ({ ...prev, nome: e.target.value }))}
                  required
                  className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                  data-testid="documento-nome-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Categoria *</label>
                <select
                  value={formData.categoria}
                  onChange={(e) => setFormData(prev => ({ ...prev, categoria: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                  data-testid="documento-categoria-select"
                >
                  {categorie.map(cat => (
                    <option key={cat.value} value={cat.value}>{cat.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descrizione</label>
                <textarea
                  value={formData.descrizione}
                  onChange={(e) => setFormData(prev => ({ ...prev, descrizione: e.target.value }))}
                  rows={3}
                  className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none resize-none"
                  data-testid="documento-descrizione-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">File *</label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-[#1E4D8C] transition-colors">
                  <input
                    type="file"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    accept=".pdf,.jpg,.jpeg,.png"
                    required
                    className="hidden"
                    id="file-upload"
                    data-testid="documento-file-input"
                  />
                  <label htmlFor="file-upload" className="cursor-pointer">
                    <Upload size={32} className="mx-auto text-gray-400 mb-2" />
                    {file ? (
                      <p className="text-sm text-gray-900 font-medium">{file.name}</p>
                    ) : (
                      <>
                        <p className="text-sm text-gray-600">Clicca per selezionare</p>
                        <p className="text-xs text-gray-400 mt-1">PDF, JPG, PNG (max 5MB)</p>
                      </>
                    )}
                  </label>
                </div>
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
                  disabled={submitting || !file}
                  className="px-4 py-2 bg-[#1E4D8C] hover:bg-[#163A6A] text-white rounded-md transition-colors disabled:opacity-50"
                  data-testid="submit-documento-btn"
                >
                  {submitting ? 'Caricamento...' : 'Carica'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
