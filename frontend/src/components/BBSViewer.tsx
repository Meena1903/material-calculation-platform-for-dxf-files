import React from 'react';
import { PileTypeInventory, RebarBarDetail } from '../types/takeoff';
import { Layers, ShieldCheck, Hash, Ruler, Weight, Sparkles, X } from 'lucide-react';

interface BBSViewerProps {
  selectedPile: PileTypeInventory | null;
  onClose: () => void;
}

export const BBSViewer: React.FC<BBSViewerProps> = ({ selectedPile, onClose }) => {
  if (!selectedPile) return null;

  return (
    <div className="bg-slate-900/95 border border-slate-800 rounded-xl overflow-hidden shadow-2xl mt-4">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/80">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-lg">
            <Weight className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-100 text-sm flex items-center gap-2">
              <span>Bar Bending Schedule (BBS) — Tag: {selectedPile.tag}</span>
              <span className="text-xs px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono">
                Ø{selectedPile.diameter_mm}mm × {selectedPile.depth_m}m
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Computed strictly via IS 1786 unit weight formula ($w = d^2 / 162.28$ kg/m) in native Python
            </p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* BBS Components Breakdown */}
      <div className="p-4">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider text-[11px] font-semibold border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Role / Component</th>
                <th className="py-2.5 px-3">Bar Dia (d)</th>
                <th className="py-2.5 px-3">Schedule Spec</th>
                <th className="py-2.5 px-3 text-right">Unit Weight ($d^2/162.28$)</th>
                <th className="py-2.5 px-3 text-right">Cut Length / Pile</th>
                <th className="py-2.5 px-3 text-right">Total Linear Length</th>
                <th className="py-2.5 px-3 text-right">Weight / Pile (kg)</th>
                <th className="py-2.5 px-3 text-right font-semibold text-amber-400">Total Steel ({selectedPile.total_piles} Piles)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {selectedPile.rebar_details.map((bar, idx) => (
                <tr key={idx} className="hover:bg-slate-800/40 transition">
                  <td className="py-2.5 px-3 font-semibold text-slate-200 flex items-center gap-2">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        bar.bar_type.includes('Main')
                          ? 'bg-blue-400'
                          : bar.bar_type.includes('Helical')
                          ? 'bg-emerald-400'
                          : 'bg-purple-400'
                      }`}
                    />
                    <span>{bar.bar_type}</span>
                  </td>
                  <td className="py-2.5 px-3 font-mono text-slate-300">Ø{bar.diameter_mm} mm</td>
                  <td className="py-2.5 px-3 text-slate-300">{bar.count_or_pitch_description}</td>
                  <td className="py-2.5 px-3 text-right font-mono text-slate-400">
                    {bar.unit_weight_kg_per_m.toFixed(4)} kg/m
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono text-slate-300">
                    {bar.cut_length_per_pile_m.toFixed(2)} m
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono text-slate-300">
                    {(bar.total_length_per_pile_m * selectedPile.total_piles).toFixed(1)} m
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono text-slate-300">
                    {bar.total_weight_per_pile_kg.toFixed(2)} kg
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono font-bold text-amber-400">
                    {bar.total_weight_all_piles_mt.toFixed(4)} MT ({bar.total_weight_all_piles_kg.toFixed(1)} kg)
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-slate-950 font-bold text-slate-200 border-t border-slate-700">
              <tr>
                <td className="py-2.5 px-3 text-amber-400" colSpan={6}>
                  TOTAL STEEL FOR {selectedPile.tag} ({selectedPile.total_piles} PILES)
                </td>
                <td className="py-2.5 px-3 text-right font-mono">
                  {selectedPile.total_steel_weight_per_pile_kg.toFixed(2)} kg/pile
                </td>
                <td className="py-2.5 px-3 text-right font-mono text-amber-400 font-extrabold">
                  {selectedPile.total_steel_tonnage_mt.toFixed(4)} MT
                </td>
              </tr>
            </tfoot>
          </table>
        </div>

        {/* Civil Engineering Compliance Formula Notes */}
        <div className="mt-4 p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs grid grid-cols-1 md:grid-cols-3 gap-3 text-slate-400">
          <div>
            <span className="font-semibold text-slate-200 block mb-0.5">1. Main Bars:</span>
            <span>Length = Depth + 1.0m (anchorage into pile cap). Total linear weight = n × L × (d²/162.28 kg/m).</span>
          </div>
          <div>
            <span className="font-semibold text-slate-200 block mb-0.5">2. Helical Ties (Ø8mm @ 180mm):</span>
            <span>Length = (Depth / 0.18m) × sqrt((π × D_cage)² + 0.18²) + 2 anchor turns.</span>
          </div>
          <div>
            <span className="font-semibold text-slate-200 block mb-0.5">3. Spacers (Ø12mm @ 1500mm):</span>
            <span>floor(Depth / 1.5m) + 1 rings of circumference (π × D_cage + 0.15m lap).</span>
          </div>
        </div>
      </div>
    </div>
  );
};
