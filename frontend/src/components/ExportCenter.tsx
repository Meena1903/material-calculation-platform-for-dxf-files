import React, { useState } from 'react';
import { Download, FileJson, FileSpreadsheet, Archive, CheckCircle, ExternalLink, Code } from 'lucide-react';
import { TakeoffResult } from '../types/takeoff';
import { apiClient } from '../services/api';

interface ExportCenterProps {
  data: TakeoffResult;
}

export const ExportCenter: React.FC<ExportCenterProps> = ({ data }) => {
  const [activeTab, setActiveTab] = useState<'boq' | 'json'>('boq');

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900/60">
        <div>
          <h3 className="font-semibold text-slate-200 text-sm">Deliverables & Export Center</h3>
          <p className="text-xs text-slate-400">
            Generate and download standard artifacts for estimating & submission
          </p>
        </div>

        {/* Download Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <a
            href={apiClient.getExportJsonUrl()}
            download="output_takeoff.json"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-emerald-400 border border-slate-700 rounded-lg text-xs font-semibold transition"
          >
            <FileJson className="w-3.5 h-3.5" />
            <span>output_takeoff.json</span>
          </a>

          <a
            href={apiClient.getExportCsvUrl()}
            download="output_boq.csv"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-amber-400 border border-slate-700 rounded-lg text-xs font-semibold transition"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>output_boq.csv</span>
          </a>

          <a
            href={apiClient.getExportZipUrl()}
            download="BuildIQ_Candidate_Assessment.zip"
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold shadow-lg shadow-emerald-900/20 transition"
          >
            <Archive className="w-3.5 h-3.5" />
            <span>Download Submission ZIP</span>
          </a>
        </div>
      </div>

      {/* Preview Tabs */}
      <div className="p-4">
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-3 text-xs">
          <button
            onClick={() => setActiveTab('boq')}
            className={`px-3 py-1.5 rounded-lg font-medium transition ${
              activeTab === 'boq'
                ? 'bg-slate-800 text-emerald-400 border border-slate-700'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Bill of Quantities (BOQ Preview)
          </button>
          <button
            onClick={() => setActiveTab('json')}
            className={`px-3 py-1.5 rounded-lg font-medium transition ${
              activeTab === 'json'
                ? 'bg-slate-800 text-emerald-400 border border-slate-700'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            JSON Schema Payload Preview
          </button>
        </div>

        {/* Tab 1: BOQ Table */}
        {activeTab === 'boq' && (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider text-[10px] font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3 w-16">Item No</th>
                  <th className="py-2.5 px-3">Description of Work</th>
                  <th className="py-2.5 px-3 text-right w-24">Quantity</th>
                  <th className="py-2.5 px-3 text-center w-20">Unit</th>
                  <th className="py-2.5 px-3 text-right w-28">Est. Rate (INR)</th>
                  <th className="py-2.5 px-3 text-right w-32">Total Amount (INR)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {data.boq_items.map((item, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40 transition">
                    <td className="py-2.5 px-3 font-mono font-bold text-slate-400">{item.item_no}</td>
                    <td className="py-2.5 px-3 text-slate-200">{item.description}</td>
                    <td className="py-2.5 px-3 text-right font-mono font-semibold text-emerald-400">
                      {item.quantity.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="py-2.5 px-3 text-center text-slate-400">{item.unit}</td>
                    <td className="py-2.5 px-3 text-right font-mono text-slate-400">
                      {item.estimated_rate_inr.toLocaleString()}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono font-bold text-white">
                      ₹{Math.round(item.estimated_amount_inr).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Tab 2: JSON Preview */}
        {activeTab === 'json' && (
          <div className="bg-slate-950 border border-slate-800 rounded-lg p-3">
            <pre className="text-[11px] font-mono text-slate-300 max-h-80 overflow-y-auto">
              {JSON.stringify(
                {
                  project_title: data.project_title,
                  total_pile_count: data.total_pile_count,
                  concrete_takeoff: data.concrete_takeoff,
                  steel_takeoff: data.steel_takeoff,
                  manpower_estimation: data.manpower_estimation,
                  pile_inventory: data.pile_inventory.map(p => ({
                    tag: p.tag,
                    diameter_mm: p.diameter_mm,
                    depth_m: p.depth_m,
                    capacity_ton: p.capacity_ton,
                    total_piles: p.total_piles,
                    concrete_volume_m3: p.total_concrete_volume_m3,
                    steel_tonnage_mt: p.total_steel_tonnage_mt,
                  })),
                },
                null,
                2
              )}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};
