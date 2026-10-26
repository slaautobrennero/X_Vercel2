import React, { useState } from 'react';
import axios from 'axios';
import { Upload, X } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const inputCls = 'w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none';

export const CaricaDocumentoDialog = ({ cartella, onClose, onUploaded }) => {
  const [nome, setNome] = useState('');
  const [descrizione, setDescrizione] = useState('');
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [errore, setErrore] = useState('');

  const invia = async (e) => {
    e.preventDefault();
    if (!file) return;
    setBusy(true); setErrore('');
    const data = new FormData();
    data.append('file', file);
    data.append('nome', nome);
    data.append('cartella_id', cartella.id);
    data.append('descrizione', descrizione);
    try {
      await axios.post(`${API}/documenti`, data, { headers: { 'Content-Type': 'multipart/form-data' } });
      onUploaded();
    } catch (err) {
      const d = err.response?.data?.detail;
      setErrore(typeof d === 'string' ? d : 'Errore durante il caricamento');
    } finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" data-testid="carica-documento-dialog">
      <form onSubmit={invia} className="bg-white rounded-lg w-full max-w-lg">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Carica documento in “{cartella.nome}”</h2>
          <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nome Documento *</label>
            <input value={nome} onChange={(e) => setNome(e.target.value)} required className={inputCls} data-testid="documento-nome-input" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Descrizione</label>
            <textarea value={descrizione} onChange={(e) => setDescrizione(e.target.value)} rows={3} className={`${inputCls} resize-none`} data-testid="documento-descrizione-input" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">File *</label>
            <label htmlFor="file-upload" className="block border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-[#1E4D8C] transition-colors cursor-pointer">
              <input type="file" id="file-upload" className="hidden" accept=".pdf,.jpg,.jpeg,.png" onChange={(e) => setFile(e.target.files?.[0] || null)} data-testid="documento-file-input" />
              <Upload size={32} className="mx-auto text-gray-400 mb-2" />
              {file ? <p className="text-sm text-gray-900 font-medium">{file.name}</p> : (
                <><p className="text-sm text-gray-600">Clicca per selezionare</p><p className="text-xs text-gray-400 mt-1">PDF, JPG, PNG (max 5MB)</p></>
              )}
            </label>
          </div>
          {errore && <p className="text-sm text-red-600" data-testid="documento-upload-error">{errore}</p>}
        </div>
        <div className="flex justify-end gap-3 px-6 pb-6">
          <button type="button" onClick={onClose} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition-colors">Annulla</button>
          <button type="submit" disabled={busy || !file} className="px-4 py-2 bg-[#1E4D8C] hover:bg-[#163A6A] text-white rounded-md transition-colors disabled:opacity-50" data-testid="submit-documento-btn">
            {busy ? 'Caricamento...' : 'Carica'}
          </button>
        </div>
      </form>
    </div>
  );
};
