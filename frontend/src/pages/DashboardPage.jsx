import { useCallback, useEffect, useMemo, useState } from 'react'
import api, { attachToken, formatApiError } from '../api.js'
import DashboardLayout from '../components/DashboardLayout.jsx'
import { useAuth } from '../context/AuthContext.jsx'

const TABS = ['Upload & Mask', 'Results', 'Unmask', 'History']

function SummaryCards({ data }) {
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
        <p className="text-sm text-slate-400">Documents processed</p>
        <p className="mt-4 text-3xl font-semibold text-white">{data.documents_processed}</p>
      </div>
      <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
        <p className="text-sm text-slate-400">Average privacy score</p>
        <p className="mt-4 text-3xl font-semibold text-white">{data.average_privacy_score}</p>
      </div>
      <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
        <p className="text-sm text-slate-400">Entities detected</p>
        <p className="mt-4 text-3xl font-semibold text-white">{Object.keys(data.entity_type_breakdown).length}</p>
      </div>
    </div>
  )
}

function UploadPanel({ onResult }) {
  const [mode, setMode] = useState('standard')
  const [style, setStyle] = useState('placeholder')
  const [text, setText] = useState('')
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')

  const canUpload = text.trim().length > 0 || file

  const handleUpload = async () => {
    setError('')
    setStatus('Uploading document…')
    try {
      const formData = new FormData()
      if (file) {
        formData.append('file', file)
      } else {
        formData.append('text', text)
      }
      const upload = await api.post('/documents/upload', formData)
      setStatus('Analyzing entities…')
      const mask = await api.post('/documents/mask', {
        document_id: upload.data.document_id,
        mode,
        style,
      })
      onResult({ document_id: upload.data.document_id, raw_text: file ? 'Uploaded file' : text, ...mask.data, mode })
      setStatus('Masking complete')
      setText('')
      setFile(null)
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail, 'Upload failed. Please try again.'))
    } finally {
      setStatus('')
    }
  }

  return (
    <section className="space-y-6 rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">Upload & Mask</h2>
          <p className="mt-2 text-sm text-slate-400">Upload a file or paste text, then choose standard or secure masking.</p>
        </div>
        <div className="flex gap-3">
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            className="rounded-3xl border border-slate-800 bg-slate-950 px-4 py-2 text-sm text-slate-100 outline-none"
          >
            <option value="standard">Standard</option>
            <option value="secure">Secure</option>
          </select>
          <select
            value={style}
            onChange={(e) => setStyle(e.target.value)}
            disabled={mode === 'secure'}
            className="rounded-3xl border border-slate-800 bg-slate-950 px-4 py-2 text-sm text-slate-100 outline-none disabled:cursor-not-allowed disabled:opacity-50"
          >
            <option value="placeholder">Placeholder</option>
            <option value="partial">Partial</option>
            <option value="full">Full</option>
          </select>
        </div>
      </div>
      <div className="grid gap-4 lg:grid-cols-[1.5fr_1fr]">
        <label className="group rounded-3xl border border-dashed border-slate-700 bg-slate-950/80 p-6 transition hover:border-indigo-500">
          <span className="text-sm font-semibold text-white">Drag & drop a text file</span>
          <p className="mt-2 text-sm text-slate-400">or click to select a file</p>
          <input
            type="file"
            accept=".txt,.docx,.pdf"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="sr-only"
          />
          {file && <p className="mt-4 text-sm text-slate-200">Selected file: {file.name}</p>}
        </label>
        <label className="block rounded-3xl border border-slate-800 bg-slate-950/80 p-6">
          <span className="text-sm font-semibold text-white">Or paste text</span>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={8}
            className="mt-3 w-full resize-none rounded-3xl border border-slate-800 bg-slate-950 px-4 py-3 text-sm text-slate-100 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20"
            placeholder="Paste document text here..."
          />
        </label>
      </div>
      {error && <p className="text-sm text-rose-400">{error}</p>}
      {status && <p className="text-sm text-slate-300">{status}</p>}
      <button
        type="button"
        disabled={!canUpload || status !== ''}
        onClick={handleUpload}
        className="rounded-3xl bg-indigo-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:opacity-60"
      >
        Upload and mask
      </button>
    </section>
  )
}

