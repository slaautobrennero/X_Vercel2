import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { FileText, FolderPlus, Download, Trash2, Upload, FolderOpen, Landmark, ArrowLeft } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { formatDateTime, hasAnyRole } from '../lib/utils';
import { CartellaCard } from '../components/documenti/CartellaCard';
import { NuovaCartellaDialog } from '../components/documenti/NuovaCartellaDialog';
import { CaricaDocumentoDialog } from '../components/documenti/CaricaDocumentoDialog';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const DocumentoCard = ({ doc, canDelete, onDownload, onDelete }) => (
  <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow" data-testid={`documento-${doc.id}`}>
    <div className="flex items-start gap-3">
      <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
        <FileText size={20} className="text-[#1E4D8C]" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 flex-wrap">
          <h3 className="font-medium text-gray-900 truncate">{doc.nome}</h3>
          {doc.broadcast_nazionale && (
            <span className="inline-flex items-center gap-0.5 bg-amber-100 text-amber-800 text-[10px] font-medium px-1.5 py-0.5 rounded" data-testid={`badge-naz-doc-${doc.id}`}>
              <Landmark size={10} /> Naz.
            </span>
          )}
        </div>
        {doc.descrizione && <p className="text-sm text-gray-600 mt-1 line-clamp-2">{doc.descrizione}</p>}
        <p className="text-xs text-gray-400 mt-2">{formatDateTime(doc.created_at)}</p>
      </div>
    </div>
    <div className="flex items-center gap-2 mt-4 pt-4 border-t border-gray-100">
      <button onClick={() => onDownload(doc)} className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm text-[#1E4D8C] hover:bg-blue-50 rounded-md transition-colors" data-testid={`download-${doc.id}`}>
        <Download size={16} /> Scarica
      </button>
      {canDelete && (
        <button onClick={() => onDelete(doc.id)} className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors" data-testid={`delete-${doc.id}`}>
          <Trash2 size={16} />
        </button>
      )}
    </div>
  </div>
);

export default function DocumentiPage() {
  const { user } = useAuth();
  const [cartelle, setCartelle] = useState([]);
  const [aperta, setAperta] = useState(null);
  const [documenti, setDocumenti] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [showNuovaCartella, setShowNuovaCartella] = useState(false);

  const canCreateFolder = hasAnyRole(user, ['admin', 'superadmin']);
  const canUpload = !!aperta?.caricabile;

  const fetchCartelle = async () => {
    try {
      const res = await axios.get(`${API}/cartelle`);
      setCartelle(res.data);
      setAperta((prev) => (prev ? res.data.find((c) => c.id === prev.id) || null : null));
    } catch (error) {
      console.error('Error fetching cartelle:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDocumenti = async (cartella) => {
    try {
      const res = await axios.get(`${API}/documenti?cartella_id=${cartella.id}`);
      setDocumenti(res.data);
    } catch (error) {
      console.error('Error fetching documenti:', error);
    }
  };

  useEffect(() => { fetchCartelle(); }, []);
  useEffect(() => { if (aperta) fetchDocumenti(aperta); }, [aperta?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const refresh = () => { fetchCartelle(); if (aperta) fetchDocumenti(aperta); };

  const azione = async (fn, ok) => {
    try {
      await fn();
      toast.success(ok);
      refresh();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Operazione non riuscita');
    }
  };

  const toggleCartella = (c) => azione(
    () => axios.put(`${API}/cartelle/${c.id}/visibilita`, { visibile: !c.visibile }),
    c.visibile ? 'Cartella riservata agli Admin' : 'Cartella visibile a tutti',
  );

  const eliminaCartella = (c) => {
    if (window.confirm(`Eliminare la cartella "${c.nome}"?`)) azione(() => axios.delete(`${API}/cartelle/${c.id}`), 'Cartella eliminata');
  };

  const eliminaDocumento = (id) => {
    if (window.confirm('Sei sicuro di voler eliminare questo documento?')) azione(() => axios.delete(`${API}/documenti/${id}`), 'Documento eliminato');
  };

  const scarica = async (doc) => {
    try {
      const response = await axios.get(`${API}/documenti/${doc.id}/download`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', doc.filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      toast.error('Download non riuscito');
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
          <p className="text-gray-600 mt-1">Modulistica e documenti condivisi, divisi per cartella</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {canCreateFolder && !aperta && (
            <button onClick={() => setShowNuovaCartella(true)} className="flex items-center gap-2 border border-gray-300 bg-white hover:bg-gray-50 text-gray-800 font-medium rounded-md px-4 py-2 transition-colors" data-testid="nuova-cartella-btn">
              <FolderPlus size={18} /> Nuova cartella
            </button>
          )}
          {canUpload && (
            <button onClick={() => setShowUpload(true)} className="flex items-center gap-2 bg-[#1E4D8C] hover:bg-[#163A6A] text-white font-medium rounded-md px-4 py-2 transition-colors" data-testid="upload-documento-btn">
              <Upload size={18} /> Carica Documento
            </button>
          )}
        </div>
      </div>

      {!aperta && cartelle.length === 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center" data-testid="nessuna-cartella">
          <FolderOpen size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">Nessuna cartella disponibile</p>
        </div>
      )}

      {!aperta && cartelle.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="cartelle-grid">
          {cartelle.map((c) => <CartellaCard key={c.id} cartella={c} onOpen={setAperta} onToggle={toggleCartella} onDelete={eliminaCartella} />)}
        </div>
      )}

      {aperta && (
        <div className="space-y-4">
          <button onClick={() => { setAperta(null); setDocumenti([]); }} className="flex items-center gap-2 text-sm text-[#1E4D8C] hover:underline" data-testid="torna-cartelle-btn">
            <ArrowLeft size={16} /> Tutte le cartelle <span className="text-gray-400">/</span> <span className="font-semibold text-gray-900">{aperta.nome}</span>
          </button>
          {documenti.length === 0 ? (
            <div className="bg-white border border-gray-200 rounded-lg p-12 text-center" data-testid="cartella-vuota">
              <FolderOpen size={48} className="mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">Questa cartella è vuota</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {documenti.map((doc) => <DocumentoCard key={doc.id} doc={doc} canDelete={canUpload} onDownload={scarica} onDelete={eliminaDocumento} />)}
            </div>
          )}
        </div>
      )}

      {showNuovaCartella && (
        <NuovaCartellaDialog user={user} onClose={() => setShowNuovaCartella(false)}
          onCreated={() => { setShowNuovaCartella(false); toast.success('Cartella creata'); fetchCartelle(); }} />
      )}
      {showUpload && aperta && (
        <CaricaDocumentoDialog cartella={aperta} onClose={() => setShowUpload(false)}
          onUploaded={() => { setShowUpload(false); toast.success('Documento caricato'); refresh(); }} />
      )}
    </div>
  );
}
