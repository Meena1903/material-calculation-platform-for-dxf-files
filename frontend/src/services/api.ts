import axios from 'axios';
import { TakeoffResult, HealthResponse } from '../types/takeoff';

const API_BASE = '/api';

export const apiClient = {
  async getHealth(): Promise<HealthResponse> {
    const res = await axios.get<HealthResponse>(`${API_BASE}/health`);
    return res.data;
  },

  async getSampleTakeoff(): Promise<TakeoffResult> {
    const res = await axios.get<TakeoffResult>(`${API_BASE}/takeoff/sample`);
    return res.data;
  },

  async uploadAndProcess(dxfFile?: File, pdfFile?: File, projectTitle?: string): Promise<TakeoffResult> {
    const formData = new FormData();
    if (dxfFile) formData.append('dxf_file', dxfFile);
    if (pdfFile) formData.append('pdf_file', pdfFile);
    if (projectTitle) formData.append('project_title', projectTitle);

    const res = await axios.post<TakeoffResult>(`${API_BASE}/takeoff/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  async recalculate(pileSpecs: any[], projectTitle?: string): Promise<TakeoffResult> {
    const res = await axios.post<TakeoffResult>(`${API_BASE}/takeoff/calculate`, {
      pile_specs: pileSpecs,
      project_title: projectTitle || 'Custom Calculation',
    });
    return res.data;
  },

  getExportJsonUrl(): string {
    return `${API_BASE}/export/json`;
  },

  getExportCsvUrl(): string {
    return `${API_BASE}/export/csv`;
  },

  getExportZipUrl(): string {
    return `${API_BASE}/export/zip`;
  },
};
