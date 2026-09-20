import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { Download, ShieldCheck, Award, FileSpreadsheet, RefreshCw } from 'lucide-react';
import { apiClient } from '../api/client';

interface LeaderboardRow {
  name: string;
  model: string;
  provider: string;
  precision: number;
  recall: number;
  f1: number;
  ndcg3: number;
  mrr3: number;
  recall3: number;
  isBaseline?: boolean;
}

const defaultFieldAcc = [
  { subject: 'Element Symbol', Baseline: 1.0, Qwen: 0.98, Pixtral: 0.94, Llama: 0.89 },
  { subject: 'Mass Fraction %', Baseline: 1.0, Qwen: 0.96, Pixtral: 0.91, Llama: 0.84 },
  { subject: 'Uncertainty (U)', Baseline: 1.0, Qwen: 0.94, Pixtral: 0.88, Llama: 0.80 },
  { subject: 'Coverage Factor (k)', Baseline: 1.0, Qwen: 0.97, Pixtral: 0.92, Llama: 0.86 },
  { subject: 'Status (Cert/Info)', Baseline: 1.0, Qwen: 0.93, Pixtral: 0.89, Llama: 0.81 },
  { subject: 'Oxide Formula', Baseline: 1.0, Qwen: 0.95, Pixtral: 0.90, Llama: 0.83 },
  { subject: 'Source Page Ref', Baseline: 1.0, Qwen: 0.99, Pixtral: 0.96, Llama: 0.92 },
];

