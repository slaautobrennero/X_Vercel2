import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { ShieldAlert } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const AvvisiSicurezza = () => {
  const [avvisi, setAvvisi] = useState([]);

  useEffect(() => {
    axios.get(`${API}/system/avvisi-sicurezza`).then((r) => setAvvisi(r.data.avvisi || [])).catch(() => setAvvisi([]));
  }, []);

  if (!avvisi.length) return null;
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4" data-testid="avvisi-sicurezza">
      <p className="flex items-center gap-2 font-semibold text-red-800 mb-2"><ShieldAlert size={18} /> Avvisi di sicurezza</p>
      <ul className="list-disc ml-6 space-y-1 text-sm text-red-800">
        {avvisi.map((a) => <li key={a}>{a}</li>)}
      </ul>
    </div>
  );
};
