import React, { useState, useEffect } from 'react';
import { Eye, EyeOff, Check, X, Loader2, Server, ShieldCheck, Key } from 'lucide-react';
import { apiClient, ApiKey } from '../api/client';

const providersInfo = [
  {
    id: 'custom_gpu',
    name: 'Department On-Premise GPU (vLLM / TGI)',
    desc: 'BAM Internal GPU cluster hosting open-source models with private API keys',
    models: 3,
    letter: 'B',
    color: 'bg-emerald-600',
    placeholderUrl: 'http://gpu-cluster.bam.de:8000/v1 or http://localhost:8000/v1',
    isSpecial: true
  },
  {
    id: 'together',
    name: 'Together AI',
    desc: 'Access Qwen2.5-VL (72B/7B), Llama 3.2 Vision (90B/11B), InternVL2.5',
    models: 4,
    letter: 'T',
    color: 'bg-blue-600',
    placeholderUrl: 'https://api.together.xyz/v1'
  },
  {
    id: 'fireworks',
    name: 'Fireworks AI',
    desc: 'Access Qwen2.5-VL, Llama 3.2 Vision, Phi-4 Multimodal, DeepSeek-VL2',
    models: 5,
    letter: 'F',
    color: 'bg-orange-600',
    placeholderUrl: 'https://api.fireworks.ai/inference/v1'
  },
  {
    id: 'mistral',
    name: 'Mistral AI',
    desc: 'Access Pixtral 12B and Pixtral Large 124B (high-resolution PDF processing)',
    models: 2,
    letter: 'M',
    color: 'bg-amber-600',
    placeholderUrl: 'https://api.mistral.ai/v1'
  },
  {
    id: 'groq',
    name: 'Groq (LPU)',
    desc: 'Ultra-fast LPU inference for Llama 3.2 Vision models',
    models: 2,
    letter: 'G',
    color: 'bg-rose-600',
    placeholderUrl: 'https://api.groq.com/openai/v1'
  },
  {
    id: 'deepseek',
    name: 'DeepSeek',
    desc: 'Access DeepSeek-VL2 open-source vision-language model',
    models: 1,
    letter: 'D',
    color: 'bg-indigo-600',
    placeholderUrl: 'https://api.deepseek.com/v1'
  },
  {
    id: 'huggingface',
    name: 'HuggingFace',
    desc: 'Access Idefics3, Florence-2 Large, GOT-OCR2.0',
    models: 3,
    letter: 'H',
    color: 'bg-yellow-600',
    placeholderUrl: 'https://router.huggingface.co/hf-inference/v1'
  },
  {
    id: 'openrouter',
    name: 'OpenRouter',
    desc: 'Multi-provider aggregator with Qwen2.5-VL, InternVL3, Pixtral',
    models: 7,
    letter: 'O',
    color: 'bg-violet-600',
    placeholderUrl: 'https://openrouter.ai/api/v1'
  },
];

