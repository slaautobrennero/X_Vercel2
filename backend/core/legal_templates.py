"""
core/legal_templates.py
Template dei documenti legali (Informativa Privacy, Cookie Policy, Termini di Servizio).

I placeholder {{...}} vengono popolati con i dati da `impostazioni_sindacato` (collection MongoDB).
Se in futuro serve modificare il testo, aggiornare qui e incrementare le versioni.

Riferimenti:
- Art. 13 GDPR (informativa)
- Provvedimento Garante 8/5/2014 (cookie)
- Best practice sindacali
"""

# ==================== VERSIONI ATTUALI ====================
PRIVACY_VERSION = "1.0"
COOKIE_VERSION = "1.0"
TERMINI_VERSION = "1.0"


# ==================== INFORMATIVA PRIVACY (art. 13 GDPR) ====================
PRIVACY_TEMPLATE = """# Informativa sulla Privacy

*Versione {{privacy_version}} — ultimo aggiornamento: {{oggi}}*

Ai sensi degli artt. 13 e 14 del Regolamento UE 2016/679 (GDPR), il Titolare del trattamento fornisce le seguenti informazioni relative al trattamento dei dati personali degli utenti del Portale SLA.

## 1. Titolare del trattamento

**{{denominazione}}**
Sede legale: {{sede_legale}}
Codice Fiscale: {{codice_fiscale}}
{{piva_riga}}
PEC: {{pec}}
Email per esercizio diritti privacy: **{{email_privacy}}**
{{sito_web_riga}}

## 2. Responsabile Protezione Dati (DPO)

{{dpo_info}}

## 3. Finalità e base giuridica del trattamento

I dati personali sono trattati per le seguenti finalità:

| Finalità | Base giuridica | Dati trattati |
|---|---|---|
| Gestione iscrizione al sindacato | Contratto (art. 6.1.b GDPR) | Nome, cognome, email, codice fiscale, sede lavorativa |
| Erogazione rimborsi | Contratto e obbligo legale (art. 6.1.b/c) | IBAN, indirizzo di residenza, ricevute, importi |
| Comunicazioni istituzionali (bacheca, notifiche) | Legittimo interesse (art. 6.1.f) | Email, dati account |
| Sicurezza portale (login, audit) | Legittimo interesse (art. 6.1.f) | IP, timestamp accessi |
| Adempimenti fiscali/contabili | Obbligo legale (art. 6.1.c) | Dati rimborsi, IBAN |

Il conferimento dei dati è **obbligatorio** per l'iscrizione al sindacato e la fruizione dei servizi del portale. Il mancato conferimento comporta l'impossibilità di iscriversi.

## 4. Modalità del trattamento

I dati sono trattati con strumenti informatici e telematici, con misure di sicurezza adeguate a garantire riservatezza e integrità, tra cui:
- Crittografia password (bcrypt)
- Autenticazione a due fattori (2FA) per amministratori
- Backup cifrati AES-256
- Log di audit sugli accessi
- Comunicazione HTTPS (Cloudflare Tunnel)

## 5. Destinatari dei dati

I dati **non** vengono diffusi. Possono essere comunicati a:
- Amministratori del portale, delegati sindacali e cassieri (nell'ambito delle rispettive funzioni)
- Consulenti fiscali/legali del sindacato (in caso di necessità)
- Autorità competenti (in caso di richieste legittime)

## 6. Trasferimento dati extra-UE

Il portale utilizza i seguenti servizi che comportano trasferimenti di dati extra-UE:

- **Google Maps API** (Google LLC, USA): per il calcolo automatico dei chilometri nei rimborsi. Trasferisce indirizzi di origine e destinazione.
- **Cloudflare** (USA): per il tunnel HTTPS di accesso al portale. Il traffico è cifrato end-to-end.

Entrambi i fornitori sono aderenti al **Data Privacy Framework** UE-USA (Decisione di adeguatezza 10/07/2023).

## 7. Periodo di conservazione

I dati sono conservati:
- **Per la durata dell'iscrizione** al sindacato, e successivamente:
- **10 anni** per i dati contabili (rimborsi, IBAN, ricevute) — obbligo fiscale
- **5 anni** per i log di audit e accessi
- **Immediatamente** cancellati per dati non essenziali su richiesta dell'interessato

## 8. Diritti dell'interessato

L'iscritto ha diritto a:
- **Accesso** ai propri dati (art. 15)
- **Rettifica** (art. 16)
- **Cancellazione** ("diritto all'oblio", art. 17)
- **Limitazione** del trattamento (art. 18)
- **Portabilità** in formato leggibile (art. 20)
- **Opposizione** al trattamento (art. 21)
- **Revoca del consenso** in qualsiasi momento

L'esercizio dei diritti è **libero, gratuito e senza formalità**. È possibile:
- Utilizzare le funzioni dedicate nella sezione **"I miei dati"** del proprio profilo
- Scrivere a: **{{email_privacy}}**
- Inviare PEC a: **{{pec}}**

L'esercizio del diritto di cancellazione avviene con un periodo di grace di **30 giorni** durante il quale la richiesta può essere annullata. Trascorso tale termine, i dati sono cancellati definitivamente, salvo obblighi di conservazione previsti dalla legge (dati contabili).

## 9. Reclamo al Garante

L'interessato ha diritto di proporre reclamo all'**Autorità Garante per la protezione dei dati personali** (www.garanteprivacy.it, Piazza Venezia 11, 00187 Roma).

## 10. Processi automatizzati

Il portale **non effettua** profilazione né processi decisionali automatizzati che producano effetti giuridici.

## 11. Modifiche all'informativa

La presente informativa può essere aggiornata. In caso di modifiche sostanziali, sarà richiesto un nuovo consenso al successivo accesso al portale.
"""


