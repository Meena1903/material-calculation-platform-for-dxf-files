import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { KPICards } from './components/KPICards';
import { CADViewer } from './components/CADViewer';
import { PileInventoryTable } from './components/PileInventoryTable';
import { BBSViewer } from './components/BBSViewer';
import { TakeoffCharts } from './components/TakeoffCharts';
import { NIMVisionInspector } from './components/NIMVisionInspector';
import { ExportCenter } from './components/ExportCenter';
import { FileUploadModal } from './components/FileUploadModal';
import { apiClient } from './services/api';
import { TakeoffResult, HealthResponse, PileTypeInventory } from './types/takeoff';
import { Loader2, AlertCircle, Sparkles, Building2, CheckCircle2 } from 'lucide-react';

export function App() {
  const [data, setData] = useState<TakeoffResult | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPile, setSelectedPile] = useState<PileTypeInventory | null>(null);
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false);

  // Initial load
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [healthRes, sampleData] = await Promise.all([
        apiClient.getHealth().catch(() => null),
        apiClient.getSampleTakeoff(),
      ]);
      setHealth(healthRes);
      setData(sampleData);
      if (sampleData.pile_inventory.length > 0) {
        setSelectedPile(sampleData.pile_inventory[0]);
      }
    } catch (err: any) {
      console.error('Failed to load sample takeoff data:', err);
      setError(
        'Could not connect to FastAPI backend on http://127.0.0.1:8000. Please make sure the backend server is running.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-emerald-500 selection:text-white">
      {/* Top Navbar */}
      <Navbar
        health={health}
        onOpenUpload={() => setIsUploadOpen(true)}
        onRefreshSample={loadInitialData}
        isLoading={isLoading}
      />

      {/* Main Content Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Error Alert */}
        {error && (
          <div className="p-4 bg-red-950/60 border border-red-800 rounded-xl flex items-center justify-between gap-3 text-sm text-red-300">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
              <span>{error}</span>
            </div>
            <button
              onClick={loadInitialData}
              className="px-3 py-1 bg-red-900/60 hover:bg-red-900 text-xs text-white rounded-lg font-semibold transition"
            >
              Retry Connection
            </button>
          </div>
        )}

        {/* Loading Spinner */}
        {isLoading && !data && (
          <div className="min-h-[400px] flex flex-col items-center justify-center gap-3">
            <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
            <p className="text-sm text-slate-400 font-medium">
              Initializing CAD Vector Engine & NVIDIA NIM Vision Pipeline...
            </p>
          </div>
        )}

        {data && (
          <>
            {/* Project Banner */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-2 border-b border-slate-800/80">
              <div>
                <h1 className="text-xl font-extrabold text-white tracking-tight flex items-center gap-2">
                  <Building2 className="w-5 h-5 text-emerald-400" />
                  <span>{data.project_title}</span>
                </h1>
                <p className="text-xs text-slate-400 mt-0.5">
                  Source: {data.source_files.join(', ') || 'CAD DXF & PDF Blueprint Engine'}
                </p>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 font-mono text-emerald-400 font-semibold">
                  {data.calculation_engine}
                </span>
              </div>
            </div>

            {/* 1. KPI Metric Summary Cards */}
            <KPICards data={data} />

            {/* 2. Interactive CAD Geometry Viewer */}
            <CADViewer
              entities={data.cad_entities}
              pileInventory={data.pile_inventory}
              boundingBox={data.bounding_box}
            />

            {/* 3. Pile Inventory & Schedule Table */}
            <PileInventoryTable
              inventory={data.pile_inventory}
              onSelectPileType={pile => setSelectedPile(pile)}
              selectedTag={selectedPile?.tag}
            />

            {/* 4. Selected Pile Bar Bending Schedule (BBS) Drawer */}
            {selectedPile && (
              <BBSViewer
                selectedPile={selectedPile}
                onClose={() => setSelectedPile(null)}
              />
            )}

            {/* 5. Takeoff Visual Analytics Charts */}
            <TakeoffCharts data={data} />

            {/* 6. NVIDIA NIM Multimodal Vision Studio */}
            <NIMVisionInspector nimInfo={data.nim_extraction_info} />

            {/* 7. Deliverables & Export Center */}
            <ExportCenter data={data} />
          </>
        )}
      </main>

      {/* File Upload Modal */}
      <FileUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onSuccess={newResult => {
          setData(newResult);
          if (newResult.pile_inventory.length > 0) {
            setSelectedPile(newResult.pile_inventory[0]);
          }
        }}
      />

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-4 px-6 mt-12 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>BuildIQ AI — Automated Pile Foundation Takeoff Engine</span>
          <span>IS 1786 / SP 34 Civil Engineering Standard Compliance</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
