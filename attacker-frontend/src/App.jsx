import { useState } from 'react'
import { Terminal, Crosshair, Play, Check, AlertTriangle, ShieldOff } from 'lucide-react'

const API = 'http://localhost:8000'

const ATTACKS = [
  {
    id: 'brute_force',
    label: 'Brute Force / Cred Stuffing',
    desc: 'Simulate high-velocity failed logins. Triggers network / application tier flags.',
  },
  {
    id: 'lateral_movement',
    label: 'Lateral Movement',
    desc: 'Internal pivot targeting internal subnets via SMB port scanning.',
  },
  {
    id: 'data_exfiltration',
    label: 'Data Exfiltration',
    desc: 'Massive outbound HTTPS transfers bypassing standard egress gates.',
  },
  {
    id: 'command_and_control',
    label: 'C2 Beaconing',
    desc: 'Periodic, perfectly spaced DNS lookups mimicking implant callbacks.',
  },
  {
    id: 'false_positive',
    label: 'Nessus Scanner (FP)',
    desc: 'Noisy authorized scanner. Tests Blue Team FP thresholding.',
  },
]

function ResultTerminal({ result }) {
  if (!result) return null
  const isOk = result.status === 'simulated'
  
  return (
    <div className="terminal-box bg-dark-900 mt-6 p-4 font-mono text-xs border border-white/5 shadow-none">
      <div className="flex items-center gap-2 mb-3 pb-2 border-b border-white/5 text-slate-500 uppercase tracking-widest text-[10px]">
        {isOk ? <Check size={12} className="text-neon-green" /> : <AlertTriangle size={12} className="text-red-500" />}
        <span>Payload Execution Log</span>
      </div>
      
      {isOk ? (
        <div className="space-y-1 text-neon-green/80">
          <p>[+] Establishing generic relay connection...</p>
          <p>[-] Connected to {API}</p>
          <p className="mt-2 text-white">[*] INJECTING PAYLOAD: {result.attack_type.toUpperCase()}</p>
          <p>[+] Parameters: intensity={result.events_injected}, target_src={result.source_ip}</p>
          <p className="mt-2 text-neon-green opacity-70">➔ {result.message}</p>
          <p className="mt-2 animate-blink">_</p>
        </div>
      ) : (
        <div className="space-y-1 text-red-500/80">
          <p>[!] TRANSMISSION FAILED</p>
          <p>[-] {result.message || 'Unknown network interruption'}</p>
        </div>
      )}
    </div>
  )
}

export default function App() {
  const [selected, setSelected] = useState('brute_force')
  const [intensity, setIntensity] = useState(50)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const runAttack = async () => {
    setLoading(true)
    setResult(null)
    try {
      const res = await fetch(`${API}/simulate/attack`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ attack_type: selected, intensity }),
      })
      const data = await res.json()
      setResult(data)
    } catch (e) {
      setResult({ status: 'error', message: e.message })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-dark-900 p-6 sm:p-10 relative">
      <div className="scanline" />
      
      <div className="max-w-3xl mx-auto space-y-8 relative z-10">
        
        {/* Header */}
        <div className="border-b border-red-500/20 pb-4">
          <div className="flex items-center gap-3">
            <ShieldOff className="text-red-500" size={32} />
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
              PROJECT HACKSAW
            </h1>
          </div>
          <p className="text-slate-500 text-sm mt-2 tracking-wide">
            Automated Threat Simulation & Payload Injection Framework v1.0
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* Module Selection */}
          <div className="terminal-box p-5 space-y-4">
            <h2 className="text-red-400 text-sm uppercase tracking-widest font-bold flex items-center gap-2 mb-4">
              <Terminal size={14} /> Available Modules
            </h2>
            
            <div className="space-y-2">
              {ATTACKS.map(atk => (
                <button
                  key={atk.id}
                  onClick={() => setSelected(atk.id)}
                  className={`w-full text-left p-3 rounded-sm border transition-all duration-100 ${
                    selected === atk.id 
                    ? 'border-red-500 bg-red-500/10 shadow-[inset_4px_0_0_#ff3333]' 
                    : 'border-white/5 bg-dark-900 hover:border-white/20'
                  }`}
                >
                  <div className="flex justify-between items-center mb-1">
                    <span className={`text-sm tracking-wide font-mono ${selected === atk.id ? 'text-red-400' : 'text-slate-300'}`}>
                      &gt; {atk.label}
                    </span>
                    {selected === atk.id && <span className="animate-blink text-red-500">_</span>}
                  </div>
                  <p className="text-slate-500 text-[10px] uppercase leading-relaxed tracking-wider ml-4">
                    {atk.desc}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* Config & Launch */}
          <div className="space-y-6">
            <div className="terminal-box p-5">
              <h2 className="text-white text-sm uppercase tracking-widest font-bold flex items-center gap-2 mb-5">
                <Crosshair size={14} className="text-red-400" /> Deployment Config
              </h2>

              <div className="space-y-6">
                <div>
                  <div className="flex justify-between text-xs tracking-widest uppercase text-slate-400 mb-2">
                    <span>Intensity (Events)</span>
                    <span className="text-red-400 font-bold">{intensity}</span>
                  </div>
                  <input
                    type="range"
                    min={10} max={500} step={10}
                    value={intensity}
                    onChange={e => setIntensity(Number(e.target.value))}
                    className="w-full accent-red-500 h-1 bg-dark-900 rounded-lg appearance-none cursor-pointer"
                  />
                  <p className="text-[10px] text-slate-500 mt-2 uppercase tracking-wide">
                    WARNING: High intensity may trigger threshold traps sooner.
                  </p>
                </div>

                <button
                  onClick={runAttack}
                  disabled={loading}
                  className="btn-attack w-full uppercase tracking-widest text-sm"
                >
                  {loading ? 'Transmitting Data...' : (
                    <>
                      <Play size={16} fill="currentColor" /> Initialize Attack
                    </>
                  )}
                </button>
              </div>
            </div>

            <ResultTerminal result={result} />
          </div>
        </div>

      </div>
    </div>
  )
}
