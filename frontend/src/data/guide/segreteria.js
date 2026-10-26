import { Briefcase, Megaphone, FileUp, Users, History, Globe } from 'lucide-react';

const guidaSegreteria = {
  id: 'segreteria',
  titolo: 'Guida Segreteria e Segretario',
  sottotitolo: 'Comunicare con gli iscritti, gestire la modulistica e, per il Segretario, gli utenti della sede',
  icona: Briefcase,
  colore: '#7C3AED',
  ruoli: ['segreteria', 'segretario', 'admin', 'superuser'],
  sezioni: [
    {
      id: 'annuncio',
      titolo: 'Pubblicare un annuncio in Bacheca',
      icona: Megaphone,
      intro: 'Gli annunci arrivano a tutti gli iscritti della tua concessionaria, che ricevono anche una notifica.',
      passi: [
        { t: 'Apri la Bacheca', d: 'Dal menu scegli Bacheca e premi il pulsante per creare.', btn: 'Nuovo Annuncio' },
        { t: 'Titolo e Contenuto', d: 'Scrivi un titolo chiaro e il testo del comunicato.' },
        { t: 'Link e allegato (facoltativi)', d: 'Puoi aggiungere un link esterno e un allegato PDF, JPG o PNG fino a 5 MB.' },
        { t: 'Pubblica', d: 'Conferma: l\'annuncio compare subito e parte la notifica agli iscritti.' },
      ],
      nota: { tipo: 'info', testo: 'Per eliminare un annuncio usa l\'icona cestino: viene cancellato anche l\'allegato.' },
    },
    {
      id: 'documento',
      titolo: 'Caricare un documento',
      icona: FileUp,
      intro: 'I documenti sono divisi in cartelle. Le cartelle le crea l\'Admin; tu carichi i documenti dentro.',
      passi: [
        { t: 'Apri la cartella', d: 'In Documenti clicca sulla cartella giusta (es. Modulistica).', btn: 'Carica Documento' },
        { t: 'Compila i campi', d: 'Nome Documento, una breve Descrizione e il File (PDF, JPG, PNG, max 5 MB).' },
        { t: 'Conferma il caricamento', d: 'Il documento è subito disponibile e gli iscritti ricevono una notifica.' },
      ],
    },
    {
      id: 'utenti',
      titolo: 'Gestire gli utenti (Segretario)',
      icona: Users,
      intro: 'Il Segretario gestisce gli utenti della propria concessionaria. Non può vedere né modificare utenti di altre sedi, né Admin e SuperAdmin. I ruoli li assegna l\'Admin.',
      ruoliSezione: ['segretario', 'admin', 'superuser'],
      passi: [
        { t: 'Approva le nuove registrazioni', d: 'Quando qualcuno si registra ricevi una notifica. In cima alla pagina Utenti trovi il riquadro "Registrazioni da approvare": controlla che sia davvero un iscritto della tua concessionaria.', btn: 'Approva' },
        { t: 'Rifiuta chi non conosci', d: 'Se la persona non è un iscritto, rifiuta: l\'account e i suoi dati vengono eliminati.', btn: 'Rifiuta' },
        { t: 'Cerca un utente', d: 'In Utenti usa la ricerca per nome, cognome o email.' },
        { t: 'Reset password', d: 'Se un utente ha dimenticato la password, genera una password temporanea, copiala e comunicala di persona o per telefono.', btn: 'Copia password' },
        { t: 'Disabilitare un account', d: 'Blocca temporaneamente l\'accesso senza cancellare nulla. Si può riattivare in qualsiasi momento.' },
        { t: 'Cancellare definitivamente', d: 'Solo il SuperAdmin può cancellare un account in modo definitivo: chiediglielo se serve.' },
      ],
      nota: { tipo: 'attenzione', testo: 'Non mandare mai la password temporanea per email o in chat di gruppo. Al primo accesso il portale obbliga l\'utente a sceglierne una nuova.' },
    },
    {
      id: 'audit',
      titolo: 'Controllare l\'Audit Log (Segretario)',
      icona: History,
      intro: 'L\'Audit Log è il registro di "chi ha fatto cosa e quando" sulle operazioni importanti.',
      ruoliSezione: ['segretario', 'admin', 'superuser'],
      passi: [
        { t: 'Apri Audit Log', d: 'Dal menu scegli Audit Log.', btn: 'Audit Log' },
        { t: 'Leggi le colonne', d: 'Quando, Chi, Azione, Target (su cosa) e Dettaglio.' },
        { t: 'Storico variazioni', d: 'Per alcune azioni vedi il valore prima e dopo la modifica.' },
      ],
    },
    {
      id: 'nazionale',
      titolo: 'Se fai parte della Sede Nazionale',
      icona: Globe,
      intro: 'La Sede Nazionale ha una visione d\'insieme su tutte le concessionarie.',
      passi: [
        { t: 'Pubblicare per tutti', d: 'Annunci e documenti pubblicati dalla Sede Nazionale arrivano a tutte le concessionarie.' },
        { t: 'Pubblicare solo per il Nazionale', d: 'Spunta "Pubblica solo per membri del Nazionale" per i contenuti interni.' },
        { t: 'Consultare le altre sedi', d: 'Puoi vedere in sola lettura annunci, documenti e rimborsi delle altre sedi, senza poterli modificare.' },
      ],
    },
  ],
  faq: [
    { d: 'Posso approvare i rimborsi?', r: 'No: l\'approvazione e il pagamento spettano a Cassiere e Admin. Puoi però creare e seguire le tue richieste.' },
    { d: 'Ho pubblicato un annuncio con un errore.', r: 'Eliminalo e ripubblicalo corretto. Gli iscritti riceveranno una nuova notifica.' },
    { d: 'Un utente si è registrato nella sede sbagliata.', r: 'Contatta l\'Admin o il SuperAdmin per spostarlo nella sede corretta.' },
  ],
};

export default guidaSegreteria;
