import React, { useState } from 'react';
import { UploadCloud, FileText, X, AlertCircle, Loader2 } from 'lucide-react';
import { apiClient } from '../services/api';
import { TakeoffResult } from '../types/takeoff';

interface FileUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (result: TakeoffResult) => void;
}

export const FileUploadModal: React.FC<FileUploadModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [dxfFile, setDxfFile] = useState<File | null>(null);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [projectTitle, setProjectTitle] = useState<string>('Foundation Layout Drawing Takeoff');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!dxfFile && !pdfFile) {
      setError('Please select at least one CAD DXF or PDF drawing file.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await apiClient.uploadAndProcess(
        dxfFile || undefined,
        pdfFile || undefined,
        projectTitle
      );
      onSuccess(result);
      onClose();
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.message ||
        err.response?.data?.detail ||
        (typeof err.response?.data === 'string' ? err.response.data : null) ||
        err.message ||
        'Failed to process drawing files.';
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-lg">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-100 text-base">Upload Foundation Drawings</h3>
              <p className="text-xs text-slate-400">Process CAD vector (DXF) and high-res blueprint (PDF) up to 500MB</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {error && (
            <div className="p-3 bg-red-950/40 border border-red-800/50 rounded-lg flex items-center gap-2 text-xs text-red-300">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Project Title */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Project / Drawing Title
            </label>
            <input
              type="text"
              value={projectTitle}
              onChange={e => setProjectTitle(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-emerald-500 transition"
              placeholder="e.g. Tower 1 - Pile Layout"
            />
          </div>

          {/* DXF File Upload */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              CAD Vector File (.DXF)
            </label>
            <div className="border-2 border-dashed border-slate-700 hover:border-emerald-500/50 rounded-xl p-4 text-center cursor-pointer bg-slate-950/50 transition relative">
              <input
                type="file"
                accept=".dxf"
                onChange={e => setDxfFile(e.target.files?.[0] || null)}
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
              <FileText className="w-6 h-6 mx-auto text-slate-400 mb-1" />
              {dxfFile ? (
                <div className="text-xs text-emerald-400 font-medium">
                  {dxfFile.name} ({formatFileSize(dxfFile.size)})
                </div>
              ) : (
                <div className="text-xs text-slate-400">
                  <span className="text-emerald-400 font-medium">Click to select DXF</span> or drag & drop (up to 500MB)
                </div>
              )}
            </div>
          </div>

          {/* PDF File Upload */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              High-Resolution Blueprint (.PDF)
            </label>
            <div className="border-2 border-dashed border-slate-700 hover:border-emerald-500/50 rounded-xl p-4 text-center cursor-pointer bg-slate-950/50 transition relative">
              <input
                type="file"
                accept=".pdf"
                onChange={e => setPdfFile(e.target.files?.[0] || null)}
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
              <FileText className="w-6 h-6 mx-auto text-slate-400 mb-1" />
              {pdfFile ? (
                <div className="text-xs text-emerald-400 font-medium">
                  {pdfFile.name} ({formatFileSize(pdfFile.size)})
                </div>
              ) : (
                <div className="text-xs text-slate-400">
                  <span className="text-emerald-400 font-medium">Click to select PDF</span> for vision parsing (up to 500MB)
                </div>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="pt-3 flex items-center justify-end gap-2 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white shadow-lg shadow-emerald-900/30 flex items-center gap-2 transition disabled:opacity-50"
            >
              {isLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              <span>{isLoading ? 'Processing Pipeline...' : 'Run Takeoff Engine'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
