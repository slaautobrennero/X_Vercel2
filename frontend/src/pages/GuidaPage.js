import React, { useMemo, useState } from 'react';
import { Download, BookOpen, Files } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';
import { guideVisibili } from '../data/guide';
import { scaricaHtml } from '../lib/guidaOffline';
import { GuidaViewer } from '../components/guida/GuidaViewer';

export default function GuidaPage() {
  const { user } = useAuth();
  const guide = useMemo(() => guideVisibili(user), [user]);
  const [attiva, setAttiva] = useState(guide[0]?.id);
  const guida = guide.find((g) => g.id === attiva) || guide[0];

  const scarica = (lista, nome) => {
    scaricaHtml(lista, nome);
    toast.success('Guida scaricata: aprila con un doppio clic, funziona anche senza internet');
  };

  return (
    <div className="space-y-6" data-testid="guida-page">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <h1 className="font-heading text-3xl font-bold text-gray-900 flex items-center gap-2"><BookOpen className="text-[#1E4D8C]" /> Guide</h1>
          <p className="text-gray-600 text-sm mt-1">Le istruzioni per il tuo ruolo, passo dopo passo. Puoi scaricarle e leggerle anche offline.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => scarica([guida], `guida-${guida.id}.html`)} data-testid="scarica-guida-btn"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#1E4D8C] hover:bg-[#163A6A] text-white text-sm font-medium transition-colors">
            <Download size={16} /> Scarica questa guida
          </button>
          {guide.length > 1 && (
            <button onClick={() => scarica(guide, 'guide-portale-sla.html')} data-testid="scarica-tutte-btn"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 bg-white hover:bg-gray-50 text-gray-800 text-sm font-medium transition-colors">
              <Files size={16} /> Scarica tutte ({guide.length})
            </button>
          )}
        </div>
      </div>

      <div className="grid lg:grid-cols-[260px_1fr] gap-6 items-start">
        <aside className="flex lg:flex-col gap-2 overflow-x-auto lg:overflow-visible pb-1 lg:sticky lg:top-20" data-testid="guida-elenco">
          {guide.map((g) => {
            const Icona = g.icona;
            const sel = g.id === guida.id;
            return (
              <button key={g.id} onClick={() => { setAttiva(g.id); window.scrollTo({ top: 0, behavior: 'smooth' }); }} data-testid={`guida-tab-${g.id}`}
                className={`shrink-0 flex items-center gap-3 text-left rounded-lg border px-3 py-2.5 transition-colors ${sel ? 'bg-white border-gray-900 shadow-sm' : 'bg-white/60 border-gray-200 hover:border-gray-400'}`}>
                <span className="w-8 h-8 rounded-md flex items-center justify-center text-white shrink-0" style={{ background: g.colore }}><Icona size={16} /></span>
                <span className="text-sm font-medium text-gray-900 whitespace-nowrap lg:whitespace-normal">{g.titolo}</span>
              </button>
            );
          })}
        </aside>
        {guida && <GuidaViewer guida={guida} />}
      </div>
    </div>
  );
}
