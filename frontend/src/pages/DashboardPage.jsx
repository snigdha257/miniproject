import React, { useCallback, useEffect, useMemo, useState } from 'react'
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

const LABEL_MAP = {
  'PERSON': 'Person',
  'ORG': 'Organization',
  'EMAIL': 'Email',
  'PHONE': 'Phone',
  'AADHAAR': 'Aadhaar',
  'PAN': 'PAN',
  'PASSPORT': 'Passport',
  'SALARY': 'Salary',
  'JOINING_DATE': 'Joining Date',
  'CREDIT_CARD': 'Credit Card',
  'SSN': 'SSN',
  'DOB': 'Date of Birth',
  'AGE': 'Age',
  'GENDER': 'Gender',
  'NATIONALITY': 'Nationality',
  'NATIONAL_ID': 'National ID',
  'IP_ADDRESS': 'IP Address',
  'MAC_ADDRESS': 'MAC Address',
  'PHYSICAL_ADDRESS': 'Physical Address',
  'BANK_ACCOUNT': 'Bank Account',
  'IBAN': 'IBAN',
  'ROUTING_NUMBER': 'Routing Number',
  'TAX_ID': 'Tax ID',
  'INSURANCE_ID': 'Insurance ID',
  'EMPLOYEE_ID': 'Employee ID',
  'JOB_TITLE': 'Job Title',
  'MANAGER_NAME': 'Manager Name',
  'WORK_LOCATION': 'Work Location',
  'MEDICAL_RECORD': 'Medical Record Number',
  'DIAGNOSIS': 'Diagnosis/Condition',
  'PRESCRIPTION': 'Prescription/Medication',
  'PROVIDER_NAME': 'Provider Name',
  'USERNAME': 'Username',
  'PASSWORD': 'Password',
  'DEVICE_ID': 'Device ID',
  'IMEI': 'IMEI',
  'LICENSE_KEY': 'License Key',
  'LICENSE_PLATE': 'License Plate',
  'VIN': 'VIN',
  'DRIVERS_LICENSE': 'Driver\'s License',
  'CASE_NUMBER': 'Case/Ticket/Order Number',
  'DATE': 'Date',
  'SIGNATURE': 'Signature',
}

