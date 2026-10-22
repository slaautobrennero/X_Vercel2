import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Timer } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const LIMITE_MS = 30 * 60 * 1000;
const AVVISO_MS = 60 * 1000;
const CHIAVE = 'sla_last_activity';
const EVENTI = ['mousemove', 'mousedown', 'keydown', 'scroll', 'touchstart'];

const ultimaAttivita = () => Number(localStorage.getItem(CHIAVE)) || Date.now();

export const InattivitaLogout = () => {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [secondi, setSecondi] = useState(null);
  const avvisoAttivo = useRef(false);
  const esci = useRef(null);
  esci.current = async () => {
    try { await logout(); } catch { /* sessione già scaduta */ }
    toast.info('Sei stato disconnesso per inattività');
    navigate('/login');
  };

  useEffect(() => {
    let ultimoSalvataggio = 0;
    const segna = () => {
      if (avvisoAttivo.current) return;
      const ora = Date.now();
      if (ora - ultimoSalvataggio > 5000) { localStorage.setItem(CHIAVE, String(ora)); ultimoSalvataggio = ora; }
    };
    localStorage.setItem(CHIAVE, String(Date.now()));
    EVENTI.forEach((e) => window.addEventListener(e, segna, { passive: true }));

    const timer = setInterval(() => {
      const rimanente = LIMITE_MS - (Date.now() - ultimaAttivita());
      if (rimanente <= 0) {
        clearInterval(timer);
        esci.current();
      } else if (rimanente <= AVVISO_MS) {
        avvisoAttivo.current = true;
        setSecondi(Math.ceil(rimanente / 1000));
      } else if (avvisoAttivo.current) {
        avvisoAttivo.current = false;
        setSecondi(null);
      }
    }, 1000);

    return () => {
      clearInterval(timer);
      EVENTI.forEach((e) => window.removeEventListener(e, segna));
    };
  }, []);

  const resta = () => {
    localStorage.setItem(CHIAVE, String(Date.now()));
    avvisoAttivo.current = false;
    setSecondi(null);
  };

  if (secondi === null) return null;
  return (
    <div className="fixed inset-0 z-[100] bg-black/50 flex items-center justify-center p-4" data-testid="inattivita-dialog">
      <div className="bg-white rounded-xl shadow-xl max-w-sm w-full p-6 text-center">
        <div className="w-12 h-12 mx-auto rounded-full bg-amber-100 text-amber-700 flex items-center justify-center mb-3"><Timer size={24} /></div>
        <h2 className="text-lg font-bold text-gray-900">Sei ancora lì?</h2>
        <p className="text-sm text-gray-600 mt-1">Per sicurezza verrai disconnesso tra <span className="font-semibold text-gray-900" data-testid="inattivita-secondi">{secondi}</span> secondi.</p>
        <button onClick={resta} data-testid="inattivita-resta-btn"
          className="mt-5 w-full px-4 py-2 rounded-lg bg-[#1E4D8C] hover:bg-[#163A6A] text-white font-medium transition-colors">
          Resta collegato
        </button>
      </div>
    </div>
  );
};
