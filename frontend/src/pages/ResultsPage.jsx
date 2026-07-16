import React, { useState } from 'react'
import api, { formatApiError } from '../api.js'
import AppLayout from '../components/AppLayout.jsx'
import { useResult } from '../context/ResultContext.jsx'

export default function ResultsPage() {
  const { result } = useResult()
  const [format, setFormat] = useState('txt')
  const [downloadStatus, setDownloadStatus] = useState('')
  const [downloadError, setDownloadError] = useState('')
  const [downloadLoading, setDownloadLoading] = useState(false)

  const handleDownload = async () => {
    if (!result?.document_id) return

    setDownloadError('')
    setDownloadStatus('Preparing download…')
    setDownloadLoading(true)
    try {
      const response = await api.get(`/documents/${result.document_id}/download`, {
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
      setDownloadStatus('Download started successfully.')
    } catch (err) {
      setDownloadError(formatApiError(err.response?.data?.detail, 'Unable to download.'))
    } finally {
      setDownloadLoading(false)
    }
  }

  if (!result) {
    return (
      <AppLayout>
        <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 text-center text-slate-400">
          <p>No results to display. Upload or mask a document first.</p>
        </div>
      </AppLayout>
    )
  }

  const entityCounts = result.entity_counts ?? {}
  const totalEntities = Object.values(entityCounts).reduce((sum, val) => sum + val, 0)

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-4xl font-bold text-white">Results</h1>
          <p className="mt-2 text-slate-400">Masking results and analysis</p>
        </div>

        {/* Summary Cards */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-3xl border border-slate-800 bg-slate-950 p-6">
            <p className="text-sm text-slate-400">Privacy Score</p>
            <p className="mt-3 text-3xl font-bold text-white">{result.privacy_score}</p>
          </div>
          <div className="rounded-3xl border border-slate-800 bg-slate-950 p-6">
            <p className="text-sm text-slate-400">Risk Level</p>
            <p className="mt-3 text-3xl font-bold text-white">{result.risk_level}</p>
          </div>
          <div className="rounded-3xl border border-slate-800 bg-slate-950 p-6">
            <p className="text-sm text-slate-400">Total Entities</p>
            <p className="mt-3 text-3xl font-bold text-white">{totalEntities}</p>
          </div>
          <div className="rounded-3xl border border-slate-800 bg-slate-950 p-6">
            <p className="text-sm text-slate-400">Processing Mode</p>
            <p className="mt-3 text-3xl font-bold text-white capitalize">{result.mode}</p>
          </div>
        </div>

        {/* Secure Key */}
        {result.mode === 'secure' && result.secure_key && (
          <div className="rounded-3xl border border-amber-800 bg-amber-950/30 p-6">
            <h3 className="text-sm uppercase tracking-widest font-semibold text-amber-400">⚠️ Secure Unmask Key</h3>
            <p className="mt-3 break-all font-mono text-sm text-slate-100 bg-slate-950 rounded-lg p-3">{result.secure_key}</p>
            <p className="mt-3 text-xs text-amber-300">Use this key in the Unmask Document page to restore the original content.</p>
          </div>
        )}

        {/* Download Section */}
        <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
          <h2 className="text-lg font-semibold text-white">Download Masked Document</h2>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value)}
              className="rounded-3xl border border-slate-800 bg-slate-950 px-4 py-2 text-sm text-slate-100 outline-none"
            >
              <option value="txt">TXT</option>
              <option value="docx">DOCX</option>
              <option value="pdf">PDF</option>
            </select>
            <button
              onClick={handleDownload}
              disabled={downloadLoading || !result?.document_id}
              className="rounded-3xl bg-indigo-500 px-6 py-2 text-sm font-semibold text-white hover:bg-indigo-400 disabled:opacity-60"
            >
              {downloadLoading ? 'Preparing…' : 'Download'}
            </button>
          </div>
          {downloadStatus && <p className="mt-3 text-sm text-emerald-400">{downloadStatus}</p>}
          {downloadError && <p className="mt-3 text-sm text-rose-400">{downloadError}</p>}
        </div>

        {/* Content Comparison */}
        <div className="grid gap-6 lg:grid-cols-2">
          {result.masked_text && (
            <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
              <h3 className="text-sm uppercase tracking-widest font-semibold text-indigo-400">Masked Content</h3>
              <div className="mt-4 max-h-96 overflow-y-auto rounded-lg border border-slate-800 bg-slate-950 p-4">
                <pre className="whitespace-pre-wrap break-words text-sm text-slate-100 font-mono">{result.masked_text}</pre>
              </div>
            </div>
          )}

          {result.restored_text && (
            <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
              <h3 className="text-sm uppercase tracking-widest font-semibold text-emerald-400">Restored Content</h3>
              <div className="mt-4 max-h-96 overflow-y-auto rounded-lg border border-slate-800 bg-slate-950 p-4">
                <pre className="whitespace-pre-wrap break-words text-sm text-slate-100 font-mono">{result.restored_text}</pre>
              </div>
            </div>
          )}
        </div>

        {/* Entity Breakdown */}
        {Object.keys(entityCounts).length > 0 && (
          <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
            <h3 className="text-lg font-semibold text-white">Detected Entities</h3>
            <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {Object.entries(entityCounts).map(([label, count]) => (
                <div key={label} className="rounded-lg border border-slate-800 bg-slate-950 p-4">
                  <p className="text-sm text-slate-400">{label}</p>
                  <p className="mt-2 text-2xl font-bold text-indigo-400">{count}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
