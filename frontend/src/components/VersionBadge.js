import React, { useState } from 'react';
import { APP_VERSION, BUILD_DATE, RELEASE_NAME } from '../version';

/**
 * Badge versione fisso in basso a sinistra.
 * - Click: espande mostrando data build e nome release.
 * - Posizione: bottom-left per non collidere con "Made with Emergent" (bottom-right).
 */
export default function VersionBadge() {
  const [open, setOpen] = useState(false);
  return (
    <div
      className="fixed bottom-3 left-3 z-40 select-none"
      data-testid="version-badge"
    >
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="px-2.5 py-1 rounded-full bg-gray-900/80 hover:bg-gray-900 text-white text-[11px] font-mono shadow-md backdrop-blur-sm transition-colors"
        title="Versione applicazione"
      >
        v{APP_VERSION}
      </button>
      {open && (
        <div className="absolute bottom-8 left-0 w-64 p-3 rounded-lg bg-white border border-gray-200 shadow-lg text-xs text-gray-700 space-y-1">
          <div><span className="font-semibold">Versione:</span> {APP_VERSION}</div>
          <div><span className="font-semibold">Build:</span> {BUILD_DATE}</div>
          {RELEASE_NAME && (
            <div><span className="font-semibold">Rilascio:</span> {RELEASE_NAME}</div>
          )}
          <div className="pt-1 text-[10px] text-gray-400 border-t border-gray-100">
            Click sul badge per chiudere
          </div>
        </div>
      )}
    </div>
  );
}
