import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { hasRole } from '../lib/utils';
import axios from 'axios';
import {
  Settings, Save, Shield, FileText, ClipboardList, Eye, Lock,
  AlertCircle, CheckCircle, Download, RefreshCw, User, Building2, Mail
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TABS = [
  { id: 'dati', label: 'Dati Sindacato', icon: Building2 },
  { id: 'documenti', label: 'Documenti Legali', icon: FileText },
  { id: 'compliance', label: 'Compliance', icon: ClipboardList },
];

const DOC_TYPES = [
  { id: 'privacy', label: 'Informativa Privacy (art. 13 GDPR)', endpoint: 'privacy' },
  { id: 'cookie', label: 'Cookie Policy', endpoint: 'cookie-policy' },
  { id: 'termini', label: 'Termini di Servizio', endpoint: 'termini' },
];

export default function ImpostazioniSindacatoPage() {
  const { user } = useAuth();
  const [tab, setTab] = useState('dati');

  if (!hasRole(user, 'superadmin')) {
    return (
      <div className="text-center py-12" data-testid="impostazioni-forbidden">
        <p className="text-gray-500">Accesso riservato al SuperAdmin</p>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="impostazioni-sindacato-page">
      <div className="flex items-center gap-3">
        <Settings size={28} className="text-[#1E4D8C]" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900 font-['Manrope']">Impostazioni Sindacato</h1>
          <p className="text-gray-600 text-sm">Gestione dati titolare, documenti legali e compliance GDPR</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-2 -mb-px">
          {TABS.map((t) => {
            const Icon = t.icon;
            const active = tab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex items-center gap-2 px-4 py-3 border-b-2 text-sm font-medium transition-colors ${
                  active
                    ? 'border-[#1E4D8C] text-[#1E4D8C]'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
                data-testid={`tab-${t.id}`}
              >
                <Icon size={16} />
                {t.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab content */}
      {tab === 'dati' && <TabDatiSindacato />}
      {tab === 'documenti' && <TabDocumentiLegali user={user} />}
      {tab === 'compliance' && <TabCompliance />}
    </div>
  );
}

// ==================== TAB 1: DATI SINDACATO ====================

function TabDatiSindacato() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    load();
  }, []);

  const load = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/impostazioni-sindacato`);
      setData(res.data);
    } catch (e) {
      setError('Errore caricamento dati');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess(false);
    try {
      await axios.put(`${API}/impostazioni-sindacato`, data);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Errore salvataggio');
    } finally {
      setSaving(false);
    }
  };

  if (loading || !data) {
    return <div className="text-center py-8 text-gray-400">Caricamento...</div>;
  }

  const field = (key, label, placeholder = '', required = false) => (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      <input
        type="text"
        value={data[key] || ''}
        onChange={(e) => setData((prev) => ({ ...prev, [key]: e.target.value }))}
        placeholder={placeholder}
        required={required}
        className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
        data-testid={`dati-${key}-input`}
      />
    </div>
  );

  return (
    <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-lg p-6 space-y-6" data-testid="tab-dati-form">
      <div className="text-sm bg-blue-50 border border-blue-200 rounded-md p-3 text-blue-900">
        <User size={14} className="inline mr-1" />
        Questi dati compaiono nell&apos;Informativa Privacy, Cookie Policy e Termini di Servizio.
        Modificabili liberamente (senza 2FA aggiuntivo).
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm flex items-center gap-2">
          <AlertCircle size={16} /> {error}
        </div>
      )}
      {success && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-md text-green-700 text-sm flex items-center gap-2">
          <CheckCircle size={16} /> Dati salvati con successo
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {field('denominazione', 'Denominazione', 'SLA - CISAL', true)}
        {field('codice_fiscale', 'Codice Fiscale', '91027960102', true)}
        <div className="md:col-span-2">{field('sede_legale', 'Sede legale', 'Via ... - Città', true)}</div>
        {field('partita_iva', 'Partita IVA (opzionale)', 'IT...')}
        {field('foro_competente', 'Foro competente', 'Genova', true)}
      </div>

      <hr className="border-gray-200" />
      <div className="text-sm font-medium text-gray-700"><Mail size={14} className="inline mr-1" />Contatti privacy</div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {field('pec', 'PEC', 'sla-cisal@pec.esempio.it', true)}
        {field('email_privacy', 'Email per esercizio diritti privacy', 'privacy@sla-cisal.example.it', true)}
        <div className="md:col-span-2">{field('sito_web', 'Sito web (opzionale)', 'https://...')}</div>
      </div>

      <hr className="border-gray-200" />
      <div className="text-sm font-medium text-gray-700"><Shield size={14} className="inline mr-1" />DPO — Data Protection Officer (opzionale)</div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {field('dpo_nome', 'Nome DPO', 'Nome Cognome')}
        {field('dpo_email', 'Email DPO', 'dpo@...')}
      </div>

      <div className="pt-2">
        <button
          type="submit"
          disabled={saving}
          className="flex items-center gap-2 bg-[#1E4D8C] hover:bg-[#163A6A] text-white font-medium rounded-md px-6 py-2 transition-colors disabled:opacity-50"
          data-testid="save-dati-btn"
        >
          <Save size={18} />
          {saving ? 'Salvataggio...' : 'Salva dati sindacato'}
        </button>
      </div>
    </form>
  );
}

// ==================== TAB 2: DOCUMENTI LEGALI ====================

function TabDocumentiLegali({ user }) {
  const [docId, setDocId] = useState('privacy');
  const [content, setContent] = useState('');
  const [version, setVersion] = useState('');
  const [loading, setLoading] = useState(true);
  const [preview, setPreview] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [showTotpModal, setShowTotpModal] = useState(false);

  useEffect(() => {
    loadDoc();
     
  }, [docId]);

  const loadDoc = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const doc = DOC_TYPES.find((d) => d.id === docId);
      const res = await axios.get(`${API}/${doc.endpoint}`);
      setContent(res.data.contenuto);
      setVersion(res.data.version);
    } catch (e) {
      setError('Errore caricamento documento');
    } finally {
      setLoading(false);
    }
  };

  const loadPreview = async () => {
    try {
      const res = await axios.get(`${API}/documenti-legali/${docId}/anteprima`);
      setPreview(res.data.contenuto);
      setShowPreview(true);
    } catch (e) {
      setError('Errore caricamento anteprima');
    }
  };

  const doSave = async (code = null) => {
    setSaving(true);
    setError('');
    try {
      const payload = { contenuto: content };
      if (code) payload.totp_code = code;
      const res = await axios.put(`${API}/documenti-legali/${docId}`, payload);
      setSuccess(`Salvato — nuova versione: ${res.data.version}`);
      setVersion(res.data.version);
      setShowTotpModal(false);
      setTotpCode('');
      setTimeout(() => setSuccess(''), 4000);
    } catch (err) {
      if (err.response?.status === 401 && err.response?.data?.detail?.includes('2FA')) {
        setShowTotpModal(true);
        setError('');
      } else {
        setError(err.response?.data?.detail || 'Errore salvataggio');
        setShowTotpModal(false);
      }
    } finally {
      setSaving(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (user?.totp_enabled) {
      setShowTotpModal(true);
    } else {
      doSave();
    }
  };

  return (
    <div className="space-y-4" data-testid="tab-documenti">
      <div className="text-sm bg-amber-50 border border-amber-200 rounded-md p-3 text-amber-900 flex items-start gap-2">
        <Lock size={16} className="flex-shrink-0 mt-0.5" />
        <div>
          <b>Step-up 2FA:</b> Se hai attivato l&apos;autenticazione a due fattori sul tuo account, ti sarà richiesto il codice al momento del salvataggio.
          Ogni salvataggio incrementa automaticamente la versione del documento.
        </div>
      </div>

      {/* Selector documento */}
      <div className="flex flex-wrap gap-2">
        {DOC_TYPES.map((d) => (
          <button
            key={d.id}
            onClick={() => setDocId(d.id)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              docId === d.id ? 'bg-[#1E4D8C] text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
            data-testid={`doc-tab-${d.id}`}
          >
            {d.label}
          </button>
        ))}
      </div>

      <div className="bg-white border border-gray-200 rounded-lg">
        <div className="px-4 py-3 border-b border-gray-200 flex flex-wrap items-center justify-between gap-2">
          <div className="text-sm">
            <span className="font-medium text-gray-700">Versione corrente:</span>{' '}
            <span className="inline-flex items-center px-2 py-0.5 rounded bg-blue-100 text-blue-800 text-xs font-mono" data-testid="doc-version-badge">
              v{version}
            </span>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={loadPreview}
              className="flex items-center gap-1.5 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md px-3 py-1.5"
              data-testid="preview-btn"
            >
              <Eye size={14} /> Anteprima template
            </button>
            <button
              type="button"
              onClick={loadDoc}
              className="flex items-center gap-1.5 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md px-3 py-1.5"
              data-testid="reload-doc-btn"
            >
              <RefreshCw size={14} /> Ricarica
            </button>
          </div>
        </div>

        {error && (
          <div className="p-3 mx-4 mt-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm flex items-center gap-2">
            <AlertCircle size={16} /> {error}
          </div>
        )}
        {success && (
          <div className="p-3 mx-4 mt-3 bg-green-50 border border-green-200 rounded-md text-green-700 text-sm flex items-center gap-2">
            <CheckCircle size={16} /> {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="p-4">
          {loading ? (
            <div className="text-center py-8 text-gray-400">Caricamento...</div>
          ) : (
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={22}
              className="w-full border border-gray-300 rounded-md px-3 py-2 font-mono text-xs focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
              placeholder="Contenuto Markdown..."
              data-testid="doc-textarea"
            />
          )}

          <div className="pt-4 flex justify-end">
            <button
              type="submit"
              disabled={saving || loading}
              className="flex items-center gap-2 bg-[#1E4D8C] hover:bg-[#163A6A] text-white font-medium rounded-md px-6 py-2 transition-colors disabled:opacity-50"
              data-testid="save-doc-btn"
            >
              <Save size={18} />
              {saving ? 'Salvataggio...' : 'Salva nuova versione'}
            </button>
          </div>
        </form>
      </div>

      {/* Modal Anteprima */}
      {showPreview && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-3xl w-full max-h-[85vh] overflow-hidden flex flex-col" data-testid="preview-modal">
            <div className="p-4 border-b border-gray-200 flex justify-between items-center">
              <h3 className="font-semibold text-gray-900">Anteprima template — {DOC_TYPES.find((d) => d.id === docId)?.label}</h3>
              <button onClick={() => setShowPreview(false)} className="text-gray-500 hover:text-gray-800" data-testid="preview-close-btn">✕</button>
            </div>
            <div className="p-4 overflow-y-auto flex-1">
              <pre className="whitespace-pre-wrap text-xs text-gray-700 font-mono">{preview}</pre>
            </div>
          </div>
        </div>
      )}

      {/* Modal Step-up 2FA */}
      {showTotpModal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6" data-testid="totp-modal">
            <div className="flex items-center gap-2 mb-3">
              <Lock size={20} className="text-[#1E4D8C]" />
              <h3 className="text-lg font-semibold">Conferma con 2FA</h3>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Inserisci il codice a 6 cifre dalla tua app authenticator per confermare il salvataggio del documento legale.
            </p>
            <input
              type="text"
              value={totpCode}
              onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="000000"
              maxLength={6}
              autoFocus
              className="w-full border border-gray-300 rounded-md px-4 py-3 text-center text-2xl font-mono tracking-widest focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
              data-testid="totp-input"
            />
            {error && (
              <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded-md text-red-700 text-xs flex items-center gap-1">
                <AlertCircle size={14} /> {error}
              </div>
            )}
            <div className="flex gap-2 justify-end mt-4">
              <button
                onClick={() => { setShowTotpModal(false); setTotpCode(''); setError(''); }}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-md text-sm"
                data-testid="totp-cancel-btn"
              >
                Annulla
              </button>
              <button
                onClick={() => doSave(totpCode)}
                disabled={totpCode.length !== 6 || saving}
                className="px-4 py-2 bg-[#1E4D8C] hover:bg-[#163A6A] text-white rounded-md text-sm disabled:opacity-50"
                data-testid="totp-confirm-btn"
              >
                {saving ? 'Verifica...' : 'Conferma'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ==================== TAB 3: COMPLIANCE ====================

function TabCompliance() {
  const [registro, setRegistro] = useState([]);
  const [richieste, setRichieste] = useState([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/gdpr/registro-trattamenti`),
      axios.get(`${API}/gdpr/richieste-cancellazione`),
    ])
      .then(([regRes, reqRes]) => {
        setRegistro(regRes.data.trattamenti || []);
        setRichieste(reqRes.data.richieste || []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleExport = async (formato) => {
    setExporting(formato);
    try {
      const res = await axios.get(`${API}/gdpr/registro-trattamenti/export?formato=${formato}`, {
        responseType: 'blob',
      });
      const ext = formato;
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `registro_trattamenti.${ext}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert('Errore export');
    } finally {
      setExporting(false);
    }
  };

  const fmtDate = (v) => {
    if (!v) return '-';
    try {
      return new Date(v).toLocaleString('it-IT');
    } catch {
      return v;
    }
  };

  if (loading) return <div className="text-center py-8 text-gray-400">Caricamento...</div>;

  return (
    <div className="space-y-6" data-testid="tab-compliance">
      {/* Registro trattamenti */}
      <div className="bg-white border border-gray-200 rounded-lg">
        <div className="p-4 border-b border-gray-200 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <ClipboardList size={18} className="text-[#1E4D8C]" />
            <h3 className="font-semibold text-gray-900">Registro dei Trattamenti (art. 30 GDPR)</h3>
          </div>
          <div className="flex gap-2">
            {['csv', 'xlsx', 'pdf'].map((f) => (
              <button
                key={f}
                onClick={() => handleExport(f)}
                disabled={!!exporting}
                className="flex items-center gap-1.5 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md px-3 py-1.5 disabled:opacity-50"
                data-testid={`export-registro-${f}-btn`}
              >
                <Download size={14} /> {f.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
        <div className="p-4 space-y-3">
          {registro.map((t, i) => (
            <details key={i} className="border border-gray-200 rounded-md" data-testid={`trattamento-${i}`}>
              <summary className="px-4 py-2.5 cursor-pointer font-medium text-gray-900 hover:bg-gray-50">
                {t.nome}
              </summary>
              <div className="px-4 py-3 border-t border-gray-100 text-sm space-y-1.5">
                {Object.entries(t).filter(([k]) => k !== 'nome').map(([k, v]) => (
                  <div key={k} className="grid grid-cols-1 sm:grid-cols-3 gap-1">
                    <span className="text-gray-500 capitalize">{k.replace(/_/g, ' ')}</span>
                    <span className="sm:col-span-2 text-gray-800">{v}</span>
                  </div>
                ))}
              </div>
            </details>
          ))}
        </div>
      </div>

      {/* Richieste cancellazione */}
      <div className="bg-white border border-gray-200 rounded-lg">
        <div className="p-4 border-b border-gray-200 flex items-center gap-2">
          <Shield size={18} className="text-[#1E4D8C]" />
          <h3 className="font-semibold text-gray-900">Richieste cancellazione utenti ({richieste.length})</h3>
        </div>
        {richieste.length === 0 ? (
          <div className="p-8 text-center text-gray-400 text-sm">Nessuna richiesta in corso</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  <th className="px-4 py-2 text-left">Email</th>
                  <th className="px-4 py-2 text-left">Stato</th>
                  <th className="px-4 py-2 text-left">Richiesta il</th>
                  <th className="px-4 py-2 text-left">Disabilita il</th>
                  <th className="px-4 py-2 text-left">Anonimizza il</th>
                  <th className="px-4 py-2 text-left">Motivo</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {richieste.map((r, i) => (
                  <tr key={i} data-testid={`richiesta-${i}`}>
                    <td className="px-4 py-2 font-medium">{r.email}</td>
                    <td className="px-4 py-2">
                      <span className={`inline-block px-2 py-0.5 rounded text-xs ${
                        r.stato === 'pending' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {r.stato}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-gray-600">{fmtDate(r.richiesta_il)}</td>
                    <td className="px-4 py-2 text-gray-600">{fmtDate(r.esecuzione_prevista)}</td>
                    <td className="px-4 py-2 text-gray-600">{fmtDate(r.anonimizzazione_prevista)}</td>
                    <td className="px-4 py-2 text-gray-500 max-w-xs truncate" title={r.motivo}>{r.motivo || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
