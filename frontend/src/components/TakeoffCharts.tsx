import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import { TakeoffResult } from '../types/takeoff';

interface TakeoffChartsProps {
  data: TakeoffResult;
}

export const TakeoffCharts: React.FC<TakeoffChartsProps> = ({ data }) => {
  // Concrete Volume Data per Tag
  const concreteData = data.pile_inventory.map(p => ({
    name: p.tag,
    volume: Number(p.total_concrete_volume_m3.toFixed(1)),
    piles: p.total_piles,
    dia: `Ø${p.diameter_mm}mm`,
  }));

  // Steel Component Breakdown Data
  const steelComponentData = Object.entries(data.steel_takeoff.steel_by_component_mt).map(([key, val]) => ({
    name: key,
    value: Number(val.toFixed(2)),
  }));

  // Manpower Breakdown Data
  const manpowerData = [
    {
      name: 'Piling & Concreting (0.25 d/m³)',
      value: Number(data.manpower_estimation.piling_and_concreting_mandays.toFixed(1)),
      color: '#3b82f6',
    },
    {
      name: 'Rebar Fabrication (2.50 d/MT)',
      value: Number(data.manpower_estimation.rebar_fabrication_mandays.toFixed(1)),
      color: '#f59e0b',
    },
    {
      name: 'Pile Head Chipping (0.50 d/pile)',
      value: Number(data.manpower_estimation.pile_head_chipping_mandays.toFixed(1)),
      color: '#8b5cf6',
    },
  ];

  const PIE_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      {/* 1. Concrete Volume by Pile Tag */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-xl flex flex-col justify-between">
        <div>
          <h3 className="font-semibold text-slate-200 text-sm">Concrete (RMC) Volume by Pile Tag</h3>
          <p className="text-xs text-slate-400">Theoretical volumetric distribution (m³)</p>
        </div>
        <div className="h-64 mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={concreteData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis
                dataKey="name"
                stroke="#64748b"
                tick={{ fill: '#94a3b8', fontSize: 10 }}
                interval={0}
                angle={-30}
                textAnchor="end"
              />
              <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 10 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                formatter={(val: any) => [`${val} m³`, 'Volume']}
              />
              <Bar dataKey="volume" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 2. Steel Breakdown by Rebar Role */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-xl flex flex-col justify-between">
        <div>
          <h3 className="font-semibold text-slate-200 text-sm">Steel Tonnage by Rebar Component</h3>
          <p className="text-xs text-slate-400">Main Bars vs Helical Ties vs Spacers (MT)</p>
        </div>
        <div className="h-64 mt-4 flex items-center justify-center">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={steelComponentData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                paddingAngle={4}
                dataKey="value"
              >
                {steelComponentData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                formatter={(val: any) => [`${val} MT`, 'Steel Weight']}
              />
              <Legend
                verticalAlign="bottom"
                height={36}
                formatter={(val: string) => <span className="text-[11px] text-slate-300">{val}</span>}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 3. Manpower Activity Distribution */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-xl flex flex-col justify-between">
        <div>
          <h3 className="font-semibold text-slate-200 text-sm">Manpower Labor Allocation</h3>
          <p className="text-xs text-slate-400">Productivity ratios breakdown (Man-Days)</p>
        </div>
        <div className="h-64 mt-4 flex items-center justify-center">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={manpowerData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                paddingAngle={4}
                dataKey="value"
              >
                {manpowerData.map((entry, index) => (
                  <Cell key={`cell-mp-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                formatter={(val: any) => [`${val} Man-Days`, 'Labor']}
              />
              <Legend
                verticalAlign="bottom"
                height={36}
                formatter={(val: string) => <span className="text-[11px] text-slate-300">{val}</span>}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