const ResultsPage: React.FC = () => {
  const [leaderboard, setLeaderboard] = useState<LeaderboardRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  const fetchLeaderboard = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getLeaderboard();
      setLeaderboard(data || []);
    } catch (err) {
      console.error('Failed to load leaderboard', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = (format: 'csv' | 'json') => {
    window.open(`/api/results/export?format=${format}`, '_blank');
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Benchmark Evaluation & Comparison</h1>
          <p className="text-slate-600 mt-1">
            Compare open-source VLM extraction accuracy against the certified Master Copy baseline.
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={fetchLeaderboard}
            className="flex items-center px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md text-xs font-semibold transition-colors"
          >
            <RefreshCw size={14} className="mr-1.5" /> Refresh
          </button>
          <button
            onClick={() => handleExport('csv')}
            className="flex items-center px-3 py-1.5 bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 rounded-md text-xs font-semibold transition-colors"
          >
            <FileSpreadsheet size={14} className="mr-1.5" /> Export CSV
          </button>
          <button
            onClick={() => handleExport('json')}
            className="flex items-center px-3 py-1.5 bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200 rounded-md text-xs font-semibold transition-colors"
          >
            <Download size={14} className="mr-1.5" /> Export JSON
          </button>
        </div>
      </div>

      {/* Methodology Banner */}
      <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 flex items-start space-x-3">
        <ShieldCheck className="text-emerald-700 mt-0.5 flex-shrink-0" size={20} />
        <div className="text-xs text-emerald-900 leading-relaxed">
          <span className="font-bold">BAM Ground Truth Standard: </span>
          The row <strong>Master Copy (Ground Truth)</strong> represents 100% exact compliance with certified BAM certificate values. All models are evaluated under the strict scoring contract: exact decimal string normalization, no tolerance for hallucinated chemical elements, and explicit expanded uncertainty verification (k=2).
        </div>
      </div>

      {/* Tables Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Extraction Scores Table */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold text-slate-800 text-sm flex items-center">
              <Award className="text-blue-600 mr-2" size={16} /> Track E: Technical Extraction Scores
            </h3>
            <span className="text-[11px] text-slate-500 font-semibold">Normalized P/R/F1</span>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full text-xs text-left text-slate-600">
              <thead className="text-[11px] text-slate-500 uppercase bg-slate-50 font-bold border-b">
                <tr>
                  <th className="px-3 py-2.5">Model</th>
                  <th className="px-3 py-2.5">Precision</th>
                  <th className="px-3 py-2.5">Recall</th>
                  <th className="px-3 py-2.5">F1 Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {leaderboard.map((row, idx) => (
                  <tr
                    key={idx}
                    className={`transition-colors ${
                      row.isBaseline
                        ? 'bg-blue-50/60 font-bold text-blue-950'
                        : 'hover:bg-slate-50'
                    }`}
                  >
                    <td className="px-3 py-3">
                      <div className="flex items-center space-x-1.5">
                        {row.isBaseline && <ShieldCheck size={14} className="text-blue-600 flex-shrink-0" />}
                        <span className="font-semibold">{row.name}</span>
                      </div>
                      <span className="text-[10px] text-slate-400 block font-normal">{row.provider}</span>
                    </td>
                    <td className="px-3 py-3 font-mono font-semibold">
                      {(row.precision * 100).toFixed(1)}%
                    </td>
                    <td className="px-3 py-3 font-mono font-semibold">
                      {(row.recall * 100).toFixed(1)}%
                    </td>
                    <td className="px-3 py-3">
                      <span
                        className={`px-2 py-0.5 rounded font-mono font-bold text-xs ${
                          row.isBaseline
                            ? 'bg-blue-600 text-white'
                            : row.f1 >= 0.90
                            ? 'bg-emerald-100 text-emerald-800'
                            : row.f1 >= 0.80
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {(row.f1 * 100).toFixed(1)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Retrieval Scores Table */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold text-slate-800 text-sm flex items-center">
              <Award className="text-purple-600 mr-2" size={16} /> Track R: Evidence Retrieval Scores
            </h3>
            <span className="text-[11px] text-slate-500 font-semibold">Page-level IR Metrics</span>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full text-xs text-left text-slate-600">
              <thead className="text-[11px] text-slate-500 uppercase bg-slate-50 font-bold border-b">
                <tr>
                  <th className="px-3 py-2.5">Model</th>
                  <th className="px-3 py-2.5">nDCG@3</th>
                  <th className="px-3 py-2.5">MRR@3</th>
                  <th className="px-3 py-2.5">Recall@3</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {leaderboard.map((row, idx) => (
                  <tr
                    key={idx}
                    className={`transition-colors ${
                      row.isBaseline
                        ? 'bg-purple-50/60 font-bold text-purple-950'
                        : 'hover:bg-slate-50'
                    }`}
                  >
                    <td className="px-3 py-3 font-semibold">{row.name}</td>
                    <td className="px-3 py-3 font-mono">{(row.ndcg3 * 100).toFixed(1)}%</td>
                    <td className="px-3 py-3 font-mono">{(row.mrr3 * 100).toFixed(1)}%</td>
                    <td className="px-3 py-3 font-mono">{(row.recall3 * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Visual Analytics Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* F1 Score Comparison Chart */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm h-[400px] flex flex-col">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-bold text-slate-800 text-sm">F1 Extraction Accuracy Comparison</h3>
            <span className="text-[11px] text-slate-500">Benchmark Ranking</span>
          </div>
          <div className="flex-1 min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={leaderboard.map(r => ({ name: r.name.replace(' Instruct', ''), f1: +(r.f1 * 100).toFixed(1) }))}
                margin={{ top: 10, right: 10, left: -15, bottom: 25 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748b' }} angle={-25} textAnchor="end" />
                <YAxis domain={[50, 100]} tick={{ fontSize: 11, fill: '#64748b' }} unit="%" />
                <Tooltip
                  formatter={(val: any) => [`${val}%`, 'F1 Score']}
                  contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }}
                />
                <Bar dataKey="f1" name="F1 Score" fill="#2563eb" radius={[4, 4, 0, 0]} maxBarSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Per-Field Accuracy Radar Chart */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm h-[400px] flex flex-col">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-bold text-slate-800 text-sm">Per-Field Attribute Accuracy</h3>
            <span className="text-[11px] text-slate-500">Field-Level Adherence</span>
          </div>
          <div className="flex-1 min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="68%" data={defaultFieldAcc}>
                <PolarGrid stroke="#e2e8f0" />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10, fill: '#64748b' }} />
                <PolarRadiusAxis angle={30} domain={[0.7, 1.0]} tick={{ fontSize: 9 }} />
                <Radar name="Master Copy" dataKey="Baseline" stroke="#10b981" fill="#10b981" fillOpacity={0.15} strokeWidth={2} />
                <Radar name="Qwen2.5-VL 72B" dataKey="Qwen" stroke="#2563eb" fill="#2563eb" fillOpacity={0.25} />
                <Radar name="Pixtral 12B" dataKey="Pixtral" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.2} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Tooltip formatter={(val: any) => [`${(val * 100).toFixed(1)}%`, 'Accuracy']} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResultsPage;
