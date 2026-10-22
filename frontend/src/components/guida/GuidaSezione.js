import React, { useEffect, useRef, useState } from 'react';
import { Info, AlertTriangle } from 'lucide-react';

function useInView() {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || !('IntersectionObserver' in window)) { setVisible(true); return undefined; }
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setVisible(true); obs.disconnect(); } }, { threshold: 0.12 });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return [ref, visible];
}

export const GuidaSezione = ({ sezione, indice, colore }) => {
  const [ref, visible] = useInView();
  const Icona = sezione.icona;
  return (
    <section ref={ref} id={`sez-${sezione.id}`} data-testid={`guida-sezione-${sezione.id}`}
      className={`guida-sezione bg-white border border-gray-200 rounded-xl overflow-hidden scroll-mt-24 ${visible ? 'is-visible' : ''}`}>
      <div className="grid md:grid-cols-[220px_1fr]">
        <div className="guida-illustrazione relative p-6 flex md:flex-col items-center md:items-start gap-4" style={{ '--c': colore }}>
          <span className="guida-dot-grid" aria-hidden="true" />
          <div className="guida-icona-box relative z-10"><Icona size={34} strokeWidth={1.6} /></div>
          <div className="relative z-10">
            <p className="text-xs font-mono uppercase tracking-wider text-gray-500">Capitolo {indice + 1}</p>
            <h3 className="font-heading text-lg font-bold text-gray-900 leading-tight">{sezione.titolo}</h3>
          </div>
        </div>
        <div className="p-6">
          <p className="text-sm text-gray-600 mb-5">{sezione.intro}</p>
          <ol className="guida-passi">
            {sezione.passi.map((p, i) => (
              <li key={p.t} className="guida-passo" style={{ animationDelay: `${120 + i * 110}ms` }} data-testid={`guida-passo-${sezione.id}-${i + 1}`}>
                <span className="guida-num" style={{ background: colore }}>{i + 1}</span>
                <div className="min-w-0">
                  <p className="font-semibold text-gray-900 text-sm">{p.t}</p>
                  <p className="text-sm text-gray-600 mt-0.5">{p.d}</p>
                  {p.btn && <span className="guida-btn-mock" style={{ borderColor: colore, color: colore }}>{p.btn}</span>}
                </div>
              </li>
            ))}
          </ol>
          {sezione.nota && <GuidaNota nota={sezione.nota} />}
        </div>
      </div>
    </section>
  );
};

const GuidaNota = ({ nota }) => {
  const att = nota.tipo === 'attenzione';
  const Icona = att ? AlertTriangle : Info;
  return (
    <div className={`mt-5 flex gap-3 rounded-lg p-3 text-sm ${att ? 'bg-amber-50 text-amber-900 border border-amber-200' : 'bg-blue-50 text-blue-900 border border-blue-200'}`}>
      <Icona size={18} className="shrink-0 mt-0.5" />
      <p>{nota.testo}</p>
    </div>
  );
};
