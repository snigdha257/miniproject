import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api, { attachToken, formatApiError } from '../api.js'
import AppLayout from '../components/AppLayout.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { useResult } from '../context/ResultContext.jsx'

const LABEL_MAP = {
  'PERSON': 'Person', 'ORG': 'Organization', 'EMAIL': 'Email', 'PHONE': 'Phone',
  'AADHAAR': 'Aadhaar', 'PAN': 'PAN', 'PASSPORT': 'Passport', 'SALARY': 'Salary',
  'JOINING_DATE': 'Joining Date', 'CREDIT_CARD': 'Credit Card', 'SSN': 'SSN',
  'DOB': 'Date of Birth', 'AGE': 'Age', 'GENDER': 'Gender', 'NATIONALITY': 'Nationality',
}

export default function TextMaskingPage() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const { setResult } = useResult()

  const [text, setText] = useState('')
  const [mode, setMode] = useState('standard')
  const [style, setStyle] = useState('placeholder')
  const [processingMode, setProcessingMode] = useState('standard')
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [docId, setDocId] = useState(null)
  const [entities, setEntities] = useState(null)

  const charCount = text.length
  const wordCount = text.trim().split(/\s+/).filter(Boolean).length
  const lineCount = text.split('\n').length

  const handleAnalyze = async () => {
    attachToken(token)
    setError('')
    setStatus('Uploading text…')
    try {
      const formData = new FormData()
      formData.append('text', text)
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
      setError(formatApiError(err.response?.data?.detail, 'Analysis failed'))
      setDocId(null)
      setEntities(null)
      setStatus('')
    }
  }

  const handleConfirmMask = async () => {
    setError('')
    setStatus('Masking…')
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

      setResult({
        document_id: docId,
        raw_text: text,
        ...mask.data,
        mode
      })
      setText('')
      setDocId(null)
      setEntities(null)
      setStatus('')
      navigate('/dashboard/results')
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail, 'Masking failed'))
    } finally {
      setStatus('')
    }
  }

  if (entities !== null) {
    const grouped = {}
    entities.forEach((ent, index) => {
      const label = ent.label
      if (!grouped[label]) grouped[label] = []
      grouped[label].push({ ...ent, originalIndex: index })
    })

    return (
      <AppLayout>
        <div className="space-y-6">
          <div>
            <h1 className="text-4xl font-bold text-white">Text Masking</h1>
            <p className="mt-2 text-slate-400">Review entities before masking</p>
          </div>

          <section className="space-y-6 rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
            <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-950">
              <table className="min-w-full text-left text-sm text-slate-300">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-900/50">
                    <th className="px-4 py-3 text-slate-100 font-semibold">Entity</th>
                    <th className="px-4 py-3 text-slate-100 font-semibold">Type</th>
                    <th className="px-4 py-3 text-slate-100 font-semibold text-center w-24">Mask</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(grouped).map(([label, list]) => (
                    <React.Fragment key={label}>
                      <tr className="bg-slate-900/30 border-b border-slate-800">
                        <td colSpan={2} className="px-4 py-2 font-semibold text-indigo-400">
                          {label} ({list.length})
                        </td>
                        <td className="px-4 py-2 text-center">
                          <input
                            type="checkbox"
                            checked={list.every(e => e.checked)}
                            onChange={() => {
                              const allChecked = list.every(e => e.checked)
                              setEntities(prev => prev.map(ent => 
                                ent.label === label ? { ...ent, checked: !allChecked } : ent
                              ))
                            }}
                            className="w-4 h-4 rounded text-indigo-600 bg-slate-950 border-slate-800"
                          />
                        </td>
                      </tr>
                      {list.map((ent) => (
                        <tr key={ent.originalIndex} className="border-b border-slate-800">
                          <td className="px-6 py-3 font-mono text-slate-100">{ent.text}</td>
                          <td className="px-6 py-3 text-slate-400">{label}</td>
                          <td className="px-6 py-3 text-center">
                            <input
                              type="checkbox"
                              checked={ent.checked}
                              onChange={() => {
                                setEntities(prev => prev.map((e, idx) => 
                                  idx === ent.originalIndex ? { ...e, checked: !e.checked } : e
                                ))
                              }}
                              className="w-4 h-4 rounded text-indigo-600 bg-slate-950 border-slate-800"
                            />
                          </td>
                        </tr>
                      ))}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>

            {error && <p className="text-sm text-rose-400">{error}</p>}
            {status && <p className="text-sm text-slate-300">{status}</p>}

            <div className="flex gap-3">
              <button
                onClick={handleConfirmMask}
                disabled={status !== ''}
                className="rounded-3xl bg-indigo-500 px-6 py-3 text-sm font-semibold text-white hover:bg-indigo-400 disabled:opacity-60"
              >
                Confirm and Mask
              </button>
              <button
                onClick={() => { setEntities(null); setDocId(null) }}
                className="rounded-3xl border border-slate-800 bg-slate-950 px-6 py-3 text-sm font-semibold text-slate-300 hover:bg-slate-900"
              >
                Cancel
              </button>
            </div>
          </section>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-4xl font-bold text-white">Text Masking</h1>
          <p className="mt-2 text-slate-400">Paste or type text to mask sensitive data</p>
        </div>

        <section className="space-y-6 rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-xl font-semibold text-white">Text Input</h2>
              <p className="mt-2 text-sm text-slate-400">Enter or paste your text content</p>
            </div>
            <div className="flex gap-3">
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                className="rounded-3xl border border-slate-800 bg-slate-950 px-4 py-2 text-sm text-white"
              >
                <option value="standard">Standard</option>
                <option value="secure">Secure</option>
              </select>
              <select
                value={style}
                onChange={(e) => setStyle(e.target.value)}
                disabled={mode === 'secure'}
                className="rounded-3xl border border-slate-800 bg-slate-950 px-4 py-2 text-sm text-white disabled:opacity-50"
              >
                <option value="placeholder">Placeholder</option>
                <option value="partial">Partial</option>
                <option value="full">Full</option>
              </select>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex flex-wrap gap-6">
              <label className="flex items-center gap-2.5 text-sm text-slate-200">
                <input
                  type="radio"
                  value="standard"
                  checked={processingMode === 'standard'}
                  onChange={(e) => setProcessingMode(e.target.value)}
                  className="accent-indigo-500"
                />
                Standard Mode
              </label>
              <label className="flex items-center gap-2.5 text-sm text-slate-200">
                <input
                  type="radio"
                  value="enhanced"
                  checked={processingMode === 'enhanced'}
                  onChange={(e) => setProcessingMode(e.target.value)}
                  className="accent-indigo-500"
                />
                Enhanced AI Mode
              </label>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-semibold text-white">Your Text</label>
              <div className="text-xs text-slate-400 space-x-4">
                <span>Chars: {charCount}</span>
                <span>Words: {wordCount}</span>
                <span>Lines: {lineCount}</span>
              </div>
            </div>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste or type your content here..."
              rows={12}
              className="w-full rounded-3xl border border-slate-800 bg-slate-950 px-4 py-3 text-sm text-slate-100 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 resize-none font-mono"
            />
          </div>

          {error && <p className="text-sm text-rose-400">{error}</p>}
          {status && <p className="text-sm text-slate-300">{status}</p>}

          <button
            onClick={handleAnalyze}
            disabled={!text.trim() || status !== ''}
            className="w-full rounded-3xl bg-indigo-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 hover:bg-indigo-400 disabled:opacity-60"
          >
            Analyze and Mask
          </button>
        </section>
      </div>
    </AppLayout>
  )
}
