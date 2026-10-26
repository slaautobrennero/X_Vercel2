import React, { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { BellRing, BellOff } from 'lucide-react';
import { attivaPush, disattivaPush, iscrizioneAttuale, isIOS, isStandalone, pushSupportato } from '../lib/push';

export const NotifichePushCard = () => {
  const [attive, setAttive] = useState(false);
  const [busy, setBusy] = useState(false);
  const supportato = pushSupportato();

  useEffect(() => {
    iscrizioneAttuale().then((s) => setAttive(!!s)).catch(() => {});
  }, []);

  const cambia = async () => {
    setBusy(true);
    try {
      if (attive) { await disattivaPush(); setAttive(false); toast.success('Notifiche disattivate su questo dispositivo'); }
      else { await attivaPush(); setAttive(true); toast.success('Notifiche attivate su questo dispositivo'); }
    } catch (e) {
      toast.error(e.message || 'Non è stato possibile attivare le notifiche');
    } finally { setBusy(false); }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6" data-testid="notifiche-push-card">
      <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900"><BellRing size={18} /> Notifiche sul telefono</h2>
      <p className="text-sm text-gray-600 mt-1">Ricevi un avviso su questo dispositivo per rimborsi, comunicati e registrazioni, anche con il portale chiuso. È gratuito.</p>
      {!supportato && isIOS() && !isStandalone() ? (
        <p className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-md p-3 mt-3" data-testid="push-ios-hint">
          Su iPhone: apri il portale con Safari, premi il tasto Condividi e scegli <b>"Aggiungi alla schermata Home"</b>. Poi apri il portale dall'icona e torna qui.
        </p>
      ) : !supportato ? (
        <p className="text-sm text-gray-500 mt-3" data-testid="push-non-supportato">Questo browser non supporta le notifiche.</p>
      ) : (
        <button onClick={cambia} disabled={busy} data-testid="push-toggle-btn"
          className={`mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-colors disabled:opacity-50 ${attive ? 'border border-gray-300 text-gray-700 hover:bg-gray-50' : 'bg-[#1E4D8C] hover:bg-[#163A6A] text-white'}`}>
          {attive ? <><BellOff size={16} /> Disattiva su questo dispositivo</> : <><BellRing size={16} /> Attiva le notifiche</>}
        </button>
      )}
    </div>
  );
};
