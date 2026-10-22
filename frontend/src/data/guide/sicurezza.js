import { Lock, KeyRound, Timer, UserCheck, FileCheck2, Globe2, Eye, Scale, DatabaseBackup, HeartHandshake, Cpu, AlertTriangle } from 'lucide-react';

const ADMIN = ['admin', 'superuser'];

const guidaSicurezza = {
  id: 'sicurezza',
  titolo: 'Guida alla Sicurezza',
  sottotitolo: 'Come proteggiamo il portale e i tuoi dati, spiegato in modo semplice',
  icona: Lock,
  colore: '#15803D',
  ruoli: 'tutti',
  sezioni: [
    {
      id: 'account',
      titolo: 'Il tuo account è protetto',
      icona: KeyRound,
      intro: 'La prima barriera è l\'accesso: abbiamo messo più "serrature" una dopo l\'altra.',
      passi: [
        { t: 'Password mai salvate in chiaro', d: 'La password viene trasformata in un codice irreversibile (bcrypt). Nessuno, nemmeno gli amministratori, può leggerla.' },
        { t: 'Password robuste obbligatorie', d: 'Almeno 8 caratteri con lettere, numeri e simboli.' },
        { t: 'Blocco dopo 5 errori', d: 'Chi prova a indovinare la password viene fermato per 15 minuti.' },
        { t: 'Limite di richieste', d: 'Il portale rallenta chi fa troppe richieste in poco tempo, bloccando i programmi automatici.' },
        { t: 'Verifica anti-robot', d: 'La registrazione è protetta da hCaptcha, che distingue le persone dai bot.' },
        { t: 'Approvazione delle registrazioni', d: 'Un nuovo account non può entrare finché la segreteria della sua concessionaria non conferma che è davvero un iscritto.' },
        { t: 'Verifica in due passaggi', d: 'Per i ruoli con più poteri (Admin, SuperAdmin) è disponibile il codice dal telefono, chiesto anche per le operazioni più delicate.' },
      ],
    },
    {
      id: 'sessione',
      titolo: 'La sessione di lavoro',
      icona: Timer,
      intro: 'Quando entri, il portale ti riconosce con un "pass" digitale temporaneo.',
      passi: [
        { t: 'Pass protetto', d: 'Il pass è salvato in un cookie protetto che i programmi nella pagina non possono leggere o rubare, e viaggia solo su connessione cifrata.' },
        { t: 'Scadenza automatica', d: 'Il pass scade dopo 24 ore; oltre una settimana devi rifare l\'accesso.' },
        { t: 'Uscita automatica', d: 'Dopo 30 minuti senza attività il portale ti disconnette, con un avviso un minuto prima. Così nessuno può usare un computer lasciato acceso.' },
        { t: 'Account bloccati subito', d: 'Se un account viene disattivato, smette di funzionare immediatamente, anche se era già collegato.' },
        { t: 'Cambio password = uscita ovunque', d: 'Quando cambi password, o un responsabile la reimposta, vieni disconnesso da tutti i dispositivi: telefono, PC, tablet.' },
        { t: 'Password temporanea da cambiare subito', d: 'Se ricevi una password temporanea, il portale ti obbliga a sceglierne una nuova prima di fare qualsiasi altra cosa.' },
      ],
    },
    {
      id: 'permessi',
      titolo: 'Ognuno vede solo ciò che gli spetta',
      icona: UserCheck,
      intro: 'I permessi sono decisi in base al ruolo e alla concessionaria.',
      passi: [
        { t: 'Ruoli', d: 'Iscritto, Delegato, Segreteria, Segretario, Cassiere, Admin, SuperAdmin: ogni ruolo ha solo le funzioni necessarie.' },
        { t: 'Separazione tra concessionarie', d: 'I dati di una concessionaria non sono visibili alle altre. La Sede Nazionale vede tutto, ma solo in lettura.' },
        { t: 'Nessuno può modificare chi sta "sopra"', d: 'Admin e Segretari gestiscono solo gli utenti della propria concessionaria, mai altri Admin né i propri ruoli. Le modifiche all\'IBAN vengono registrate.' },
        { t: 'Controlli sul server', d: 'Ogni permesso viene verificato dal server a ogni richiesta: nascondere un pulsante non basta, e infatti non ci affidiamo a quello.' },
      ],
    },
    {
      id: 'file',
      titolo: 'Ricevute e documenti caricati',
      icona: FileCheck2,
      intro: 'I file sono una porta d\'ingresso tipica per gli attacchi: per questo sono filtrati.',
      passi: [
        { t: 'Solo formati sicuri', d: 'Accettiamo solo PDF, JPG e PNG, fino a 5 MB.' },
        { t: 'Contenuto verificato', d: 'Il portale controlla il contenuto reale del file, non solo il nome: un file che finge di essere un PDF viene rifiutato.' },
        { t: 'Nomi casuali', d: 'Ogni file viene rinominato con un codice casuale, così non si può indovinare o sovrascrivere.' },
        { t: 'Download controllato', d: 'Una ricevuta può essere scaricata solo da chi ne ha diritto (il richiedente e i responsabili della sua sede).' },
        { t: 'Doppia copia', d: 'Ogni file è salvato sia su disco sia nel database, quindi è incluso nei backup.' },
      ],
    },
    {
      id: 'connessione',
      titolo: 'Connessione cifrata e server nascosto',
      icona: Globe2,
      intro: 'Il server non è esposto direttamente su Internet.',
      passi: [
        { t: 'Sempre HTTPS', d: 'Tutto il traffico tra il tuo dispositivo e il portale è cifrato (il lucchetto nel browser).' },
        { t: 'Nessuna porta aperta', d: 'Il server è raggiungibile solo tramite un tunnel sicuro Cloudflare, che filtra anche gli attacchi di massa (DDoS).' },
        { t: 'Protezioni del browser', d: 'Il portale chiede al browser di bloccare trucchi noti, come mostrare il sito dentro pagine false (clickjacking) o eseguire codice non autorizzato.' },
        { t: 'Niente azioni da siti esterni', d: 'Il portale accetta modifiche solo se arrivano dalle sue pagine: un sito malevolo aperto in un\'altra scheda non può agire al posto tuo.' },
        { t: 'Link sicuri', d: 'Negli annunci e nei documenti sono ammessi solo link web normali (http/https): niente link che eseguono codice.' },
        { t: 'Database isolato', d: 'Il database non è raggiungibile dall\'esterno ed è protetto da password.' },
      ],
    },
    {
      id: 'tracciabilita',
      titolo: 'Tutto è tracciato',
      icona: Eye,
      intro: 'Le operazioni importanti lasciano una traccia nell\'Audit Log.',
      passi: [
        { t: 'Chi, cosa, quando', d: 'Cambi di ruolo, approvazioni, pagamenti, modifiche ai documenti legali e alle impostazioni vengono registrati con autore e data.' },
        { t: 'Prima e dopo', d: 'Per molte modifiche viene salvato il valore precedente e quello nuovo.' },
      ],
    },
    {
      id: 'privacy',
      titolo: 'Privacy e GDPR',
      icona: Scale,
      intro: 'Il portale è stato progettato rispettando il Regolamento europeo sulla privacy.',
      passi: [
        { t: 'Consensi registrati', d: 'Al momento della registrazione salviamo quale versione di Privacy e Termini hai accettato e quando.' },
        { t: 'I tuoi dati quando vuoi', d: 'Dal Profilo scarichi tutti i tuoi dati (anche le ricevute) in autonomia.' },
        { t: 'Diritto all\'oblio', d: 'Puoi chiedere la cancellazione; i dati contabili vengono anonimizzati solo quando la legge lo consente.' },
        { t: 'Solo i dati necessari', d: 'Chiediamo l\'IBAN e l\'indirizzo solo ai delegati, che ne hanno bisogno per i rimborsi.' },
      ],
    },
    {
      id: 'backup',
      titolo: 'Backup',
      icona: DatabaseBackup,
      intro: 'Se qualcosa va storto, i dati si possono recuperare.',
      passi: [
        { t: 'Copie cifrate', d: 'Le copie di sicurezza del database sono cifrate (AES-256): anche se venissero rubate, sarebbero illeggibili.' },
        { t: 'Copia fuori sede', d: 'Le copie possono essere inviate anche su Google Drive, così sopravvivono a un guasto del server.' },
      ],
    },
    {
      id: 'consigli',
      titolo: 'Cosa puoi fare tu',
      icona: HeartHandshake,
      intro: 'La sicurezza è un lavoro di squadra. Bastano poche abitudini.',
      passi: [
        { t: 'Una password solo per il portale', d: 'Non riutilizzare la password di email o social.' },
        { t: 'Non condividerla mai', d: 'Il sindacato non ti chiederà mai la password, né per email né per telefono. Se qualcuno lo fa, è una truffa.' },
        { t: 'Esci dai computer condivisi', d: 'Premi sempre Esci quando usi un PC non tuo.' },
        { t: 'Controlla l\'indirizzo', d: 'Prima di inserire la password verifica che l\'indirizzo nel browser sia quello del portale e che ci sia il lucchetto.' },
        { t: 'Segnala le anomalie', d: 'Se vedi qualcosa di strano nel tuo account, avvisa subito il responsabile della tua sede.' },
      ],
    },
    {
      id: 'tecnico',
      titolo: 'Dettagli tecnici (riservato ai responsabili)',
      icona: Cpu,
      ruoliSezione: ADMIN,
      intro: 'Riepilogo tecnico delle misure, utile per audit interni o per il DPO.',
      passi: [
        { t: 'Autenticazione', d: 'JWT HS256 in cookie httpOnly + Secure; access token 24h, refresh 7 giorni, revocati con token_version a cambio/reset password e disattivazione. Hash bcrypt. JWT_SECRET obbligatoria (≥32 caratteri), il backend non si avvia senza.' },
        { t: '2FA', d: 'TOTP (RFC 6238) per Admin/SuperAdmin, con step-up obbligatorio su modifiche a documenti legali e impostazioni.' },
        { t: 'Anti brute-force e rate limit', d: 'Blocco 15 min dopo 5 errori per IP+email; login 10/min, registrazione 3/ora, limite globale 200/min. IP reale da CF-Connecting-IP (Cloudflare).' },
        { t: 'CSRF, XSS ed export', d: 'Controllo Origin su POST/PUT/PATCH/DELETE; link solo http(s); celle CSV/Excel che iniziano con = + - @ neutralizzate.' },
        { t: 'Header HTTP', d: 'HSTS, Content-Security-Policy, X-Frame-Options DENY, X-Content-Type-Options nosniff, Referrer-Policy, Permissions-Policy.' },
        { t: 'Infrastruttura', d: 'Docker con rete interna; backend esposto solo su 127.0.0.1; MongoDB autenticato e non esposto; segreti nel file .env; accesso SSH amministrativo solo via VPN Tailscale; esposizione pubblica solo via Cloudflare Tunnel.' },
        { t: 'Allegati', d: 'Verifica firma reale PDF/PNG/JPG, 5 MB, nomi UUID con estensione dal contenuto; copia durevole in MongoDB GridFS con cache su disco.' },
      ],
    },
    {
      id: 'limiti',
      titolo: 'Limiti noti e miglioramenti previsti',
      icona: AlertTriangle,
      ruoliSezione: ADMIN,
      intro: 'Per trasparenza, ecco cosa non è ancora presente o dipende dalla configurazione.',
      passi: [
        { t: 'Avvisi via email', d: 'Nessun avviso automatico via email per accessi sospetti o blocchi dell\'account.' },
        { t: 'Cifratura dei singoli campi', d: 'IBAN e indirizzi sono protetti dal database e dai backup cifrati, ma non cifrati campo per campo. Prevista prima del trasferimento su server online.' },
        { t: 'Verifica anti-robot', d: 'Senza le chiavi hCaptcha nel file .env la verifica resta disattivata: in quel caso la Dashboard del SuperAdmin mostra un avviso.' },
      ],
    },
  ],
  faq: [
    { d: 'Il portale può vedere la mia password?', r: 'No. Viene salvata solo una sua "impronta" irreversibile: per questo, se la dimentichi, si può solo reimpostare, non recuperare.' },
    { d: 'Chi può vedere il mio IBAN?', r: 'Tu e i responsabili dei rimborsi della tua sede (Cassiere, Admin), oltre al SuperAdmin.' },
    { d: 'Cosa succede se il server si guasta?', r: 'I dati vengono ripristinati dai backup cifrati, che includono anche le ricevute.' },
    { d: 'Ho ricevuto un\'email che chiede la mia password del portale.', r: 'È una truffa (phishing): non rispondere e avvisa il responsabile della tua sede.' },
  ],
};

export default guidaSicurezza;
