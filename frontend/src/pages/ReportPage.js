import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { formatCurrency } from '../lib/utils';
import axios from 'axios';
import { FileSpreadsheet, Download, BarChart3 } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function ReportPage() {
  const { user } = useAuth();
  const [anno, setAnno] = useState(new Date().getFullYear());
  const [report, setReport] = useState([]);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => currentYear - i);

  const isAllowed = ['admin', 'superadmin', 'superuser'].includes(user?.ruolo);

  useEffect(() => {
    if (isAllowed) {
      fetchReport();
    }
  }, [anno, isAllowed]);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/reports/rimborsi-annuali?anno=${anno}`);
      setReport(res.data);
    } catch (error) {
      console.error('Error fetching report:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const response = await axios.get(`${API}/reports/rimborsi-export?anno=${anno}&formato=csv`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `rimborsi_${anno}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting:', error);
      alert('Errore durante l\'esportazione');
    } finally {
      setExporting(false);
    }
  };

  if (!isAllowed) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Accesso non autorizzato</p>
      </div>
    );
  }

  // Calculate totals
  const totals = report.reduce((acc, r) => ({
    rimborsi: acc.rimborsi + (r.totale_rimborsi || 0),
    importo: acc.importo + (r.totale_importo || 0),
    km: acc.km + (r.totale_km || 0),
    pagati: acc.pagati + (r.rimborsi_pagati || 0),
    importoPagato: acc.importoPagato + (r.importo_pagato || 0)
  }), { rimborsi: 0, importo: 0, km: 0, pagati: 0, importoPagato: 0 });

  return (
    <div className="space-y-6" data-testid="report-page">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 font-['Manrope']">Report Rimborsi</h1>
          <p className="text-gray-600 mt-1">Rendiconto annuale rimborsi</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={anno}
            onChange={(e) => setAnno(parseInt(e.target.value))}
            className="border border-gray-300 rounded-md px-4 py-2 focus:border-[#1E4D8C] focus:ring-1 focus:ring-[#1E4D8C] outline-none"
            data-testid="anno-select"
          >
            {years.map(y => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
          <button
            onClick={handleExport}
            disabled={exporting || report.length === 0}
            className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white font-medium rounded-md px-4 py-2 transition-colors disabled:opacity-50"
            data-testid="export-csv-btn"
          >
            <Download size={18} />
            {exporting ? 'Esportazione...' : 'Esporta CSV'}
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <p className="text-sm text-gray-500">Totale Rimborsi</p>
          <p className="text-2xl font-bold text-gray-900">{totals.rimborsi}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <p className="text-sm text-gray-500">Importo Totale</p>
          <p className="text-2xl font-bold text-[#1E4D8C]">{formatCurrency(totals.importo)}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <p className="text-sm text-gray-500">KM Totali</p>
          <p className="text-2xl font-bold text-gray-900">{totals.km.toLocaleString('it-IT')}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <p className="text-sm text-gray-500">Pagati</p>
          <p className="text-2xl font-bold text-green-600">{formatCurrency(totals.importoPagato)}</p>
          <p className="text-xs text-gray-400">{totals.pagati} rimborsi</p>
        </div>
      </div>

      {/* Report Table */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1E4D8C]"></div>
        </div>
      ) : report.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
          <BarChart3 size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">Nessun dato per l'anno {anno}</p>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <th className="px-6 py-3">Utente</th>
                  <th className="px-6 py-3">Email</th>
                  <th className="px-6 py-3 text-right">Rimborsi</th>
                  <th className="px-6 py-3 text-right">KM</th>
                  <th className="px-6 py-3 text-right">Importo Totale</th>
                  <th className="px-6 py-3 text-right">Pagati</th>
                  <th className="px-6 py-3 text-right">Importo Pagato</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {report.map((r, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="px-6 py-4 font-medium text-gray-900">{r.user_nome || 'N/A'}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{r.user_email || 'N/A'}</td>
                    <td className="px-6 py-4 text-right text-sm">{r.totale_rimborsi}</td>
                    <td className="px-6 py-4 text-right text-sm">{r.totale_km?.toLocaleString('it-IT')}</td>
                    <td className="px-6 py-4 text-right font-medium">{formatCurrency(r.totale_importo)}</td>
                    <td className="px-6 py-4 text-right text-sm">{r.rimborsi_pagati}</td>
                    <td className="px-6 py-4 text-right font-medium text-green-600">{formatCurrency(r.importo_pagato)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="bg-gray-50 font-semibold">
                  <td className="px-6 py-3" colSpan="2">Totale</td>
                  <td className="px-6 py-3 text-right">{totals.rimborsi}</td>
                  <td className="px-6 py-3 text-right">{totals.km.toLocaleString('it-IT')}</td>
                  <td className="px-6 py-3 text-right text-[#1E4D8C]">{formatCurrency(totals.importo)}</td>
                  <td className="px-6 py-3 text-right">{totals.pagati}</td>
                  <td className="px-6 py-3 text-right text-green-600">{formatCurrency(totals.importoPagato)}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
