import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Mail } from 'lucide-react';
import { Switch } from './ui/switch';
import { useAuth } from '../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const PreferenzeEmailCard = () => {
  const { user, updateUser } = useAuth();
  const [attive, setAttive] = useState(user?.email_documenti !== false);

  const cambia = async (valore) => {
    setAttive(valore);
    try {
      await axios.put(`${API}/auth/me/preferenze`, { email_documenti: valore });
      updateUser({ email_documenti: valore });
      toast.success(valore ? 'Riceverai le email dei nuovi documenti' : 'Email dei nuovi documenti disattivate');
    } catch { setAttive(!valore); toast.error('Non è stato possibile salvare'); }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 flex items-start justify-between gap-4" data-testid="preferenze-email-card">
      <div>
        <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900"><Mail size={18} /> Email dei nuovi documenti</h2>
        <p className="text-sm text-gray-600 mt-1">Ricevi un'email quando la tua concessionaria carica un nuovo documento in una cartella con invio automatico.</p>
      </div>
      <Switch checked={attive} onCheckedChange={cambia} data-testid="preferenze-email-documenti-switch" />
    </div>
  );
};
