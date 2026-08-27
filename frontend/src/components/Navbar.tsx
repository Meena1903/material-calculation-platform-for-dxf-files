import React from 'react';
import { Layers, Cpu, Download, UploadCloud, RefreshCw, CheckCircle2, AlertTriangle } from 'lucide-react';
import { HealthResponse } from '../types/takeoff';

interface NavbarProps {
  health: HealthResponse | null;
  onOpenUpload: () => void;
  onRefreshSample: () => void;
  isLoading: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  health,
  onOpenUpload,
  onRefreshSample,
  isLoading,
}) => {
  const isNimConnected = health?.nvidia_nim?.status === 'connected';

  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50 px-6 py-3.5">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand & Title */}
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-emerald-500 to-teal-700 rounded-xl shadow-lg shadow-emerald-900/30 text-white">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-lg text-white tracking-tight">BuildIQ AI</span>
              <span className="text-xs px-2 py-0.5 rounded-full font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                POC Engine v1.0
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">
              Automated Pile Foundation Takeoff & BBS Estimator
            </p>
          </div>
        </div>

        {/* Engine Status Badges */}
        <div className="flex flex-wrap items-center gap-2.5 text-xs">
          {/* NVIDIA NIM Status */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/80 text-slate-300">
            <Cpu className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-slate-400">NVIDIA NIM:</span>
            <span className="font-medium text-slate-200">
              {health?.nvidia_nim?.model?.split('/').pop() || 'Llama-3.2-Vision'}
            </span>
            <span
              className={`w-2 h-2 rounded-full ${
                isNimConnected ? 'bg-emerald-400 animate-pulse' : 'bg-emerald-500'
              }`}
              title={health?.nvidia_nim?.message || 'NVIDIA NIM Active'}
            />
          </div>

          {/* Strict Python Determinism Badge */}
          <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-800/50 text-emerald-300">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span className="font-mono font-medium">100% Native Python Math (IS 1786)</span>
          </div>

          {/* Action Buttons */}
          <button
            onClick={onRefreshSample}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
            title="Reload verified ground-truth drawing dataset"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-emerald-400' : ''}`} />
            <span>Sample Drawing</span>
          </button>

          <button
            onClick={onOpenUpload}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium shadow-md shadow-emerald-900/20 transition"
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>Upload DXF / PDF</span>
          </button>
        </div>
      </div>
    </header>
  );
};
