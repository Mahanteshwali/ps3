import { useState, useEffect, useRef } from 'react'
import { Terminal, Copy, ShieldAlert, Cpu, Activity, Server, Database, Shield, Zap, Globe, AlertTriangle } from 'lucide-react'

// ----------------------------------------------------------------------
// DATA
// ----------------------------------------------------------------------
const MODULES = [
  {
    id: 'brute_force',
    type: 'NET/APP',
    label: 'Brute Force / Cred Stuffing',
    desc: 'Simulate high-velocity failed logins against authentication gates. Triggers network and application tier correlation flags.',
    nodes: ['attacker', 'firewall', 'target', 'db']
  },
  {
    id: 'lateral_movement',
    type: 'SMB/RPC',
    label: 'Lateral Movement',
    desc: 'Internal pivot targeting isolated subnets via active SMB port scanning and mapped drive enumeration.',
    nodes: ['attacker', 'firewall', 'target']
  },
  {
    id: 'data_exfiltration',
    type: 'HTTPS',
    label: 'Data Exfiltration',
    desc: 'Massive outbound HTTPS transfers bypassing standard egress gates, simulating DB dumping.',
    nodes: ['attacker', 'target', 'db']
  },
  {
    id: 'command_and_control',
    type: 'DNS/HTTP',
    label: 'C2 Beaconing',
    desc: 'Periodic, perfectly spaced DNS lookups mimicking implant callbacks to external infrastructure.',
    nodes: ['attacker', 'dns', 'target']
  },
  {
    id: 'false_positive',
    type: 'SCAN',
    label: 'Nessus Flood (FP)',
    desc: 'Noisy authorized vulnerability scanner. Tests Blue Team False Positive suppression thresholding.',
    nodes: ['attacker', 'firewall', 'siem']
  },
]

const VECTOR_TOGGLES = [
  'Auth Bypass', 'Payload Inject', 'Header Spoof', 'DNS Tunnel'
]

// ----------------------------------------------------------------------
// UI COMPONENTS
// ----------------------------------------------------------------------

function Topbar() {
  return (
    <div className="h-14 border-b border-white/10 flex items-center justify-between px-6 select-none bg-surface/50">
      <div className="flex items-center gap-4">
        {/* Geometric Logo */}
        <div className="relative w-6 h-6 flex justify-center items-center">
          <div className="absolute w-4 h-4 border border-cyan rotate-45 transform origin-center" />
          <div className="absolute w-4 h-4 border border-red rotate-[75deg] transform origin-center" />
        </div>
        <span className="font-display text-xl tracking-wider text-slate-200">HACKSAW</span>
        <div className="h-4 w-px bg-white/10 mx-2" />
        <nav className="flex gap-6 text-xs uppercase tracking-widest font-bold">
          <span className="text-cyan border-b-2 border-cyan pb-1 translate-y-0.5 cursor-pointer">Simulate</span>
          <span className="text-slate-600 hover:text-slate-400 cursor-pointer">Payloads</span>
          <span className="text-slate-600 hover:text-slate-400 cursor-pointer">Config</span>
        </nav>
      </div>
      <div className="flex items-center gap-2">
        <span className="flex h-2 w-2 relative">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan"></span>
        </span>
        <span className="text-[10px] font-bold tracking-widest text-cyan uppercase">Live Link</span>
      </div>
    </div>
  )
}

function StatCard({ label, value, colorClass }) {
  return (
    <div className="panel p-3 flex flex-col justify-between">
      <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider pb-2">{label}</span>
      <span className={`text-2xl font-mono ${colorClass}`}>{value}</span>
    </div>
  )
}

// ----------------------------------------------------------------------
// MAIN APP
// ----------------------------------------------------------------------