# ==================== COOKIE POLICY ====================
COOKIE_TEMPLATE = """# Cookie Policy

*Versione {{cookie_version}} — ultimo aggiornamento: {{oggi}}*

Il portale **{{denominazione}}** utilizza esclusivamente **cookie tecnici essenziali**, per i quali NON è richiesto il consenso ai sensi del Provvedimento del Garante Privacy dell'8 maggio 2014 e successivi aggiornamenti.

## Quali cookie usiamo

| Nome | Tipo | Scopo | Durata |
|---|---|---|---|
| `access_token` | Tecnico (essenziale) | Mantenimento sessione utente autenticata | Sessione |
| `refresh_token` | Tecnico (essenziale) | Rinnovo automatico del login | 7 giorni |

Tutti i cookie sono configurati con flag di sicurezza:
- **HttpOnly**: non accessibili via JavaScript
- **Secure**: trasmessi solo su HTTPS
- **SameSite**: protezione anti-CSRF

## Cookie NON presenti

Il portale **non utilizza**:
- Cookie di profilazione
- Cookie di terze parti per analytics (Google Analytics, ecc.)
- Cookie pubblicitari o di marketing
- Pixel di tracciamento (Meta, TikTok, ecc.)

## Gestione da parte dell'utente

I cookie tecnici essenziali sono necessari al funzionamento del portale. Disabilitarli tramite le impostazioni del browser impedirà l'accesso all'area riservata.

Le impostazioni del browser possono essere consultate ai seguenti link:
- [Chrome](https://support.google.com/chrome/answer/95647)
- [Firefox](https://support.mozilla.org/it/kb/Attivare%20e%20disattivare%20i%20cookie)
- [Safari](https://support.apple.com/it-it/guide/safari/sfri11471/mac)
- [Edge](https://support.microsoft.com/it-it/microsoft-edge/eliminare-i-cookie-in-microsoft-edge-63947406-40ac-c3b8-57b9-2a946a29ae09)

## Contatti

Per qualsiasi domanda: **{{email_privacy}}**
"""


