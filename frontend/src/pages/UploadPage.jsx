import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api, { attachToken, formatApiError } from '../api.js'
import AppLayout from '../components/AppLayout.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { useResult } from '../context/ResultContext.jsx'

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
  'DRIVERS_LICENSE': "Driver's License",
  'CASE_NUMBER': 'Case/Ticket/Order Number',
  'DATE': 'Date',
  'SIGNATURE': 'Signature',
}

export default function UploadPage() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const { setResult } = useResult()

  const [mode, setMode] = useState('standard')
  const [style, setStyle] = useState('placeholder')
  const [processingMode, setProcessingMode] = useState('standard')
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [docId, setDocId] = useState(null)
  const [entities, setEntities] = useState(null)

  const canUpload = !!file

  const handleUpload = async () => {
    attachToken(token)
    setError('')
    setStatus('Uploading document…')
    try {
      const formData = new FormData()
      formData.append('file', file)
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

      const result = {
        document_id: docId,
        raw_text: file?.name || 'Uploaded file',
        ...mask.data,
        mode
      }
      setResult(result)
      setFile(null)
      setDocId(null)
      setEntities(null)
      setStatus('')
      navigate('/dashboard/results')
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

  if (entities !== null) {
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

    return (
      <AppLayout>
        <div className="space-y-6">
          <div>
            <h1 className="text-4xl font-bold text-white">Upload Document</h1>
            <p className="mt-2 text-slate-400">Review and confirm the entities to mask</p>
          </div>

          <section className="space-y-6 rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
            <h2 className="text-xl font-semibold text-white">Review Detected Entities</h2>
            <p className="text-sm text-slate-400">
              Review the detected sensitive entities below. Customize your selection before masking.
            </p>

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
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-4xl font-bold text-white">Upload Document</h1>
          <p className="mt-2 text-slate-400">Upload a file and choose masking options</p>
        </div>

        <section className="space-y-6 rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-xl font-semibold text-white">Document Input</h2>
              <p className="mt-2 text-sm text-slate-400">Choose how you want to provide your document</p>
            </div>
            <div className="flex gap-3">
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                className="rounded-3xl border border-slate-800 bg-slate-950 px-4 py-2 text-sm text-slate-100 outline-none"
              >
                <option value="standard">Standard Mode</option>
                <option value="secure">Secure Mode</option>
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

          <div className="space-y-4">
            <label className="group flex flex-col items-center justify-center rounded-3xl border-2 border-dashed border-slate-700 bg-slate-950/80 py-12 px-6 transition hover:border-indigo-500 hover:bg-slate-900/50 cursor-pointer">
              <svg className="w-12 h-12 text-slate-400 group-hover:text-indigo-400 transition mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <span className="text-sm font-semibold text-white">Drag & drop your file</span>
              <p className="mt-1 text-sm text-slate-400">or click to browse</p>
              <p className="mt-3 text-xs text-slate-500">Supports PDF, DOCX, TXT</p>
              <input
                type="file"
                accept=".txt,.docx,.pdf"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="sr-only"
              />
            </label>
            {file && (
              <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/30 p-4">
                <p className="text-sm text-emerald-400">✓ Selected: <span className="font-semibold">{file.name}</span></p>
              </div>
            )}
          </div>

          {error && <p className="text-sm text-rose-400">{error}</p>}
          {status && <p className="text-sm text-slate-300">{status}</p>}

          <button
            type="button"
            disabled={!canUpload || status !== ''}
            onClick={handleUpload}
            className="w-full rounded-3xl bg-indigo-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Upload and Analyze
          </button>
        </section>
      </div>
    </AppLayout>
  )
}
