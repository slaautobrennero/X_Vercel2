# 📱 Guida Completa: PWA (Progressive Web App) - App Mobile per Portale SLA

## 🎯 Cosa Otterrai

Trasformerai il Portale SLA in un'**app installabile** su Android e iOS senza dover passare per Play Store/App Store!

**Risultato finale:**
- ✅ Icona app sulla home del telefono
- ✅ Funziona offline (visualizza dati cached)
- ✅ Notifiche push (future)
- ✅ Schermo intero (senza barra browser)
- ✅ Look & feel di app nativa
- ✅ **Zero costi** pubblicazione store

---

## 📋 Cosa è una PWA?

Una **Progressive Web App (PWA)** è un sito web che si comporta come un'app mobile:

| Feature | Sito Web Normale | PWA | App Nativa |
|---------|------------------|-----|------------|
| Installabile | ❌ | ✅ | ✅ |
| Funziona offline | ❌ | ✅ | ✅ |
| Icona su home | ❌ | ✅ | ✅ |
| Notifiche push | ❌ | ✅ | ✅ |
| Accesso hardware | ❌ | ⚠️ Limitato | ✅ Completo |
| App store | - | ❌ Non serve | ✅ Richiesto |
| Costo sviluppo | Basso | **Bassissimo** | Alto |

---

## 🚀 SETUP PASSO-PASSO

### **STEP 1: Verifica File PWA Creati**

I file necessari sono già stati creati in `/app/frontend/public/`:

```bash
# Sul progetto Emergent (da copiare poi sul Raspberry)
ls -la /app/frontend/public/

# Dovresti vedere:
# - manifest.json          ✅
# - service-worker.js      ✅
```

---

### **STEP 2: Genera Icone App**

Le PWA richiedono icone in varie dimensioni. Hai **2 opzioni**:

#### **Opzione A: Usa il Logo SLA Esistente**

Se hai già il logo SLA (il file `Full logo.png` negli assets):

1. Vai su https://www.pwabuilder.com/imageGenerator
2. Upload logo SLA
3. Clicca **Generate**
4. Scarica lo zip con tutte le icone
5. Estrai nella cartella `/opt/portale-sla/frontend/public/icons/`

#### **Opzione B: Crea Icone Manualmente con ImageMagick**

Sul Raspberry Pi:

```bash
# Installa ImageMagick
sudo apt install imagemagick -y

# Crea directory icons
mkdir -p /opt/portale-sla/frontend/public/icons

# Vai nella directory dove hai il logo SLA
cd /path/al/tuo/logo

# Genera tutte le dimensioni (sostituisci logo.png con il tuo file)
convert logo.png -resize 72x72 /opt/portale-sla/frontend/public/icons/icon-72x72.png
convert logo.png -resize 96x96 /opt/portale-sla/frontend/public/icons/icon-96x96.png
convert logo.png -resize 128x128 /opt/portale-sla/frontend/public/icons/icon-128x128.png
convert logo.png -resize 144x144 /opt/portale-sla/frontend/public/icons/icon-144x144.png
convert logo.png -resize 152x152 /opt/portale-sla/frontend/public/icons/icon-152x152.png
convert logo.png -resize 192x192 /opt/portale-sla/frontend/public/icons/icon-192x192.png
convert logo.png -resize 384x384 /opt/portale-sla/frontend/public/icons/icon-384x384.png
convert logo.png -resize 512x512 /opt/portale-sla/frontend/public/icons/icon-512x512.png
```

Verifica icone create:
```bash
ls -lh /opt/portale-sla/frontend/public/icons/
```

---

### **STEP 3: Copia File PWA sul Raspberry Pi**

Sul **Raspberry Pi**:

```bash
# Crea directory se non esiste
mkdir -p /opt/portale-sla/frontend/public

# Copia manifest.json
nano /opt/portale-sla/frontend/public/manifest.json
# Incolla il contenuto da /app/frontend/public/manifest.json
# Salva: CTRL+X → Y → INVIO

# Copia service-worker.js
nano /opt/portale-sla/frontend/public/service-worker.js
# Incolla il contenuto da /app/frontend/public/service-worker.js
# Salva: CTRL+X → Y → INVIO
```

---

### **STEP 4: Modifica index.html per Registrare Service Worker**

Apri `index.html`:

```bash
nano /opt/portale-sla/frontend/public/index.html
```

**Trova il tag `<head>` e aggiungi queste righe DOPO `<title>`:**