export default function App() {
  const [selected, setSelected] = useState(MODULES[0])
  const [intensity, setIntensity] = useState(50)
  const [apiGateway, setApiGateway] = useState('http://localhost:8000')
  const [targetIP, setTargetIP] = useState('10.0.0.50')
  const [vectors, setVectors] = useState(new Set(['Payload Inject']))
  
  // Firing State
  const [armed, setArmed] = useState(false)
  const [running, setRunning] = useState(false)
  
  // Stats
  const [eventsFired, setEventsFired] = useState(0)
  const [detections, setDetections] = useState(0)
  const [eps, setEps] = useState(0)
  
  // Logs
  const [logs, setLogs] = useState([{ id: 0, raw: '* SESSION INITIALIZED', type: 'info' }])

  const armTimer = useRef(null)
  
  // Reset Stats on module change
  useEffect(() => {
    if (!running) {
      setEventsFired(0)
      setDetections(0)
      setEps(0)
      setLogs([{ id: Date.now(), raw: `* LOADED MODULE [${selected.id}]`, type: 'info' }])
    }
  }, [selected])

  const toggleVector = (v) => {
    const next = new Set(vectors)
    if (next.has(v)) next.delete(v)
    else next.add(v)
    setVectors(next)
  }

  // Two-stage fire handler
  const handleFireClick = () => {
    if (running) return
    if (!armed) {
      setArmed(true)
      armTimer.current = setTimeout(() => setArmed(false), 3000)
    } else {
      clearTimeout(armTimer.current)
      setArmed(false)
      executeAttack()
    }
  }

  const executeAttack = async () => {
    setRunning(true)
    setEventsFired(0)
    setDetections(0)
    setLogs([{ id: Date.now(), raw: `* EXECUTING MODULE: ${selected.id.toUpperCase()}`, type: 'info' }])
    
    const rate = Math.max(1, Math.floor(intensity / 8))
    setEps(rate)

    // Trigger API call to backend (don't await so frontend runs concurrently)
    fetch(`${apiGateway}/simulate/attack`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ attack_type: selected.id, intensity, source_ip: '10.0.8.42', target_ip: targetIP }),
    }).catch(() => {})

    let currentEvents = 0
    let logCounter = 0

    // Visual simulation loop
    const runInterval = setInterval(() => {
      currentEvents += rate
      if (currentEvents >= intensity) currentEvents = intensity
      setEventsFired(currentEvents)
      
      // Stochastically trigger fake detection count just for visual flavor on attacker side
      if (Math.random() < 0.15) {
        setDetections(prev => prev + 1)
        setLogs(prev => [...prev, { id: ++logCounter, raw: '! PROXIMITY ALERT: Defense signatures triggered', type: 'warn' }])
      } else {
        setLogs(prev => [...prev, { id: ++logCounter, raw: `+ INJECTED ${rate} PAYLOADS @ ${targetIP}`, type: 'success' }])
      }

      if (currentEvents >= intensity) {
        clearInterval(runInterval)
        setTimeout(() => {
          setRunning(false)
          setEps(0)
          setLogs(prev => [...prev, { id: ++logCounter, raw: `* MODULE EXECUTION COMPLETE (${intensity} fired)`, type: 'info' }])
        }, 500)
      }
    }, 1000)
  }

  return (
    <div className="min-h-screen bg-dark flex flex-col font-mono text-sm">
      <Topbar />

      {/* 3-Column Layout */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 p-6">
        
        {/* LEFT COLUMN: Modules */}
        <div className="lg:col-span-3 flex flex-col gap-3">
          <h2 className="text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-1">Targeting Modules</h2>
          {MODULES.map(m => (
            <button
              key={m.id}
              disabled={running}
              onClick={() => setSelected(m)}
              className={`panel text-left p-4 transition-all ${
                selected.id === m.id ? 'panel-active' : 'hover:border-white/20'
              } ${running ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              <div className="flex justify-between items-start mb-2">
                <span className={`font-bold tracking-wide ${selected.id === m.id ? 'text-white' : 'text-slate-300'}`}>
                  {m.label}
                </span>
                <span className={`text-[9px] px-1.5 py-0.5 rounded uppercase font-bold tracking-wider ${
                  selected.id === m.id ? 'bg-cyan/20 text-cyan border border-cyan/30' : 'bg-white/5 text-slate-500 border border-white/5'
                }`}>
                  {m.type}
                </span>
              </div>
              {selected.id === m.id && (
                <p className="text-xs text-slate-400 leading-relaxed mt-3 border-t border-white/5 pt-3">
                  {m.desc}
                </p>
              )}
            </button>
          ))}
        </div>

        {/* CENTER COLUMN: Topology & Stats */}
        <div className="lg:col-span-6 flex flex-col gap-6 relative">
          
          <h2 className="text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-[-12px]">Attack Surface Topology</h2>
          
          <div className="panel flex-1 relative overflow-hidden flex items-center justify-center min-h-[400px] border-b-0 pb-10">
            {/* Grid bg */}
            <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: 'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)', backgroundSize: '30px 30px' }} />
            
            {/* Run Animation Overlay */}
            {running && <div className="absolute inset-0 scanner-sweep pointer-events-none z-10" />}

            {/* SVG Network */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
              <defs>
                <linearGradient id="cyanLine" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#00d4c8" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#00d4c8" stopOpacity="0.2" />
                </linearGradient>
              </defs>
              
              {/* Lines rendering logic (highly simplified for visual effect) */}
              <line x1="15%" y1="50%" x2="45%" y2="50%" stroke={running && selected.nodes.includes('firewall') ? "url(#cyanLine)" : "#ffffff10"} strokeWidth="2" strokeDasharray="4 4" className={running ? "animate-pulse" : ""} />
              <line x1="45%" y1="50%" x2="80%" y2="50%" stroke={running && selected.nodes.includes('target') ? "url(#cyanLine)" : "#ffffff10"} strokeWidth="2" strokeDasharray="4 4" className={running ? "animate-pulse" : ""} />
              <line x1="45%" y1="50%" x2="60%" y2="20%" stroke={running && selected.nodes.includes('dns') ? "url(#cyanLine)" : "#ffffff10"} strokeWidth="2" strokeDasharray="4 4" />
              <line x1="80%" y1="50%" x2="80%" y2="85%" stroke={running && selected.nodes.includes('db') ? "url(#cyanLine)" : "#ffffff10"} strokeWidth="2" strokeDasharray="4 4" />
              <line x1="45%" y1="50%" x2="25%" y2="85%" stroke={running && selected.nodes.includes('siem') ? "url(#cyanLine)" : "#ffffff10"} strokeWidth="2" strokeDasharray="4 4" />
            </svg>

            {/* Nodes */}
            <div className="absolute flex justify-between w-full h-full p-10 z-10">
              {/* Attacker */}
              <div className="absolute top-1/2 left-[10%] -translate-y-1/2 flex flex-col items-center gap-2">
                <div className={`w-12 h-12 rounded border-2 flex items-center justify-center bg-dark ${running ? 'border-red animate-pulse text-red' : 'border-cyan text-cyan'}`}>
                  <Terminal size={20} />
                </div>
                <span className={`text-[9px] uppercase tracking-widest font-bold ${running ? 'text-red' : 'text-cyan'}`}>Attacker</span>
              </div>
              
              {/* DNS */}
              <div className="absolute top-[20%] left-[55%] -translate-y-1/2 flex flex-col items-center gap-2 opacity-80">
                <div className={`w-10 h-10 rounded border-1 flex items-center justify-center bg-dark transition-colors ${running && selected.nodes.includes('dns') ? 'border-red text-red' : 'border-white/20 text-slate-500'}`}>
                  <Globe size={16} />
                </div>
                <span className="text-[9px] uppercase tracking-widest text-slate-500">Route/DNS</span>
              </div>

              {/* Firewall */}
              <div className="absolute top-1/2 left-[40%] -translate-y-1/2 flex flex-col items-center gap-2">
                <div className={`w-12 h-12 rounded border-1 flex items-center justify-center bg-dark transition-colors ${running && selected.nodes.includes('firewall') ? 'border-red text-red' : 'border-white/20 text-slate-500'}`}>
                  <Shield size={20} />
                </div>
                <span className="text-[9px] uppercase tracking-widest text-slate-500">Egress/FW</span>
              </div>

              {/* SIEM */}
              <div className="absolute top-[85%] left-[25%] -translate-y-1/2 flex flex-col items-center gap-2 opacity-80">
                <div className={`w-10 h-10 rounded border-1 flex items-center justify-center bg-dark transition-colors ${running && selected.nodes.includes('siem') ? 'border-red text-red animate-pulse' : 'border-white/20 text-slate-500'}`}>
                  <Activity size={16} />
                </div>
                <span className="text-[9px] uppercase tracking-widest text-slate-500">SOC/SIEM</span>
              </div>

              {/* Target Server */}
              <div className="absolute top-1/2 left-[75%] -translate-y-1/2 flex flex-col items-center gap-2">
                <div className={`w-14 h-14 rounded border-2 flex items-center justify-center bg-dark transition-colors ${running && selected.nodes.includes('target') ? 'border-red text-red bg-red/5 animate-pulse' : 'border-white/20 text-slate-400'}`}>
                  <Server size={24} />
                </div>
                <span className="text-[9px] uppercase tracking-widest text-slate-300">DC-01</span>
              </div>

              {/* DB */}
              <div className="absolute top-[85%] left-[75%] -translate-y-1/2 flex flex-col items-center gap-2 opacity-80">
                <div className={`w-10 h-10 rounded border-1 flex items-center justify-center bg-dark transition-colors ${running && selected.nodes.includes('db') ? 'border-red text-red' : 'border-white/20 text-slate-500'}`}>
                  <Database size={16} />
                </div>
                <span className="text-[9px] uppercase tracking-widest text-slate-500">SQL/Store</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-6">
            <StatCard label="Events Fired" value={running || eventsFired > 0 ? eventsFired : '—'} colorClass="text-cyan" />
            <StatCard label="Detections Triggered" value={running || detections > 0 ? detections : '—'} colorClass="text-slate-400" />
            <StatCard label="Events / Sec" value={running ? eps : '—'} colorClass="text-red" />
          </div>

        </div>

        {/* RIGHT COLUMN: Config & Log */}
        <div className="lg:col-span-3 flex flex-col gap-6">
          
          <h2 className="text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-[-12px]">Deployment Config</h2>
          
          {/* Controls */}
          <div className="panel p-5 space-y-6">
            <div>
              <div className="flex justify-between items-center mb-2 text-xs uppercase tracking-widest font-bold">
                <span className="text-slate-500">Intensity</span>
                <span className={intensity > 120 ? 'text-amber' : 'text-slate-300'}>{intensity}x</span>
              </div>
              <input type="range" min="10" max="200" step="10" value={intensity} disabled={running} onChange={(e) => setIntensity(Number(e.target.value))} className="w-full appearance-none bg-dark h-1 border-y border-white/10 rounded-none accent-cyan cursor-none hover:cursor-none" style={{ cursor: 'crosshair' }} />
              {intensity > 120 && (
                <div className="flex items-center gap-1.5 mt-2 text-amber text-[9px] uppercase tracking-widest font-bold">
                  <AlertTriangle size={10} /> High detection risk
                </div>
              )}
            </div>

            <div>
              <label className="block text-[10px] uppercase font-bold tracking-widest text-slate-500 mb-2">API Gateway URL</label>
              <input type="text" value={apiGateway} disabled={running} onChange={(e) => setApiGateway(e.target.value)} className="w-full bg-dark border border-white/10 focus:border-cyan text-cyan outline-none p-2.5 text-xs font-mono disabled:opacity-50" />
            </div>

            <div>
              <label className="block text-[10px] uppercase font-bold tracking-widest text-slate-500 mb-2">Target Endpoint Domain/IP</label>
              <input type="text" value={targetIP} disabled={running} onChange={(e) => setTargetIP(e.target.value)} className="w-full bg-dark border border-white/10 focus:border-cyan outline-none text-slate-300 p-2.5 text-xs font-mono disabled:opacity-50" />
            </div>

            <div>
              <label className="block text-[10px] uppercase font-bold tracking-widest text-slate-500 mb-2">Vector Toggles</label>
              <div className="grid grid-cols-2 gap-2">
                {VECTOR_TOGGLES.map(v => (
                  <button key={v} disabled={running} onClick={() => toggleVector(v)} className={`border px-2 py-2 text-[9px] uppercase tracking-widest font-bold transition-colors ${vectors.has(v) ? 'border-cyan text-cyan bg-cyan/5' : 'border-white/5 text-slate-500 hover:border-white/20'}`}>
                    {v}
                  </button>
                ))}
              </div>
            </div>

            <button disabled={running} onClick={handleFireClick} className={`w-full btn-fire ${armed ? 'btn-fire-armed' : ''} ${running ? '!border-white/5 !text-slate-700 cursor-not-allowed' : ''}`}>
              {!armed && !running && 'Arm System'}
              {armed && !running && 'Confirm Execute'}
              {running && 'Deploying...'}
            </button>
          </div>

          <h2 className="text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-[-12px] mt-2">Execution Log</h2>
          
          {/* Output Log */}
          <div className="panel flex-1 min-h-[250px] p-4 font-mono text-[11px] overflow-y-auto leading-relaxed flex flex-col items-start select-text border-t-2 border-t-cyan">
            {logs.map((l) => (
              <div key={l.id} className="animate-log-in flex gap-2 w-full">
                <span className="text-slate-600">[{new Date().toISOString().split('T')[1].slice(0,8)}]</span>
                <span className={`${l.type === 'success' ? 'text-cyan' : l.type === 'warn' ? 'text-amber' : l.type === 'error' ? 'text-red' : 'text-slate-400'}`}>
                  {l.raw}
                </span>
              </div>
            ))}
            <div className="mt-1 flex gap-2">
              <span className="text-slate-600">[{new Date().toISOString().split('T')[1].slice(0,8)}]</span>
              <span className="w-2 h-3.5 bg-cyan animate-blink inline-block translate-y-[2px]" />
            </div>
          </div>

        </div>

      </div>
    </div>
  )
}
