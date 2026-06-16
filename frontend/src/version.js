/**
 * SLA Portale - Versione applicazione
 *
 * Aggiorna questi valori a OGNI rilascio significativo (feature, fix, sicurezza).
 * - APP_VERSION:  semver. Suffisso "-beta" finché il portale non è validato in produzione.
 * - BUILD_DATE:   data ISO del rilascio (YYYY-MM-DD).
 * - RELEASE_NAME: nome breve descrittivo dell'ultimo cambiamento (facoltativo).
 *
 * Visibile in basso a destra in ogni pagina (componente VersionBadge).
 * Letto anche dal backend tramite GET /api/version per verifica incrociata.
 */
export const APP_VERSION = '0.9.2-beta';
export const BUILD_DATE = '2026-02-14';
export const RELEASE_NAME = 'Fix Dockerfile: Node 20 + yarn senza lockfile';
