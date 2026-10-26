import React from 'react';
import { Folder, FolderLock, Eye, EyeOff, Trash2, Globe } from 'lucide-react';

export const CartellaCard = ({ cartella, onOpen, onToggle, onDelete }) => {
  const Icona = cartella.visibile ? Folder : FolderLock;
  const piena = cartella.num_documenti > 0;
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow flex flex-col" data-testid={`cartella-${cartella.id}`}>
      <button onClick={() => onOpen(cartella)} className="flex items-start gap-3 text-left flex-1" data-testid={`apri-cartella-${cartella.id}`}>
        <div className={`w-11 h-11 rounded-lg flex items-center justify-center flex-shrink-0 ${cartella.visibile ? 'bg-blue-50 text-[#1E4D8C]' : 'bg-gray-100 text-gray-500'}`}>
          <Icona size={22} />
        </div>
        <div className="min-w-0">
          <h3 className="font-medium text-gray-900 truncate">{cartella.nome}</h3>
          <p className="text-sm text-gray-500">{cartella.num_documenti} {cartella.num_documenti === 1 ? 'documento' : 'documenti'}</p>
          <div className="flex flex-wrap gap-1 mt-1">
            {!cartella.visibile && <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-gray-200 text-gray-700" data-testid={`badge-riservata-${cartella.id}`}>Riservata agli Admin</span>}
            {cartella.sede_id === null && <span className="inline-flex items-center gap-0.5 text-[10px] font-medium px-1.5 py-0.5 rounded bg-amber-100 text-amber-800"><Globe size={10} /> Tutte le sedi</span>}
          </div>
        </div>
      </button>
      {cartella.gestibile && (
        <div className="flex items-center gap-1 mt-3 pt-3 border-t border-gray-100">
          <button onClick={() => onToggle(cartella)} className="flex-1 flex items-center justify-center gap-1.5 px-2 py-1.5 text-xs text-gray-700 hover:bg-gray-100 rounded-md transition-colors" data-testid={`toggle-cartella-${cartella.id}`}>
            {cartella.visibile ? <><EyeOff size={14} /> Rendi riservata</> : <><Eye size={14} /> Rendi visibile</>}
          </button>
          <button onClick={() => onDelete(cartella)} disabled={piena} title={piena ? 'Elimina prima i documenti contenuti' : 'Elimina cartella'}
            className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors disabled:opacity-40 disabled:hover:bg-transparent disabled:hover:text-gray-400" data-testid={`delete-cartella-${cartella.id}`}>
            <Trash2 size={15} />
          </button>
        </div>
      )}
    </div>
  );
};
