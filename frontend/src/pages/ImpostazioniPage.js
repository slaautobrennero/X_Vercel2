import React, { useCallback, useEffect, useState } from 'react';
import axios from 'axios';
import { Link, Navigate, useParams } from 'react-router-dom';
import { ArrowLeft, Landmark } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { hasRole } from '../lib/utils';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { RiepilogoSedi } from '../components/impostazioni/RiepilogoSedi';
import { RimborsiSedeCard } from '../components/impostazioni/RimborsiSedeCard';
import { MotiviSedeCard } from '../components/impostazioni/MotiviSedeCard';
import { InviiAutomaticiCard } from '../components/impostazioni/InviiAutomaticiCard';
import { SedeAzioniSuper } from '../components/impostazioni/SedeAzioniSuper';
import { SedeEmailConfig } from '../components/SedeEmailConfig';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SedeImpostazioni = ({ sedeId, isSuper }) => {
  const [sede, setSede] = useState(null);
  const carica = useCallback(() => {
    axios.get(`${API}/sedi`).then((r) => setSede(r.data.find((s) => s.id === sedeId) || false));
  }, [sedeId]);
  useEffect(() => { carica(); }, [carica]);

  if (sede === null) return <div className="flex justify-center h-64 items-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1E4D8C]" /></div>;
  if (!sede) return <p className="text-gray-500">Concessionaria non trovata.</p>;
  return (
    <div className="space-y-6 max-w-4xl" data-testid="impostazioni-sede">
      {isSuper && <Link to="/impostazioni" className="inline-flex items-center gap-1 text-sm text-[#1E4D8C] hover:underline" data-testid="impostazioni-back"><ArrowLeft size={15} /> Tutte le concessionarie</Link>}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold text-gray-900 font-['Manrope']" data-testid="impostazioni-sede-nome">
            {sede.nome}
            {sede.is_nazionale && <span className="inline-flex items-center gap-1 bg-amber-100 text-amber-800 text-xs font-medium px-2 py-0.5 rounded"><Landmark size={12} /> Nazionale</span>}
          </h1>
          <p className="text-gray-600 mt-1">Impostazioni della concessionaria</p>
        </div>
        {isSuper && <SedeAzioniSuper sede={sede} onCambio={carica} />}
      </div>
      <Tabs defaultValue="rimborsi">
        <TabsList>
          <TabsTrigger value="rimborsi" data-testid="tab-rimborsi">Rimborsi</TabsTrigger>
          <TabsTrigger value="email" data-testid="tab-email">Email</TabsTrigger>
          <TabsTrigger value="invii" data-testid="tab-invii">Invii automatici</TabsTrigger>
        </TabsList>
        <TabsContent value="rimborsi" className="space-y-6 mt-4">
          <RimborsiSedeCard sede={sede} onSalvato={carica} />
          <MotiviSedeCard sedeId={sede.id} isSuper={isSuper} />
        </TabsContent>
        <TabsContent value="email" className="mt-4"><SedeEmailConfig sedeId={sede.id} emailContatto={sede.email_contatto} onSalvato={carica} /></TabsContent>
        <TabsContent value="invii" className="mt-4"><InviiAutomaticiCard sede={sede} /></TabsContent>
      </Tabs>
    </div>
  );
};

export default function ImpostazioniPage() {
  const { user } = useAuth();
  const { sedeId } = useParams();
  const isSuper = hasRole(user, 'superadmin');
  if (isSuper && !sedeId) return <RiepilogoSedi />;
  if (!isSuper && sedeId && sedeId !== user?.sede_id) return <Navigate to="/impostazioni" replace />;
  const id = sedeId || user?.sede_id;
  if (!id) return <p className="text-gray-500">Il tuo account non è collegato a una concessionaria.</p>;
  return <SedeImpostazioni key={id} sedeId={id} isSuper={isSuper} />;
}
