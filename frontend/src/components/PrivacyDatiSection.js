import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Shield, Download, FileArchive, Trash2, RotateCcw, AlertCircle, CheckCircle,
  Info, Clock,
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function PrivacyDatiSection() {
  const [stato, setStato] = useState(null); // {pending, esecuzione_prevista, anonimizzazione_prevista, ...}
  const [loading, setLoading] = useState(true);
  const [downloadingJson, setDownloadingJson] = useState(false);
  const [downloadingZip, setDownloadingZip] = useState(false);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [motivo, setMotivo] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    loadStato();
  }, []);

  const loadStato = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/gdpr/stato-cancellazione`);
      setStato(res.data);
    } catch (e) {
      setStato({ pending: false });
    } finally {
      setLoading(false);
    }
  };

  const downloadJSON = async () => {
    setDownloadingJson(true);
    try {
      const res = await axios.get(`${API}/gdpr/my-data`);
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `miei_dati_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert('Errore download dati');
    } finally {
      setDownloadingJson(false);
    }
  };

  const downloadZIP = async () => {
    setDownloadingZip(true);
    try {
      const res = await axios.get(`${API}/gdpr/export-zip`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = `miei_dati_${new Date().toISOString().split('T')[0]}.zip`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert('Errore download ZIP');
    } finally {
      setDownloadingZip(false);
    }
  };

  const richiediCancellazione = async () => {
    setSubmitting(true);
    setError('');
    setSuccess('');
    try {
      const res = await axios.post(`${API}/gdpr/richiedi-cancellazione`, { motivo });
      setSuccess(res.data.messaggio || 'Richiesta ricevuta');
      setShowCancelModal(false);
      setMotivo('');
      await loadStato();
    } catch (err) {
      setError(err.response?.data?.detail || 'Errore invio richiesta');
    } finally {
      setSubmitting(false);
    }
  };

  const annullaCancellazione = async () => {
    if (!window.confirm('Sei sicuro di voler annullare la richiesta di cancellazione? Il tuo account resterà attivo.')) return;
    setSubmitting(true);
    try {
      await axios.post(`${API}/gdpr/annulla-cancellazione`);
      setSuccess('Richiesta annullata. Il tuo account resta attivo.');
      await loadStato();
    } catch (err) {
      setError(err.response?.data?.detail || 'Errore annullamento');
    } finally {
      setSubmitting(false);
    }
  };

  const fmtDate = (v) => {
    if (!v) return '-';
    try {
      return new Date(v).toLocaleDateString('it-IT', { day: '2-digit', month: 'long', year: 'numeric' });
    } catch {
      return v;
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6" data-testid="privacy-dati-section">
      <div className="flex items-center gap-2 mb-4">
        <Shield size={20} className="text-[#1E4D8C]" />
        <h2 className="text-lg font-semibold text-gray-900">Privacy & I miei dati</h2>
      </div>
      <p className="text-sm text-gray-500 mb-4">
        Esercita i tuoi diritti secondo il Regolamento GDPR: accesso, portabilità e cancellazione dei tuoi dati.
      </p>

      {error && (
        <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm flex items-center gap-2">
          <AlertCircle size={16} /> {error}
        </div>
      )}
      {success && (
        <div className="mb-3 p-3 bg-green-50 border border-green-200 rounded-md text-green-700 text-sm flex items-center gap-2">
          <CheckCircle size={16} /> {success}
        </div>
      )}

      {/* Download dati */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
        <button
          onClick={downloadJSON}
          disabled={downloadingJson}
          className="flex items-start gap-3 border border-gray-200 hover:border-[#1E4D8C] hover:bg-blue-50/40 rounded-md p-3 text-left transition-colors disabled:opacity-50"
          data-testid="download-json-btn"
        >
          <Download size={20} className="text-[#1E4D8C] flex-shrink-0 mt-0.5" />
          <div>
            <div className="text-sm font-medium text-gray-900">Scarica i miei dati (JSON)</div>
            <div className="text-xs text-gray-500">Estratto leggibile dei tuoi dati anagrafici, rimborsi e consensi</div>
          </div>
        </button>
        <button
          onClick={downloadZIP}
          disabled={downloadingZip}
          className="flex items-start gap-3 border border-gray-200 hover:border-[#1E4D8C] hover:bg-blue-50/40 rounded-md p-3 text-left transition-colors disabled:opacity-50"
          data-testid="download-zip-btn"
        >
          <FileArchive size={20} className="text-[#1E4D8C] flex-shrink-0 mt-0.5" />
          <div>
            <div className="text-sm font-medium text-gray-900">Archivio completo (ZIP)</div>
            <div className="text-xs text-gray-500">Dati JSON + tutte le ricevute e contabili caricate</div>
          </div>
        </button>
      </div>

      {/* Cancellazione */}
      <div className="border-t border-gray-200 pt-5">
        {loading ? (
          <div className="text-sm text-gray-400">Caricamento stato cancellazione...</div>
        ) : stato?.pending ? (
          <div className="bg-red-50 border border-red-200 rounded-md p-4" data-testid="stato-cancellazione-pending">
            <div className="flex items-start gap-3">
              <Clock size={20} className="text-red-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <div className="font-semibold text-red-900">Richiesta cancellazione in corso</div>
                <div className="text-sm text-red-800 mt-1 space-y-0.5">
                  <div>Account verrà disabilitato il: <b>{fmtDate(stato.esecuzione_prevista)}</b> ({stato.giorni_residui} gg residui)</div>
                  {stato.anonimizzazione_prevista && (
                    <div>Anonimizzazione dati anagrafici: <b>{fmtDate(stato.anonimizzazione_prevista)}</b></div>
                  )}
                  <div className="text-xs mt-2 italic">I rimborsi contabili restano conservati per obblighi fiscali (10 anni).</div>
                </div>
                <button
                  onClick={annullaCancellazione}
                  disabled={submitting}
                  className="mt-3 flex items-center gap-2 bg-white border border-red-300 hover:bg-red-100 text-red-700 font-medium rounded-md px-4 py-2 text-sm transition-colors disabled:opacity-50"
                  data-testid="annulla-cancellazione-btn"
                >
                  <RotateCcw size={16} /> Annulla la richiesta
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Trash2 size={16} className="text-red-600" />
              <span className="text-sm font-medium text-gray-900">Cancellazione account</span>
            </div>
            <p className="text-xs text-gray-500 mb-3">
              Dopo la richiesta hai 30 giorni per annullarla, poi il tuo account verrà disabilitato.
              L'anonimizzazione dei dati anagrafici avviene a fine marzo dell'anno successivo (per obblighi contabili).
            </p>
            <button
              onClick={() => setShowCancelModal(true)}
              className="flex items-center gap-2 border border-red-300 hover:bg-red-50 text-red-700 font-medium rounded-md px-4 py-2 text-sm transition-colors"
              data-testid="richiedi-cancellazione-btn"
            >
              <Trash2 size={16} /> Richiedi cancellazione account
            </button>
          </div>
        )}
      </div>

      {/* Info GDPR */}
      <div className="mt-5 pt-5 border-t border-gray-200">
        <div className="flex items-start gap-2 text-xs text-gray-500">
          <Info size={14} className="flex-shrink-0 mt-0.5" />
          <div>
            Per ulteriori diritti (rettifica, limitazione, opposizione), consulta l'
            <a href="/privacy" className="text-[#1E4D8C] hover:underline">Informativa Privacy</a> completa
            oppure contatta il titolare tramite i canali indicati.
          </div>
        </div>
      </div>

      {/* Modal conferma cancellazione */}
      {showCancelModal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6" data-testid="cancel-modal">
            <div className="flex items-center gap-2 mb-3">
              <Trash2 size={20} className="text-red-600" />
              <h3 className="text-lg font-semibold">Conferma richiesta cancellazione</h3>
            </div>
            <div className="text-sm text-gray-700 space-y-2 mb-4">
              <p><b>Cosa succede dopo la conferma:</b></p>
              <ul className="list-disc list-inside text-xs space-y-1 ml-2">
                <li><b>Entro 30 giorni:</b> puoi annullare la richiesta in qualsiasi momento</li>
                <li><b>Dopo 30 giorni:</b> il tuo account viene disabilitato (login bloccato)</li>
                <li><b>Fine marzo anno successivo:</b> dati anagrafici anonimizzati definitivamente</li>
                <li><b>Rimborsi contabili:</b> conservati 10 anni per obbligo fiscale (art. 2220 c.c.)</li>
              </ul>
            </div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Motivo (opzionale)</label>
            <textarea
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              rows={3}
              placeholder="Puoi indicare il motivo per aiutarci a migliorare il servizio..."
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
              data-testid="cancel-motivo-input"
            />
            {error && (
              <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded-md text-red-700 text-xs flex items-center gap-1">
                <AlertCircle size={14} /> {error}
              </div>
            )}
            <div className="flex gap-2 justify-end mt-4">
              <button
                onClick={() => { setShowCancelModal(false); setMotivo(''); setError(''); }}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-md text-sm"
                data-testid="cancel-modal-close-btn"
              >
                Annulla
              </button>
              <button
                onClick={richiediCancellazione}
                disabled={submitting}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md text-sm disabled:opacity-50"
                data-testid="cancel-modal-confirm-btn"
              >
                {submitting ? 'Invio...' : 'Conferma richiesta'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