function UploadPanel({ onResult }) {
  const [mode, setMode] = useState('standard')
  const [style, setStyle] = useState('placeholder')
  const [text, setText] = useState('')
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')

  // New States
  const [processingMode, setProcessingMode] = useState('standard')
  const [docId, setDocId] = useState(null)
  const [entities, setEntities] = useState(null)

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
      const uploadedDocId = upload.data.document_id
      setDocId(uploadedDocId)

      setStatus('Analyzing entities…')
      const analyze = await api.post('/documents/analyze', {
        document_id: uploadedDocId,
        processing_mode: processingMode,
      })

      const mappedEntities = analyze.data.entities.map(ent => ({
        ...ent,
        checked: processingMode === 'enhanced' ? ent.recommendMask : true
      }))
      setEntities(mappedEntities)
      setStatus('')
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail, 'Upload failed. Please try again.'))
      setDocId(null)
      setEntities(null)
      setStatus('')
    }
  }

  if (entities !== null) {
    // Group entities by category
    const grouped = {}
    entities.forEach((ent, index) => {
      const label = ent.label
      if (!grouped[label]) {
        grouped[label] = []
      }
      grouped[label].push({ ...ent, originalIndex: index })
    })

    const handleToggleEntity = (originalIndex) => {
      setEntities(prev => prev.map((ent, idx) => {
        if (idx === originalIndex) {
          return { ...ent, checked: !ent.checked }
        }
        return ent
      }))
    }

    const handleToggleCategory = (label, allChecked) => {
      setEntities(prev => prev.map(ent => {
        if (ent.label === label) {
          return { ...ent, checked: !allChecked }
        }
        return ent
      }))
    }

    const handleConfirmMask = async () => {
      setError('')
      setStatus('Masking document…')
      try {
        const finalEntities = entities.filter(ent => ent.checked).map(ent => ({
          text: ent.text,
          label: ent.label,
          start: ent.start,
          end: ent.end
        }))

        const mask = await api.post('/documents/mask', {
          document_id: docId,
          mode,
          style,
          entities: finalEntities,
        })
        onResult({
          document_id: docId,
          raw_text: file ? 'Uploaded file' : text,
          ...mask.data,
          mode
        })
        setStatus('Masking complete')
        setText('')
        setFile(null)
        setDocId(null)
        setEntities(null)
      } catch (err) {
        setError(formatApiError(err.response?.data?.detail, 'Masking failed. Please try again.'))
      } finally {
        setStatus('')
      }
    }

    const handleCancel = () => {
      setEntities(null)
      setDocId(null)
      setError('')
    }

    return (
      <section className="space-y-6 rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
        <div>
          <h2 className="text-xl font-semibold text-white">Review Detected Entities</h2>
          <p className="mt-2 text-sm text-slate-400">
            Review the detected sensitive entities below. Pre-select masking options as recommended or customize.
          </p>
        </div>

        <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-950">
          <table className="min-w-full text-left text-sm text-slate-300">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/50">
                <th className="px-4 py-3 text-slate-100 font-semibold">Entity</th>
                <th className="px-4 py-3 text-slate-100 font-semibold">Type</th>
                {processingMode === 'enhanced' && (
                  <th className="px-4 py-3 text-slate-100 font-semibold">AI Recommendation</th>
                )}
                <th className="px-4 py-3 text-slate-100 font-semibold text-center w-24">Mask</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(grouped).map(([label, list]) => {
                const readableLabel = LABEL_MAP[label] || label.charAt(0).toUpperCase() + label.slice(1).toLowerCase()
                const isAllChecked = list.every(ent => ent.checked)
                return (
                  <React.Fragment key={label}>
                    <tr className="bg-slate-900/30 border-b border-slate-800">
                      <td colSpan={processingMode === 'enhanced' ? 3 : 2} className="px-4 py-2 font-semibold text-indigo-400">
                        {readableLabel} ({list.length} item{list.length > 1 ? 's' : ''})
                      </td>
                      <td className="px-4 py-2 text-center">
                        <label className="inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={isAllChecked}
                            onChange={() => handleToggleCategory(label, isAllChecked)}
                            className="w-4 h-4 rounded text-indigo-600 bg-slate-950 border-slate-800 focus:ring-indigo-500 focus:ring-offset-slate-950"
                          />
                        </label>
                      </td>
                    </tr>
                    {list.map((ent) => (
                      <tr key={ent.originalIndex} className="border-b border-slate-800 hover:bg-slate-900/10">
                        <td className="px-6 py-3 font-mono text-slate-100">{ent.text}</td>
                        <td className="px-6 py-3 text-slate-400">{readableLabel}</td>
                        {processingMode === 'enhanced' && (
                          <td className="px-6 py-3 text-slate-400">
                            <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-semibold ${ent.recommendMask ? 'bg-rose-500/10 text-rose-400' : 'bg-emerald-500/10 text-emerald-400'}`}>
                              {ent.recommendMask ? 'Mask' : 'Keep'}
                            </span>
                            {ent.reason && <p className="text-xs text-slate-500 mt-0.5">{ent.reason}</p>}
                          </td>
                        )}
                        <td className="px-6 py-3 text-center">
                          <label className="inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={ent.checked}
                              onChange={() => handleToggleEntity(ent.originalIndex)}
                              className="w-4 h-4 rounded text-indigo-600 bg-slate-950 border-slate-800 focus:ring-indigo-500 focus:ring-offset-slate-950"
                            />
                          </label>
                        </td>
                      </tr>
                    ))}
                  </React.Fragment>
                )
              })}
            </tbody>
          </table>
        </div>

        {error && <p className="text-sm text-rose-400">{error}</p>}
        {status && <p className="text-sm text-slate-300">{status}</p>}

        <div className="flex gap-3">
          <button
            type="button"
            disabled={status !== ''}
            onClick={handleConfirmMask}
            className="rounded-3xl bg-indigo-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Confirm and Mask
          </button>
          <button
            type="button"
            disabled={status !== ''}
            onClick={handleCancel}
            className="rounded-3xl border border-slate-800 bg-slate-950 px-6 py-3 text-sm font-semibold text-slate-300 transition hover:bg-slate-900 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
        </div>
      </section>
    )
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
      
      <div className="space-y-3">
        <span className="text-sm font-semibold text-white">Processing Mode</span>
        <div className="flex flex-wrap gap-6">
          <label className="flex items-center gap-2.5 text-sm text-slate-200 cursor-pointer">
            <input
              type="radio"
              name="processingMode"
              value="standard"
              checked={processingMode === 'standard'}
              onChange={(e) => setProcessingMode(e.target.value)}
              className="w-4.5 h-4.5 accent-indigo-500"
            />
            Standard Mode (spaCy + Regex)
          </label>
          <label className="flex items-center gap-2.5 text-sm text-slate-200 cursor-pointer">
            <input
              type="radio"
              name="processingMode"
              value="enhanced"
              checked={processingMode === 'enhanced'}
              onChange={(e) => setProcessingMode(e.target.value)}
              className="w-4.5 h-4.5 accent-indigo-500"
            />
            Enhanced AI Mode (spaCy + Regex + Groq Verification)
          </label>
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
  const [format, setFormat] = useState('txt')
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleDownload = async () => {
    if (!result?.document_id) {
      return
    }

    setError('')
    setStatus('Preparing download…')
    setLoading(true)
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
      setStatus('Download started successfully.')
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail, 'Unable to download the document.'))
    } finally {
      setLoading(false)
    }
  }

  if (!result) {
    return (
      <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 text-slate-400">
        Mask a document to see results here.
      </div>
    )
  }

  const entityCounts = result.entity_counts ?? {}

  // Handle case when result comes from history (no masked_text initially)
  if (!result.masked_text && !result.restored_text) {
    return (
      <section className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-white">Results</h2>
            <p className="mt-2 text-sm text-slate-400">Document selected from history. Use the Unmask tab to restore secure documents.</p>
          </div>
        </div>
        <div className="mt-4 rounded-3xl border border-slate-800 bg-slate-950 p-3">
          <p className="text-xs text-slate-400">Document ID: {result.document_id}</p>
          <p className="text-xs text-slate-400">Mode: {result.mode || 'Unknown'}</p>
        </div>
      </section>
    )
  }

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

      <div className="mt-6 flex flex-wrap items-center gap-3">
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
          type="button"
          onClick={handleDownload}
          disabled={loading || !result?.document_id}
          className="rounded-3xl bg-indigo-500 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? 'Preparing…' : 'Download'}
        </button>
      </div>
      {status && <p className="mt-3 text-sm text-emerald-400">{status}</p>}
      {error && <p className="mt-3 text-sm text-rose-400">{error}</p>}

      {result.masked_text && (
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
      )}
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
  const [restoredText, setRestoredText] = useState('')
  const [downloadFormat, setDownloadFormat] = useState('txt')
  const [downloadLoading, setDownloadLoading] = useState(false)

  const handleUnmask = async () => {
    setMessage('')
    setLoading(true)
    try {
      const response = await api.post('/documents/unmask', {
        document_id: result.document_id,
        key,
      })
      setRestoredText(response.data.restored_text)
      onRestored(response.data.restored_text)
      setMessage('Restored successfully.')
    } catch (err) {
      setMessage(formatApiError(err.response?.data?.detail, 'Unable to unmask with that key.'))
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadRestored = async () => {
    setMessage('')
    setDownloadLoading(true)
    try {
      const response = await api.get(`/documents/${result.document_id}/download`, {
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
      setMessage('Download started successfully.')
    } catch (err) {
      setMessage(formatApiError(err.response?.data?.detail, 'Unable to download the restored document.'))
    } finally {
      setDownloadLoading(false)
    }
  }

  if (!result?.document_id) {
    return (
      <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 text-slate-400">
        Select a secure-mode document from the History tab to enable unmasking.
      </div>
    )
  }

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
      <h2 className="text-xl font-semibold text-white">Secure Unmask</h2>
      <p className="mt-2 text-sm text-slate-400">Enter the key to restore your secure masked document.</p>
      <div className="mt-4 rounded-3xl border border-slate-800 bg-slate-950 p-3">
        <p className="text-xs text-slate-400">Document ID: {result.document_id}</p>
        <p className="text-xs text-slate-400">Mode: {result.mode || 'Unknown'}</p>
      </div>
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
      
      {restoredText && (
        <div className="mt-6 space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-300">Restored Document:</h3>
            <div className="mt-2 max-h-64 overflow-y-auto rounded-3xl border border-slate-800 bg-slate-950 p-4 text-sm text-slate-400">
              {restoredText}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <select
              value={downloadFormat}
              onChange={(e) => setDownloadFormat(e.target.value)}
              className="rounded-full border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-100 outline-none"
            >
              <option value="txt">TXT</option>
              <option value="docx">DOCX</option>
              <option value="pdf">PDF</option>
            </select>
            <button
              type="button"
              onClick={handleDownloadRestored}
              disabled={downloadLoading}
              className="rounded-3xl bg-emerald-500 px-6 py-3 text-sm font-semibold text-white transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {downloadLoading ? 'Downloading…' : 'Download Restored'}
            </button>
          </div>
        </div>
      )}
    </section>
  )
}

function HistoryRow({ item, onUnmask }) {
  const [format, setFormat] = useState('txt')
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleDownload = async () => {
    setError('')
    setStatus('Preparing download…')
    setLoading(true)
    try {
      const response = await api.get(`/documents/${item.document_id}/download`, {
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
      setStatus('Download started successfully.')
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail, 'Unable to download the document.'))
    } finally {
      setLoading(false)
    }
  }

  const handleUnmaskClick = () => {
    onUnmask(item)
  }

  return (
    <tr className="border-b border-slate-800 last:border-b-0">
      <td className="px-4 py-4 text-slate-100">{item.filename || 'Text snippet'}</td>
      <td className="px-4 py-4 text-slate-400">{new Date(item.created_at).toLocaleString()}</td>
      <td className="px-4 py-4 text-slate-400">{item.mode}</td>
      <td className="px-4 py-4 text-slate-400">{item.risk_level}</td>
      <td className="px-4 py-4">
        <div className="flex flex-wrap items-center gap-2">
          {item.mode === 'secure' && (
            <button
              type="button"
              onClick={handleUnmaskClick}
              className="rounded-full bg-emerald-500 px-3 py-2 text-xs font-semibold text-white transition hover:bg-emerald-400"
            >
              Unmask
            </button>
          )}
          <select
            value={format}
            onChange={(e) => setFormat(e.target.value)}
            className="rounded-full border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-100 outline-none"
          >
            <option value="txt">TXT</option>
            <option value="docx">DOCX</option>
            <option value="pdf">PDF</option>
          </select>
          <button
            type="button"
            onClick={handleDownload}
            disabled={loading}
            className="rounded-full bg-indigo-500 px-3 py-2 text-xs font-semibold text-white transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? '…' : 'Download'}
          </button>
        </div>
        {status && <p className="mt-2 text-xs text-emerald-400">{status}</p>}
        {error && <p className="mt-2 text-xs text-rose-400">{error}</p>}
      </td>
    </tr>
  )
}

function HistoryPanel({ history, onRefresh, onUnmask }) {
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
              <th className="border-b border-slate-800 px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {history.documents.map((item) => (
              <HistoryRow key={item.document_id} item={item} onUnmask={onUnmask} />
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

  const handleHistoryUnmask = useCallback((item) => {
    // Set the result to the history item for unmasking
    setResult({
      document_id: item.document_id,
      mode: item.mode,
      masked_text: null, // Will be fetched from backend
    })
    // Switch to Unmask tab
    setActiveTab('Unmask')
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
        {activeTab === 'History' && <HistoryPanel history={history} onRefresh={refreshHistory} onUnmask={handleHistoryUnmask} />}
      </div>
    </DashboardLayout>
  )
}
