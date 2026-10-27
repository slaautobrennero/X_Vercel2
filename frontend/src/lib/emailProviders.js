// Impostazioni SMTP dei provider più diffusi in Italia. nota = cosa serve oltre a utente e password.
const APP_PWD = 'Serve una "password per le app", non la password normale.';

export const EMAIL_PROVIDERS = [
  { id: 'gmail', nome: 'Gmail', host: 'smtp.gmail.com', port: 587, tls: 'starttls', nota: `${APP_PWD} Account Google → Sicurezza → Verifica in due passaggi → Password per le app.` },
  { id: 'outlook', nome: 'Outlook / Hotmail / Live', host: 'smtp-mail.outlook.com', port: 587, tls: 'starttls', nota: 'Se hai la verifica in due passaggi attiva serve una password per le app (account.microsoft.com → Sicurezza).' },
  { id: 'office365', nome: 'Microsoft 365 (aziendale)', host: 'smtp.office365.com', port: 587, tls: 'starttls', nota: "L'amministratore del dominio deve abilitare l'invio SMTP per la casella." },
  { id: 'libero', nome: 'Libero', host: 'smtp.libero.it', port: 465, tls: 'ssl', nota: 'Usa indirizzo email completo e password della casella.' },
  { id: 'aruba', nome: 'Aruba (dominio)', host: 'smtps.aruba.it', port: 465, tls: 'ssl', nota: 'Per le caselle del vostro dominio ospitato su Aruba.' },
  { id: 'yahoo', nome: 'Yahoo Mail', host: 'smtp.mail.yahoo.com', port: 465, tls: 'ssl', nota: `${APP_PWD} Yahoo → Sicurezza account → Genera password app.` },
  { id: 'virgilio', nome: 'Virgilio', host: 'out.virgilio.it', port: 465, tls: 'ssl', nota: 'Usa indirizzo email completo e password della casella.' },
  { id: 'tim', nome: 'TIM / Alice', host: 'smtp.tim.it', port: 465, tls: 'ssl', nota: 'Usa indirizzo email completo e password della casella.' },
  { id: 'tiscali', nome: 'Tiscali', host: 'smtp.tiscali.it', port: 465, tls: 'ssl', nota: 'Usa indirizzo email completo e password della casella.' },
  { id: 'fastweb', nome: 'Fastweb', host: 'smtp.fastwebnet.it', port: 587, tls: 'starttls', nota: 'Usa indirizzo email completo e password della casella.' },
  { id: 'icloud', nome: 'iCloud', host: 'smtp.mail.me.com', port: 587, tls: 'starttls', nota: `${APP_PWD} appleid.apple.com → Password specifiche per le app.` },
  { id: 'register', nome: 'Register.it (dominio)', host: 'authsmtp.securemail.pro', port: 465, tls: 'ssl', nota: 'Per le caselle del vostro dominio ospitato su Register.it.' },
  { id: 'zoho', nome: 'Zoho Mail', host: 'smtp.zoho.eu', port: 465, tls: 'ssl', nota: 'Se hai la verifica in due passaggi serve una password per le app.' },
  { id: 'altro', nome: 'Altro (inserisco i dati a mano)', host: '', port: 587, tls: 'starttls', nota: 'Chiedi server, porta e sicurezza a chi gestisce la vostra casella email.' },
];

export const providerDaHost = (host) =>
  EMAIL_PROVIDERS.find((p) => p.host && p.host === host)?.id || (host ? 'altro' : '');
