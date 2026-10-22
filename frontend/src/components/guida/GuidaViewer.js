import React from 'react';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '../ui/accordion';
import { GuidaSezione } from './GuidaSezione';

export const GuidaViewer = ({ guida }) => {
  const Icona = guida.icona;
  return (
    <article key={guida.id} className="space-y-6 guida-fade" data-testid={`guida-viewer-${guida.id}`}>
      <header className="guida-hero rounded-xl p-6 md:p-8 text-white relative overflow-hidden" style={{ background: guida.colore }}>
        <span className="guida-hero-ring" aria-hidden="true" />
        <div className="relative z-10 flex items-start gap-4">
          <div className="w-14 h-14 rounded-xl bg-white/15 flex items-center justify-center shrink-0"><Icona size={30} /></div>
          <div>
            <h2 className="font-heading text-2xl md:text-3xl font-bold" data-testid="guida-titolo">{guida.titolo}</h2>
            <p className="text-white/85 text-sm md:text-base mt-1">{guida.sottotitolo}</p>
            <p className="text-white/70 text-xs font-mono mt-3">{guida.sezioni.length} capitoli · {guida.faq.length} domande frequenti</p>
          </div>
        </div>
      </header>

      <nav className="flex flex-wrap gap-2" data-testid="guida-indice">
        {guida.sezioni.map((s, i) => (
          <a key={s.id} href={`#sez-${s.id}`} className="text-xs px-3 py-1.5 rounded-full bg-white border border-gray-200 text-gray-700 hover:border-gray-400 transition-colors"
            onClick={(e) => { e.preventDefault(); document.getElementById(`sez-${s.id}`)?.scrollIntoView({ behavior: 'smooth' }); }}
            data-testid={`guida-indice-${s.id}`}>
            {i + 1}. {s.titolo}
          </a>
        ))}
      </nav>

      {guida.sezioni.map((s, i) => <GuidaSezione key={s.id} sezione={s} indice={i} colore={guida.colore} />)}

      <section className="bg-white border border-gray-200 rounded-xl p-6" data-testid="guida-faq">
        <h3 className="font-heading text-lg font-bold text-gray-900 mb-2">Domande frequenti</h3>
        <Accordion type="single" collapsible>
          {guida.faq.map((f, i) => (
            <AccordionItem key={f.d} value={`faq-${i}`}>
              <AccordionTrigger className="text-sm text-left" data-testid={`guida-faq-${i}`}>{f.d}</AccordionTrigger>
              <AccordionContent className="text-sm text-gray-600">{f.r}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </section>
    </article>
  );
};
