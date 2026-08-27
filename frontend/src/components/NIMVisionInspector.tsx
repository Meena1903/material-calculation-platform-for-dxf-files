import React, { useState } from 'react';
import { Cpu, CheckCircle2, ShieldAlert, Sparkles, FileCode, Image as ImageIcon, ChevronDown, ChevronUp } from 'lucide-react';
import { NIMVisualExtractionResponse } from '../types/takeoff';

interface NIMVisionInspectorProps {
  nimInfo?: NIMVisualExtractionResponse;
}

export const NIMVisionInspector: React.FC<NIMVisionInspectorProps> = ({ nimInfo }) => {
  const [showJson, setShowJson] = useState(false);

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 bg-slate-900/60">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-lg">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-slate-100 text-sm">NVIDIA NIM Multimodal Vision Studio</h3>
              <span className="text-[10px] px-2 py-0.5 rounded font-mono font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                Pydantic Schema Validated
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Visual Table Localization & Schema Extraction ({nimInfo?.model_used || 'meta/llama-3.2-90b-vision-instruct'})
            </p>
          </div>
        </div>

        {/* Toggle JSON */}
        <button
          onClick={() => setShowJson(!showJson)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition"
        >
          <FileCode className="w-3.5 h-3.5" />
          <span>{showJson ? 'Hide Schema JSON' : 'View Pydantic JSON'}</span>
          {showJson ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      <div className="p-4 space-y-4">
        {/* Critical Engineering Constraint Banner */}
        <div className="p-3 bg-emerald-950/40 border border-emerald-800/50 rounded-lg flex items-start gap-3 text-xs text-emerald-200">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <strong className="text-emerald-300">Engineering Constraint Guarantee:</strong> Multimodal LLMs are restricted strictly to visual table detection and schema structuring. Mathematical quantities, concrete volumes (V = π × (d/2)² × L), unit weights (w = d² / 162.28 kg/m), and manpower estimations are calculated entirely in native deterministic Python.
          </div>
        </div>

        {/* Extracted Schedule Cards from Vision */}
        {nimInfo && nimInfo.extracted_schedule && nimInfo.extracted_schedule.length > 0 ? (
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Vision-Extracted Schema Items ({nimInfo.extracted_schedule.length} Schedule Rows)
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
              {nimInfo.extracted_schedule.map((item, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-slate-950/80 border border-slate-800 rounded-lg text-xs space-y-1.5"
                >
                  <div className="flex items-center justify-between font-bold text-slate-200">
                    <span className="text-emerald-400">{item.pile_tag}</span>
                    <span className="text-slate-400 font-mono">Count: {item.total_count} Nos</span>
                  </div>
                  <div className="text-slate-400 grid grid-cols-2 gap-1 text-[11px]">
                    <div>Dia: <span className="text-slate-200 font-mono">Ø{item.pile_diameter_mm}mm</span></div>
                    <div>Depth: <span className="text-slate-200 font-mono">{item.depth_m}m</span></div>
                  </div>
                  {item.main_reinforcement && (
                    <div className="text-[11px] text-slate-400 border-t border-slate-800 pt-1">
                      <span className="text-slate-500">Rebar:</span> {item.main_reinforcement}
                    </div>
                  )}
                  <div className="flex items-center justify-between pt-1 text-[10px] text-slate-500">
                    <span>Confidence: {(item.confidence_score * 100).toFixed(0)}%</span>
                    <span className="text-emerald-400 font-semibold">Valid</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="p-6 text-center text-xs text-slate-500">
            NVIDIA NIM vision extraction results will display here after drawing ingestion.
          </div>
        )}

        {/* JSON Schema Drawer */}
        {showJson && nimInfo && (
          <div className="mt-4 p-3 bg-slate-950 border border-slate-800 rounded-lg">
            <div className="text-xs font-mono text-slate-400 mb-2 flex items-center justify-between">
              <span>Structured Pydantic Model Output:</span>
              <span className="text-emerald-400">is_valid_schema: true</span>
            </div>
            <pre className="text-[11px] font-mono text-slate-300 max-h-72 overflow-y-auto p-2 bg-slate-900 rounded">
              {JSON.stringify(nimInfo, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};
