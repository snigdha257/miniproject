import React, { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import api, { attachToken, formatApiError } from '../api.js'
import AppLayout from '../components/AppLayout.jsx'
import { useAuth } from '../context/AuthContext.jsx'

export default function UnmaskPage() {
  const { token } = useAuth()
  const location = useLocation()
  const [documents, setDocuments] = useState([])
  const [selectedDocId, setSelectedDocId] = useState(null)
  const [key, setKey] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [restoredText, setRestoredText] = useState('')
  const [downloadFormat, setDownloadFormat] = useState('txt')
  const [downloadLoading, setDownloadLoading] = useState(false)
  const [pageLoading, setPageLoading] = useState(true)

  useEffect(() => {
    if (!token) return
    attachToken(token)

    async function loadSecureDocuments() {
      try {
        const response = await api.get('/documents/history', {
          params: { page: 1, page_size: 10 },
        })
        const secureOnly = response.data.documents.filter(d => d.mode === 'secure')
        setDocuments(secureOnly)

        // Pre-select document if passed from History page
        const preselectedDocId = location.state?.preselectedDocId
        if (preselectedDocId) {
          setSelectedDocId(preselectedDocId)
        }
      } catch (err) {
        console.error('Failed to load documents:', err)
      } finally {
        setPageLoading(false)
      }
    }

    loadSecureDocuments()
  }, [token, location])

  const handleUnmask = async () => {
    if (!selectedDocId || !key) return
    setMessage('')
    setLoading(true)
    try {
      const response = await api.post('/documents/unmask', {
        document_id: selectedDocId,
        key,
      })
      setRestoredText(response.data.restored_text)
      setMessage('Restored successfully!')
    } catch (err) {
      setMessage(formatApiError(err.response?.data?.detail, 'Unable to unmask. Check the key and try again.'))
      setRestoredText('')
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadRestored = async () => {
    if (!selectedDocId) return
    setMessage('')
    setDownloadLoading(true)
    try {
      const response = await api.get(`/documents/${selectedDocId}/download`, {
        params: { format: downloadFormat },
        responseType: 'blob',
      })

      const blob = new Blob([response.data], { type: response.headers['content-type'] || 'application/octet-stream' })
      const contentDisposition = response.headers['content-disposition'] || ''
      const match = contentDisposition.match(/filename="?([^";]+)"?/)
      const fileName = match?.[1] || `restored.${downloadFormat}`
      const blobUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = blobUrl
      link.download = fileName
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(blobUrl)
      setMessage('Downloaded successfully!')
    } catch (err) {
      setMessage(formatApiError(err.response?.data?.detail, 'Unable to download the document.'))
    } finally {
      setDownloadLoading(false)
    }
  }

  if (pageLoading) {
    return (
      <AppLayout>
        <div className="flex items-center justify-center text-slate-400">
          Loading documents...
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-4xl font-bold text-white">Unmask Document</h1>
          <p className="mt-2 text-slate-400">Restore secure-mode documents with your decryption key</p>
        </div>

        {documents.length === 0 ? (
          <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 text-center text-slate-400">
            <p>No secure-mode documents found.</p>
            <p className="mt-2 text-sm">Upload and mask a document using Secure mode first.</p>
          </div>
        ) : (
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Document Selector */}
            <div className="lg:col-span-1">
              <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 space-y-4">
                <h2 className="text-lg font-semibold text-white">Select Document</h2>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {documents.map((doc) => (
                    <button
                      key={doc.document_id}
                      onClick={() => {
                        setSelectedDocId(doc.document_id)
                        setRestoredText('')
                        setKey('')
                        setMessage('')
                      }}
                      className={`w-full text-left rounded-lg p-3 transition ${
                        selectedDocId === doc.document_id
                          ? 'bg-indigo-500 text-white'
                          : 'bg-slate-950 text-slate-200 hover:bg-slate-900'
                      }`}
                    >
                      <p className="font-semibold">{doc.filename || 'Text snippet'}</p>
                      <p className="text-xs opacity-75">{new Date(doc.created_at).toLocaleDateString()}</p>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Unmask Form */}
            <div className="lg:col-span-2">
              <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 space-y-6">
                {selectedDocId ? (
                  <>
                    <div>
                      <h2 className="text-lg font-semibold text-white">Restore Document</h2>
                      <p className="mt-2 text-sm text-slate-400">Enter your decryption key to restore the content</p>
                    </div>

                    <div className="space-y-4">
                      <input
                        type="password"
                        value={key}
                        onChange={(e) => setKey(e.target.value)}
                        placeholder="Enter decryption key"
                        className="w-full rounded-3xl border border-slate-800 bg-slate-950 px-4 py-3 text-sm text-slate-100 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20"
                      />

                      <button
                        onClick={handleUnmask}
                        disabled={!key || loading}
                        className="w-full rounded-3xl bg-indigo-500 px-6 py-3 text-sm font-semibold text-white hover:bg-indigo-400 disabled:opacity-60"
                      >
                        {loading ? 'Restoring…' : 'Unmask Document'}
                      </button>
                    </div>

                    {message && (
                      <p className={`text-sm ${
                        message.includes('success') || message.includes('Successfully') || message.includes('Downloaded')
                          ? 'text-emerald-400'
                          : 'text-rose-400'
                      }`}>
                        {message}
                      </p>
                    )}

                    {restoredText && (
                      <div className="space-y-4">
                        <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
                          <h3 className="text-sm uppercase tracking-widest font-semibold text-emerald-400">Restored Content</h3>
                          <div className="mt-3 max-h-64 overflow-y-auto">
                            <pre className="whitespace-pre-wrap break-words text-sm text-slate-100 font-mono">{restoredText}</pre>
                          </div>
                        </div>

                        <div className="flex flex-wrap items-center gap-3">
                          <select
                            value={downloadFormat}
                            onChange={(e) => setDownloadFormat(e.target.value)}
                            className="rounded-3xl border border-slate-800 bg-slate-950 px-4 py-2 text-sm text-slate-100 outline-none"
                          >
                            <option value="txt">TXT</option>
                            <option value="docx">DOCX</option>
                            <option value="pdf">PDF</option>
                          </select>
                          <button
                            onClick={handleDownloadRestored}
                            disabled={downloadLoading}
                            className="rounded-3xl bg-emerald-500 px-6 py-2 text-sm font-semibold text-white hover:bg-emerald-400 disabled:opacity-60"
                          >
                            {downloadLoading ? 'Downloading…' : 'Download'}
                          </button>
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <p className="text-slate-400 text-center py-8">Select a document to unmask</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
