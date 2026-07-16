import React, { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api, { attachToken, formatApiError } from '../api.js'
import AppLayout from '../components/AppLayout.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { Search, Download, Unlock } from 'lucide-react'

export default function HistoryPage() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const [documents, setDocuments] = useState([])
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [search, setSearch] = useState('')
  const [filters, setFilters] = useState({
    mode: 'all',
  })
  const [downloadLoading, setDownloadLoading] = useState({})
  const [loading, setLoading] = useState(false)

  const loadHistory = useCallback(async (pageNum = 1) => {
    if (!token) return
    attachToken(token)
    setLoading(true)
    try {
      const response = await api.get('/documents/history', {
        params: { page: pageNum, page_size: 10 },
      })
      let docs = response.data.documents || []

      // Apply search filter
      if (search) {
        const searchLower = search.toLowerCase()
        docs = docs.filter(d => 
          (d.filename && d.filename.toLowerCase().includes(searchLower)) ||
          d.document_id.toLowerCase().includes(searchLower)
        )
      }

      // Apply mode filter
      if (filters.mode !== 'all') {
        docs = docs.filter(d => d.mode === filters.mode)
      }

      setDocuments(docs)
      setTotalPages(Math.ceil((response.data.total || docs.length) / 10))
      setPage(pageNum)
    } catch (err) {
      console.error('Failed to load history:', err)
    } finally {
      setLoading(false)
    }
  }, [token, search, filters])

  useEffect(() => {
    const timer = setTimeout(() => {
      loadHistory(1)
    }, 300)
    return () => clearTimeout(timer)
  }, [search, filters, loadHistory])

  const handleDownload = async (docId, format = 'txt') => {
    setDownloadLoading(prev => ({ ...prev, [docId]: true }))
    try {
      const response = await api.get(`/documents/${docId}/download`, {
        params: { format },
        responseType: 'blob',
      })

      const blob = new Blob([response.data], { type: response.headers['content-type'] || 'application/octet-stream' })
      const contentDisposition = response.headers['content-disposition'] || ''
      const match = contentDisposition.match(/filename="?([^";]+)"?/)
      const fileName = match?.[1] || `document.${format}`
      const blobUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = blobUrl
      link.download = fileName
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(blobUrl)
    } catch (err) {
      console.error('Download failed:', err)
    } finally {
      setDownloadLoading(prev => ({ ...prev, [docId]: false }))
    }
  }

  const handleUnmask = (docId) => {
    navigate('/dashboard/unmask', { state: { preselectedDocId: docId } })
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-4xl font-bold text-white">History</h1>
          <p className="mt-2 text-slate-400">View and manage your masked documents</p>
        </div>

        {/* Search and Filters */}
        <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 space-y-4">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:gap-3">
            {/* Search */}
            <div className="flex-1">
              <label className="block text-sm font-semibold text-white mb-2">Search</label>
              <div className="relative">
                <Search size={18} className="absolute left-3 top-3.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search by filename or document ID..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-10 rounded-3xl border border-slate-800 bg-slate-950 px-4 py-2.5 text-sm text-slate-100 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>
            </div>

            {/* Mode Filter */}
            <div>
              <label className="block text-sm font-semibold text-white mb-2">Mode</label>
              <select
                value={filters.mode}
                onChange={(e) => setFilters({ ...filters, mode: e.target.value })}
                className="rounded-3xl border border-slate-800 bg-slate-950 px-4 py-2.5 text-sm text-slate-100 outline-none focus:border-indigo-500"
              >
                <option value="all">All Modes</option>
                <option value="standard">Standard</option>
                <option value="secure">Secure</option>
              </select>
            </div>
          </div>
        </div>

        {/* Documents Table */}
        {loading ? (
          <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 text-center text-slate-400">
            Loading documents...
          </div>
        ) : documents.length === 0 ? (
          <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 text-center text-slate-400">
            <p>No documents found.</p>
            {search && <p className="text-sm mt-2">Try adjusting your search or filters.</p>}
          </div>
        ) : (
          <>
            <div className="rounded-3xl border border-slate-800 bg-slate-900/80 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm text-slate-300">
                  <thead>
                    <tr className="border-b border-slate-800 bg-slate-950/50">
                      <th className="px-6 py-4 font-semibold text-slate-100">Filename</th>
                      <th className="px-6 py-4 font-semibold text-slate-100">Date</th>
                      <th className="px-6 py-4 font-semibold text-slate-100">Mode</th>
                      <th className="px-6 py-4 font-semibold text-slate-100">Risk Level</th>
                      <th className="px-6 py-4 font-semibold text-slate-100">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {documents.map((doc) => (
                      <tr key={doc.document_id} className="border-b border-slate-800 hover:bg-slate-900/30 transition">
                        <td className="px-6 py-4 text-slate-100 font-medium">{doc.filename || 'Text snippet'}</td>
                        <td className="px-6 py-4 text-slate-400 text-sm">
                          {new Date(doc.created_at).toLocaleDateString()} {new Date(doc.created_at).toLocaleTimeString()}
                        </td>
                        <td className="px-6 py-4">
                          <span className="inline-flex items-center rounded-full bg-slate-800 px-3 py-1 text-xs font-semibold text-slate-200 capitalize">
                            {doc.mode}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${
                            doc.risk_level === 'HIGH'
                              ? 'bg-red-500/20 text-red-400'
                              : doc.risk_level === 'MEDIUM'
                                ? 'bg-amber-500/20 text-amber-400'
                                : 'bg-emerald-500/20 text-emerald-400'
                          }`}>
                            {doc.risk_level}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex flex-wrap items-center gap-2">
                            {doc.mode === 'secure' && (
                              <button
                                onClick={() => handleUnmask(doc.document_id)}
                                className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20 px-3 py-1.5 text-xs font-semibold transition"
                              >
                                <Unlock size={14} />
                                Unmask
                              </button>
                            )}
                            <select
                              onChange={(e) => {
                                if (e.target.value) {
                                  handleDownload(doc.document_id, e.target.value)
                                  e.target.value = ''
                                }
                              }}
                              className="rounded-full border border-slate-800 bg-slate-950 px-3 py-1.5 text-xs text-slate-100 outline-none hover:border-slate-700"
                            >
                              <option value="">Download as...</option>
                              <option value="txt">TXT</option>
                              <option value="docx">DOCX</option>
                              <option value="pdf">PDF</option>
                            </select>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-400">
                Showing <span className="font-semibold">{documents.length}</span> documents
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="rounded-full border border-slate-800 bg-slate-950 px-3 py-2 text-sm transition hover:bg-slate-900 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <span className="text-sm text-slate-400">
                  Page <span className="font-semibold text-white">{page}</span> of <span className="font-semibold text-white">{totalPages}</span>
                </span>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={page >= totalPages}
                  className="rounded-full border border-slate-800 bg-slate-950 px-3 py-2 text-sm transition hover:bg-slate-900 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </AppLayout>
  )
}
