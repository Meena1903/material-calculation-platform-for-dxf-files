import React, { useState } from 'react';
import { PileTypeInventory } from '../types/takeoff';
import { Search, Filter, ArrowUpDown, ChevronRight, Eye } from 'lucide-react';

interface PileInventoryTableProps {
  inventory: PileTypeInventory[];
  onSelectPileType: (pile: PileTypeInventory) => void;
  selectedTag?: string;
}

export const PileInventoryTable: React.FC<PileInventoryTableProps> = ({
  inventory,
  onSelectPileType,
  selectedTag,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<keyof PileTypeInventory>('tag');
  const [sortAsc, setSortAsc] = useState(true);

  const filteredInventory = inventory
    .filter(
      p =>
        p.tag.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.diameter_mm.toString().includes(searchTerm) ||
        p.depth_m.toString().includes(searchTerm)
    )
    .sort((a, b) => {
      const valA = a[sortField];
      const valB = b[sortField];
      if (typeof valA === 'number' && typeof valB === 'number') {
        return sortAsc ? valA - valB : valB - valA;
      }
      return sortAsc
        ? String(valA).localeCompare(String(valB))
        : String(valB).localeCompare(String(valA));
    });

  const handleSort = (field: keyof PileTypeInventory) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  const totalPiles = inventory.reduce((sum, p) => sum + p.total_piles, 0);
  const totalVolume = inventory.reduce((sum, p) => sum + p.total_concrete_volume_m3, 0);
  const totalSteel = inventory.reduce((sum, p) => sum + p.total_steel_tonnage_mt, 0);

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
      {/* Table Header Controls */}
      <div className="p-4 border-b border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900/50">
        <div>
          <h3 className="font-semibold text-slate-200 text-sm">Pile Schedule & Material Breakdown</h3>
          <p className="text-xs text-slate-400">Structured inventory extracted from CAD drawing schedule</p>
        </div>

        {/* Search input */}
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Filter by tag, diameter..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition"
          />
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs text-left">
          <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider text-[11px] font-semibold border-b border-slate-800">
            <tr>
              <th className="py-3 px-4 cursor-pointer hover:text-slate-200" onClick={() => handleSort('tag')}>
                <div className="flex items-center gap-1">
                  <span>Pile Tag</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-3 px-4 cursor-pointer hover:text-slate-200" onClick={() => handleSort('diameter_mm')}>
                <div className="flex items-center gap-1">
                  <span>Dia (Ø)</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-3 px-4 cursor-pointer hover:text-slate-200" onClick={() => handleSort('depth_m')}>
                <div className="flex items-center gap-1">
                  <span>Depth</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-3 px-4 cursor-pointer hover:text-slate-200" onClick={() => handleSort('capacity_ton')}>
                <div className="flex items-center gap-1">
                  <span>Capacity</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-3 px-4 text-center">Config (Caps x Mult)</th>
              <th className="py-3 px-4 text-right cursor-pointer hover:text-slate-200" onClick={() => handleSort('total_piles')}>
                <div className="flex items-center justify-end gap-1">
                  <span>Count</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-3 px-4 text-right cursor-pointer hover:text-slate-200" onClick={() => handleSort('concrete_volume_per_pile_m3')}>
                <div className="flex items-center justify-end gap-1">
                  <span>Vol / Pile</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-3 px-4 text-right cursor-pointer hover:text-slate-200" onClick={() => handleSort('total_concrete_volume_m3')}>
                <div className="flex items-center justify-end gap-1">
                  <span>Total RMC</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-3 px-4 text-right cursor-pointer hover:text-slate-200" onClick={() => handleSort('total_steel_tonnage_mt')}>
                <div className="flex items-center justify-end gap-1">
                  <span>Steel (MT)</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-3 px-4 text-center">BBS Detail</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {filteredInventory.map(pile => {
              const isSelected = selectedTag === pile.tag;
              return (
                <tr
                  key={pile.tag}
                  onClick={() => onSelectPileType(pile)}
                  className={`hover:bg-slate-800/60 cursor-pointer transition ${
                    isSelected ? 'bg-emerald-950/30 border-l-2 border-emerald-500' : ''
                  }`}
                >
                  <td className="py-3 px-4 font-bold text-slate-100 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    <span>{pile.tag}</span>
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-300">Ø{pile.diameter_mm} mm</td>
                  <td className="py-3 px-4 font-mono text-slate-300">{pile.depth_m} m</td>
                  <td className="py-3 px-4 text-slate-300">{pile.capacity_ton} T</td>
                  <td className="py-3 px-4 text-center font-mono text-slate-400">
                    {pile.cap_count} caps × {pile.group_multiplier}
                  </td>
                  <td className="py-3 px-4 text-right font-extrabold text-white">{pile.total_piles}</td>
                  <td className="py-3 px-4 text-right font-mono text-slate-300">
                    {pile.concrete_volume_per_pile_m3.toFixed(3)} m³
                  </td>
                  <td className="py-3 px-4 text-right font-mono font-semibold text-emerald-400">
                    {pile.total_concrete_volume_m3.toFixed(2)} m³
                  </td>
                  <td className="py-3 px-4 text-right font-mono font-semibold text-amber-400">
                    {pile.total_steel_tonnage_mt.toFixed(3)} MT
                  </td>
                  <td className="py-3 px-4 text-center">
                    <button
                      onClick={e => {
                        e.stopPropagation();
                        onSelectPileType(pile);
                      }}
                      className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                      title="View Bar Bending Schedule (BBS)"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
          {/* Total Footer Row */}
          <tfoot className="bg-slate-950 font-bold text-slate-200 border-t border-slate-700">
            <tr>
              <td className="py-3 px-4 text-emerald-400">TOTAL</td>
              <td className="py-3 px-4">-</td>
              <td className="py-3 px-4">-</td>
              <td className="py-3 px-4">-</td>
              <td className="py-3 px-4 text-center">83 Piles</td>
              <td className="py-3 px-4 text-right text-white font-extrabold">{totalPiles} Nos</td>
              <td className="py-3 px-4 text-right">-</td>
              <td className="py-3 px-4 text-right font-mono text-emerald-400 font-extrabold">
                {totalVolume.toFixed(2)} m³
              </td>
              <td className="py-3 px-4 text-right font-mono text-amber-400 font-extrabold">
                {totalSteel.toFixed(3)} MT
              </td>
              <td className="py-3 px-4 text-center">-</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
};
