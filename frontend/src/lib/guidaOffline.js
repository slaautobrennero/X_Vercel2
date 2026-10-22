import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const svg = (Icon, size) => renderToStaticMarkup(createElement(Icon, { size, strokeWidth: 1.7 }));

const CSS = `
*{box-sizing:border-box}body{margin:0;font-family:"IBM Plex Sans",-apple-system,"Segoe UI",Roboto,sans-serif;background:#F3F5F8;color:#1f2937;line-height:1.55}
h1,h2,h3{font-family:Manrope,"Segoe UI",sans-serif;margin:0}.wrap{max-width:960px;margin:0 auto;padding:24px 16px 64px}
.top{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:20px}.brand{font-weight:800;color:#1E4D8C}.meta{font-size:12px;color:#6b7280}
.tabs{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:24px}.tabs a{font-size:13px;padding:6px 12px;border-radius:999px;background:#fff;border:1px solid #d1d5db;color:#374151;text-decoration:none}
.guida{margin-bottom:56px}.hero{color:#fff;border-radius:14px;padding:28px;display:flex;gap:16px;align-items:flex-start}.hero .ic{background:rgba(255,255,255,.15);border-radius:12px;padding:12px;display:flex}
.hero p{margin:4px 0 0;opacity:.85}.toc{display:flex;flex-wrap:wrap;gap:6px;margin:16px 0}.toc a{font-size:12px;padding:4px 10px;border-radius:999px;background:#fff;border:1px solid #e5e7eb;color:#374151;text-decoration:none}
.sez{background:#fff;border:1px solid #e5e7eb;border-radius:14px;margin:16px 0;display:grid;grid-template-columns:200px 1fr;overflow:hidden}
.ill{padding:22px;background:color-mix(in srgb,var(--c) 8%,#fff);border-right:1px solid #eef0f3}.ill .box{width:60px;height:60px;border-radius:14px;display:flex;align-items:center;justify-content:center;background:#fff;color:var(--c);box-shadow:0 6px 18px -8px var(--c);margin-bottom:12px}
.cap{font:600 11px "IBM Plex Mono",monospace;letter-spacing:.08em;text-transform:uppercase;color:#6b7280}.body{padding:22px}.intro{color:#4b5563;font-size:14px;margin:0 0 16px}
ol{list-style:none;margin:0;padding:0;position:relative}ol:before{content:"";position:absolute;left:13px;top:6px;bottom:6px;width:2px;background:#e5e7eb}
li{position:relative;display:flex;gap:12px;padding:0 0 14px;opacity:0;transform:translateY(10px)}.vis li{animation:in .5s ease forwards}
.num{position:relative;z-index:1;flex:0 0 28px;height:28px;border-radius:50%;color:#fff;font:700 13px Manrope,sans-serif;display:flex;align-items:center;justify-content:center}
li b{font-size:14px}li p{margin:2px 0 0;font-size:14px;color:#4b5563}.btn{display:inline-block;margin-top:6px;font-size:12px;font-weight:600;padding:3px 10px;border-radius:6px;border:1.5px solid;background:#fff}
.nota{margin-top:12px;border-radius:10px;padding:10px 12px;font-size:14px}.info{background:#eff6ff;border:1px solid #bfdbfe;color:#1e3a8a}.attenzione{background:#fffbeb;border:1px solid #fde68a;color:#78350f}
.faq{background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:20px}details{border-bottom:1px solid #eef0f3;padding:10px 0}summary{cursor:pointer;font-weight:600;font-size:14px}details p{margin:8px 0 0;color:#4b5563;font-size:14px}
@keyframes in{to{opacity:1;transform:none}}@media(max-width:700px){.sez{grid-template-columns:1fr}.ill{border-right:0;border-bottom:1px solid #eef0f3}}
@media print{li{opacity:1!important;transform:none!important}.tabs,.toc{display:none}.sez,.faq{break-inside:avoid}body{background:#fff}}
@media(prefers-reduced-motion:reduce){li{opacity:1;transform:none;animation:none!important}}`;

const JS = `(function(){var s=document.querySelectorAll('.sez');if(!('IntersectionObserver' in window)){s.forEach(function(e){e.classList.add('vis')});return}
var o=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('vis');o.unobserve(e.target)}})},{threshold:.12});s.forEach(function(e){o.observe(e)})})();`;

function sezioneHtml(g, s, i) {
  const passi = s.passi.map((p, k) => `<li style="animation-delay:${120 + k * 110}ms"><span class="num" style="background:${g.colore}">${k + 1}</span><div><b>${esc(p.t)}</b><p>${esc(p.d)}</p>${p.btn ? `<span class="btn" style="color:${g.colore};border-color:${g.colore}">${esc(p.btn)}</span>` : ''}</div></li>`).join('');
  const nota = s.nota ? `<div class="nota ${s.nota.tipo}">${esc(s.nota.testo)}</div>` : '';
  return `<section class="sez" id="${g.id}-${s.id}" style="--c:${g.colore}"><div class="ill"><div class="box">${svg(s.icona, 30)}</div><div class="cap">Capitolo ${i + 1}</div><h3>${esc(s.titolo)}</h3></div><div class="body"><p class="intro">${esc(s.intro)}</p><ol>${passi}</ol>${nota}</div></section>`;
}

function guidaHtml(g) {
  const toc = g.sezioni.map((s, i) => `<a href="#${g.id}-${s.id}">${i + 1}. ${esc(s.titolo)}</a>`).join('');
  const faq = g.faq.map((f) => `<details><summary>${esc(f.d)}</summary><p>${esc(f.r)}</p></details>`).join('');
  return `<div class="guida" id="${g.id}"><header class="hero" style="background:${g.colore}"><div class="ic">${svg(g.icona, 30)}</div><div><h2>${esc(g.titolo)}</h2><p>${esc(g.sottotitolo)}</p></div></header><nav class="toc">${toc}</nav>${g.sezioni.map((s, i) => sezioneHtml(g, s, i)).join('')}<section class="faq"><h3>Domande frequenti</h3>${faq}</section></div>`;
}

export function buildOfflineHtml(guide, nomeSindacato) {
  const data = new Date().toLocaleDateString('it-IT');
  const tabs = guide.length > 1 ? `<nav class="tabs">${guide.map((g) => `<a href="#${g.id}">${esc(g.titolo)}</a>`).join('')}</nav>` : '';
  const titolo = guide.length === 1 ? guide[0].titolo : 'Guide del Portale';
  return `<!DOCTYPE html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(titolo)} — Portale SLA</title><style>${CSS}</style><noscript><style>li{opacity:1;transform:none}</style></noscript></head><body><div class="wrap"><div class="top"><span class="brand">${esc(nomeSindacato)}</span><span class="meta">Versione offline · scaricata il ${data}</span></div>${tabs}${guide.map(guidaHtml).join('')}</div><script>${JS}</script></body></html>`;
}

export function scaricaHtml(guide, nomeFile, nomeSindacato = 'SLA - CISAL · Portale') {
  const blob = new Blob([buildOfflineHtml(guide, nomeSindacato)], { type: 'text/html;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = nomeFile;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