function ResultsPanel({ result }) {
  if (!result) {
    return (
      <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 text-slate-400">
        Mask a document to see results here.
      </div>
    )
  }

  const entityCounts = result.entity_counts ?? {}

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">Results</h2>
          <p className="mt-2 text-sm text-slate-400">Review the masked output and privacy insights.</p>
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-3xl bg-slate-950 p-4 text-center">
            <p className="text-sm text-slate-400">Score</p>
            <p className="mt-2 text-2xl font-semibold text-white">{result.privacy_score}</p>
          </div>
          <div className="rounded-3xl bg-slate-950 p-4 text-center">
            <p className="text-sm text-slate-400">Risk</p>
            <p className="mt-2 text-2xl font-semibold text-white">{result.risk_level}</p>
          </div>
          <div className="rounded-3xl bg-slate-950 p-4 text-center">
            <p className="text-sm text-slate-400">Entities</p>
            <p className="mt-2 text-2xl font-semibold text-white">{Object.values(entityCounts).reduce((sum, value) => sum + value, 0)}</p>
          </div>
        </div>
      </div>

      {result.mode === 'secure' && result.secure_key && (
        <div className="mt-6 rounded-3xl border border-slate-800 bg-slate-950 p-4 text-slate-200">
          <h3 className="text-sm uppercase tracking-[0.2em] text-slate-400">Secure unmask key</h3>
          <p className="mt-3 break-all text-sm text-slate-100">{result.secure_key}</p>
          <p className="mt-2 text-xs text-slate-400">Use this key in the Unmask tab to restore the secure document.</p>
        </div>
      )}

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <div className="rounded-3xl border border-slate-800 bg-slate-950 p-4">
          <h3 className="text-sm uppercase tracking-[0.2em] text-slate-400">Masked text</h3>
          <pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap break-words text-sm text-slate-100">{result.masked_text}</pre>
        </div>
        <div className="rounded-3xl border border-slate-800 bg-slate-950 p-4">
          <h3 className="text-sm uppercase tracking-[0.2em] text-slate-400">Entity counts</h3>
          <div className="mt-3 space-y-2">
            {Object.entries(entityCounts).map(([label, count]) => (
              <div key={label} className="flex items-center justify-between rounded-2xl bg-slate-900 px-4 py-3 text-sm text-slate-200">
                <span>{label}</span>
                <span className="font-semibold">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
      {result.restored_text && (
        <div className="mt-6 rounded-3xl border border-slate-800 bg-slate-950 p-4 text-slate-100">
          <h3 className="text-sm uppercase tracking-[0.2em] text-slate-400">Restored text</h3>
          <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap break-words text-sm">{result.restored_text}</pre>
        </div>
      )}
    </section>
  )
}

function UnmaskPanel({ result, onRestored }) {
  const [key, setKey] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  const handleUnmask = async () => {
    setMessage('')
    setLoading(true)
    try {
      const response = await api.post('/documents/unmask', {
        document_id: result.document_id,
        key,
      })
      onRestored(response.data.restored_text)
      setMessage('Restored successfully.')
    } catch (err) {
      setMessage(formatApiError(err.response?.data?.detail, 'Unable to unmask with that key.'))
    } finally {
      setLoading(false)
    }
  }

  if (!result?.mode || result.mode !== 'secure') {
    return (
      <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 text-slate-400">
        Upload a secure-mode document to enable unmasking.
      </div>
    )
  }

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
      <h2 className="text-xl font-semibold text-white">Secure Unmask</h2>
      <p className="mt-2 text-sm text-slate-400">Enter the key to restore your secure masked document.</p>
      <div className="mt-5 grid gap-4 sm:grid-cols-[1.5fr_auto]">
        <input
          type="text"
          value={key}
          onChange={(e) => setKey(e.target.value)}
          placeholder="Enter secure key"
          className="w-full rounded-3xl border border-slate-800 bg-slate-950 px-4 py-3 text-sm text-slate-100 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20"
        />
        <button
          type="button"
          onClick={handleUnmask}
          disabled={!key || loading}
          className="rounded-3xl bg-indigo-500 px-6 py-3 text-sm font-semibold text-white transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? 'Restoring…' : 'Unmask'}
        </button>
      </div>
      {message && <p className="mt-4 text-sm text-slate-300">{message}</p>}
    </section>
  )
}

function HistoryPanel({ history, onRefresh }) {
  const [page, setPage] = useState(1)

  useEffect(() => {
    onRefresh(page)
  }, [page, onRefresh])

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">History</h2>
          <p className="mt-2 text-sm text-slate-400">Your past masked documents and risk profile.</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-300">
          <button
            type="button"
            onClick={() => setPage((value) => Math.max(1, value - 1))}
            className="rounded-full bg-slate-950 px-3 py-2 transition hover:bg-slate-800"
          >
            Prev
          </button>
          <span>Page {page}</span>
          <button
            type="button"
            onClick={() => setPage((value) => value + 1)}
            className="rounded-full bg-slate-950 px-3 py-2 transition hover:bg-slate-800"
          >
            Next
          </button>
        </div>
      </div>
      <div className="mt-6 overflow-x-auto">
        <table className="min-w-full text-left text-sm text-slate-300">
          <thead>
            <tr>
              <th className="border-b border-slate-800 px-4 py-3">Filename</th>
              <th className="border-b border-slate-800 px-4 py-3">Date</th>
              <th className="border-b border-slate-800 px-4 py-3">Mode</th>
              <th className="border-b border-slate-800 px-4 py-3">Risk</th>
            </tr>
          </thead>
          <tbody>
            {history.documents.map((item) => (
              <tr key={item.document_id} className="border-b border-slate-800 last:border-b-0">
                <td className="px-4 py-4 text-slate-100">{item.filename || 'Text snippet'}</td>
                <td className="px-4 py-4 text-slate-400">{new Date(item.created_at).toLocaleString()}</td>
                <td className="px-4 py-4 text-slate-400">{item.mode}</td>
                <td className="px-4 py-4 text-slate-400">{item.risk_level}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default function DashboardPage() {
  const { token } = useAuth()
  const [summary, setSummary] = useState({ documents_processed: 0, average_privacy_score: 0, entity_type_breakdown: {} })
  const [activeTab, setActiveTab] = useState(TABS[0])
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState({ documents: [], page: 1, page_size: 10, total: 0 })
  const [restoredText, setRestoredText] = useState('')

  useEffect(() => {
    if (!token) {
      return
    }

    attachToken(token)

    async function loadDashboard() {
      const response = await api.get('/documents/dashboard')
      setSummary(response.data)
    }
    loadDashboard()
  }, [token])

  const refreshHistory = useCallback(async (page = 1) => {
    const response = await api.get('/documents/history', { params: { page, page_size: 10 } })
    setHistory(response.data)
  }, [])

  const resultWithRestored = useMemo(
    () => (result ? { ...result, restored_text: restoredText || result.restored_text } : result),
    [result, restoredText],
  )

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <SummaryCards data={summary} />
        <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-4">
          <div className="flex flex-wrap items-center gap-3">
            {TABS.map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setActiveTab(tab)}
                className={`rounded-full px-4 py-2 text-sm font-semibold transition ${activeTab === tab ? 'bg-indigo-500 text-white' : 'bg-slate-950 text-slate-300 hover:bg-slate-900'}`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
        {activeTab === 'Upload & Mask' && <UploadPanel onResult={setResult} />}
        {activeTab === 'Results' && <ResultsPanel result={resultWithRestored} />}
        {activeTab === 'Unmask' && <UnmaskPanel result={result} onRestored={setRestoredText} />}
        {activeTab === 'History' && <HistoryPanel history={history} onRefresh={refreshHistory} />}
      </div>
    </DashboardLayout>
  )
}
