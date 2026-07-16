import React from 'react'
import Sidebar from './Sidebar.jsx'

export default function AppLayout({ children }) {
  return (
    <div className="flex h-screen bg-slate-950">
      <Sidebar />
      <main className="flex-1 overflow-y-auto pl-64">
        <div className="min-h-screen p-8">
          {children}
        </div>
      </main>
    </div>
  )
}
