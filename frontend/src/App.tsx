import { useState, useEffect } from 'react'
import { TrendingUp, LayoutDashboard, History } from 'lucide-react'
import TradingDashboard from './components/TradingDashboard'
import Backtesting from './components/Backtesting'

function App() {
  const [healthStatus, setHealthStatus] = useState<string>('checking')
  const [activeTab, setActiveTab] = useState<'dashboard' | 'backtest'>('dashboard')

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/health')
      .then(res => res.json())
      .then(data => setHealthStatus(data.status))
      .catch(() => setHealthStatus('offline'))
  }, [])

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans">
      <nav className="bg-slate-900 border-b border-slate-800 px-6 py-4 flex justify-between items-center">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <TrendingUp className="text-blue-500" />
            <h1 className="text-xl font-bold text-white tracking-tight">TradePilot</h1>
          </div>
          
          <div className="flex bg-slate-800/50 rounded-lg p-1 border border-slate-800 ml-4">
            <button 
              onClick={() => setActiveTab('dashboard')}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'dashboard' ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'}`}
            >
              <LayoutDashboard className="w-4 h-4" />
              LIVE DASHBOARD
            </button>
            <button 
              onClick={() => setActiveTab('backtest')}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'backtest' ? 'bg-purple-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'}`}
            >
              <History className="w-4 h-4" />
              BACKTESTING
            </button>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-slate-400">Backend Status:</span>
            <span className={`px-2 py-1 rounded text-xs font-bold ${healthStatus === 'ok' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>
              {healthStatus.toUpperCase()}
            </span>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {activeTab === 'dashboard' ? (
          <TradingDashboard />
        ) : (
          <Backtesting />
        )}
      </main>
    </div>
  )
}

export default App
