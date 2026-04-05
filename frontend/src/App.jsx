import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { Shield, LayoutDashboard, Bell, Zap } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import AlertDetail from './pages/AlertDetail'
import './index.css'

function Sidebar() {
  return (
    <aside className="w-56 flex-shrink-0 flex flex-col bg-dark-800 border-r border-white/5 h-screen sticky top-0">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-white/5">
        <div className="w-8 h-8 rounded-lg bg-accent-blue/20 border border-accent-blue/40 flex items-center justify-center">
          <Shield size={16} className="text-accent-blue" />
        </div>
        <div>
          <p className="text-white font-semibold text-sm leading-none">ThreatAI</p>
          <p className="text-slate-500 text-xs mt-0.5">SOC Engine</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex flex-col gap-1 p-3 flex-1">
        <NavLink to="/" end className={({isActive}) => `flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${isActive ? 'bg-accent-blue/10 text-accent-blue font-medium' : 'text-slate-400 hover:text-white hover:bg-dark-600/50'}`}>
          <LayoutDashboard size={20} />
          Dashboard Feed
        </NavLink>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-white/5">
        <p className="text-xs text-slate-600 font-mono">v1.0.0 · AI Engine</p>
      </div>
    </aside>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/alerts/:id" element={<AlertDetail />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
