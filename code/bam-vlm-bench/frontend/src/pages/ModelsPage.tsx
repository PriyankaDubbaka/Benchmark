import React, { useState, useEffect } from 'react';
import { Brain, CheckCircle, XCircle } from 'lucide-react';
import { apiClient, Model } from '../api/client';

const ModelsPage: React.FC = () => {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterProvider, setFilterProvider] = useState('all');
  const [showAvailableOnly, setShowAvailableOnly] = useState(false);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const data = await apiClient.getModels();
        // Mock fallback if API not ready
        if (!data || data.length === 0) {
          setModels([
            { id: 'qwen-2.5-vl-72b', name: 'Qwen2.5-VL', provider: 'Together AI', parameters: '72B', capabilities: ['Vision', 'Text'], isAvailable: true },
            { id: 'llama-3.2-90b-vision', name: 'Llama 3.2 Vision', provider: 'Fireworks AI', parameters: '90B', capabilities: ['Vision'], isAvailable: false },
            { id: 'pixtral-12b', name: 'Pixtral 12B', provider: 'Mistral AI', parameters: '12B', capabilities: ['Vision', 'Fast'], isAvailable: true },
          ]);
        } else {
          setModels(data);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchModels();
  }, []);

  const providers = ['all', ...Array.from(new Set(models.map(m => m.provider)))];

  const filteredModels = models.filter(m => {
    if (filterProvider !== 'all' && m.provider !== filterProvider) return false;
    if (showAvailableOnly && !m.isAvailable) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Models</h1>
        <p className="text-slate-600 mt-2">Browse and manage vision-language models for benchmarking.</p>
      </div>

      <div className="flex flex-wrap gap-4 items-center bg-white p-4 rounded-lg shadow-sm border border-slate-200">
        <select 
          value={filterProvider} 
          onChange={e => setFilterProvider(e.target.value)}
          className="border border-slate-300 rounded-md py-2 px-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
        >
          {providers.map(p => <option key={p} value={p}>{p === 'all' ? 'All Providers' : p}</option>)}
        </select>
        
        <label className="flex items-center space-x-2 text-sm text-slate-700 cursor-pointer">
          <input 
            type="checkbox" 
            checked={showAvailableOnly} 
            onChange={e => setShowAvailableOnly(e.target.checked)}
            className="rounded text-blue-600 focus:ring-blue-500"
          />
          <span>Show available only</span>
        </label>
      </div>

      {loading ? (
        <p>Loading models...</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredModels.map(model => (
            <div key={model.id} className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 hover:border-blue-300 transition-colors cursor-pointer group">
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-slate-100 rounded text-slate-600 group-hover:bg-blue-50 group-hover:text-blue-600 transition-colors">
                    <Brain size={20} />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-800 leading-tight">{model.name}</h3>
                    <span className="text-xs font-medium text-slate-500">{model.id}</span>
                  </div>
                </div>
              </div>
              
              <div className="mt-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Provider</span>
                  <span className="font-medium text-slate-700">{model.provider}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Parameters</span>
                  <span className="font-medium text-slate-700">{model.parameters}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Status</span>
                  <span className={`flex items-center text-xs font-medium px-2 py-0.5 rounded-full ${model.isAvailable ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
                    {model.isAvailable ? <CheckCircle size={12} className="mr-1" /> : <XCircle size={12} className="mr-1" />}
                    {model.isAvailable ? 'Ready' : 'Needs Key'}
                  </span>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-slate-100 flex flex-wrap gap-2">
                {model.capabilities.map(cap => (
                  <span key={cap} className="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded">
                    {cap}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ModelsPage;
