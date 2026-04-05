import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, ShieldAlert, CheckCircle, AlertTriangle, Clock, Layers, Brain } from 'lucide-react'

const API = 'http://localhost:8000'

const SEV_CONFIG = {
  CRITICAL: { cls: 'border-severity-critical/40 bg-severity-critical/5', badge: 'badge-critical' },
  HIGH:     { cls: 'border-severity-high/40    bg-severity-high/5',    badge: 'badge-high' },
  MEDIUM:   { cls: 'border-severity-medium/40  bg-severity-medium/5',  badge: 'badge-medium' },
  LOW:      { cls: 'border-severity-low/40     bg-severity-low/5',     badge: 'badge-low' },
}

const THREAT_ICONS = {
  brute_force:         '🔒',
  lateral_movement:    '🕸️',
  data_exfiltration:   '📤',
  command_and_control: '📡',
  false_positive:      '✅',
  benign:              '🟢',
}

function formatThreat(t) {
  return (t || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function ConfidenceBar({ value }) {
  const pct = Math.round(value * 100)
  const color = pct >= 90 ? '#ef4444' : pct >= 70 ? '#f97316' : pct >= 50 ? '#eab308' : '#10b981'
  return (
    <div>
      <div className="flex justify-between text-xs mb-1.5">
        <span className="text-slate-400">Confidence</span>
        <span className="font-semibold" style={{ color }}>{pct}%</span>
      </div>
      <div className="h-2 bg-dark-600 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
    </div>
  )
}

export default function AlertDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [alert, setAlert] = useState(null)
  const [loading, setLoading] = useState(true)
  const [checked, setChecked] = useState({})

  useEffect(() => {
    fetch(`${API}/alerts/${id}`)
      .then(r => r.json())
      .then(d => { setAlert(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [id])

  if (loading) return (
    <div className="flex items-center justify-center h-full p-20 text-slate-500">
      Loading alert…
    </div>
  )
  if (!alert) return (
    <div className="flex flex-col items-center justify-center h-full p-20 gap-4">
      <AlertTriangle className="text-severity-critical" size={32} />
      <p className="text-slate-400">Alert not found.</p>
      <button className="btn-ghost text-sm" onClick={() => navigate('/')}>Back to Dashboard</button>
    </div>
  )

  const sevConf = SEV_CONFIG[alert.severity] || SEV_CONFIG.LOW

  return (
    <div className="p-6 max-w-4xl mx-auto animate-fade-in space-y-5">
      {/* Back */}
      <button className="flex items-center gap-2 text-slate-400 hover:text-white text-sm transition-colors"
        onClick={() => navigate('/')}>
        <ArrowLeft size={14} /> Back to Dashboard
      </button>

      {/* Header card */}
      <div className={`glass border ${sevConf.cls} p-6`}>
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-4">
            <span className="text-4xl">{THREAT_ICONS[alert.threat_type] || '⚠️'}</span>
            <div>
              <h1 className="text-xl font-bold text-white">{formatThreat(alert.threat_type)}</h1>
              {alert.source_ip && (
                <p className="text-slate-400 font-mono text-sm mt-0.5">{alert.source_ip}</p>
              )}
            </div>
          </div>
          <div className="flex flex-col items-end gap-2">
            <span className={sevConf.badge}>{alert.severity}</span>
            <ConfidenceBar value={alert.confidence} />
          </div>
        </div>

        {/* Meta grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mt-5 pt-5 border-t border-white/5">
          <div>
            <p className="text-slate-500 text-xs uppercase tracking-wide">Alert ID</p>
            <p className="text-white font-mono text-xs mt-1 truncate">{alert.alert_id}</p>
          </div>
          <div>
            <p className="text-slate-500 text-xs uppercase tracking-wide">Layers</p>
            <p className="text-white text-sm mt-1">{alert.layers_involved?.join(', ') || '—'}</p>
          </div>
          <div>
            <p className="text-slate-500 text-xs uppercase tracking-wide">Events Correlated</p>
            <p className="text-white text-sm mt-1">{alert.event_ids?.length ?? 0}</p>
          </div>
          <div>
            <p className="text-slate-500 text-xs uppercase tracking-wide">First Seen</p>
            <p className="text-white text-xs font-mono mt-1">{alert.first_seen || '—'}</p>
          </div>
          <div>
            <p className="text-slate-500 text-xs uppercase tracking-wide">Last Seen</p>
            <p className="text-white text-xs font-mono mt-1">{alert.last_seen || '—'}</p>
          </div>
          <div>
            <p className="text-slate-500 text-xs uppercase tracking-wide">Detected At</p>
            <p className="text-white text-xs font-mono mt-1">
              {alert.created_at ? new Date(alert.created_at).toLocaleString() : '—'}
            </p>
          </div>
        </div>
      </div>

      {/* Explanation */}
      <div className="glass p-5">
        <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
          <Brain size={14} className="text-accent-purple" /> AI Explanation
        </h2>
        <p className="text-slate-300 text-sm leading-relaxed bg-dark-600/50 rounded-lg p-4 border border-white/5">
          {alert.explanation || 'No explanation available.'}
        </p>
      </div>

      {/* Playbook */}
      <div className="glass p-5">
        <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <ShieldAlert size={14} className="text-accent-cyan" /> Mitigation Playbook
        </h2>
        <p className="text-slate-500 text-xs mb-4">
          Check off steps as you complete them:
        </p>
        <div className="space-y-2.5">
          {(alert.playbook || []).map((step, i) => (
            <label
              key={i}
              className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all duration-150 ${
                checked[i]
                  ? 'border-accent-green/30 bg-accent-green/5 opacity-60'
                  : 'border-white/5 hover:border-accent-blue/20 hover:bg-dark-600/30'
              }`}
            >
              <input
                type="checkbox"
                className="mt-0.5 accent-green-500 flex-shrink-0"
                checked={!!checked[i]}
                onChange={() => setChecked(prev => ({ ...prev, [i]: !prev[i] }))}
              />
              <span className={`text-sm ${checked[i] ? 'line-through text-slate-500' : 'text-slate-300'}`}>
                <span className="text-slate-600 font-mono text-xs mr-2">{String(i + 1).padStart(2, '0')}.</span>
                {step}
              </span>
            </label>
          ))}
        </div>
        {alert.playbook?.length > 0 && (
          <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between text-xs text-slate-500">
            <span>{Object.values(checked).filter(Boolean).length} / {alert.playbook.length} steps completed</span>
            <div className="w-32 h-1.5 bg-dark-600 rounded-full overflow-hidden">
              <div
                className="h-full bg-accent-green rounded-full transition-all duration-300"
                style={{ width: `${(Object.values(checked).filter(Boolean).length / alert.playbook.length) * 100}%` }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
