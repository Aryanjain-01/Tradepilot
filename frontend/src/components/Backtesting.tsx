import { useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Play, TrendingUp, ShieldAlert, Activity, Clock } from 'lucide-react'

const SYMBOLS = ['RELIANCE', 'NIFTY', 'TCS', 'INFY']

export default function Backtesting() {
  const [symbol, setSymbol] = useState(SYMBOLS[0])
  const [capital, setCapital] = useState(100000)
  const [riskPct, setRiskPct] = useState(1.0)
  const [stopLossPct, setStopLossPct] = useState(2.0)
  const [targetPct, setTargetPct] = useState(4.0)

  const [isRunning, setIsRunning] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const handleRunBacktest = async () => {
    setIsRunning(true)
    setError(null)
    setResult(null)

    try {
      const payload = {
        symbol,
        initial_capital: capital,
        risk_percentage: riskPct,
        stop_loss_percentage: stopLossPct,
        target_percentage: targetPct
      }

      const res = await fetch('/api/backtest/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Backtest failed')

      setResult(data)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setIsRunning(false)
    }
  }

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center gap-2 mb-2 text-rose-400 bg-rose-500/10 border border-rose-500/20 px-4 py-2 rounded-lg font-bold">
        <ShieldAlert className="w-5 h-5" /> HISTORICAL SIMULATION • NO REAL MONEY
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* LEFT PANEL: CONFIGURATION */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-slate-900 p-6 rounded-lg shadow-sm border border-slate-800">
            <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <Activity className="w-5 h-5 text-purple-500" />
              Backtest Setup
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Symbol</label>
                <select 
                  className="w-full bg-slate-950 border border-slate-700 text-white rounded p-2 text-sm focus:ring-2 focus:ring-purple-500 outline-none"
                  value={symbol}
                  onChange={e => setSymbol(e.target.value)}
                >
                  {SYMBOLS.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Initial Capital (₹)</label>
                <input 
                  type="number" 
                  className="w-full bg-slate-950 border border-slate-700 text-white rounded p-2 text-sm focus:ring-2 focus:ring-purple-500 outline-none"
                  value={capital}
                  onChange={e => setCapital(parseFloat(e.target.value) || 0)}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Risk per Trade (%)</label>
                <input 
                  type="number" step="0.1"
                  className="w-full bg-slate-950 border border-slate-700 text-white rounded p-2 text-sm focus:ring-2 focus:ring-purple-500 outline-none"
                  value={riskPct}
                  onChange={e => setRiskPct(parseFloat(e.target.value) || 0)}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Stop Loss (%)</label>
                  <input 
                    type="number" step="0.1"
                    className="w-full bg-slate-950 border border-slate-700 text-white rounded p-2 text-sm focus:ring-2 focus:ring-purple-500 outline-none"
                    value={stopLossPct}
                    onChange={e => setStopLossPct(parseFloat(e.target.value) || 0)}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Target (%)</label>
                  <input 
                    type="number" step="0.1"
                    className="w-full bg-slate-950 border border-slate-700 text-white rounded p-2 text-sm focus:ring-2 focus:ring-purple-500 outline-none"
                    value={targetPct}
                    onChange={e => setTargetPct(parseFloat(e.target.value) || 0)}
                  />
                </div>
              </div>

              <button 
                onClick={handleRunBacktest}
                disabled={isRunning}
                className="w-full mt-4 bg-purple-600 hover:bg-purple-500 text-white font-bold py-3 rounded shadow-sm transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isRunning ? <Clock className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                {isRunning ? 'SIMULATING...' : 'RUN BACKTEST'}
              </button>
            </div>
            
            {error && (
              <div className="mt-4 p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded text-sm">
                {error}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT PANEL: RESULTS */}
        <div className="lg:col-span-3 space-y-6">
          {!result && !isRunning && (
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-12 text-center text-slate-500 flex flex-col items-center justify-center h-full">
              <TrendingUp className="w-16 h-16 mb-4 text-slate-700" />
              <h2 className="text-xl font-bold text-slate-400 mb-2">Ready to Simulate</h2>
              <p className="max-w-md">Configure your strategy parameters on the left and run a historical backtest to evaluate performance without risking real capital.</p>
            </div>
          )}

          {isRunning && (
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-12 text-center text-purple-500 flex flex-col items-center justify-center h-full">
              <Activity className="w-16 h-16 mb-4 animate-pulse" />
              <h2 className="text-xl font-bold mb-2">Simulating Trades...</h2>
              <p className="text-slate-400">Processing chronological historical data.</p>
            </div>
          )}

          {result && (
            <>
              {/* METRICS ROW */}
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <div className="bg-slate-900 p-4 rounded-lg border border-slate-800">
                  <div className="text-slate-400 text-xs font-bold mb-1 uppercase">Final Equity</div>
                  <div className={`text-xl font-bold ${result.final_equity >= result.initial_capital ? 'text-emerald-400' : 'text-rose-400'}`}>
                    ₹{result.final_equity.toLocaleString()}
                  </div>
                </div>
                <div className="bg-slate-900 p-4 rounded-lg border border-slate-800">
                  <div className="text-slate-400 text-xs font-bold mb-1 uppercase">Total P&L</div>
                  <div className={`text-xl ${result.total_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    ₹{result.total_pnl.toLocaleString()}
                  </div>
                </div>
                <div className="bg-slate-900 p-4 rounded-lg border border-slate-800">
                  <div className="text-slate-400 text-xs font-bold mb-1 uppercase">Return</div>
                  <div className={`text-xl ${result.return_percentage >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {result.return_percentage}%
                  </div>
                </div>
                <div className="bg-slate-900 p-4 rounded-lg border border-slate-800">
                  <div className="text-slate-400 text-xs font-bold mb-1 uppercase">Max Drawdown</div>
                  <div className="text-xl text-rose-400">
                    -{result.max_drawdown}%
                  </div>
                </div>
                <div className="bg-slate-900 p-4 rounded-lg border border-slate-800">
                  <div className="text-slate-400 text-xs font-bold mb-1 uppercase">Win Rate</div>
                  <div className="text-xl text-blue-400">
                    {result.win_rate}%
                  </div>
                </div>
                <div className="bg-slate-900 p-4 rounded-lg border border-slate-800">
                  <div className="text-slate-400 text-xs font-bold mb-1 uppercase">Profit Factor</div>
                  <div className="text-xl text-blue-400">
                    {result.profit_factor}
                  </div>
                </div>
              </div>

              {/* EQUITY CURVE */}
              <div className="bg-slate-900 p-6 rounded-lg shadow-sm border border-slate-800">
                <h3 className="text-slate-300 font-bold mb-4">Portfolio Equity Curve</h3>
                <div className="h-[350px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={result.equity_curve} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />
                      <XAxis dataKey="timestamp" stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} minTickGap={50} />
                      <YAxis domain={['auto', 'auto']} stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `₹${value}`} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0f172a', color: '#f8fafc', borderRadius: '8px', border: '1px solid #334155' }}
                        formatter={(value: any) => [`₹${value}`, "Equity"]}
                      />
                      <Line type="stepAfter" dataKey="equity" stroke="#a855f7" strokeWidth={2} dot={false} activeDot={{ r: 6 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* TRADES LOG */}
              <div className="bg-slate-900 p-6 rounded-lg shadow-sm border border-slate-800">
                <h3 className="text-slate-300 font-bold mb-4 flex justify-between items-center">
                  <span>Trade History ({result.total_trades} trades)</span>
                  <span className="text-xs text-slate-500 font-normal">Wins: {result.winning_trades} • Losses: {result.losing_trades}</span>
                </h3>
                <div className="overflow-x-auto h-96 overflow-y-auto">
                  <table className="w-full text-left text-sm text-slate-300">
                    <thead className="bg-slate-950 text-slate-400 border-b-2 border-slate-800 uppercase sticky top-0">
                      <tr>
                        <th className="p-3">Trade ID</th>
                        <th className="p-3">Side</th>
                        <th className="p-3 text-right">Qty</th>
                        <th className="p-3">Entry Date</th>
                        <th className="p-3 text-right">Entry</th>
                        <th className="p-3">Exit Date</th>
                        <th className="p-3 text-right">Exit</th>
                        <th className="p-3">Reason</th>
                        <th className="p-3 text-right">P&L</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.trades.length === 0 ? (
                        <tr><td colSpan={9} className="p-6 text-center text-slate-500">No trades executed during backtest.</td></tr>
                      ) : (
                        result.trades.map((t: any, i: number) => (
                          <tr key={i} className="border-b border-slate-800 hover:bg-slate-800/50">
                            <td className="p-3 text-xs text-slate-500">{t.trade_id}</td>
                            <td className={`p-3 font-bold ${t.side === 'LONG' ? 'text-emerald-400' : 'text-rose-400'}`}>{t.side}</td>
                            <td className="p-3 text-right">{t.quantity}</td>
                            <td className="p-3 text-xs">{t.entry_timestamp}</td>
                            <td className="p-3 text-right">₹{t.entry_price.toFixed(2)}</td>
                            <td className="p-3 text-xs">{t.exit_timestamp}</td>
                            <td className="p-3 text-right">₹{t.exit_price.toFixed(2)}</td>
                            <td className="p-3 text-xs">
                              <span className={`px-2 py-1 rounded font-bold ${
                                t.exit_reason === 'TARGET' ? 'bg-emerald-500/10 text-emerald-400' :
                                t.exit_reason === 'STOP_LOSS' ? 'bg-rose-500/10 text-rose-400' :
                                'bg-slate-800 text-slate-400'
                              }`}>
                                {t.exit_reason.replace('_', ' ')}
                              </span>
                            </td>
                            <td className={`p-3 text-right font-bold ${t.net_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                              ₹{t.net_pnl.toFixed(2)}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

            </>
          )}

        </div>
      </div>
    </div>
  )
}
