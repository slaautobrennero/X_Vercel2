import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export function formatApiErrorDetail(detail) {
  if (detail == null) return "Si è verificato un errore. Riprova.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail.map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e))).filter(Boolean).join(" ");
  if (detail && typeof detail.msg === "string") return detail.msg;
  return String(detail);
}

export function formatDate(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString('it-IT', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
}

export function formatDateTime(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString('it-IT', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

export function formatCurrency(amount) {
  return new Intl.NumberFormat('it-IT', {
    style: 'currency',
    currency: 'EUR'
  }).format(amount);
}

export const RUOLI = {
  superadmin: 'Super Admin',
  superuser: 'Super User',
  admin: 'Admin',
  cassiere: 'Cassiere',
  segretario: 'Segretario',
  segreteria: 'Segreteria',
  delegato: 'Delegato',
  iscritto: 'Iscritto'
};

// Classi Tailwind per badge stato rimborso
// in_attesa: bianco | approvato: giallo | rifiutato: rosso | pagato: verde
export const STATI_RIMBORSO = {
  in_attesa: { label: 'In Attesa', color: 'warning', badgeClass: 'bg-white border border-gray-300 text-gray-700' },
  approvato: { label: 'Approvato', color: 'warning', badgeClass: 'bg-yellow-100 border border-yellow-300 text-yellow-800' },
  rifiutato: { label: 'Rifiutato', color: 'error', badgeClass: 'bg-red-100 border border-red-300 text-red-800' },
  pagato: { label: 'Pagato', color: 'success', badgeClass: 'bg-green-100 border border-green-300 text-green-800' }
};
