import { useNavigate } from 'react-router-dom'
import { AlertTriangle, Shield, Clock, Layers } from 'lucide-react'

const SEVERITY_CONFIG = {
  CRITICAL: { cls: 'badge-critical', dot: 'bg-severity-critical', pulse: true },
  HIGH:     { cls: 'badge-high',     dot: 'bg-severity-high',     pulse: false },
  MEDIUM:   { cls: 'badge-medium',   dot: 'bg-severity-medium',   pulse: false },
  LOW:      { cls: 'badge-low',      dot: 'bg-severity-low',      pulse: false },
}

const THREAT_ICONS = {
  brute_force:          '🔒',
  lateral_movement:     '🕸️',
  data_exfiltration:    '📤',
  command_and_control:  '📡',
  false_positive:       '✅',
  benign:               '🟢',
}

function formatTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function formatThreat(t) {
  return t.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

export default function AlertCard({ alert, compact = false }) {
  const navigate = useNavigate()
  const sev = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.LOW

  return (
    <div
      className="glass-hover p-4 cursor-pointer animate-slide-in group"
      onClick={() => navigate(`/alerts/${alert.alert_id}`)}
      role="button"
      aria-label={`View alert: ${formatThreat(alert.threat_type)}`}
    >
      <div className="flex items-start justify-between gap-3">
        {/* Icon + Type */}
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-xl flex-shrink-0" title={alert.threat_type}>
            {THREAT_ICONS[alert.threat_type] || '⚠️'}
          </span>
          <div className="min-w-0">
            <p className="text-white font-semibold text-sm truncate group-hover:text-accent-blue transition-colors">
              {formatThreat(alert.threat_type)}
            </p>
            {alert.source_ip && (
              <p className="text-slate-500 text-xs font-mono mt-0.5">{alert.source_ip}</p>
            )}
          </div>
        </div>

        {/* Severity badge */}
        <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
          <span className={sev.cls}>
            {sev.pulse && (
              <span className={`inline-block w-1.5 h-1.5 rounded-full ${sev.dot} animate-pulse`} />
            )}
            {alert.severity}
          </span>
          <span className="text-slate-500 text-xs font-mono">
            {Math.round(alert.confidence * 100)}% conf.
          </span>
        </div>
      </div>

      {/* Explanation preview */}
      {!compact && alert.explanation && (
        <p className="text-slate-400 text-xs mt-3 leading-relaxed line-clamp-2">
          {alert.explanation}
        </p>
      )}

      {/* Footer meta */}
      <div className="flex items-center gap-4 mt-3 text-slate-600 text-xs">
        <span className="flex items-center gap-1">
          <Clock size={10} />
          {formatTime(alert.created_at)}
        </span>
        {alert.layers_involved?.length > 0 && (
          <span className="flex items-center gap-1">
            <Layers size={10} />
            {alert.layers_involved.join(', ')}
          </span>
        )}
      </div>
    </div>
  )
}
