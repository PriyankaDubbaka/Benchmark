import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Key, Play, BarChart3, FileText, Brain, Activity } from 'lucide-react';
import { apiClient, Document, Model } from '../api/client';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState({
    documents: 0,
    models: 0,
    runs: 0,
    activeKeys: 0,
  });
  
  const [recentRuns, setRecentRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [docs, models, runs, keys] = await Promise.all([
          apiClient.getDocuments().catch(() => []),
          apiClient.getAvailableModels().catch(() => []),
          apiClient.listRuns().catch(() => []),
          apiClient.getKeys().catch(() => [])
        ]);
        
        setStats({
          documents: docs.length,
          models: models.length,
          runs: runs.length,
          activeKeys: keys.filter(k => k.isConfigured).length,
        });
        
        setRecentRuns(runs.slice(0, 5));
      } catch (error) {
        console.error("Error fetching stats", error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchStats();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-slate-800">Welcome to BAM VLM Benchmark</h2>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Documents Available" value={loading ? '...' : stats.documents} icon={FileText} color="bg-blue-100 text-blue-600" />
        <StatCard title="Models Configured" value={loading ? '...' : stats.models} icon={Brain} color="bg-purple-100 text-purple-600" />
        <StatCard title="Benchmark Runs" value={loading ? '...' : stats.runs} icon={Activity} color="bg-green-100 text-green-600" />
        <StatCard title="API Keys Active" value={loading ? '...' : stats.activeKeys} icon={Key} color="bg-amber-100 text-amber-600" />
      </div>

      {/* Quick Actions */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
        <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
        <div className="flex flex-wrap gap-4">
          <Link to="/api-keys" className="flex items-center px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md font-medium transition-colors">
            <Key size={18} className="mr-2" /> Configure API Keys
          </Link>
          <Link to="/benchmark" className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium transition-colors">
            <Play size={18} className="mr-2" /> Run Benchmark
          </Link>
          <Link to="/results" className="flex items-center px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md font-medium transition-colors">
            <BarChart3 size={18} className="mr-2" /> View Results
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
        <h3 className="text-lg font-semibold mb-4">Recent Benchmark Runs</h3>
        {loading ? (
          <p className="text-slate-500">Loading...</p>
        ) : recentRuns.length === 0 ? (
          <p className="text-slate-500">No benchmark runs yet.</p>
        ) : (
          <ul className="divide-y divide-slate-100">
            {recentRuns.map((run, i) => (
              <li key={i} className="py-3 flex justify-between items-center">
                <div>
                  <p className="font-medium text-slate-800">Run #{run.id}</p>
                  <p className="text-sm text-slate-500">{new Date(run.timestamp).toLocaleString()}</p>
                </div>
                <span className={`px-2 py-1 text-xs font-semibold rounded-full ${run.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'}`}>
                  {run.status}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

const StatCard = ({ title, value, icon: Icon, color }: any) => (
  <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200 flex items-center">
    <div className={`p-3 rounded-full ${color} mr-4`}>
      <Icon size={24} />
    </div>
    <div>
      <p className="text-sm text-slate-500 font-medium">{title}</p>
      <p className="text-2xl font-bold text-slate-800">{value}</p>
    </div>
  </div>
);

export default Dashboard;
