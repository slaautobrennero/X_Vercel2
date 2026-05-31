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

// Colori badge per ogni ruolo (Tailwind classes)
export const RUOLO_BADGE_COLOR = {
  superadmin: 'bg-purple-100 text-purple-800',
  superuser: 'bg-fuchsia-100 text-fuchsia-800',
  admin: 'bg-blue-100 text-blue-800',
  cassiere: 'bg-emerald-100 text-emerald-800',
  segretario: 'bg-indigo-100 text-indigo-800',
  segreteria: 'bg-cyan-100 text-cyan-800',
  delegato: 'bg-green-100 text-green-800',
  iscritto: 'bg-gray-100 text-gray-800'
};

// ==================== MULTI-RUOLO HELPERS ====================
// Ogni utente ha un array `user.ruoli` (sorgente di verità) + il legacy `user.ruolo`
// per retro-compat (= ruoli[0]).

export function getUserRoles(user) {
  if (!user) return [];
  if (Array.isArray(user.ruoli) && user.ruoli.length > 0) return user.ruoli;
  if (user.ruolo) return [user.ruolo];
  return [];
}

export function hasRole(user, role) {
  return getUserRoles(user).includes(role);
}

export function hasAnyRole(user, roles) {
  const userRoles = getUserRoles(user);
  return roles.some(r => userRoles.includes(r));
}

// Classi Tailwind per badge stato rimborso
// in_attesa: bianco | approvato: giallo | rifiutato: rosso | pagato: verde
export const STATI_RIMBORSO = {
  in_attesa: { label: 'In Attesa', color: 'warning', badgeClass: 'bg-white border border-gray-300 text-gray-700' },
  approvato: { label: 'Approvato', color: 'warning', badgeClass: 'bg-yellow-100 border border-yellow-300 text-yellow-800' },
  rifiutato: { label: 'Rifiutato', color: 'error', badgeClass: 'bg-red-100 border border-red-300 text-red-800' },
  pagato: { label: 'Pagato', color: 'success', badgeClass: 'bg-green-100 border border-green-300 text-green-800' }
};
