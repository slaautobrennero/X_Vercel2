import { User, UserPlus, LogIn, LayoutDashboard, Megaphone, FileText, Bell, UserCog, ShieldCheck } from 'lucide-react';

const guidaIscritto = {
  id: 'iscritto',
  titolo: 'Guida Iscritto',
  sottotitolo: 'Le basi del portale: accesso, bacheca, documenti, profilo e privacy',
  icona: User,
  colore: '#1E4D8C',
  ruoli: 'tutti',
  sezioni: [
    {
      id: 'registrazione',
      titolo: 'Registrarsi al portale',
      icona: UserPlus,
      intro: 'Per entrare nel portale serve un account personale. Ti registri da solo, ci vogliono un paio di minuti.',
      passi: [
        { t: 'Apri la pagina di registrazione', d: 'Dalla pagina di accesso premi il link per registrarti.', btn: 'Registrati' },
        { t: 'Inserisci i tuoi dati', d: 'Compila Nome, Cognome, Email e, se vuoi, il Telefono. I campi con l\'asterisco (*) sono obbligatori.' },
        { t: 'Scegli una password robusta', d: 'Almeno 8 caratteri, con almeno una lettera, un numero e un carattere speciale (es. ! ? # @). Ripetila nel campo "Conferma Password".' },
        { t: 'Seleziona la tua Concessionaria e il Ruolo', d: 'Scegli la concessionaria in cui lavori. Come ruolo scegli "Iscritto"; scegli "Delegato" solo se sei delegato sindacale (ti verranno chiesti anche indirizzo e IBAN per i rimborsi).' },
        { t: 'Verifica anti-robot', d: 'Completa il riquadro "Non sono un robot": serve a bloccare le registrazioni automatiche.' },
        { t: 'Accetta Privacy e Termini', d: 'Leggi e spunta l\'Informativa sulla Privacy e i Termini di Servizio, poi conferma.', btn: 'Registrati' },
      ],
      nota: { tipo: 'info', testo: 'Altri ruoli (Segreteria, Segretario, Cassiere, Admin) non si scelgono in registrazione: li assegna il responsabile della tua sede.' },
    },
    {
      id: 'accesso',
      titolo: 'Accedere e uscire',
      icona: LogIn,
      intro: 'Ogni volta che entri usi email e password scelte in registrazione.',
      passi: [
        { t: 'Inserisci email e password', d: 'Nella pagina di accesso scrivi le tue credenziali.', btn: 'Accedi' },
        { t: 'Codice 2FA (solo se attivo)', d: 'Se hai attivato la verifica in due passaggi, ti verrà chiesto un codice di 6 cifre dall\'app sul telefono.', btn: 'Verifica codice' },
        { t: 'Esci quando hai finito', d: 'Soprattutto su computer condivisi, apri il menu in alto a destra e premi Esci.', btn: 'Esci' },
      ],
      nota: { tipo: 'attenzione', testo: 'Dopo 5 tentativi sbagliati l\'accesso viene bloccato per 15 minuti: è una protezione contro chi prova a indovinare le password.' },
    },
    {
      id: 'dashboard',
      titolo: 'Muoversi nel portale',
      icona: LayoutDashboard,
      intro: 'La Dashboard è la pagina iniziale: mostra gli ultimi annunci e, se ne hai, gli ultimi rimborsi.',
      passi: [
        { t: 'Usa il menu laterale', d: 'A sinistra trovi tutte le sezioni disponibili per il tuo ruolo: Dashboard, Bacheca, Documenti, Notifiche, Guide.' },
        { t: 'Da telefono', d: 'Su smartphone il menu è nascosto: premi l\'icona con le tre righe in alto a sinistra per aprirlo.' },
        { t: 'Menu personale', d: 'In alto a destra, cliccando sul tuo nome, trovi il Profilo e il pulsante per uscire.', btn: 'Profilo' },
      ],
    },
    {
      id: 'bacheca',
      titolo: 'Leggere la Bacheca',
      icona: Megaphone,
      intro: 'In Bacheca il sindacato pubblica comunicati e annunci per la tua concessionaria (e quelli nazionali).',
      passi: [
        { t: 'Apri la Bacheca', d: 'Dal menu laterale scegli Bacheca.', btn: 'Bacheca' },
        { t: 'Leggi gli annunci', d: 'Gli annunci più recenti sono in alto. Alcuni possono contenere un link esterno.' },
        { t: 'Scarica gli allegati', d: 'Se un annuncio ha un allegato (PDF o immagine), premi l\'icona di download per salvarlo.' },
      ],
    },
    {
      id: 'documenti',
      titolo: 'Scaricare i Documenti',
      icona: FileText,
      intro: 'La sezione Documenti raccoglie la modulistica e i documenti condivisi dal sindacato.',
      passi: [
        { t: 'Apri Documenti', d: 'Dal menu laterale scegli Documenti.', btn: 'Documenti' },
        { t: 'Trova il documento', d: 'I documenti sono divisi per categoria, con nome e descrizione.' },
        { t: 'Scarica', d: 'Premi l\'icona di download accanto al documento.' },
      ],
    },
    {
      id: 'notifiche',
      titolo: 'Le Notifiche',
      icona: Bell,
      intro: 'Il portale ti avvisa quando succede qualcosa che ti riguarda: un nuovo annuncio, un nuovo documento, un aggiornamento su un rimborso.',
      passi: [
        { t: 'Guarda la campanella', d: 'In alto, l\'icona a campanella mostra quante notifiche non hai ancora letto.' },
        { t: 'Apri le Notifiche', d: 'Clicca la campanella o la voce Notifiche nel menu per vederle tutte.', btn: 'Notifiche' },
      ],
    },
    {
      id: 'profilo',
      titolo: 'Il tuo Profilo',
      icona: UserCog,
      intro: 'Nel Profilo tieni aggiornati i tuoi dati e cambi la password.',
      passi: [
        { t: 'Apri il Profilo', d: 'Menu in alto a destra → Profilo.', btn: 'Profilo' },
        { t: 'Modifica i dati', d: 'Puoi aggiornare Nome, Cognome, Telefono, Indirizzo, Città, CAP e IBAN.', btn: 'Salva' },
        { t: 'Cambia la password', d: 'Inserisci la password attuale e quella nuova (due volte). Dopo il cambio dovrai rientrare con la nuova password.' },
      ],
    },
    {
      id: 'privacy',
      titolo: 'Privacy: i tuoi dati, i tuoi diritti',
      icona: ShieldCheck,
      intro: 'Dal Profilo, nella sezione dedicata alla privacy, eserciti i diritti previsti dal GDPR in autonomia.',
      passi: [
        { t: 'Scarica i tuoi dati', d: '"Scarica JSON" ti dà tutti i tuoi dati in un file; "Scarica ZIP" aggiunge anche le ricevute e i documenti caricati.', btn: 'Scarica ZIP' },
        { t: 'Richiedi la cancellazione', d: 'Puoi chiedere di cancellare il tuo account indicando, se vuoi, un motivo.', btn: 'Richiedi cancellazione' },
        { t: 'Puoi ripensarci', d: 'Finché la richiesta è in attesa vedi un avviso con il pulsante per annullarla.', btn: 'Annulla cancellazione' },
      ],
      nota: { tipo: 'info', testo: 'La cancellazione è differita: dopo il periodo di ripensamento l\'account viene disattivato. I dati legati a pagamenti e rimborsi vengono resi anonimi solo dopo il 31 marzo dell\'anno successivo, perché la legge obbliga a conservarli per la contabilità.' },
    },
  ],
  faq: [
    { d: 'Ho dimenticato la password, cosa faccio?', r: 'Contatta il Segretario o l\'Admin della tua sede: può generarti una password temporanea. Appena entri, cambiala dal Profilo.' },
    { d: 'Il portale dice che l\'accesso è bloccato.', r: 'Hai sbagliato la password troppe volte. Aspetta 15 minuti e riprova con calma.' },
    { d: 'Perché non vedo la voce "Rimborsi"?', r: 'I rimborsi chilometrici sono riservati ai delegati e ai ruoli sindacali. Se sei delegato ma non la vedi, chiedi al responsabile della tua sede di aggiornare il tuo ruolo.' },
    { d: 'Ho cambiato concessionaria: come aggiorno il profilo?', r: 'La concessionaria la può cambiare solo un responsabile: scrivi al Segretario o all\'Admin.' },
    { d: 'Vedo solo gli annunci della mia concessionaria, è normale?', r: 'Sì. Ogni sede vede i propri contenuti, più quelli pubblicati dalla Sede Nazionale per tutti.' },
  ],
};

export default guidaIscritto;