```html
<!-- PWA Manifest -->
<link rel="manifest" href="%PUBLIC_URL%/manifest.json" />

<!-- Meta tags PWA -->
<meta name="theme-color" content="#1e40af" />
<meta name="mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
<meta name="apple-mobile-web-app-title" content="Portale SLA" />

<!-- Apple Touch Icons -->
<link rel="apple-touch-icon" href="%PUBLIC_URL%/icons/icon-192x192.png" />
<link rel="apple-touch-icon" sizes="152x152" href="%PUBLIC_URL%/icons/icon-152x152.png" />
<link rel="apple-touch-icon" sizes="180x180" href="%PUBLIC_URL%/icons/icon-192x192.png" />
```

**Alla fine del tag `<body>`, prima di `</body>`, aggiungi:**

```html
<!-- Service Worker Registration -->
<script>
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/service-worker.js')
        .then((registration) => {
          console.log('✅ Service Worker registrato:', registration.scope);
        })
        .catch((error) => {
          console.error('❌ Service Worker registration failed:', error);
        });
    });
  }
</script>
```

**Salva:** CTRL+X → Y → INVIO

---

### **STEP 5: Rebuild Frontend Docker**

Sul Raspberry Pi:

```bash
cd /opt/portale-sla

# Rebuild frontend
docker compose -f docker/docker-compose.yml build frontend

# Riavvia
docker compose -f docker/docker-compose.yml up -d
```

Aspetta 1-2 minuti che il build completi.

---

### **STEP 6: Test PWA su Android**

**Dal tuo smartphone Android:**

1. Apri **Chrome** (NON altri browser!)
2. Vai su `https://portale-sla.tuodominio.com` (o il tuo URL Cloudflare)
3. Fai login
4. Clicca sui **3 puntini** in alto a destra
5. Cerca l'opzione **"Installa app"** o **"Aggiungi a schermata Home"**
6. Clicca e conferma!

**Risultato:**
- ✅ Icona "Portale SLA" appare sulla home
- ✅ Cliccandola si apre a schermo intero
- ✅ Look & feel come app nativa!

---

### **STEP 7: Test PWA su iOS (iPhone/iPad)**

**Dal tuo iPhone:**

1. Apri **Safari** (DEVE essere Safari!)
2. Vai su `https://portale-sla.tuodominio.com`
3. Fai login
4. Clicca il **bottone Condividi** (quadrato con freccia su)
5. Scrolla e trova **"Aggiungi alla schermata Home"**
6. Clicca → **Aggiungi**

**Risultato:**
- ✅ Icona "Portale SLA" sulla home
- ✅ Si apre come app!

---

## ✅ PWA INSTALLATA!

Ora gli utenti possono installare il Portale SLA come un'app vera!

---

## 🎨 Personalizzazioni Avanzate

### **1. Cambia Colore Tema**

Apri `manifest.json`:

```bash
nano /opt/portale-sla/frontend/public/manifest.json
```

Modifica:
```json
"theme_color": "#1e40af",        // Colore barra superiore (blu SLA)
"background_color": "#ffffff"    // Colore splash screen
```

Ricostruisci frontend dopo la modifica.

---

### **2. Aggiungi Screenshot per Store** (Opzionale)

Per rendere l'app più "bella" quando si installa:

```bash
mkdir -p /opt/portale-sla/frontend/public/screenshots
```

Fai screenshot della dashboard e rimborsi, poi caricali in quella cartella.

Nel `manifest.json`, la sezione `screenshots` è già configurata!

---

### **3. Notifiche Push (Feature Futura)**

Il service worker ha già il codice per notifiche push. Per attivarle:

**Backend - Invia notifica:**
```python
# Esempio codice da aggiungere in futuro
from pywebpush import webpush, WebPushException

def send_push_notification(user_subscription, message):
    try:
        webpush(
            subscription_info=user_subscription,
            data=message,
            vapid_private_key="YOUR_VAPID_PRIVATE_KEY",
            vapid_claims={"sub": "mailto:admin@sla.it"}
        )
    except WebPushException as ex:
        print(f"Push failed: {ex}")
```

**Frontend - Richiedi permesso:**
```javascript
// Aggiungi in App.js
if ('Notification' in window && Notification.permission === 'default') {
  Notification.requestPermission().then((permission) => {
    if (permission === 'granted') {
      console.log('✅ Notifiche permesse');
    }
  });
}
```

---

## 📊 Verifica PWA Funzionante

### **Chrome DevTools (Desktop)**

1. Apri `https://portale-sla.tuodominio.com` su Chrome desktop
2. Premi **F12** (DevTools)
3. Vai alla tab **Application**
4. Sidebar sinistra → **Manifest**

Dovresti vedere:
```
✓ Manifest exists and is valid
✓ Service Worker registered
✓ Icons loaded
```

5. Sidebar → **Service Workers**

Dovresti vedere:
```
Status: activated and running
```

---

### **Lighthouse PWA Audit**

Nel Chrome DevTools:

1. Tab **Lighthouse**
2. Seleziona solo **Progressive Web App**
3. Clicca **Generate report**

