import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const pushSupportato = () => 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;

export const isIOS = () => /iphone|ipad|ipod/i.test(navigator.userAgent);
export const isStandalone = () => window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;

export function registraServiceWorker() {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => navigator.serviceWorker.register('/service-worker.js').catch(() => {}));
  }
}

const toUint8 = (b64) => {
  const pad = '='.repeat((4 - (b64.length % 4)) % 4);
  const raw = atob((b64 + pad).replace(/-/g, '+').replace(/_/g, '/'));
  return Uint8Array.from([...raw].map((c) => c.charCodeAt(0)));
};

export async function iscrizioneAttuale() {
  if (!pushSupportato()) return null;
  const reg = await navigator.serviceWorker.getRegistration();
  return reg ? reg.pushManager.getSubscription() : null;
}

export async function attivaPush() {
  const permesso = await Notification.requestPermission();
  if (permesso !== 'granted') throw new Error('Permesso negato: abilita le notifiche per questo sito nelle impostazioni del browser');
  const reg = (await navigator.serviceWorker.getRegistration()) || (await navigator.serviceWorker.register('/service-worker.js'));
  await navigator.serviceWorker.ready;
  const { data } = await axios.get(`${API}/push/public-key`);
  const sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: toUint8(data.public_key) });
  await axios.post(`${API}/push/subscribe`, sub.toJSON());
}

export async function disattivaPush() {
  const sub = await iscrizioneAttuale();
  if (!sub) return;
  await axios.post(`${API}/push/unsubscribe`, { endpoint: sub.endpoint });
  await sub.unsubscribe();
}
