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
  segretario: 'Segretario',
  segreteria: 'Segreteria',
  delegato: 'Delegato',
  iscritto: 'Iscritto'
};

export const STATI_RIMBORSO = {
  in_attesa: { label: 'In Attesa', color: 'warning' },
  approvato: { label: 'Approvato', color: 'info' },
  rifiutato: { label: 'Rifiutato', color: 'error' },
  pagato: { label: 'Pagato', color: 'success' }
};
