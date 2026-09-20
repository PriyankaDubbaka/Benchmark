import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import ApiKeysPage from './pages/ApiKeysPage';
import ModelsPage from './pages/ModelsPage';
import DocumentsPage from './pages/DocumentsPage';
import BenchmarkRunPage from './pages/BenchmarkRunPage';
import ResultsPage from './pages/ResultsPage';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/api-keys" element={<ApiKeysPage />} />
        <Route path="/models" element={<ModelsPage />} />
        <Route path="/documents" element={<DocumentsPage />} />
        <Route path="/benchmark" element={<BenchmarkRunPage />} />
        <Route path="/results" element={<ResultsPage />} />
      </Routes>
    </Layout>
  );
}

export default App;
