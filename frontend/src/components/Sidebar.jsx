import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, Upload, FileText, Eye, Unlock, History, LogOut } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'

const NAV_ITEMS = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/dashboard/upload', label: 'Upload Document', icon: Upload },
  { path: '/dashboard/text-mask', label: 'Text Masking', icon: FileText },
  { path: '/dashboard/results', label: 'Results', icon: Eye },
  { path: '/dashboard/unmask', label: 'Unmask Document', icon: Unlock },
  { path: '/dashboard/history', label: 'History', icon: History },
]

export default function Sidebar() {
  const { logout } = useAuth()
  const location = useLocation()

  const handleLogout = () => {
    logout()
  }

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 border-r border-slate-800 bg-slate-950 p-6 overflow-y-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">DLP Suite</h1>
        <p className="mt-1 text-sm text-slate-400">Sensitive Data Masking</p>
      </div>

      <nav className="space-y-2 mb-8">
        {NAV_ITEMS.map(item => {
          const Icon = item.icon
          const isActive = location.pathname === item.path
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition ${
                isActive
                  ? 'bg-indigo-500 text-white'
                  : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
              }`}
            >
              <Icon size={20} />
              {item.label}
            </Link>
          )
        })}
      </nav>

      <button
        onClick={handleLogout}
        className="flex w-full items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium text-slate-400 transition hover:bg-slate-900 hover:text-slate-200"
      >
        <LogOut size={20} />
        Logout
      </button>
    </aside>
  )
}
