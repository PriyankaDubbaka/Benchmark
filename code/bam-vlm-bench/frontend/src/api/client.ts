import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

// Types
export interface ApiKey {
  provider: string;
  isConfigured: boolean;
  baseUrl?: string;
}

export interface Model {
  id: string;
  name: string;
  provider: string;
  parameters: string;
  capabilities: string[];
  isAvailable: boolean;
}

export interface Document {
  id: string;
  filename: string;
  pageCount: number;
  hasAnnotation: boolean;
}

// API Functions
export const apiClient = {
  // API Keys
  getKeys: () => api.get<ApiKey[]>('/keys').then(res => res.data),
  saveKey: (provider: string, key: string, baseUrl?: string) => api.post('/keys', { provider, key, baseUrl }).then(res => res.data),
  deleteKey: (provider: string) => api.delete(`/keys/${provider}`).then(res => res.data),
  testKey: (provider: string, key?: string, baseUrl?: string) => api.post('/keys/test', { provider, key, baseUrl }).then(res => res.data),

  // Models
  getModels: () => api.get<Model[]>('/models').then(res => res.data),
  getAvailableModels: () => api.get<Model[]>('/models?available=true').then(res => res.data),

  // Documents
  getDocuments: () => api.get<Document[]>('/documents').then(res => res.data),
  getDocumentAnnotation: (id: string) => api.get(`/documents/${id}/annotation`).then(res => res.data),
  getDocumentPages: (id: string) => api.get(`/documents/${id}/pages`).then(res => res.data),

  // Benchmarks
  runBenchmark: (docId: string, modelIds: string[], tasks: string[]) => api.post('/benchmark/run', { docId, modelIds, tasks }).then(res => res.data),
  listRuns: () => api.get('/benchmark/runs').then(res => res.data),
  getRunStatus: (runId: string) => api.get(`/benchmark/runs/${runId}/status`).then(res => res.data),
  getRunResult: (runId: string) => api.get(`/benchmark/runs/${runId}`).then(res => res.data),

  // Results
  compareResults: (runIds: string[]) => api.get('/results/compare', { params: { ids: runIds.join(',') } }).then(res => res.data),
  getLeaderboard: () => api.get('/results/leaderboard').then(res => res.data),
  exportResults: (format: 'json' | 'csv') => api.get(`/results/export?format=${format}`, { responseType: 'blob' }).then(res => res.data),
};
