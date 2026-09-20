import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { kbApi } from '../services/api';
import {
  UploadCloud,
  FileText,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Clock,
  Loader2,
  Database
} from 'lucide-react';

export const AdminKBPage = () => {
  const [documents, setDocuments] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    setLoadingDocs(true);
    try {
      const data = await kbApi.listDocuments();
      setDocuments(data);
    } catch (err) {
      console.error('Failed to load documents:', err);
      setErrorMsg('Failed to load knowledge base documents.');
    } finally {
      setLoadingDocs(false);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setErrorMsg('');
      setSuccessMsg('');
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile || uploading) return;

    setUploading(true);
    setErrorMsg('');
    setSuccessMsg('');

    try {
      const result = await kbApi.uploadDocument(selectedFile);
      setSuccessMsg(`Document '${result.filename}' processed successfully (${result.chunk_count} chunks embedded).`);
      setSelectedFile(null);
      // Reset file input element
      const fileInput = document.getElementById('kb-file-input');
      if (fileInput) fileInput.value = '';
      fetchDocuments();
    } catch (err) {
      console.error('Document upload failed:', err);
      const msg = err.response?.data?.detail || 'Failed to upload and process document.';
      setErrorMsg(msg);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id, filename) => {
    if (!window.confirm(`Are you sure you want to delete '${filename}'? This will remove all vector embeddings from ChromaDB.`)) {
      return;
    }

    try {
      await kbApi.deleteDocument(id);
      setSuccessMsg(`Document '${filename}' and its vector embeddings deleted successfully.`);
      fetchDocuments();
    } catch (err) {
      console.error('Failed to delete document:', err);
      const msg = err.response?.data?.detail || 'Failed to delete document.';
      setErrorMsg(msg);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-6xl w-full mx-auto p-4 sm:p-6 space-y-6">
        {/* Page Title */}
        <div className="flex items-center space-x-3 border-b border-gray-200 pb-4">
          <div className="p-2.5 bg-brand-50 text-brand-600 rounded-lg">
            <Database className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Knowledge Base Management</h1>
            <p className="text-xs text-gray-500">Upload PDF, TXT, or DOCX files to automatically index into ChromaDB for RAG.</p>
          </div>
        </div>

        {/* Feedback Alerts */}
        {successMsg && (
          <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 px-4 py-3 rounded-lg text-xs flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <span>{successMsg}</span>
            </div>
            <button onClick={() => setSuccessMsg('')} className="text-emerald-600 font-bold">×</button>
          </div>
        )}

        {errorMsg && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg text-xs flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
            <button onClick={() => setErrorMsg('')} className="text-red-600 font-bold">×</button>
          </div>
        )}

        {/* Document Upload Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-sm font-bold text-gray-900 mb-4 uppercase tracking-wider">
            Upload Knowledge Document
          </h2>

          <form onSubmit={handleUpload} className="space-y-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-brand-500 transition-colors bg-gray-50/50">
              <UploadCloud className="w-10 h-10 text-gray-400 mx-auto mb-2" />
              <div className="text-xs text-gray-600 mb-1 font-medium">
                Select a document file (PDF, TXT, DOCX)
              </div>
              <input
                id="kb-file-input"
                type="file"
                accept=".pdf,.txt,.docx"
                onChange={handleFileChange}
                className="text-xs text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-brand-50 file:text-brand-700 hover:file:bg-brand-100 cursor-pointer"
              />
            </div>

            {selectedFile && (
              <div className="flex items-center justify-between text-xs bg-brand-50 text-brand-800 p-3 rounded-lg border border-brand-200">
                <div className="flex items-center space-x-2">
                  <FileText className="w-4 h-4 text-brand-600" />
                  <span className="font-semibold">{selectedFile.name}</span>
                  <span className="text-brand-600">({formatFileSize(selectedFile.size)})</span>
                </div>
                <button
                  type="submit"
                  disabled={uploading}
                  className="bg-brand-600 hover:bg-brand-700 text-white px-4 py-1.5 rounded-md font-semibold text-xs transition-colors flex items-center space-x-1 disabled:opacity-50"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Ingesting...</span>
                    </>
                  ) : (
                    <span>Upload & Embed</span>
                  )}
                </button>
              </div>
            )}
          </form>
        </div>

        {/* Document List Table Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="p-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-sm font-bold text-gray-900 uppercase tracking-wider">
              Knowledge Base Documents ({documents.length})
            </h2>
            <button
              onClick={fetchDocuments}
              className="text-xs text-brand-600 hover:text-brand-800 font-medium"
            >
              Refresh Table
            </button>
          </div>

          {loadingDocs ? (
            <div className="p-8 text-center text-xs text-gray-500 flex justify-center items-center space-x-2">
              <Loader2 className="w-4 h-4 animate-spin text-brand-600" />
              <span>Loading documents...</span>
            </div>
          ) : documents.length === 0 ? (
            <div className="p-8 text-center text-xs text-gray-500">
              No documents uploaded yet. Upload a PDF, TXT, or DOCX above.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-gray-700">
                <thead className="bg-gray-50 text-gray-700 font-semibold border-b border-gray-200 uppercase tracking-wider text-[11px]">
                  <tr>
                    <th className="px-4 py-3">Filename</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Chunks</th>
                    <th className="px-4 py-3">Size</th>
                    <th className="px-4 py-3">Date</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {documents.map((doc) => (
                    <tr key={doc.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3 font-medium text-gray-900 flex items-center space-x-2">
                        <FileText className="w-4 h-4 text-gray-400 flex-shrink-0" />
                        <span className="truncate max-w-xs">{doc.filename}</span>
                      </td>
                      <td className="px-4 py-3">
                        {doc.status === 'completed' && (
                          <span className="inline-flex items-center space-x-1 bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded text-[11px] font-semibold border border-emerald-200">
                            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                            <span>Completed</span>
                          </span>
                        )}
                        {doc.status === 'processing' && (
                          <span className="inline-flex items-center space-x-1 bg-amber-50 text-amber-700 px-2 py-0.5 rounded text-[11px] font-semibold border border-amber-200">
                            <Clock className="w-3 h-3 text-amber-600 animate-spin" />
                            <span>Processing</span>
                          </span>
                        )}
                        {doc.status === 'failed' && (
                          <span className="inline-flex items-center space-x-1 bg-red-50 text-red-700 px-2 py-0.5 rounded text-[11px] font-semibold border border-red-200" title={doc.error_message}>
                            <AlertCircle className="w-3 h-3 text-red-600" />
                            <span>Failed</span>
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 font-medium">{doc.chunk_count}</td>
                      <td className="px-4 py-3 text-gray-500">{formatFileSize(doc.file_size)}</td>
                      <td className="px-4 py-3 text-gray-500">{new Date(doc.created_at).toLocaleDateString()}</td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => handleDelete(doc.id, doc.filename)}
                          className="text-red-600 hover:text-red-800 font-medium p-1 rounded hover:bg-red-50 transition-colors"
                          title="Delete document and remove ChromaDB embeddings"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default AdminKBPage;
