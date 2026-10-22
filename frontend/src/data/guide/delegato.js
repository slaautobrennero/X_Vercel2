import { Receipt, ClipboardCheck, MapPin, Paperclip, Activity, Filter } from 'lucide-react';

const guidaDelegato = {
  id: 'delegato',
  titolo: 'Guida Delegato',
  sottotitolo: 'Come chiedere un rimborso chilometrico e seguirlo fino al pagamento',
  icona: Receipt,
  colore: '#0F766E',
  ruoli: ['delegato', 'segreteria', 'segretario', 'admin', 'superuser'],
  sezioni: [
    {
      id: 'prima',
      titolo: 'Prima di iniziare',
      icona: ClipboardCheck,
      intro: 'Due dati nel Profilo ti fanno risparmiare tempo e assicurano che il pagamento arrivi.',
      passi: [
        { t: 'Indirizzo di casa', d: 'Inserisci Indirizzo, Città e CAP: il portale li userà come punto di partenza "Casa".', btn: 'Profilo' },
        { t: 'IBAN', d: 'Controlla che l\'IBAN sia corretto: è il conto su cui riceverai il bonifico.', btn: 'Salva' },
      ],
    },
    {
      id: 'nuova',
      titolo: 'Creare una nuova richiesta',
      icona: MapPin,
      intro: 'Il portale calcola i chilometri con Google Maps e l\'importo con la tariffa della tua sede.',
      passi: [
        { t: 'Apri Rimborsi', d: 'Dal menu scegli Rimborsi e premi il pulsante in alto.', btn: 'Nuova Richiesta' },
        { t: 'Data e Motivo', d: 'Indica il giorno della trasferta e il motivo (es. RSA, Sede, Altro). Per alcuni motivi, come "Altro", le Note sono obbligatorie.' },
        { t: 'Partenza', d: 'Scegli "Casa" (il tuo indirizzo del profilo) oppure "Altro indirizzo" e scrivilo per intero.' },
        { t: 'Destinazione', d: 'Scrivi l\'indirizzo completo di arrivo.' },
        { t: 'Calcola i chilometri', d: 'Il portale chiede a Google Maps il percorso e compila i KM di andata.', btn: 'Calcola con Google Maps' },
        { t: 'Andata e ritorno', d: 'Lascia spuntato "Andata e Ritorno" se sei tornato al punto di partenza: i KM vengono raddoppiati.' },
        { t: 'Autostrada e pasti (se previsti)', d: 'Se la tua sede lo consente, spunta "Uso Autostrada" e inserisci il costo dei pedaggi; in "Spese Pasti" indica l\'importo totale e il numero di partecipanti.' },
        { t: 'Controlla e invia', d: 'Verifica l\'"Importo stimato" in fondo, allega le ricevute e invia.', btn: 'Invia Richiesta' },
      ],
      nota: { tipo: 'attenzione', testo: 'Puoi correggere a mano i KM, ma la richiesta verrà segnata come "KM modificati manualmente" e chi approva vedrà sia i km calcolati sia quelli inseriti. Indica sempre il motivo nelle Note.' },
    },
    {
      id: 'ricevute',
      titolo: 'Allegare le ricevute',
      icona: Paperclip,
      intro: 'Pedaggi, pasti e altre spese vanno documentati con le ricevute.',
      passi: [
        { t: 'Formati accettati', d: 'PDF, JPG o PNG, massimo 5 MB per file. Una foto nitida fatta col telefono va benissimo.' },
        { t: 'Aggiungere ricevute dopo', d: 'Puoi aggiungerne altre aprendo il Dettaglio Rimborso dalla lista.' },
        { t: 'Rimuovere una ricevuta', d: 'Possibile solo finché la richiesta è "In Attesa", con l\'icona Rimuovi.' },
      ],
    },
    {
      id: 'stati',
      titolo: 'Seguire lo stato della richiesta',
      icona: Activity,
      intro: 'Ogni richiesta ha un colore che ti dice a che punto è.',
      passi: [
        { t: 'In Attesa (bianco)', d: 'La richiesta è stata inviata e aspetta di essere valutata.' },
        { t: 'Approvato (giallo)', d: 'La richiesta è stata accettata e attende il bonifico.' },
        { t: 'Rifiutato (rosso)', d: 'La richiesta non è stata accettata: chiedi alla segreteria o al cassiere della tua sede il motivo.' },
        { t: 'Pagato (verde)', d: 'Il bonifico è stato fatto. Nel dettaglio puoi scaricare la contabile del pagamento.' },
      ],
      nota: { tipo: 'info', testo: 'A ogni cambio di stato ricevi una notifica, quindi non serve controllare di continuo.' },
    },
    {
      id: 'filtri',
      titolo: 'Ritrovare i rimborsi',
      icona: Filter,
      intro: 'La lista si filtra facilmente.',
      passi: [
        { t: 'Per periodo', d: 'Usa "Data dal" e "Data al".' },
        { t: 'Per stato o importo', d: 'Filtra per stato (es. solo Pagati) o tra un importo minimo e massimo.' },
      ],
    },
  ],
  faq: [
    { d: 'Come viene calcolato l\'importo?', r: 'KM totali × tariffa al km della tua sede, più eventuali pedaggi autostradali e spese pasti previsti dalla sede.' },
    { d: 'Google Maps non trova l\'indirizzo.', r: 'Scrivi l\'indirizzo completo (via, numero civico, città). Se ancora non funziona inserisci i KM a mano e spiega nelle Note.' },
    { d: 'Ho sbagliato un dato dopo l\'invio.', r: 'Finché è In Attesa puoi aggiungere o togliere ricevute. Per altri dati contatta chi gestisce i rimborsi della tua sede.' },
    { d: 'Quanto tempo ci vuole per il pagamento?', r: 'Dipende dai tempi della tua sede. Il portale invia promemoria automatici ai responsabili per le richieste ferme da troppo tempo.' },
  ],
};

export default guidaDelegato;
