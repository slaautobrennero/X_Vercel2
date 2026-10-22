import { Wallet, Search, CheckCircle2, CreditCard, BarChart3 } from 'lucide-react';

const guidaCassiere = {
  id: 'cassiere',
  titolo: 'Guida Cassiere',
  sottotitolo: 'Verificare, approvare e pagare i rimborsi; esportare i report contabili',
  icona: Wallet,
  colore: '#B45309',
  ruoli: ['cassiere', 'admin', 'superuser'],
  sezioni: [
    {
      id: 'verifica',
      titolo: 'Verificare una richiesta',
      icona: Search,
      intro: 'Prima di approvare, controlla che tutto sia in ordine.',
      passi: [
        { t: 'Filtra le richieste in attesa', d: 'In Rimborsi filtra per stato "In Attesa".', btn: 'Rimborsi' },
        { t: 'Apri il dettaglio', d: 'Vedi richiedente, motivo, percorso, KM, importo e ricevute.' },
        { t: 'Controlla i KM', d: 'Se compare l\'avviso "KM modificati manualmente", confronta i km calcolati da Google Maps con quelli inseriti e leggi le Note.' },
        { t: 'Scarica le ricevute', d: 'Apri ogni ricevuta con l\'icona Scarica.' },
        { t: 'Storico variazioni', d: 'L\'icona dell\'orologio mostra tutte le modifiche fatte alla richiesta.' },
      ],
    },
    {
      id: 'approva',
      titolo: 'Approvare o rifiutare',
      icona: CheckCircle2,
      intro: 'La decisione viene registrata con data e autore e il richiedente riceve una notifica.',
      passi: [
        { t: 'Approva', d: 'La richiesta diventa gialla (Approvato) e viene salvata la data di approvazione.', btn: 'Approva' },
        { t: 'Rifiuta', d: 'La richiesta diventa rossa e il richiedente riceve una notifica: spiegagli il motivo, così può correggere e reinviare.', btn: 'Rifiuta' },
      ],
    },
    {
      id: 'paga',
      titolo: 'Registrare il pagamento',
      icona: CreditCard,
      intro: 'Una richiesta diventa "Pagato" solo caricando la contabile del bonifico: così ogni pagamento ha sempre la sua prova.',
      passi: [
        { t: 'Fai il bonifico', d: 'Usa l\'IBAN del richiedente: lo trovi nel report ed è incluso negli export CSV, Excel e PDF.' },
        { t: 'Carica la contabile', d: 'Nel dettaglio, sezione "Carica Contabile per chiudere il pagamento", seleziona il PDF o l\'immagine della ricevuta di bonifico e conferma.' },
        { t: 'Pagamento diretto', d: 'Se la richiesta è ancora In Attesa e va pagata subito, puoi caricare direttamente la contabile: l\'approvazione viene saltata e la richiesta passa a Pagato.' },
      ],
      nota: { tipo: 'info', testo: 'Al caricamento della contabile vengono avvisati il richiedente e gli altri responsabili della sede.' },
    },
    {
      id: 'report',
      titolo: 'Esportare i report',
      icona: BarChart3,
      intro: 'In Report trovi il riepilogo annuale dei rimborsi della sede.',
      passi: [
        { t: 'Scegli l\'anno', d: 'Seleziona l\'anno da analizzare.', btn: 'Report' },
        { t: 'Esporta', d: 'Scarica in CSV, Excel o PDF. Il report include anche la data di approvazione.', btn: 'Excel' },
      ],
    },
  ],
  faq: [
    { d: 'Posso rimettere "Approvato" una richiesta già pagata?', r: 'No: lo stato Pagato è definitivo e legato alla contabile. Per eventuali rettifiche contatta l\'Admin.' },
    { d: 'Vedo i rimborsi di altre sedi?', r: 'No, solo quelli della tua concessionaria. Fa eccezione la Sede Nazionale, che li vede in sola lettura.' },
    { d: 'Ci sono richieste ferme da tanto tempo.', r: 'Il portale manda promemoria automatici per le richieste in attesa da troppo tempo.' },
  ],
};

export default guidaCassiere;
