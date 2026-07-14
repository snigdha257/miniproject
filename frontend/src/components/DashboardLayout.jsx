import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function DashboardLayout({ children }) {
  const navigate = useNavigate()
  const { email, signOut } = useAuth()

  const handleLogout = () => {
    signOut()
    navigate('/', { replace: true })
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/90 px-6 py-4 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-indigo-400">Privacy Hub</p>
            <h1 className="text-xl font-semibold text-white">Data Protection Dashboard</h1>
          </div>
          <div className="flex items-center gap-4 text-sm text-slate-300">
            <span>{email}</span>
            <button
              onClick={handleLogout}
              className="rounded-full bg-slate-800 px-4 py-2 text-slate-200 transition hover:bg-slate-700"
            >
              Logout
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
    </div>
  )
}
