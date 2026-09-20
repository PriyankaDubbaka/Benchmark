import React, { useState, useEffect } from 'react';
import { FileText, Eye, Upload, CheckCircle2, ShieldCheck, Database, X, HelpCircle, FileCheck } from 'lucide-react';
import { apiClient, Document } from '../api/client';

interface AnnotationRecord {
  element: string;
  value: string;
  unit: string;
  expanded_uncertainty: string;
  coverage_factor: number;
  status: string;
  oxide_formula: string | null;
  oxide_value: string | null;
  source_page: number;
}

interface RetrievalQuery {
  id: string;
  query: string;
  category: string;
  expected_answer: string;
  evidence_pages: number[];
}

interface AnnotationData {
  document_id: string;
  annotation_status: string;
  scope: string;
  extraction_records: AnnotationRecord[];
  retrieval_queries: RetrievalQuery[];
  metadata: {
    filename: string;
    sha256: string;
    page_count: number;
    document_version?: string;
    revision_date?: string;
  };
  notes?: string;
}

const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [annotation, setAnnotation] = useState<AnnotationData | null>(null);
  const [loadingAnnotation, setLoadingAnnotation] = useState(false);
  const [activeTab, setActiveTab] = useState<'extraction' | 'retrieval' | 'metadata'>('extraction');

  useEffect(() => {
    fetchDocs();
  }, []);

  const fetchDocs = async () => {
    try {
      const data = await apiClient.getDocuments();
      setDocuments(data || []);
    } catch (err) {
      console.error('Failed to fetch documents', err);
    } finally {
      setLoading(false);
    }
  };

  const handleViewAnnotation = async (docId: string) => {
    setSelectedDocId(docId);
    setLoadingAnnotation(true);
    try {
      const data = await apiClient.getDocumentAnnotation(docId);
      setAnnotation(data);
    } catch (err) {
      console.error('Failed to load annotation', err);
      setAnnotation(null);
    } finally {
      setLoadingAnnotation(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Master Dataset & Annotations</h1>
          <p className="text-slate-600 mt-1">
            Certified BAM reference documents and gold standard Master Copies serving as the ground truth baseline.
          </p>
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start space-x-3">
        <ShieldCheck className="text-blue-600 mt-0.5 flex-shrink-0" size={20} />
        <div className="text-sm text-blue-900">
          <p className="font-semibold">Ground Truth Comparison Protocol (PW2 / BAM DocBench)</p>
          <p className="text-blue-700 mt-0.5">
            Model extractions are compared directly against the frozen master copy annotations below. A true positive requires exact matches on element symbol, normalized decimal mass fraction, unit, uncertainty (k=2), and certification status.
          </p>
        </div>
      </div>

      {/* Document Table */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-6 py-3.5 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Document / Certificate</th>
              <th className="px-6 py-3.5 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">PDF Pages</th>
              <th className="px-6 py-3.5 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Master Copy Status</th>
              <th className="px-6 py-3.5 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Ground Truth Records</th>
              <th className="px-6 py-3.5 text-right text-xs font-semibold text-slate-600 uppercase tracking-wider">Action</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-slate-200">
            {loading ? (
              <tr><td colSpan={5} className="px-6 py-8 text-center text-slate-500">Loading documents...</td></tr>
            ) : documents.map((doc: any) => (
              <tr key={doc.id} className="hover:bg-slate-50 transition-colors">
                <td className="px-6 py-4">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-slate-100 text-slate-600 rounded">
                      <FileText size={18} />
                    </div>
                    <div>
                      <span className="text-sm font-semibold text-slate-900 block">{doc.title || doc.filename}</span>
                      <span className="text-xs text-slate-500 font-mono">{doc.filename}</span>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600 font-medium">
                  {doc.pageCount || doc.page_count} pages
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {doc.hasAnnotation || doc.has_annotation ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                      <CheckCircle2 size={12} className="mr-1" />
                      Gold Master Ready
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600">
                      Template Registered
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                  <span className="font-semibold text-slate-800">{doc.extractionRecordsCount || (doc.hasAnnotation ? 27 : 0)}</span> elemental records
                  <span className="text-slate-400 mx-1">·</span>
                  <span className="font-semibold text-slate-800">{doc.retrievalQueriesCount || (doc.hasAnnotation ? 16 : 0)}</span> queries
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                  <button
                    onClick={() => handleViewAnnotation(doc.id)}
                    className="inline-flex items-center px-3 py-1.5 border border-blue-600 text-blue-600 hover:bg-blue-50 rounded text-xs font-semibold transition-colors"
                  >
                    <Eye size={14} className="mr-1.5" />
                    Inspect Master Copy
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Master Copy Modal / Inspector Drawer */}
      {selectedDocId && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex justify-center items-center p-4">
          <div className="bg-white rounded-xl shadow-2xl border border-slate-200 max-w-5xl w-full max-h-[90vh] flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="p-6 border-b border-slate-200 flex justify-between items-start bg-slate-50">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="px-2.5 py-0.5 bg-blue-100 text-blue-800 text-xs font-bold rounded">MASTER COPY BASELINE</span>
                  <span className="text-xs font-mono text-slate-500">{annotation?.document_id || selectedDocId}</span>
                </div>
                <h2 className="text-xl font-bold text-slate-900 mt-1">
                  {annotation?.metadata?.filename || selectedDocId}
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  SHA-256: <code className="text-slate-700">{annotation?.metadata?.sha256 || 'Frozen pilot signature'}</code>
                </p>
              </div>
              <button
                onClick={() => setSelectedDocId(null)}
                className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-200 transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-slate-200 px-6 bg-white">
              <button
                onClick={() => setActiveTab('extraction')}
                className={`py-3 px-4 text-sm font-semibold border-b-2 transition-colors ${
                  activeTab === 'extraction'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-slate-600 hover:text-slate-900'
                }`}
              >
                Elemental Mass Fractions ({annotation?.extraction_records?.length || 0})
              </button>
              <button
                onClick={() => setActiveTab('retrieval')}
                className={`py-3 px-4 text-sm font-semibold border-b-2 transition-colors ${
                  activeTab === 'retrieval'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-slate-600 hover:text-slate-900'
                }`}
              >
                Evidence Retrieval Queries ({annotation?.retrieval_queries?.length || 0})
              </button>
              <button
                onClick={() => setActiveTab('metadata')}
                className={`py-3 px-4 text-sm font-semibold border-b-2 transition-colors ${
                  activeTab === 'metadata'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-slate-600 hover:text-slate-900'
                }`}
              >
                Provenance & Validation Notes
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto flex-1">
              {loadingAnnotation ? (
                <div className="py-12 text-center text-slate-500">Loading ground truth master copy...</div>
              ) : !annotation ? (
                <div className="py-12 text-center text-slate-500">Annotation data not found for this document.</div>
              ) : activeTab === 'extraction' ? (
                <div>
                  <div className="mb-4 text-xs text-slate-500 bg-slate-50 p-3 rounded border border-slate-200 flex justify-between">
                    <span><strong>Scope:</strong> {annotation.scope}</span>
                    <span className="font-semibold text-slate-700">All uncertainties k = 2 (approx. 95% confidence)</span>
                  </div>
                  {annotation.extraction_records && annotation.extraction_records.length > 0 ? (
                    <table className="min-w-full text-xs text-left border divide-y divide-slate-200">
                      <thead className="bg-slate-100 text-slate-700 uppercase font-bold">
                        <tr>
                          <th className="px-3 py-2 border-r">Element</th>
                          <th className="px-3 py-2 border-r">Value</th>
                          <th className="px-3 py-2 border-r">Unit</th>
                          <th className="px-3 py-2 border-r">Uncertainty (U)</th>
                          <th className="px-3 py-2 border-r">k Factor</th>
                          <th className="px-3 py-2 border-r">Status</th>
                          <th className="px-3 py-2 border-r">Oxide Formula</th>
                          <th className="px-3 py-2 border-r">Oxide Value</th>
                          <th className="px-3 py-2">Page</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200 bg-white">
                        {annotation.extraction_records.map((r, i) => (
                          <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}>
                            <td className="px-3 py-2 font-bold text-slate-900 border-r">{r.element}</td>
                            <td className="px-3 py-2 font-mono font-semibold text-blue-700 border-r">{r.value}</td>
                            <td className="px-3 py-2 font-mono border-r">{r.unit}</td>
                            <td className="px-3 py-2 font-mono border-r">± {r.expanded_uncertainty}</td>
                            <td className="px-3 py-2 border-r">k = {r.coverage_factor}</td>
                            <td className="px-3 py-2 border-r">
                              <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                                r.status === 'certified' ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'
                              }`}>
                                {r.status}
                              </span>
                            </td>
                            <td className="px-3 py-2 font-mono border-r">{r.oxide_formula || '—'}</td>
                            <td className="px-3 py-2 font-mono border-r">{r.oxide_value || '—'}</td>
                            <td className="px-3 py-2 font-semibold text-slate-600">p.{r.source_page}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <div className="p-8 text-center text-slate-500">
                      This certificate template is registered. Populate extraction records using the benchmark annotation guide.
                    </div>
                  )}
                </div>
              ) : activeTab === 'retrieval' ? (
                <div>
                  {annotation.retrieval_queries && annotation.retrieval_queries.length > 0 ? (
                    <div className="space-y-4">
                      {annotation.retrieval_queries.map((q) => (
                        <div key={q.id} className="p-4 rounded-lg border border-slate-200 bg-slate-50/50">
                          <div className="flex justify-between items-center mb-1.5">
                            <span className="font-bold text-xs px-2 py-0.5 bg-slate-200 text-slate-800 rounded">{q.id}</span>
                            <span className="text-xs uppercase font-semibold text-slate-500">{q.category}</span>
                          </div>
                          <p className="font-semibold text-sm text-slate-800 mb-2">{q.query}</p>
                          <div className="bg-white p-2.5 rounded border border-slate-200 text-xs space-y-1">
                            <p><strong className="text-slate-600">Expected Reference Answer:</strong> {q.expected_answer}</p>
                            <p><strong className="text-slate-600">Evidence Page(s):</strong> Page {q.evidence_pages.join(', ')}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-8 text-center text-slate-500">No retrieval queries defined for this document yet.</div>
                  )}
                </div>
              ) : (
                <div className="space-y-4 text-sm text-slate-700">
                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
                    <h4 className="font-bold text-slate-900">Annotation Status & Provenance</h4>
                    <p>Status: <span className="font-semibold">{annotation.annotation_status}</span></p>
                    <p>Filename: <code className="font-mono">{annotation.metadata.filename}</code></p>
                    <p>Document Version: <span className="font-semibold">{annotation.metadata.document_version || 'V2'}</span></p>
                    <p>Revision Date: <span className="font-semibold">{annotation.metadata.revision_date || '2025-03-03'}</span></p>
                  </div>
                  {annotation.notes && (
                    <div className="p-4 bg-amber-50 rounded-lg border border-amber-200 text-amber-900 text-xs">
                      <strong>Methodological Notes:</strong> {annotation.notes}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-200 bg-slate-50 flex justify-end">
              <button
                onClick={() => setSelectedDocId(null)}
                className="px-4 py-2 bg-slate-800 text-white rounded-md text-sm font-medium hover:bg-slate-900 transition-colors"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentsPage;
