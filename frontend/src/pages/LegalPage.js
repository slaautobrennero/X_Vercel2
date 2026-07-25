/**
 * LegalPage - pagina pubblica che mostra un documento legale (Privacy/Cookie/Termini)
 * Recupera il markdown da backend e lo mostra con formattazione base.
 */
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { APP_VERSION } from '../version';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Renderer markdown minimale: gestisce headings, tabelle, bold, liste, link
function renderMarkdown(md) {
  if (!md) return '';
  let html = md
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    // headings
    .replace(/^# (.+)$/gm, '<h1 class="text-3xl font-bold text-[#1E4D8C] mt-6 mb-4">$1</h1>')
    .replace(/^## (.+)$/gm, '<h2 class="text-2xl font-semibold text-[#1E4D8C] mt-6 mb-3">$1</h2>')
    .replace(/^### (.+)$/gm, '<h3 class="text-xl font-semibold mt-4 mb-2">$1</h3>')
    // bold + italic
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // link markdown [text](url)
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-[#1E4D8C] underline">$1</a>');

  // Tabelle: |a|b|c|
  const lines = html.split('\n');
  const out = [];
  let inTable = false, tableRows = [];
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
      const cells = line.trim().slice(1, -1).split('|').map(c => c.trim());
      if (cells.every(c => /^-+$/.test(c))) continue; // separator
      tableRows.push(cells);
      inTable = true;
    } else {
      if (inTable) {
        const header = tableRows[0];
        const body = tableRows.slice(1);
        out.push('<table class="border-collapse border border-gray-300 my-4 w-full text-sm">');
        out.push('<thead><tr>' + header.map(h => `<th class="border border-gray-300 bg-gray-100 px-3 py-2 text-left">${h}</th>`).join('') + '</tr></thead>');
        out.push('<tbody>' + body.map(r => '<tr>' + r.map(c => `<td class="border border-gray-300 px-3 py-2 align-top">${c}</td>`).join('') + '</tr>').join('') + '</tbody>');
        out.push('</table>');
        tableRows = []; inTable = false;
      }
      // liste
      if (line.trim().startsWith('- ')) {
        out.push(`<li class="ml-6 list-disc">${line.trim().slice(2)}</li>`);
      } else if (line.trim()) {
        out.push(`<p class="my-2">${line}</p>`);
      } else {
        out.push('');
      }
    }
  }
  if (inTable) {
    const header = tableRows[0];
    const body = tableRows.slice(1);
    out.push('<table class="border-collapse border border-gray-300 my-4 w-full text-sm">');
    out.push('<thead><tr>' + header.map(h => `<th class="border border-gray-300 bg-gray-100 px-3 py-2 text-left">${h}</th>`).join('') + '</tr></thead>');
    out.push('<tbody>' + body.map(r => '<tr>' + r.map(c => `<td class="border border-gray-300 px-3 py-2 align-top">${c}</td>`).join('') + '</tr>').join('') + '</tbody>');
    out.push('</table>');
  }
  return out.join('\n');
}

export default function LegalPage({ endpoint, title, testId }) {
  const [contenuto, setContenuto] = useState('');
  const [version, setVersion] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    fetch(`${API}/${endpoint}`)
      .then(r => r.json())
      .then(d => { setContenuto(d.contenuto); setVersion(d.version); })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [endpoint]);

  return (
    <div className="min-h-screen bg-white" data-testid={testId}>
      <div className="max-w-4xl mx-auto px-6 py-8">
        <Link to="/" className="text-[#1E4D8C] hover:underline mb-4 inline-block" data-testid="legal-back-home">
          ← Torna alla home
        </Link>
        {loading && <p>Caricamento...</p>}
        {error && <p className="text-red-600">Errore: {error}</p>}
        {!loading && !error && (
          <div
            className="prose max-w-none"
            dangerouslySetInnerHTML={{ __html: renderMarkdown(contenuto) }}
          />
        )}
        <footer className="mt-12 pt-6 border-t border-gray-200 text-sm text-gray-500">
          Portale SLA {APP_VERSION} — Documento versione {version}
        </footer>
      </div>
    </div>
  );
}

// Wrapper per le 3 pagine legali
export const PrivacyPage = () => <LegalPage endpoint="privacy" title="Privacy" testId="privacy-page" />;
export const CookiePolicyPage = () => <LegalPage endpoint="cookie-policy" title="Cookie Policy" testId="cookie-page" />;
export const TerminiPage = () => <LegalPage endpoint="termini" title="Termini di Servizio" testId="termini-page" />;
