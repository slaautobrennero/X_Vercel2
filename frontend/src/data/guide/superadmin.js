import { Crown, Building2, ListChecks, Landmark, FileLock2, Rocket } from 'lucide-react';

const guidaSuperAdmin = {
  id: 'superadmin',
  titolo: 'Guida SuperAdmin',
  sottotitolo: 'Configurazione generale: sedi, motivi di rimborso, impostazioni del sindacato e privacy',
  icona: Crown,
  colore: '#0F172A',
  ruoli: [],
  sezioni: [
    {
      id: 'sedi',
      titolo: 'Gestire le concessionarie',
      icona: Building2,
      intro: 'In "Impostazioni" vedi il riepilogo di tutte le concessionarie (il Nazionale è sempre in cima): clicca una riga per correggerne le impostazioni.',
      passi: [
        { t: 'Crea una concessionaria', d: 'In Impostazioni premi "Nuova concessionaria" e inserisci Nome, Codice (es. A22, CAV, ASPI) e tariffe.', btn: 'Nuova concessionaria' },
        { t: 'Rimborsi, email, invii', d: 'Dentro la concessionaria trovi le schede Rimborsi (tariffe e motivi), Email (come invia le email) e Invii automatici (quali cartelle mandano email). Puoi correggerle se l\'Admin locale non è pratico.' },
        { t: 'Sede Nazionale', d: 'Con "Rendi Nazionale" scegli la sede che avrà visione in sola lettura su tutte le altre. Ce n\'è sempre una sola.', btn: 'Rendi Nazionale' },
      ],
    },
    {
      id: 'motivi',
      titolo: 'Motivi di rimborso',
      icona: ListChecks,
      intro: 'I motivi compaiono nel menu a tendina della richiesta di rimborso. Li gestisci solo tu, su richiesta delle concessionarie, così i report restano coerenti.',
      passi: [
        { t: 'Aggiungi o modifica', d: 'In Impostazioni apri la concessionaria → scheda Rimborsi → "Nuovo motivo". Spunta "Valido per tutte le concessionarie" per un motivo comune.', btn: 'Nuovo motivo' },
        { t: 'Note obbligatorie', d: 'Attiva "richiede note" per i motivi generici: il delegato dovrà spiegare la trasferta.' },
      ],
    },
    {
      id: 'impostazioni',
      titolo: 'Impostazioni Sindacato',
      icona: Landmark,
      intro: 'I dati del titolare del trattamento compaiono nei documenti privacy e negli export GDPR.',
      passi: [
        { t: 'Dati del sindacato', d: 'Denominazione, codice fiscale, indirizzo, Email e PEC reali.', btn: 'Impostazioni Sindacato' },
        { t: 'Contatti privacy e DPO', d: 'Email per le richieste privacy e, se nominato, il DPO (Data Protection Officer).' },
        { t: 'Conferma con 2FA', d: 'Le modifiche sensibili chiedono il codice 2FA anche se sei già collegato (step-up).', btn: 'Conferma con 2FA' },
      ],
    },
    {
      id: 'legali',
      titolo: 'Documenti legali e richieste GDPR',
      icona: FileLock2,
      intro: 'Informativa Privacy, Cookie Policy e Termini sono versionati: ogni modifica crea una nuova versione.',
      passi: [
        { t: 'Modifica un documento', d: 'Scrivi il testo (formato Markdown) e salva con il codice 2FA. Gli utenti vedranno un avviso con i documenti aggiornati.' },
        { t: 'Richieste di cancellazione', d: 'Vedi chi ha chiesto la cancellazione, la data di disattivazione ("Disabilita il") e di anonimizzazione ("Anonimizza il").' },
        { t: 'Registro dei Trattamenti', d: 'Esporta il registro richiesto dall\'art. 30 GDPR in CSV, Excel o PDF.' },
      ],
    },
    {
      id: 'golive',
      titolo: 'Checklist prima dell\'apertura a tutti',
      icona: Rocket,
      intro: 'Pochi controlli che rendono il portale sicuro e conforme.',
      passi: [
        { t: 'Cambia la password di default', d: 'Dal Profilo, sostituisci la password iniziale del SuperAdmin con una lunga e unica.' },
        { t: 'Attiva la 2FA', d: 'Obbligatoria di fatto per il SuperAdmin.' },
        { t: 'Compila PEC ed Email reali', d: 'In Impostazioni Sindacato sostituisci i valori di esempio.' },
        { t: 'Prova un ripristino del backup', d: 'Un backup che non hai mai ripristinato non è garantito: fai una prova.' },
        { t: 'Revisione legale', d: 'Fai rivedere Privacy e Termini a un consulente.' },
      ],
    },
  ],
  faq: [
    { d: 'Come porto sul Raspberry gli aggiornamenti?', r: 'Salva su GitHub e lancia il comando sla-update sul Pi (vedi GUIDA_AGGIORNAMENTO_PI.md).' },
    { d: 'Ho cambiato il file .env ma non succede nulla.', r: 'Serve ricreare il container: sudo docker compose up -d --force-recreate backend.' },
  ],
};

export default guidaSuperAdmin;
