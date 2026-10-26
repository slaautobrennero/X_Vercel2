import { Shield, Smartphone, UsersRound, ScrollText, Gauge } from 'lucide-react';

const guidaAdmin = {
  id: 'admin',
  titolo: 'Guida Admin',
  sottotitolo: 'Responsabile della concessionaria: utenti, rimborsi, report e sicurezza dell\'account',
  icona: Shield,
  colore: '#BE123C',
  ruoli: ['admin', 'superuser'],
  sezioni: [
    {
      id: 'panoramica',
      titolo: 'Il tuo ruolo in breve',
      icona: Gauge,
      intro: 'L\'Admin ha tutti i poteri sulla propria concessionaria: gestisce utenti, approva e paga rimborsi, consulta report e Audit Log.',
      passi: [
        { t: 'Gli strumenti delle altre guide', d: 'Per bacheca, documenti e utenti segui la Guida Segreteria; per rimborsi e report la Guida Cassiere.' },
        { t: 'Solo la tua sede', d: 'Ogni operazione è limitata alla tua concessionaria: il controllo è fatto dal server, non solo dall\'interfaccia.' },
      ],
    },
    {
      id: '2fa',
      titolo: 'Attivare la verifica in due passaggi (2FA)',
      icona: Smartphone,
      intro: 'Con la 2FA, anche se qualcuno scopre la tua password, non può entrare senza il tuo telefono. Per un Admin è fortemente consigliata.',
      passi: [
        { t: 'Installa un\'app di autenticazione', d: 'Ad esempio Google Authenticator, Authy o 1Password sul tuo smartphone.' },
        { t: 'Avvia l\'attivazione', d: 'Vai nel Profilo, sezione 2FA.', btn: 'Attiva 2FA' },
        { t: 'Inquadra il QR code', d: 'Con l\'app inquadra il codice QR mostrato (o inserisci a mano il codice segreto).' },
        { t: 'Conferma', d: 'Scrivi il codice di 6 cifre che vedi nell\'app.', btn: 'Verifica' },
        { t: 'Dal prossimo accesso', d: 'Dopo la password ti verrà chiesto il codice dell\'app, che cambia ogni 30 secondi.' },
      ],
      nota: { tipo: 'attenzione', testo: 'Se cambi telefono, disattiva la 2FA prima (serve la password) e riattivala sul nuovo dispositivo.' },
    },
    {
      id: 'ruoli',
      titolo: 'Assegnare i ruoli',
      icona: UsersRound,
      intro: 'Un utente può avere più ruoli contemporaneamente (es. Delegato + Cassiere).',
      passi: [
        { t: 'Apri Utenti', d: 'Cerca la persona e premi Modifica Ruoli.', btn: 'Modifica Ruoli' },
        { t: 'Scegli i ruoli', d: 'Puoi assegnare Iscritto, Delegato, Segreteria, Segretario e Cassiere. "Iscritto" è esclusivo: non si combina con gli altri.' },
        { t: 'Salva', d: 'La modifica viene registrata nell\'Audit Log con il valore precedente e quello nuovo.' },
      ],
      nota: { tipo: 'info', testo: 'I ruoli Admin, SuperUser e SuperAdmin li assegna solo il SuperAdmin. Puoi gestire solo gli utenti della tua concessionaria, non altri Admin né i tuoi stessi ruoli.' },
    },
    {
      id: 'cartelle',
      titolo: 'Cartelle dei documenti ed email della sede',
      icona: ScrollText,
      intro: 'Tu decidi come è organizzata la sezione Documenti della tua concessionaria.',
      passi: [
        { t: 'Crea una cartella', d: 'In Documenti premi "Nuova cartella" e dai un nome (es. Modulistica, Contratti).', btn: 'Nuova cartella' },
        { t: 'Visibile o riservata', d: 'Con "Rendi riservata" la cartella e i documenti dentro li vedono solo gli Admin; con "Rendi visibile" tornano visibili a tutti.', btn: 'Rendi riservata' },
        { t: 'Eliminare una cartella', d: 'Si può eliminare solo quando è vuota: prima elimina i documenti al suo interno.' },
        { t: 'Email della concessionaria', d: 'Nel Profilo, in "Email della concessionaria", indica l\'indirizzo a cui arrivano le risposte alle email del portale.', btn: 'Salva' },
      ],
    },
    {
      id: 'controllo',
      titolo: 'Controllo e trasparenza',
      icona: ScrollText,
      intro: 'Usa l\'Audit Log per verificare periodicamente le operazioni sensibili.',
      passi: [
        { t: 'Controlla i cambi di ruolo', d: 'Verifica che nessuno abbia ricevuto permessi non dovuti.' },
        { t: 'Controlla i pagamenti', d: 'Ogni approvazione e pagamento ha autore e data.' },
      ],
    },
  ],
  faq: [
    { d: 'Ho perso il telefono con la 2FA.', r: 'Contatta il SuperAdmin, che può aiutarti a ripristinare l\'accesso.' },
    { d: 'Posso vedere i dati di un\'altra concessionaria?', r: 'No. Solo SuperAdmin e SuperUser hanno visione su tutte le sedi; la Sede Nazionale in sola lettura.' },
  ],
};

export default guidaAdmin;