# ==================== TERMINI DI SERVIZIO ====================
TERMINI_TEMPLATE = """# Termini di Servizio

*Versione {{termini_version}} — ultimo aggiornamento: {{oggi}}*

Il presente documento disciplina l'utilizzo del **Portale SLA** da parte degli iscritti a **{{denominazione}}**.

## 1. Oggetto

Il portale è uno strumento riservato agli iscritti al sindacato per:
- Richiesta e gestione rimborsi
- Consultazione documentazione e modulistica
- Ricezione comunicazioni istituzionali (bacheca)
- Contatti con i delegati sindacali

## 2. Iscrizione al portale

L'accesso al portale è consentito **esclusivamente** agli iscritti a {{denominazione}}. L'utente si impegna a:
- Fornire dati **veritieri e aggiornati** in fase di registrazione (in particolare IBAN per i rimborsi)
- Custodire con cura le proprie **credenziali di accesso**, non condividerle con terzi
- Segnalare tempestivamente qualsiasi accesso non autorizzato al proprio account

## 3. Obblighi dell'utente

L'utente si impegna a:
- Utilizzare il portale nel **rispetto della legge** e del presente regolamento
- Non caricare contenuti diffamatori, offensivi o illegali
- Non tentare di accedere a dati di altri iscritti
- Non compromettere la sicurezza o l'integrità del portale (attacchi, scraping, ecc.)
- Fornire **ricevute veritiere** per le richieste di rimborso: la falsificazione comporta l'esclusione dal sindacato e conseguenze legali

## 4. Bacheca e comunicazioni

Nella bacheca sindacale gli utenti sono tenuti a mantenere un **tono rispettoso** e coerente con le finalità sindacali. È vietato l'utilizzo per scopi personali, commerciali o politici estranei all'attività sindacale.

## 5. Rimborsi

I rimborsi sono soggetti a:
- Approvazione da parte di Admin/Segretario di sede
- Validazione della documentazione allegata
- Rispetto delle tempistiche e delle procedure sindacali

L'utente è responsabile della veridicità di quanto dichiarato. In caso di irregolarità, il rimborso può essere rifiutato o revocato.

## 6. Modifica e cessazione

Il sindacato si riserva il diritto di:
- Modificare i presenti termini con preavviso agli utenti
- Sospendere l'account in caso di violazioni gravi
- Cancellare l'account su richiesta dell'utente (secondo procedura GDPR)

## 7. Limitazione di responsabilità

Il portale è fornito "as is". Il sindacato:
- Garantisce l'impegno alla continuità del servizio ma non può escludere brevi interruzioni per manutenzione
- Non risponde di danni derivanti da uso improprio del portale
- Effettua backup regolari ma raccomanda all'utente di conservare copia locale dei documenti importanti

## 8. Legge applicabile e foro competente

I presenti termini sono soggetti alla **legge italiana**. Per ogni controversia è competente il **Foro di {{foro_competente}}**.

## 9. Contatti

Per qualsiasi domanda sui termini di servizio: **{{email_privacy}}**
"""


# ==================== REGISTRO TRATTAMENTI (art. 30 GDPR) ====================
# Non è un documento pubblico, ma un registro interno.
# Elenco dei trattamenti attivi nel portale.
REGISTRO_TRATTAMENTI = [
    {
        "nome": "Gestione iscrizioni",
        "finalita": "Gestione anagrafica iscritti al sindacato",
        "base_giuridica": "Contratto (art. 6.1.b GDPR)",
        "categorie_interessati": "Iscritti al sindacato",
        "categorie_dati": "Anagrafici, di contatto, professionali",
        "destinatari": "Amministratori sistema, segretari di sede",
        "trasferimenti_extra_ue": "No",
        "conservazione": "Durata iscrizione + 10 anni (obblighi fiscali)",
        "misure_sicurezza": "Bcrypt, JWT httpOnly, HTTPS, backup cifrati AES-256",
    },
    {
        "nome": "Rimborsi spese",
        "finalita": "Gestione richieste rimborso chilometrico e spese",
        "base_giuridica": "Contratto e obbligo legale (art. 6.1.b/c GDPR)",
        "categorie_interessati": "Iscritti richiedenti rimborso",
        "categorie_dati": "IBAN, indirizzi, ricevute, importi",
        "destinatari": "Cassieri, contabili, amministratori",
        "trasferimenti_extra_ue": "Google Maps (USA) per calcolo KM — DPF adeguato",
        "conservazione": "10 anni (obbligo fiscale)",
        "misure_sicurezza": "Storage locale cifrato, upload validato, ACL per ruolo",
    },
    {
        "nome": "Comunicazioni sindacali",
        "finalita": "Diffusione annunci, notifiche, documenti tramite bacheca",
        "base_giuridica": "Legittimo interesse (art. 6.1.f GDPR)",
        "categorie_interessati": "Iscritti al portale",
        "categorie_dati": "Email, ID account, contenuti annunci",
        "destinatari": "Tutti gli iscritti (o sottogruppi per sede)",
        "trasferimenti_extra_ue": "No",
        "conservazione": "Durata iscrizione",
        "misure_sicurezza": "Autenticazione JWT, autorizzazioni per ruolo",
    },
    {
        "nome": "Sicurezza portale e audit",
        "finalita": "Prevenzione accessi non autorizzati e attività fraudolente",
        "base_giuridica": "Legittimo interesse (art. 6.1.f GDPR)",
        "categorie_interessati": "Tutti gli utenti che accedono al portale",
        "categorie_dati": "IP, timestamp, user-agent, azioni compiute",
        "destinatari": "Amministratori sicurezza (SuperAdmin)",
        "trasferimenti_extra_ue": "Cloudflare Tunnel (USA) — DPF adeguato",
        "conservazione": "5 anni",
        "misure_sicurezza": "Rate limiting, 2FA, hCaptcha, log di audit protetti",
    },
]
