import React from 'react';
import { Layers, Cuboid, Weight, Users, ShieldCheck, TrendingUp } from 'lucide-react';
import { TakeoffResult } from '../types/takeoff';

interface KPICardsProps {
  data: TakeoffResult;
}

export const KPICards: React.FC<KPICardsProps> = ({ data }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Total Pile Count */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 relative overflow-hidden group hover:border-slate-700 transition">
        <div className="absolute top-0 right-0 w-24 h-24 bg-blue-500/5 rounded-full blur-2xl group-hover:bg-blue-500/10 transition" />
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Pile Inventory</span>
          <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Layers className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-extrabold text-white tracking-tight">
            {data.total_pile_count}
          </span>
          <span className="text-sm font-medium text-slate-400">Nos</span>
        </div>
        <div className="mt-2 text-xs text-slate-400 flex items-center gap-1.5">
          <span className="text-blue-400 font-medium">{data.pile_inventory.length} Types</span>
          <span>(Ø500mm – Ø900mm)</span>
        </div>
      </div>

      {/* 2. Concrete (RMC) Takeoff */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 relative overflow-hidden group hover:border-slate-700 transition">
        <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-2xl group-hover:bg-emerald-500/10 transition" />
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Concrete (RMC) Volume</span>
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Cuboid className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-extrabold text-white tracking-tight font-mono">
            {data.concrete_takeoff.total_volume_m3.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
          <span className="text-sm font-medium text-slate-400">m³</span>
        </div>
        <div className="mt-2 text-xs text-slate-400 flex items-center gap-1.5">
          <span className="text-emerald-400 font-medium">
            +5% Overage: {data.concrete_takeoff.volume_with_5pct_wastage_m3.toFixed(1)} m³
          </span>
        </div>
      </div>

      {/* 3. Steel Reinforcement (BBS) */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 relative overflow-hidden group hover:border-slate-700 transition">
        <div className="absolute top-0 right-0 w-24 h-24 bg-amber-500/5 rounded-full blur-2xl group-hover:bg-amber-500/10 transition" />
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Steel Reinforcement (BBS)</span>
          <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Weight className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-extrabold text-white tracking-tight font-mono">
            {data.steel_takeoff.total_steel_mt.toFixed(2)}
          </span>
          <span className="text-sm font-medium text-slate-400">MT</span>
        </div>
        <div className="mt-2 text-xs text-slate-400 flex items-center gap-1.5">
          <span className="text-amber-400 font-mono">
            {Math.round(data.steel_takeoff.total_steel_kg).toLocaleString()} kg
          </span>
          <span>(IS 1786: d²/162.28)</span>
        </div>
      </div>

      {/* 4. Total Manpower Estimation */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 relative overflow-hidden group hover:border-slate-700 transition">
        <div className="absolute top-0 right-0 w-24 h-24 bg-purple-500/5 rounded-full blur-2xl group-hover:bg-purple-500/10 transition" />
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Manpower Estimate</span>
          <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <Users className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-extrabold text-white tracking-tight font-mono">
            {data.manpower_estimation.total_mandays.toFixed(1)}
          </span>
          <span className="text-sm font-medium text-slate-400">Man-Days</span>
        </div>
        <div className="mt-2 text-xs text-slate-400 flex items-center gap-1.5">
          <span className="text-purple-400 font-medium">
            {(data.manpower_estimation.total_mandays / 30).toFixed(1)} Crew-Months (at 30d/mo)
          </span>
        </div>
      </div>
    </div>
  );
};
