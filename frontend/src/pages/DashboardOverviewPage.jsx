import React, { useEffect, useState } from 'react'
import api, { attachToken } from '../api.js'
import AppLayout from '../components/AppLayout.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { TrendingUp, FileText, Zap, Shield } from 'lucide-react'

export default function DashboardOverviewPage() {
  const { token } = useAuth()
  const [summary, setSummary] = useState({
    documents_processed: 0,
    average_privacy_score: 0,
    entity_type_breakdown: {},
  })
  const [recentDocuments, setRecentDocuments] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!token) return

    attachToken(token)

    async function loadData() {
      try {
        const dashResponse = await api.get('/documents/dashboard')
        setSummary(dashResponse.data)

        const historyResponse = await api.get('/documents/history', {
          params: { page: 1, page_size: 5 },
        })
        setRecentDocuments(historyResponse.data.documents || [])
      } catch (err) {
        console.error('Failed to load dashboard data:', err)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [token])

  const topEntities = Object.entries(summary.entity_type_breakdown || {})
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5)

  if (loading) {
    return (
      <AppLayout>
        <div className="flex h-screen items-center justify-center text-slate-400">
          Loading dashboard...
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold text-white">Dashboard</h1>
          <p className="mt-2 text-slate-400">Overview of your document masking activity</p>
        </div>

        {/* Key Metrics */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Documents Processed"
            value={summary.documents_processed}
            icon={FileText}
            color="bg-blue-500/10 text-blue-400"
          />
          <MetricCard
            title="Average Privacy Score"
            value={summary.average_privacy_score.toFixed(1)}
            icon={Shield}
            color="bg-emerald-500/10 text-emerald-400"
          />
          <MetricCard
            title="Entity Types Detected"
            value={Object.keys(summary.entity_type_breakdown).length}
            icon={Zap}
            color="bg-amber-500/10 text-amber-400"
          />
          <MetricCard
            title="Total Entities Found"
            value={Object.values(summary.entity_type_breakdown).reduce((a, b) => a + b, 0)}
            icon={TrendingUp}
            color="bg-purple-500/10 text-purple-400"
          />
        </div>

        {/* Top Entities */}
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
            <h2 className="text-lg font-semibold text-white">Top Sensitive Entities</h2>
            <div className="mt-4 space-y-3">
              {topEntities.length > 0 ? (
                topEntities.map(([label, count]) => (
                  <div key={label} className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">{label}</span>
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-32 rounded-full bg-slate-800">
                        <div
                          className="h-full rounded-full bg-indigo-500"
                          style={{
                            width: `${
                              (count / Math.max(...Object.values(summary.entity_type_breakdown))) * 100
                            }%`,
                          }}
                        />
                      </div>
                      <span className="text-sm font-semibold text-white">{count}</span>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-500">No entities detected yet</p>
              )}
            </div>
          </div>

          <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
            <h2 className="text-lg font-semibold text-white">Quick Actions</h2>
            <div className="mt-4 space-y-2">
              <a
                href="/dashboard/upload"
                className="block rounded-lg bg-indigo-500 px-4 py-3 text-center text-sm font-semibold text-white transition hover:bg-indigo-400"
              >
                Upload & Mask Document
              </a>
              <a
                href="/dashboard/text-mask"
                className="block rounded-lg bg-slate-800 px-4 py-3 text-center text-sm font-semibold text-slate-100 transition hover:bg-slate-700"
              >
                Mask Text Content
              </a>
              <a
                href="/dashboard/history"
                className="block rounded-lg bg-slate-800 px-4 py-3 text-center text-sm font-semibold text-slate-100 transition hover:bg-slate-700"
              >
                View History
              </a>
            </div>
          </div>
        </div>

        {/* Recent Documents */}
        <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
          <h2 className="text-lg font-semibold text-white">Recent Documents</h2>
          {recentDocuments.length > 0 ? (
            <div className="mt-4 overflow-x-auto">
              <table className="min-w-full text-left text-sm text-slate-300">
                <thead>
                  <tr>
                    <th className="border-b border-slate-800 px-4 py-3">Filename</th>
                    <th className="border-b border-slate-800 px-4 py-3">Date</th>
                    <th className="border-b border-slate-800 px-4 py-3">Mode</th>
                    <th className="border-b border-slate-800 px-4 py-3">Risk Level</th>
                  </tr>
                </thead>
                <tbody>
                  {recentDocuments.map((doc) => (
                    <tr key={doc.document_id} className="border-b border-slate-800 last:border-b-0">
                      <td className="px-4 py-4 text-slate-100">{doc.filename || 'Text snippet'}</td>
                      <td className="px-4 py-4 text-slate-400">
                        {new Date(doc.created_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-4 text-slate-400">
                        <span className="rounded-full bg-slate-800 px-2 py-1 text-xs font-semibold">
                          {doc.mode}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <span
                          className={`rounded-full px-2 py-1 text-xs font-semibold ${
                            doc.risk_level === 'HIGH'
                              ? 'bg-red-500/20 text-red-400'
                              : doc.risk_level === 'MEDIUM'
                                ? 'bg-amber-500/20 text-amber-400'
                                : 'bg-emerald-500/20 text-emerald-400'
                          }`}
                        >
                          {doc.risk_level}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="mt-4 text-slate-400">No documents processed yet. Start by uploading a document!</p>
          )}
        </div>
      </div>
    </AppLayout>
  )
}

function MetricCard({ title, value, icon: Icon, color }) {
  return (
    <div className={`rounded-3xl border border-slate-800 ${color} p-6`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs uppercase tracking-widest opacity-75">{title}</p>
          <p className="mt-3 text-3xl font-bold">{value}</p>
        </div>
        <Icon size={24} />
      </div>
    </div>
  )
}
