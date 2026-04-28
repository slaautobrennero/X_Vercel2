import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import {
  Phone, Mail, Globe, MessageCircle, Send,
  Plus, Pencil, Trash2, X
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TIPI = [
  { value: 'link', label: 'Sito Web', icon: Globe, placeholder: 'https://...' },
  { value: 'whatsapp', label: 'WhatsApp', icon: MessageCircle, placeholder: '+39 333 1234567 oppure link wa.me' },
  { value: 'telegram', label: 'Telegram', icon: Send, placeholder: '@username oppure link t.me' },
  { value: 'email', label: 'Email', icon: Mail, placeholder: 'esempio@dominio.it' },
  { value: 'telefono', label: 'Telefono', icon: Phone, placeholder: '+39 333 1234567' },
];

// Trasforma il valore nel link cliccabile corretto
function buildHref(tipo, valore) {
  const v = (valore || '').trim();
  if (!v) return '#';

  switch (tipo) {
    case 'email':
      return v.startsWith('mailto:') ? v : `mailto:${v}`;
    case 'telefono': {
      const clean = v.replace(/[^\d+]/g, '');
      return v.startsWith('tel:') ? v : `tel:${clean}`;
    }
    case 'whatsapp': {
      if (v.startsWith('http')) return v;
      const clean = v.replace(/[^\d]/g, '');
      return `https://wa.me/${clean}`;
    }
    case 'telegram': {
      if (v.startsWith('http')) return v;
      const username = v.replace(/^@/, '');
      return `https://t.me/${username}`;
    }
    case 'link':
    default:
      return v.startsWith('http') ? v : `https://${v}`;
  }
}

function getIcon(tipo) {
  return TIPI.find(t => t.value === tipo)?.icon || Globe;
}

export default function ContattiSidebar() {
  const { user } = useAuth();
  const [contatti, setContatti] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);

  const canEdit = ['admin', 'segretario', 'segreteria', 'superadmin'].includes(user?.ruolo);

  const fetchContatti = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/contatti`);
      setContatti(res.data);
    } catch (error) {
      console.error('Error fetching contatti:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchContatti();
  }, [fetchContatti]);

  const handleDelete = async (id) => {
    if (!window.confirm('Eliminare questo contatto?')) return;
    try {
      await axios.delete(`${API}/contatti/${id}`);
      fetchContatti();
    } catch (error) {
      alert(error.response?.data?.detail || 'Errore nella cancellazione');
    }
  };

  if (loading) return null;

  return (
    <div className="border-t border-gray-200 px-4 py-3" data-testid="contatti-sidebar">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Contatti</h3>
        {canEdit && (
          <button
            onClick={() => { setEditing(null); setShowModal(true); }}
            className="text-[#1E4D8C] hover:bg-blue-50 p-1 rounded"
            title="Aggiungi contatto"
            data-testid="add-contatto-btn"
          >
            <Plus size={14} />
          </button>
        )}
      </div>

      {contatti.length === 0 ? (
        <p className="text-xs text-gray-400 italic py-2">
          {canEdit ? 'Nessun contatto. Aggiungi il primo!' : 'Nessun contatto disponibile'}
        </p>
      ) : (
        <ul className="space-y-1">
          {contatti.map(c => {
            const Icon = getIcon(c.tipo);
            return (
              <li key={c.id} className="group relative" data-testid={`contatto-${c.id}`}>
                <a
                  href={buildHref(c.tipo, c.valore)}
                  target={c.tipo === 'email' || c.tipo === 'telefono' ? '_self' : '_blank'}
                  rel="noopener noreferrer"
                  className="flex items-start gap-2 px-2 py-1.5 rounded-md text-sm text-gray-700 hover:bg-gray-50 hover:text-[#1E4D8C] transition-colors"
                >
                  <Icon size={14} className="flex-shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0 pr-12">
                    <p className="font-medium truncate">{c.titolo}</p>
                    {c.descrizione && (
                      <p className="text-xs text-gray-500 truncate">{c.descrizione}</p>
                    )}
                  </div>
                </a>
                {canEdit && (
                  <div className="absolute right-1 top-1 hidden group-hover:flex gap-0.5 bg-white shadow-sm border border-gray-100 rounded">
                    <button
                      onClick={(e) => { e.preventDefault(); setEditing(c); setShowModal(true); }}
                      className="p-1 text-gray-500 hover:text-[#1E4D8C]"
                      title="Modifica"
                      data-testid={`edit-contatto-${c.id}`}
                    >
                      <Pencil size={12} />
                    </button>
                    <button
                      onClick={(e) => { e.preventDefault(); handleDelete(c.id); }}
                      className="p-1 text-gray-500 hover:text-red-600"
                      title="Elimina"
                      data-testid={`delete-contatto-${c.id}`}
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {showModal && (
        <ContattoModal
          contatto={editing}
          onClose={() => { setShowModal(false); setEditing(null); }}
          onSaved={() => { setShowModal(false); setEditing(null); fetchContatti(); }}
        />
      )}
    </div>
  );
}

function ContattoModal({ contatto, onClose, onSaved }) {
  const [formData, setFormData] = useState({
    titolo: contatto?.titolo || '',
    descrizione: contatto?.descrizione || '',
    tipo: contatto?.tipo || 'link',
    valore: contatto?.valore || ''
  });
  const [submitting, setSubmitting] = useState(false);

  const tipoConfig = TIPI.find(t => t.value === formData.tipo) || TIPI[0];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (contatto) {
        await axios.put(`${API}/contatti/${contatto.id}`, formData);
      } else {
        await axios.post(`${API}/contatti`, formData);
      }
      onSaved();
    } catch (error) {
      alert(error.response?.data?.detail || 'Errore nel salvataggio');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-[60] flex items-center justify-center p-4">
      <div className="bg-white rounded-lg w-full max-w-md">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            {contatto ? 'Modifica Contatto' : 'Nuovo Contatto'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
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
              placeholder="Es: Ufficio Sede / Resp. Personale"
              className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
              data-testid="contatto-titolo-input"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Descrizione (opzionale)</label>
            <input
              type="text"
              value={formData.descrizione}
              onChange={(e) => setFormData(prev => ({ ...prev, descrizione: e.target.value }))}
              placeholder="Es: Lun-Ven 9-18"
              className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
              data-testid="contatto-descrizione-input"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tipo *</label>
            <div className="grid grid-cols-5 gap-1">
              {TIPI.map(t => {
                const Icon = t.icon;
                const active = formData.tipo === t.value;
                return (
                  <button
                    key={t.value}
                    type="button"
                    onClick={() => setFormData(prev => ({ ...prev, tipo: t.value }))}
                    className={`flex flex-col items-center justify-center p-2 rounded-md border text-xs transition-colors ${
                      active
                        ? 'border-[#1E4D8C] bg-blue-50 text-[#1E4D8C]'
                        : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                    }`}
                    data-testid={`contatto-tipo-${t.value}`}
                  >
                    <Icon size={16} />
                    <span className="mt-1 truncate max-w-full">{t.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {tipoConfig.label} *
            </label>
            <input
              type="text"
              value={formData.valore}
              onChange={(e) => setFormData(prev => ({ ...prev, valore: e.target.value }))}
              required
              placeholder={tipoConfig.placeholder}
              className="w-full border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
              data-testid="contatto-valore-input"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
            >
              Annulla
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 bg-[#1E4D8C] hover:bg-[#163A6A] text-white rounded-md transition-colors disabled:opacity-50"
              data-testid="submit-contatto-btn"
            >
              {submitting ? 'Salvataggio...' : (contatto ? 'Aggiorna' : 'Crea')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
