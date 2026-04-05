import { useState, useEffect, useRef, useCallback } from 'react'
import { AlertTriangle, ShieldCheck, Activity, Layers, RefreshCw, Wifi } from 'lucide-react'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import AlertCard from '../components/AlertCard'
import ThreatTimeline from '../components/ThreatTimeline'

const API = 'http://localhost:8000'

const SEV_COLORS = {
  CRITICAL: '#ef4444', HIGH: '#f97316', MEDIUM: '#eab308', LOW: '#10b981'
}

function StatCard({ icon: Icon, label, value, color = 'text-white', sub }) {
  return (
    <div className="stat-card">
      <div className="flex items-center justify-between">
        <span className="text-slate-500 text-xs font-medium uppercase tracking-wide">{label}</span>
        <Icon size={14} className={color} />
      </div>
      <p className={`text-3xl font-bold mt-1 ${color}`}>{value ?? '—'}</p>
      {sub && <p className="text-slate-600 text-xs mt-1">{sub}</p>}
    </div>
  )
}

function buildTimeline(alerts) {
  if (!alerts.length) return []
  const buckets = {}
  alerts.forEach(a => {
    const t = new Date(a.created_at)
    const key = `${t.getHours()}:${String(t.getMinutes()).padStart(2, '0')}`
    if (!buckets[key]) buckets[key] = { time: key, CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 }
    buckets[key][a.severity] = (buckets[key][a.severity] || 0) + (a.count || 1)
  })
  return Object.values(buckets).slice(-20)
}

function groupAlerts(alerts) {
  const map = new Map()
  alerts.forEach(a => {
    const key = `${a.threat_type}|${a.source_ip}`
    if (!map.has(key)) {
      map.set(key, { ...a, count: 1 })
    } else {
      const existing = map.get(key)
      existing.count += (a.count || 1)
      if (new Date(a.created_at) > new Date(existing.created_at)) {
        existing.created_at = a.created_at
      }
    }
  })
  return Array.from(map.values()).sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
}

export default function Dashboard() {
  const [alerts, setAlerts] = useState([])
  const [stats, setStats] = useState(null)
  const [liveAlerts, setLiveAlerts] = useState([])
  const [sseStatus, setSseStatus] = useState('connecting')
  const [loading, setLoading] = useState(true)
  const esRef = useRef(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [aRes, sRes] = await Promise.all([
        fetch(`${API}/alerts/?limit=50`),
        fetch(`${API}/alerts/stats`),
      ])
      const aData = await aRes.json()
      const sData = await sRes.json()
      setAlerts(aData.alerts || [])
      setStats(sData)
    } catch (e) {
      console.error('Failed to fetch alerts', e)
    } finally {
      setLoading(false)
    }
  }, [])

  // Initial load
  useEffect(() => { fetchData() }, [fetchData])

  // SSE live feed
  useEffect(() => {
    const es = new EventSource(`${API}/alerts/live`)
    esRef.current = es
    es.onopen = () => setSseStatus('connected')
    es.onerror = () => setSseStatus('error')
    es.onmessage = (e) => {
      try {
        const alert = JSON.parse(e.data)
        setLiveAlerts(prev => [alert, ...prev].slice(0, 100))
        setStats(prev => prev ? {
          ...prev,
          total: (prev.total || 0) + 1,
          by_severity: {
            ...prev.by_severity,
            [alert.severity]: ((prev.by_severity || {})[alert.severity] || 0) + 1,
          },
          by_threat_type: {
            ...prev.by_threat_type,
            [alert.threat_type]: ((prev.by_threat_type || {})[alert.threat_type] || 0) + 1,
          }
        } : prev)
      } catch {}
    }
    return () => es.close()
  }, [])

  const allAlertsMap = new Map()
  ;[...liveAlerts, ...alerts].forEach(a => {
    if (!allAlertsMap.has(a.alert_id)) allAlertsMap.set(a.alert_id, a)
  })
  const allAlerts = Array.from(allAlertsMap.values())
  const groupedAlerts = groupAlerts(allAlerts).slice(0, 200)
  const timeline = buildTimeline(allAlerts)

  const pieData = stats ? Object.entries(stats.by_threat_type || {}).map(([name, value]) => ({
    name: name.replace(/_/g, ' '),
    value,
  })) : []

  const THREAT_COLORS = ['#3b82f6','#ef4444','#f97316','#8b5cf6','#10b981','#06b6d4']

  return (
    <div className="p-6 space-y-6 animate-fade-in">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">SOC Dashboard</h1>
          <p className="text-slate-500 text-sm mt-0.5">Real-time threat monitoring &amp; detection</p>
        </div>
        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-2 text-xs px-3 py-1.5 rounded-full border ${
            sseStatus === 'connected'
              ? 'border-accent-green/30 text-accent-green bg-accent-green/10'
              : 'border-severity-critical/30 text-severity-critical bg-severity-critical/10'
          }`}>
            <Wifi size={11} className={sseStatus === 'connected' ? 'animate-pulse' : ''} />
            {sseStatus === 'connected' ? 'Live' : 'Disconnected'}
          </div>
          <button onClick={fetchData} className="btn-ghost flex items-center gap-2 text-xs py-1.5">
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={AlertTriangle} label="Total Alerts" value={stats?.total ?? 0} color="text-white" />
        <StatCard icon={AlertTriangle} label="Critical" value={stats?.by_severity?.CRITICAL ?? 0}
          color="text-severity-critical" sub="Immediate action required" />
        <StatCard icon={Activity} label="High" value={stats?.by_severity?.HIGH ?? 0}
          color="text-severity-high" sub="Investigate soon" />
        <StatCard icon={ShieldCheck} label="Live Feed" value={liveAlerts.length}
          color="text-accent-blue" sub="Events this session" />
      </div>

      {/* Timeline + Pie */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 glass p-5">
          <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Activity size={14} className="text-accent-blue" /> Threat Timeline
          </h2>
          <ThreatTimeline data={timeline} />
        </div>

        <div className="glass p-5">
          <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Layers size={14} className="text-accent-purple" /> By Threat Type
          </h2>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={45} outerRadius={75}
                  dataKey="value" paddingAngle={3}>
                  {pieData.map((_, i) => (
                    <Cell key={i} fill={THREAT_COLORS[i % THREAT_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#161b27', border: '1px solid #252d3d', borderRadius: 8, fontSize: 12 }}
                  labelStyle={{ color: '#94a3b8' }}
                  itemStyle={{ color: '#e2e8f0' }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-44 flex items-center justify-center text-slate-600 text-sm">
              No data yet
            </div>
          )}
          <div className="space-y-1.5 mt-2">
            {pieData.map((d, i) => (
              <div key={d.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{ background: THREAT_COLORS[i % THREAT_COLORS.length] }} />
                  <span className="text-slate-400 capitalize">{d.name}</span>
                </div>
                <span className="text-white font-semibold">{d.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Live alert feed */}
      <div className="glass p-5">
        <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <AlertTriangle size={14} className="text-severity-critical" />
          Alert Feed
          {liveAlerts.length > 0 && (
            <span className="badge badge-critical ml-1">{liveAlerts.length} live</span>
          )}
        </h2>
        {groupedAlerts.length === 0 ? (
          <div className="text-slate-600 text-sm text-center py-10">
            No alerts yet — run a simulation to see detections appear here in real-time.
          </div>
        ) : (
          <div className="space-y-2 max-h-[480px] overflow-y-auto pr-1">
            {groupedAlerts.map(a => (
              <AlertCard key={a.alert_id} alert={a} compact />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