const ApiKeysPage: React.FC = () => {
  const [keys, setKeys] = useState<Record<string, ApiKey>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchKeys();
  }, []);

  const fetchKeys = async () => {
    try {
      const data = await apiClient.getKeys();
      const keysMap: Record<string, ApiKey> = {};
      data.forEach(k => keysMap[k.provider] = k);
      setKeys(keysMap);
    } catch (err) {
      console.error('Failed to fetch keys', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">API Key & Endpoint Configuration</h1>
        <p className="text-slate-600 mt-1">
          Configure API keys provided by your organization's GPU department or cloud providers to enable open-source VLM benchmark testing.
        </p>
      </div>

      {/* Corporate Guidance Banner */}
      <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 flex items-start space-x-3">
        <Server className="text-emerald-700 mt-0.5 flex-shrink-0" size={20} />
        <div className="text-xs text-emerald-900 leading-relaxed">
          <span className="font-bold">Department On-Premise GPU Hosting: </span>
          If your IT/AI department hosts open-source models (vLLM, TGI, Ollama) on internal GPUs, configure the <strong>Department On-Premise GPU</strong> card below with your provided API key and internal endpoint URL (e.g. <code>http://gpu-cluster.bam.de:8000/v1</code>). All models use the OpenAI-compatible chat completions interface.
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center p-12"><Loader2 className="animate-spin text-blue-500" size={32} /></div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {providersInfo.map(provider => (
            <ProviderCard
              key={provider.id}
              provider={provider}
              keyData={keys[provider.id]}
              onUpdate={fetchKeys}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const ProviderCard = ({ provider, keyData, onUpdate }: any) => {
  const [showKey, setShowKey] = useState(false);
  const [keyValue, setKeyValue] = useState('');
  const [baseUrl, setBaseUrl] = useState(keyData?.baseUrl || '');
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{success: boolean, message: string} | null>(null);
  
  const isConfigured = keyData?.isConfigured;

  useEffect(() => {
    if (keyData?.baseUrl) {
      setBaseUrl(keyData.baseUrl);
    }
  }, [keyData]);

  const handleSave = async () => {
    if (!keyValue && !baseUrl && !isConfigured) return;
    try {
      await apiClient.saveKey(provider.id, keyValue, baseUrl);
      setKeyValue('');
      setTestResult(null);
      onUpdate();
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async () => {
    try {
      await apiClient.deleteKey(provider.id);
      setKeyValue('');
      setBaseUrl('');
      setTestResult(null);
      onUpdate();
    } catch (e) {
      console.error(e);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res: any = await apiClient.testKey(provider.id, keyValue || undefined, baseUrl || undefined);
      if (res && res.success) {
        setTestResult({ success: true, message: res.message || 'Connected successfully' });
      } else {
        setTestResult({ success: false, message: res?.error || 'Connection check failed' });
      }
    } catch (e: any) {
      setTestResult({ success: false, message: e.response?.data?.error || e.message || 'Connection failed' });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className={`bg-white rounded-xl border p-5 flex flex-col shadow-sm transition-all ${
      provider.isSpecial ? 'border-emerald-300 ring-1 ring-emerald-400/30' : 'border-slate-200'
    }`}>
      <div className="flex items-start mb-4">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-lg mr-3 flex-shrink-0 ${provider.color}`}>
          {provider.letter}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex justify-between items-center">
            <h3 className="font-bold text-slate-800 text-sm truncate">{provider.name}</h3>
            <div className="flex items-center ml-2">
              <span className={`w-2.5 h-2.5 rounded-full mr-1.5 ${
                testResult
                  ? (testResult.success ? 'bg-emerald-500' : 'bg-rose-500')
                  : (isConfigured ? 'bg-emerald-500' : 'bg-slate-300')
              }`}></span>
              <span className="text-xs font-semibold text-slate-500">
                {isConfigured ? 'Ready' : 'Unconfigured'}
              </span>
            </div>
          </div>
          <p className="text-xs text-slate-500 mt-1 line-clamp-2">{provider.desc}</p>
          <span className="inline-block mt-2 text-[10px] font-bold bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
            {provider.models} VLM models available
          </span>
        </div>
      </div>

      <div className="space-y-3 mt-auto pt-2">
        <div className="relative">
          <input
            type={showKey ? "text" : "password"}
            value={keyValue}
            onChange={(e) => setKeyValue(e.target.value)}
            placeholder={isConfigured ? "•••••••••••••••• (API Key Active)" : "Enter API Key"}
            className="w-full pr-10 pl-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-xs font-mono"
          />
          <button 
            type="button"
            className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600"
            onClick={() => setShowKey(!showKey)}
          >
            {showKey ? <EyeOff size={15} /> : <Eye size={15} />}
          </button>
        </div>

        <input
          type="text"
          value={baseUrl}
          onChange={(e) => setBaseUrl(e.target.value)}
          placeholder={provider.placeholderUrl || "Custom Base URL (optional)"}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-xs font-mono"
        />

        {testResult && (
          <div className={`text-xs flex items-center p-2 rounded ${testResult.success ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'}`}>
            {testResult.success ? <Check size={14} className="mr-1 flex-shrink-0" /> : <X size={14} className="mr-1 flex-shrink-0" />}
            <span className="truncate">{testResult.message}</span>
          </div>
        )}

        <div className="flex space-x-2 pt-1">
          <button 
            onClick={handleTest} 
            disabled={testing || (!keyValue && !isConfigured)}
            className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-700 py-2 rounded-lg text-xs font-semibold transition-colors flex justify-center items-center disabled:opacity-50"
          >
            {testing ? <Loader2 size={14} className="animate-spin" /> : 'Test Connection'}
          </button>
          <button 
            onClick={handleSave}
            disabled={!keyValue && !baseUrl}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg text-xs font-semibold transition-colors disabled:opacity-50"
          >
            Save
          </button>
          {isConfigured && (
            <button 
              onClick={handleDelete}
              className="bg-rose-50 hover:bg-rose-100 text-rose-600 px-3 py-2 rounded-lg text-xs font-semibold transition-colors border border-rose-200"
              title="Delete Key"
            >
              Delete
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ApiKeysPage;
