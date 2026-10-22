import { hasAnyRole } from '../../lib/utils';
import iscritto from './iscritto';
import delegato from './delegato';
import segreteria from './segreteria';
import cassiere from './cassiere';
import admin from './admin';
import superadmin from './superadmin';
import sicurezza from './sicurezza';

export const GUIDE = [iscritto, delegato, segreteria, cassiere, admin, superadmin, sicurezza];

const puoVedere = (user, ruoli) => ruoli === 'tutti' || hasAnyRole(user, ['superadmin', ...ruoli]);

// Guide e sezioni filtrate in base ai ruoli dell'utente
export function guideVisibili(user) {
  return GUIDE
    .filter((g) => puoVedere(user, g.ruoli))
    .map((g) => ({ ...g, sezioni: g.sezioni.filter((s) => !s.ruoliSezione || puoVedere(user, s.ruoliSezione)) }));
}