**Score atteso: 90-100** ✅

---

## 🆘 Troubleshooting

### "Aggiungi a Home" non appare

**Cause possibili:**

1. **Manca HTTPS** → La PWA richiede HTTPS (Cloudflare lo fornisce!)
   - Verifica URL: deve essere `https://` NON `http://`

2. **manifest.json non caricato**
   ```bash
   # Verifica nel browser
   https://portale-sla.tuodominio.com/manifest.json
   # Deve ritornare il JSON
   ```

3. **Service Worker non registrato**
   - F12 → Console → Cerca errori
   - F12 → Application → Service Workers → Deve essere "activated"

4. **Browser non supportato**
   - Android: Usa **Chrome** o **Edge**
   - iOS: Usa **Safari** (altri non funzionano!)

---

### Service Worker non si aggiorna

**Fix - Hard Refresh:**

Desktop:
- Chrome: CTRL+SHIFT+R (Windows) o CMD+SHIFT+R (Mac)
- Safari: CMD+OPTION+R

Mobile:
- Svuota cache browser: Impostazioni → App → Chrome/Safari → Cancella dati

**Fix - Force Update Service Worker:**

F12 → Application → Service Workers → Check **"Update on reload"**

---

### Icons non appaiono

**Verifica path icone:**
```bash
# Sul Raspberry Pi
ls -la /opt/portale-sla/frontend/public/icons/

# Devono esserci:
# icon-72x72.png
# icon-96x96.png
# icon-128x128.png
# icon-144x144.png
# icon-152x152.png
# icon-192x192.png
# icon-384x384.png
# icon-512x512.png
```

Se mancano, rigenera con ImageMagick (Step 2)

---

### App installata ma si apre nel browser

**Causa:** App non riconosciuta come standalone

**Fix - Verifica manifest.json:**
```json
"display": "standalone"  // NON "browser"
```

Poi rebuild frontend.

---

## 📱 Distribuzione agli Utenti

### **Metodo 1: Istruzioni per Utenti**

Crea una pagina "Come installare l'app":

**Per Android:**
1. Apri Chrome
2. Vai su https://portale-sla.tuodominio.com
3. Menu (3 puntini) → "Installa app"

**Per iOS:**
1. Apri Safari
2. Vai su https://portale-sla.tuodominio.com
3. Bottone Condividi → "Aggiungi a schermata Home"

---

### **Metodo 2: QR Code**

Genera QR code che punta al tuo sito:

1. Vai su https://www.qr-code-generator.com/
2. Inserisci URL: `https://portale-sla.tuodominio.com`
3. Scarica QR code
4. Stampalo e distribuiscilo

Gli utenti scansionano → vengono al sito → installano app!

---

### **Metodo 3: Web App Manifest Sharing**

Se in futuro vuoi pubblicare anche su store (opzionale):

**Google Play:** Puoi pubblicare PWA usando **TWA (Trusted Web Activity)**
- Tool: https://www.pwabuilder.com/
- Genera APK da caricare su Play Store
- Costo: $25 una tantum

**App Store Apple:** PWA non supportate nativamente, serve wrapper
- Tool: Capacitor (richiede sviluppo aggiuntivo)

---

## 📊 Analytics PWA

### **Traccia Installazioni**

Aggiungi al codice (in `index.html`):

```javascript
window.addEventListener('beforeinstallprompt', (e) => {
  console.log('📱 PWA installabile!');
  
  // Traccia con Google Analytics (se ce l'hai)
  if (window.gtag) {
    gtag('event', 'pwa_prompt_shown');
  }
});

window.addEventListener('appinstalled', (e) => {
  console.log('✅ PWA installata!');
  
  if (window.gtag) {
    gtag('event', 'pwa_installed');
  }
});
```

---

## 🎉 Configurazione Completata!

Il Portale SLA è ora:
- ✅ Installabile come app mobile
- ✅ Funziona offline (cache)
- ✅ Look & feel nativo
- ✅ Pronto per notifiche push (future)

**Testa su Android e iOS e condividi con gli utenti!** 📱

---

## 📚 Risorse Utili

- **PWA Best Practices:** https://web.dev/progressive-web-apps/
- **Service Worker Guide:** https://developers.google.com/web/fundamentals/primers/service-workers
- **PWA Builder:** https://www.pwabuilder.com/
- **Manifest Generator:** https://www.simicart.com/manifest-generator.html/
- **Test PWA:** https://www.pwatips.com/

---

**Fine Guida PWA** 🎊

**Documenti correlati:**
- [Backup Google Drive](./GUIDA_BACKUP_GOOGLE_DRIVE.md)
- [Cloudflare Tunnel](./GUIDA_CLOUDFLARE_TUNNEL.md)
