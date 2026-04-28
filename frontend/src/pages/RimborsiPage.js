import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { formatDate, formatCurrency, STATI_RIMBORSO } from '../lib/utils';
import axios from 'axios';
import { Receipt, Plus, X, Upload, Eye, Check, XCircle, CreditCard, MapPin, AlertTriangle, FileText } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function RimborsiPage() {
  const { user } = useAuth();
  const [rimborsi, setRimborsi] = useState([]);
  const [motivi, setMotivi] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(null);
  const [selectedStato, setSelectedStato] = useState('');
  const [formData, setFormData] = useState({
    data: new Date().toISOString().split('T')[0],
    motivo_id: '',
    indirizzo_partenza: user?.indirizzo || '',
    indirizzo_partenza_tipo: user?.indirizzo ? 'casa' : 'manuale',
    indirizzo_arrivo: '',
    km_andata: 0,
    km_calcolati: null,
    km_modificati_manualmente: false,
    andata_ritorno: true,
    uso_autostrada: false,
    costo_autostrada: 0,
    importo_pasti: 0,
    numero_partecipanti_pasto: 0,
    note: ''
  });
  const [submitting, setSubmitting] = useState(false);
  const [calcolandoKm, setCalcolandoKm] = useState(false);
  const [selectedMotivo, setSelectedMotivo] = useState(null);

  const isAdmin = ['admin', 'cassiere', 'superadmin'].includes(user?.ruolo);

  useEffect(() => {
    fetchData();
  }, [selectedStato]);

  const fetchData = async () => {
    try {
      const [rimborsiRes, motiviRes] = await Promise.all([
        axios.get(`${API}/rimborsi${selectedStato ? `?stato=${selectedStato}` : ''}`),
        axios.get(`${API}/motivi-rimborso`)
      ]);
      setRimborsi(rimborsiRes.data);
      setMotivi(motiviRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMotivoChange = (motivoId) => {
    const motivo = motivi.find(m => m.id === motivoId);
    setSelectedMotivo(motivo);
    setFormData(prev => ({ ...prev, motivo_id: motivoId }));
  };

  const calcolaKm = useCallback(async () => {
    if (!formData.indirizzo_partenza || !formData.indirizzo_arrivo) return;
    
    setCalcolandoKm(true);
    try {
      const response = await axios.post(`${API}/calcola-km`, {
        origine: formData.indirizzo_partenza,
        destinazione: formData.indirizzo_arrivo
      });
      
      const kmCalcolati = response.data.km;
      setFormData(prev => ({
        ...prev,
        km_andata: kmCalcolati,
        km_calcolati: kmCalcolati,
        km_modificati_manualmente: false
      }));
    } catch (error) {
      console.error('Error calculating km:', error);
      alert(error.response?.data?.detail || 'Impossibile calcolare il percorso');
    } finally {
      setCalcolandoKm(false);
    }
  }, [formData.indirizzo_partenza, formData.indirizzo_arrivo]);

  const handleKmChange = (value) => {
    const newKm = parseFloat(value) || 0;
    const wasModified = formData.km_calcolati !== null && newKm !== formData.km_calcolati;
    setFormData(prev => ({
      ...prev,
      km_andata: newKm,
      km_modificati_manualmente: wasModified
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate note if motivo requires it
    if (selectedMotivo?.richiede_note && !formData.note) {
      alert('Per questo motivo le note sono obbligatorie');
      return;
    }
    
    setSubmitting(true);
    try {
      await axios.post(`${API}/rimborsi`, formData);
      setShowModal(false);
      resetForm();
      fetchData();
    } catch (error) {
      console.error('Error creating rimborso:', error);
      alert(error.response?.data?.detail || 'Errore durante la creazione');
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormData({
      data: new Date().toISOString().split('T')[0],
      motivo_id: '',
      indirizzo_partenza: user?.indirizzo || '',
      indirizzo_partenza_tipo: user?.indirizzo ? 'casa' : 'manuale',
      indirizzo_arrivo: '',
      km_andata: 0,
      km_calcolati: null,
      km_modificati_manualmente: false,
      andata_ritorno: true,
      uso_autostrada: false,
      costo_autostrada: 0,
      importo_pasti: 0,
      numero_partecipanti_pasto: 0,
      note: ''
    });
    setSelectedMotivo(null);
  };

  const handleUpdateStato = async (id, stato) => {
    try {
      await axios.put(`${API}/rimborsi/${id}`, { stato });
      fetchData();
      setShowDetailModal(null);
    } catch (error) {
      console.error('Error updating rimborso:', error);
      alert(error.response?.data?.detail || 'Errore durante l\'aggiornamento');
    }
  };

  const handleUploadContabile = async (id, file) => {
    try {
      const data = new FormData();
      data.append('file', file);
      await axios.post(`${API}/rimborsi/${id}/contabile`, data, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      fetchData();
      setShowDetailModal(null);
    } catch (error) {
      console.error('Error uploading contabile:', error);
      alert(error.response?.data?.detail || 'Errore durante il caricamento della contabile');
    }
  };

  const calcImportoPreview = () => {
    const km = formData.km_andata * (formData.andata_ritorno ? 2 : 1);
    const importoKm = km * 0.35; // Default rate, actual rate from sede
    const importoPasti = formData.importo_pasti;
    const importoAutostrada = formData.uso_autostrada ? formData.costo_autostrada : 0;
    return importoKm + importoPasti + importoAutostrada;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1E4D8C]"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="rimborsi-page">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 font-['Manrope']">Rimborsi</h1>
          <p className="text-gray-600 mt-1">
            {isAdmin ? 'Gestione richieste di rimborso' : 'Le tue richieste di rimborso'}
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-[#1E4D8C] hover:bg-[#163A6A] text-white font-medium rounded-md px-4 py-2 transition-colors"
          data-testid="new-rimborso-btn"
        >
          <Plus size={18} />
          Nuova Richiesta
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setSelectedStato('')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            selectedStato === '' ? 'bg-[#1E4D8C] text-white' : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
          }`}
          data-testid="filter-all"
        >
          Tutti
        </button>
        {Object.entries(STATI_RIMBORSO).map(([key, { label }]) => (
          <button
            key={key}
            onClick={() => setSelectedStato(key)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedStato === key ? 'bg-[#1E4D8C] text-white' : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
            data-testid={`filter-${key}`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Rimborsi Table */}
      {rimborsi.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
          <Receipt size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">Nessun rimborso trovato</p>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <th className="px-4 py-3">Data</th>
                  {isAdmin && <th className="px-4 py-3">Richiedente</th>}
                  <th className="px-4 py-3">Motivo</th>
                  <th className="px-4 py-3">KM</th>
                  <th className="px-4 py-3">Importo</th>
                  <th className="px-4 py-3">Stato</th>
                  <th className="px-4 py-3">Azioni</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {rimborsi.map(rimborso => (
                  <tr key={rimborso.id} className="hover:bg-gray-50" data-testid={`rimborso-row-${rimborso.id}`}>
                    <td className="px-4 py-3 text-sm text-gray-900">{formatDate(rimborso.data)}</td>
                    {isAdmin && (
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {rimborso.user_nome}
                        {rimborso.km_modificati_manualmente && (
                          <span className="ml-2 text-orange-500" title="KM modificati manualmente">
                            <AlertTriangle size={14} className="inline" />
                          </span>
                        )}
                      </td>
                    )}
                    <td className="px-4 py-3 text-sm text-gray-600">{rimborso.motivo_nome || 'N/A'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{rimborso.km_totali}</td>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{formatCurrency(rimborso.importo_totale)}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        STATI_RIMBORSO[rimborso.stato]?.badgeClass || 'bg-gray-100 text-gray-700'
                      }`}>
                        {STATI_RIMBORSO[rimborso.stato]?.label || rimborso.stato}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => setShowDetailModal(rimborso)}
                        className="p-2 text-gray-600 hover:text-[#1E4D8C] hover:bg-blue-50 rounded-md transition-colors"
                        data-testid={`view-rimborso-${rimborso.id}`}
                      >
                        <Eye size={18} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* New Rimborso Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-lg w-full max-w-2xl my-8">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Nuova Richiesta Rimborso</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Data *</label>
                  <input
                    type="date"
                    value={formData.data}
                    onChange={(e) => setFormData(prev => ({ ...prev, data: e.target.value }))}
                    required
                    className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                    data-testid="rimborso-data-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Motivo *</label>
                  <select
                    value={formData.motivo_id}
                    onChange={(e) => handleMotivoChange(e.target.value)}
                    required
                    className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                    data-testid="rimborso-motivo-select"
                  >
                    <option value="">Seleziona motivo</option>
                    {motivi.map(m => (
                      <option key={m.id} value={m.id}>{m.nome}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Indirizzo Partenza */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Partenza da</label>
                <div className="flex gap-4 mb-2">
                  {user?.indirizzo && (
                    <label className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="partenza_tipo"
                        value="casa"
                        checked={formData.indirizzo_partenza_tipo === 'casa'}
                        onChange={() => setFormData(prev => ({ 
                          ...prev, 
                          indirizzo_partenza_tipo: 'casa', 
                          indirizzo_partenza: user?.indirizzo || '' 
                        }))}
                        className="text-[#1E4D8C]"
                      />
                      <span className="text-sm">Casa ({user.indirizzo})</span>
                    </label>
                  )}
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="partenza_tipo"
                      value="manuale"
                      checked={formData.indirizzo_partenza_tipo === 'manuale'}
                      onChange={() => setFormData(prev => ({ 
                        ...prev, 
                        indirizzo_partenza_tipo: 'manuale', 
                        indirizzo_partenza: '' 
                      }))}
                      className="text-[#1E4D8C]"
                    />
                    <span className="text-sm">Altro indirizzo</span>
                  </label>
                </div>
                {formData.indirizzo_partenza_tipo === 'manuale' && (
                  <input
                    type="text"
                    value={formData.indirizzo_partenza}
                    onChange={(e) => setFormData(prev => ({ ...prev, indirizzo_partenza: e.target.value }))}
                    placeholder="Indirizzo completo di partenza"
                    required
                    className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                    data-testid="rimborso-partenza-input"
                  />
                )}
              </div>

              {/* Indirizzo Arrivo */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Destinazione *</label>
                <input
                  type="text"
                  value={formData.indirizzo_arrivo}
                  onChange={(e) => setFormData(prev => ({ ...prev, indirizzo_arrivo: e.target.value }))}
                  placeholder="Indirizzo completo di destinazione"
                  required
                  className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                  data-testid="rimborso-arrivo-input"
                />
              </div>

              {/* Calcolo KM */}
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-gray-700">Calcolo Chilometri</span>
                  <button
                    type="button"
                    onClick={calcolaKm}
                    disabled={calcolandoKm || !formData.indirizzo_partenza || !formData.indirizzo_arrivo}
                    className="flex items-center gap-2 px-3 py-1.5 bg-[#1E4D8C] hover:bg-[#163A6A] text-white text-sm rounded-md disabled:opacity-50"
                    data-testid="calcola-km-btn"
                  >
                    <MapPin size={14} />
                    {calcolandoKm ? 'Calcolo...' : 'Calcola con Google Maps'}
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-gray-600 mb-1">KM Andata</label>
                    <input
                      type="number"
                      step="1"
                      min="0"
                      value={formData.km_andata}
                      onChange={(e) => handleKmChange(e.target.value)}
                      required
                      className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                      data-testid="rimborso-km-input"
                    />
                    {formData.km_modificati_manualmente && (
                      <p className="text-xs text-orange-600 mt-1 flex items-center gap-1">
                        <AlertTriangle size={12} />
                        KM modificati manualmente (verrà notificato all'admin)
                      </p>
                    )}
                  </div>
                  <div className="flex items-end pb-2">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={formData.andata_ritorno}
                        onChange={(e) => setFormData(prev => ({ ...prev, andata_ritorno: e.target.checked }))}
                        className="rounded text-[#1E4D8C]"
                      />
                      <span className="text-sm">Andata e Ritorno</span>
                    </label>
                  </div>
                </div>
              </div>

              {/* Autostrada */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="flex items-center gap-2 mb-2">
                    <input
                      type="checkbox"
                      checked={formData.uso_autostrada}
                      onChange={(e) => setFormData(prev => ({ 
                        ...prev, 
                        uso_autostrada: e.target.checked, 
                        costo_autostrada: e.target.checked ? prev.costo_autostrada : 0 
                      }))}
                      className="rounded text-[#1E4D8C]"
                    />
                    <span className="text-sm font-medium text-gray-700">Uso Autostrada</span>
                  </label>
                  {formData.uso_autostrada && (
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={formData.costo_autostrada}
                      onChange={(e) => setFormData(prev => ({ ...prev, costo_autostrada: parseFloat(e.target.value) || 0 }))}
                      placeholder="Costo pedaggi €"
                      className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                      data-testid="rimborso-autostrada-input"
                    />
                  )}
                </div>
              </div>

              {/* Pasti */}
              <div className="border-t border-gray-200 pt-4">
                <label className="block text-sm font-medium text-gray-700 mb-3">Spese Pasti</label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-gray-600 mb-1">Importo Totale Pasti (€)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={formData.importo_pasti}
                      onChange={(e) => setFormData(prev => ({ ...prev, importo_pasti: parseFloat(e.target.value) || 0 }))}
                      placeholder="0.00"
                      className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                      data-testid="rimborso-importo-pasti-input"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-600 mb-1">Numero Partecipanti</label>
                    <input
                      type="number"
                      min="0"
                      value={formData.numero_partecipanti_pasto}
                      onChange={(e) => setFormData(prev => ({ ...prev, numero_partecipanti_pasto: parseInt(e.target.value) || 0 }))}
                      placeholder="0"
                      className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
                      data-testid="rimborso-partecipanti-input"
                    />
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-2">Ricorda di caricare la ricevuta dopo aver creato il rimborso</p>
              </div>

              {/* Note */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Note {selectedMotivo?.richiede_note && <span className="text-red-500">*</span>}
                </label>
                <textarea
                  value={formData.note}
                  onChange={(e) => setFormData(prev => ({ ...prev, note: e.target.value }))}
                  required={selectedMotivo?.richiede_note}
                  rows={3}
                  placeholder={selectedMotivo?.richiede_note ? 'Note obbligatorie per questo motivo' : 'Note aggiuntive (opzionale)'}
                  className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none resize-none"
                  data-testid="rimborso-note-input"
                />
              </div>

              {/* Preview */}
              <div className="bg-green-50 rounded-lg p-4">
                <p className="text-sm text-gray-600">Importo stimato:</p>
                <p className="text-2xl font-bold text-[#1E4D8C]">{formatCurrency(calcImportoPreview())}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {formData.km_andata * (formData.andata_ritorno ? 2 : 1)} km × €0.35 = {formatCurrency(formData.km_andata * (formData.andata_ritorno ? 2 : 1) * 0.35)}
                  {formData.importo_pasti > 0 && ` + pasti = ${formatCurrency(formData.importo_pasti)}`}
                  {formData.uso_autostrada && formData.costo_autostrada > 0 && ` + autostrada = ${formatCurrency(formData.costo_autostrada)}`}
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
                  data-testid="submit-rimborso-btn"
                >
                  {submitting ? 'Invio...' : 'Invia Richiesta'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {showDetailModal && (
        <RimborsoDetailModal
          rimborso={showDetailModal}
          isAdmin={isAdmin}
          onClose={() => setShowDetailModal(null)}
          onUpdateStato={handleUpdateStato}
          onUploadContabile={handleUploadContabile}
          onRefresh={fetchData}
        />
      )}
    </div>
  );
}

function RimborsoDetailModal({ rimborso, isAdmin, onClose, onUpdateStato, onUploadContabile, onRefresh }) {
  const [contabileFile, setContabileFile] = useState(null);
  const [uploadingSpesa, setUploadingSpesa] = useState(false);
  const [spesaFile, setSpesaFile] = useState(null);
  const [spesaTipo, setSpesaTipo] = useState('pasto');
  const [spesaDescrizione, setSpesaDescrizione] = useState('');

  const handleUploadSpesa = async () => {
    if (!spesaFile) return;
    setUploadingSpesa(true);
    try {
      const formData = new FormData();
      formData.append('file', spesaFile);
      formData.append('tipo', spesaTipo);
      formData.append('descrizione', spesaDescrizione);
      
      await axios.post(`${API}/rimborsi/${rimborso.id}/ricevute-spese`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setSpesaFile(null);
      setSpesaDescrizione('');
      onRefresh();
    } catch (error) {
      console.error('Error uploading spesa:', error);
      alert(error.response?.data?.detail || 'Errore durante il caricamento');
    } finally {
      setUploadingSpesa(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-lg w-full max-w-lg my-8">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Dettaglio Rimborso</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={20} />
          </button>
        </div>
        <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
          {/* Alert KM modificati */}
          {rimborso.km_modificati_manualmente && (
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 flex items-start gap-2">
              <AlertTriangle size={18} className="text-orange-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-orange-800">KM modificati manualmente</p>
                <p className="text-xs text-orange-600">
                  Calcolati: {rimborso.km_calcolati || 'N/A'} km | Inseriti: {rimborso.km_andata} km
                </p>
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500">Data</p>
              <p className="font-medium">{formatDate(rimborso.data)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Stato</p>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                STATI_RIMBORSO[rimborso.stato]?.badgeClass || 'bg-gray-100 text-gray-700'
              }`}>
                {STATI_RIMBORSO[rimborso.stato]?.label || rimborso.stato}
              </span>
            </div>
            <div>
              <p className="text-sm text-gray-500">Motivo</p>
              <p className="font-medium">{rimborso.motivo_nome || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">KM Totali</p>
              <p className="font-medium">{rimborso.km_totali}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Partenza</p>
              <p className="font-medium text-sm">{rimborso.indirizzo_partenza}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Destinazione</p>
              <p className="font-medium text-sm">{rimborso.indirizzo_arrivo}</p>
            </div>
          </div>

          <div className="border-t border-gray-200 pt-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Rimborso KM</span>
              <span className="font-medium">{formatCurrency(rimborso.importo_km)}</span>
            </div>
            {rimborso.importo_pasti > 0 && (
              <div className="flex justify-between items-center mt-2">
                <span className="text-gray-600">Pasti ({rimborso.numero_partecipanti_pasto || 0} pers.)</span>
                <span className="font-medium">{formatCurrency(rimborso.importo_pasti)}</span>
              </div>
            )}
            {rimborso.uso_autostrada && (
              <div className="flex justify-between items-center mt-2">
                <span className="text-gray-600">Autostrada</span>
                <span className="font-medium">{formatCurrency(rimborso.costo_autostrada)}</span>
              </div>
            )}
            <div className="flex justify-between items-center mt-4 pt-4 border-t border-gray-200">
              <span className="text-lg font-semibold">Totale</span>
              <span className="text-lg font-bold text-[#1E4D8C]">{formatCurrency(rimborso.importo_totale)}</span>
            </div>
          </div>

          {rimborso.note && (
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-sm text-gray-500 mb-1">Note</p>
              <p className="text-sm">{rimborso.note}</p>
            </div>
          )}

          {/* Ricevute spese */}
          {rimborso.ricevute_spese && rimborso.ricevute_spese.length > 0 && (
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">Ricevute Spese</p>
              <div className="space-y-2">
                {rimborso.ricevute_spese.map((r, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm bg-gray-50 px-3 py-2 rounded">
                    <FileText size={14} className="text-gray-400" />
                    <span className="capitalize">{r.tipo}</span>
                    {r.descrizione && <span className="text-gray-500">- {r.descrizione}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Upload ricevuta spesa (solo se in_attesa e proprietario) */}
          {rimborso.stato === 'in_attesa' && (
            <div className="border-t border-gray-200 pt-4">
              <p className="text-sm font-medium text-gray-700 mb-2">Carica Ricevuta Spesa</p>
              <div className="space-y-2">
                <select
                  value={spesaTipo}
                  onChange={(e) => setSpesaTipo(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  <option value="pasto">Pasto</option>
                  <option value="altro">Altro</option>
                </select>
                <input
                  type="text"
                  value={spesaDescrizione}
                  onChange={(e) => setSpesaDescrizione(e.target.value)}
                  placeholder="Descrizione (opzionale)"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                />
                <div className="flex gap-2">
                  <input
                    type="file"
                    onChange={(e) => setSpesaFile(e.target.files?.[0] || null)}
                    accept=".pdf,.jpg,.jpeg,.png"
                    className="flex-1 text-sm"
                  />
                  <button
                    onClick={handleUploadSpesa}
                    disabled={!spesaFile || uploadingSpesa}
                    className="px-3 py-2 bg-[#1E4D8C] text-white text-sm rounded-md disabled:opacity-50"
                  >
                    <Upload size={16} />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Admin Actions */}
          {isAdmin && rimborso.stato === 'in_attesa' && (
            <div className="space-y-3 pt-4 border-t border-gray-200">
              <div className="flex gap-2">
                <button
                  onClick={() => onUpdateStato(rimborso.id, 'approvato')}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded-md transition-colors"
                  data-testid="approve-rimborso-btn"
                >
                  <Check size={18} />
                  Approva
                </button>
                <button
                  onClick={() => onUpdateStato(rimborso.id, 'rifiutato')}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
                  data-testid="reject-rimborso-btn"
                >
                  <XCircle size={18} />
                  Rifiuta
                </button>
              </div>

              {/* Pagamento diretto: salta approvazione */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                <p className="text-xs font-medium text-gray-700 mb-2">
                  Oppure paga direttamente (carica contabile)
                </p>
                <div className="flex gap-2">
                  <input
                    type="file"
                    onChange={(e) => setContabileFile(e.target.files?.[0] || null)}
                    accept=".pdf,.jpg,.jpeg,.png"
                    className="flex-1 text-sm"
                    data-testid="contabile-file-direct"
                  />
                  <button
                    onClick={() => contabileFile && onUploadContabile(rimborso.id, contabileFile)}
                    disabled={!contabileFile}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors disabled:opacity-50"
                    data-testid="pay-direct-btn"
                  >
                    <CreditCard size={18} />
                    Paga
                  </button>
                </div>
              </div>
            </div>
          )}

          {isAdmin && rimborso.stato === 'approvato' && (
            <div className="pt-4 border-t border-gray-200">
              <p className="text-sm font-medium text-gray-700 mb-2">
                Carica Contabile per chiudere il pagamento <span className="text-red-500">*</span>
              </p>
              <div className="flex gap-2">
                <input
                  type="file"
                  onChange={(e) => setContabileFile(e.target.files?.[0] || null)}
                  accept=".pdf,.jpg,.jpeg,.png"
                  className="flex-1 text-sm"
                  data-testid="contabile-file-input"
                />
                <button
                  onClick={() => contabileFile && onUploadContabile(rimborso.id, contabileFile)}
                  disabled={!contabileFile}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors disabled:opacity-50"
                  data-testid="upload-contabile-btn"
                >
                  <CreditCard size={18} />
                  Paga
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-1">PDF, JPG, PNG (max 5MB)</p>
            </div>
          )}

          {/* Mostra contabile se pagato */}
          {rimborso.stato === 'pagato' && rimborso.contabile && (
            <div className="pt-4 border-t border-gray-200">
              <p className="text-sm font-medium text-gray-700 mb-2">Contabile pagamento</p>
              <div className="flex items-center gap-2 bg-green-50 px-3 py-2 rounded">
                <FileText size={16} className="text-green-600" />
                <span className="text-sm">{rimborso.contabile.filename}</span>
              </div>
              {rimborso.pagato_by_nome && (
                <p className="text-xs text-gray-500 mt-2">
                  Pagato da: {rimborso.pagato_by_nome}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
