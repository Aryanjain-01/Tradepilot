import { useState, useEffect } from 'react'
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Bar, ReferenceLine, ComposedChart 
} from 'recharts'
import { 
  Activity, Play, CheckCircle2, XCircle, Clock, ShieldAlert
} from 'lucide-react'

const SYMBOLS = ['NIFTY', 'RELIANCE', 'TCS', 'INFY']

export default function TradingDashboard() {
  const [symbol, setSymbol] = useState(SYMBOLS[1])
  const [dataSource, setDataSource] = useState('SAMPLE DATA')
  
  // Market & Strategy State
  const [marketData, setMarketData] = useState<any>(null)
  const [historyData, setHistoryData] = useState<any[]>([])
  const [strategyResult, setStrategyResult] = useState<any>(null)
  
  // Account & Portfolio State
  const [account, setAccount] = useState<any>(null)
  const [positions, setPositions] = useState<any[]>([])
  const [orders, setOrders] = useState<any[]>([])
  const [trades, setTrades] = useState<any[]>([])

  // Risk & Execution State
  const [riskPercentage, setRiskPercentage] = useState(1.0)
  const [stopLoss, setStopLoss] = useState('')
  const [target, setTarget] = useState('')
  const [riskData, setRiskData] = useState<any>(null)
  
  const [isExecuting, setIsExecuting] = useState(false)
  const [pipelineResult, setPipelineResult] = useState<any>(null)
  const [executionError, setExecutionError] = useState<string | null>(null)
  
  // Simulated Price state for P&L updates
  const [simPrice, setSimPrice] = useState<number | ''>('')
  
  const [globalError, setGlobalError] = useState<string | null>(null)

  const fetchPortfolio = async () => {
    try {
      const [accRes, posRes, ordRes, trdRes] = await Promise.all([
        fetch('http://127.0.0.1:8000/api/paper/account'),
        fetch('http://127.0.0.1:8000/api/paper/positions'),
        fetch('http://127.0.0.1:8000/api/paper/orders'),
        fetch('http://127.0.0.1:8000/api/paper/trades')
      ])
      
      setAccount(await accRes.json())
      setPositions(await posRes.json())
      
      const o = await ordRes.json()
      setOrders(Array.isArray(o) ? o.reverse() : [])
      
      const t = await trdRes.json()
      setTrades(Array.isArray(t) ? t.reverse() : [])
      setGlobalError(null)
    } catch (e) {
      console.error("Failed to fetch portfolio", e)
      setGlobalError("Backend unavailable. Please ensure the server is running.")
    }
  }

  const fetchMarketAndStrategy = async () => {
    try {
      const [historyRes, strategyRes] = await Promise.all([
        fetch(`http://127.0.0.1:8000/api/indicators/${symbol}`),
        fetch(`http://127.0.0.1:8000/api/strategy/${symbol}`)
      ])
      
      const hist = await historyRes.json()
      if (Array.isArray(hist) && hist.length > 0) {
        setHistoryData(hist.slice(-100))
        setMarketData(hist[hist.length - 1]) // Latest indicator data
      }
      const strategyData = await strategyRes.json()
      if (!strategyData || strategyData.detail) {
        setStrategyResult(null)
      } else {
        setStrategyResult(strategyData)
      }
      setGlobalError(null)
    } catch (e) {
      console.error("Failed to fetch market/strategy", e)
      setGlobalError("Market data unavailable or invalid symbol.")
    }
  }

  // Calculate risk dynamically when inputs change
  useEffect(() => {
    if (!account || !marketData || !stopLoss || !target || !strategyResult?.signal || strategyResult.signal === 'HOLD') {
      setRiskData(null)
      return
    }

    const sl = parseFloat(stopLoss)
    const tg = parseFloat(target)
    if (isNaN(sl) || isNaN(tg)) return

    const direction = strategyResult.signal === 'BUY' ? 'LONG' : 'SHORT'
    const payload = {
      capital: account.available_cash,
      risk_percentage: riskPercentage,
      entry_price: marketData.close,
      stop_loss: sl,
      target: tg,
      direction
    }

    fetch('http://127.0.0.1:8000/api/risk/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    .then(r => {
      if(r.ok) return r.json()
      throw new Error("Invalid risk bounds")
    })
    .then(data => setRiskData(data))
    .catch(() => setRiskData(null))
  }, [account, marketData, stopLoss, target, riskPercentage, strategyResult])

  useEffect(() => {
    fetchPortfolio()
    fetchMarketAndStrategy()
    // Polling
    const interval = setInterval(() => {
      fetchPortfolio()
    }, 5000)
    return () => clearInterval(interval)
  }, [symbol])

  const handleSimulatePrice = async () => {
    if (!simPrice) return
    try {
      await fetch('http://127.0.0.1:8000/api/paper/market-price', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol, price: simPrice })
      })
      fetchPortfolio()
    } catch (e) {
      console.error(e)
    }
  }

  const handleExecute = async () => {
    setIsExecuting(true)
    setExecutionError(null)
    setPipelineResult(null)
    
    try {
      const payload = {
        symbol,
        risk_percentage: riskPercentage,
        stop_loss: stopLoss ? parseFloat(stopLoss) : null,
        target: target ? parseFloat(target) : null
      }
      
      const res = await fetch('http://127.0.0.1:8000/api/trading/analyze-and-execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Execution failed')
      
      setPipelineResult(data)
      fetchPortfolio() // refresh portfolio
    } catch (e: any) {
      setExecutionError(e.message)
    } finally {
      setIsExecuting(false)
    }
  }

  const handleClosePosition = async (sym: string) => {
    if(!window.confirm(`This will close the paper position for ${sym}. No real money is involved.`)) return
    try {
      await fetch(`http://127.0.0.1:8000/api/paper/positions/${sym}/close`, { method: 'POST' })
      fetchPortfolio()
    } catch (e) {
      console.error(e)
    }
  }

  const renderStatusIcon = (status: boolean | null | undefined, rejected: boolean = false) => {
    if (status === undefined || status === null) return <Clock className="w-5 h-5 text-slate-600" />
    if (rejected) return <XCircle className="w-5 h-5 text-rose-500" />
    if (status) return <CheckCircle2 className="w-5 h-5 text-emerald-500" />
    return <XCircle className="w-5 h-5 text-rose-500" />
  }

  if (globalError) {
    return (
      <div className="p-8 text-center text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg max-w-2xl mx-auto mt-12">
        <h2 className="text-xl font-bold mb-2">Error</h2>
        <p>{globalError}</p>
        <button onClick={() => window.location.reload()} className="mt-4 px-4 py-2 bg-slate-800 text-white rounded hover:bg-slate-700">Retry</button>
      </div>
    )
  }

  if (!account || !marketData) return <div className="p-8 text-center text-slate-400">Loading Dashboard...</div>

  return (
    <div className="space-y-6 pb-12">
      {/* 2. ACCOUNT SUMMARY */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        <div className="bg-slate-900 p-4 rounded-lg border border-slate-800">
          <div className="text-slate-400 text-xs font-bold mb-1 uppercase">Initial Capital</div>
          <div className="text-xl text-white">₹{account.initial_capital.toLocaleString()}</div>
        </div>
        <div className="bg-slate-900 p-4 rounded-lg border border-slate-800">
          <div className="text-slate-400 text-xs font-bold mb-1 uppercase">Available Cash</div>
          <div className="text-xl text-emerald-400">₹{account.available_cash.toLocaleString()}</div>
        </div>
        <div className="bg-slate-900 p-4 rounded-lg border border-slate-800">
          <div className="text-slate-400 text-xs font-bold mb-1 uppercase">Used Capital</div>
          <div className="text-xl text-white">₹{account.used_capital.toLocaleString()}</div>
        </div>
        <div className="bg-slate-900 p-4 rounded-lg border border-slate-800">
          <div className="text-slate-400 text-xs font-bold mb-1 uppercase">Realized P&L</div>
          <div className={`text-xl ${account.realized_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            ₹{account.realized_pnl.toFixed(2)}
          </div>
        </div>
        <div className="bg-slate-900 p-4 rounded-lg border border-slate-800">
          <div className="text-slate-400 text-xs font-bold mb-1 uppercase">Unrealized P&L</div>
          <div className={`text-xl ${account.unrealized_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            ₹{account.unrealized_pnl.toFixed(2)}
          </div>
        </div>
        <div className="bg-slate-900 p-4 rounded-lg border border-slate-800">
          <div className="text-slate-400 text-xs font-bold mb-1 uppercase">Total P&L</div>
          <div className={`text-xl ${account.total_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            ₹{account.total_pnl.toFixed(2)}
          </div>
        </div>
        <div className="bg-slate-900 p-4 rounded-lg border border-slate-800">
          <div className="text-slate-400 text-xs font-bold mb-1 uppercase">Equity</div>
          <div className="text-xl text-blue-400 font-bold">₹{account.equity.toLocaleString()}</div>
        </div>
      </div>

      {/* 3. MARKET OVERVIEW */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-center bg-slate-900 p-4 rounded-lg border border-slate-800">
        <div className="flex items-center gap-4">
          <select 
            className="bg-slate-950 border border-slate-700 text-white rounded p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            value={symbol}
            onChange={e => setSymbol(e.target.value)}
          >
            {SYMBOLS.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <select 
            className="bg-slate-950 border border-slate-700 text-white rounded p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            value={dataSource}
            onChange={e => setDataSource(e.target.value)}
          >
            <option value="SAMPLE DATA">Sample Data</option>
            <option value="ZERODHA MARKET DATA">Zerodha Sandbox</option>
          </select>
          <div className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3 py-1 rounded text-xs font-bold tracking-wider">
            {dataSource}
          </div>
        </div>
        <div className="flex items-center gap-6">
          <div><span className="text-slate-400 text-xs">PRICE</span> <span className="text-white font-bold block">₹{marketData.close}</span></div>
          <div><span className="text-slate-400 text-xs">OPEN</span> <span className="text-white block">₹{marketData.open}</span></div>
          <div><span className="text-slate-400 text-xs">HIGH</span> <span className="text-emerald-400 block">₹{marketData.high}</span></div>
          <div><span className="text-slate-400 text-xs">LOW</span> <span className="text-rose-400 block">₹{marketData.low}</span></div>
          <div><span className="text-slate-400 text-xs">VOL</span> <span className="text-slate-300 block">{marketData.volume}</span></div>
          <div className="flex gap-2">
            <input type="number" step="any" placeholder="Sim Price" className="w-24 bg-slate-950 border border-slate-700 text-white rounded p-1 text-sm outline-none" value={simPrice} onChange={e => setSimPrice(parseFloat(e.target.value) || '')} />
            <button onClick={handleSimulatePrice} className="bg-slate-700 hover:bg-slate-600 text-white px-2 py-1 rounded text-xs font-bold">SET</button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* LEFT COLUMN: CHARTS */}
        <div className="lg:col-span-2 space-y-6">
          {/* 4. PRICE CHART */}
          <div className="bg-slate-900 p-6 rounded-lg shadow-sm border border-slate-800">
            <h3 className="text-slate-300 font-bold mb-4">Price & Moving Averages</h3>
            <div className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={historyData} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />
                  <XAxis dataKey="timestamp" stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} minTickGap={30} />
                  <YAxis domain={['auto', 'auto']} stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `₹${value}`} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', color: '#f8fafc', borderRadius: '8px', border: '1px solid #334155', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.3)' }} />
                  <Line type="monotone" name="Close Price" dataKey="close" stroke="#2563eb" strokeWidth={3} dot={false} activeDot={{ r: 6 }} />
                  <Line type="monotone" name="SMA 20" dataKey="sma_20" stroke="#f59e0b" strokeWidth={2} dot={false} />
                  <Line type="monotone" name="SMA 50" dataKey="sma_50" stroke="#8b5cf6" strokeWidth={2} dot={false} />
                  <Line type="monotone" name="EMA 20" dataKey="ema_20" stroke="#ec4899" strokeWidth={2} dot={false} strokeDasharray="5 5" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 5. RSI */}
            <div className="bg-slate-900 p-6 rounded-lg shadow-sm border border-slate-800">
              <h3 className="text-slate-300 font-bold mb-4 flex justify-between">
                <span>RSI (14)</span>
                <span className="text-blue-400">{marketData.rsi_14?.toFixed(2)}</span>
              </h3>
              <div className="h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={historyData} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />
                    <XAxis dataKey="timestamp" stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} minTickGap={30} />
                    <YAxis domain={[0, 100]} stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
                    <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="3 3" />
                    <ReferenceLine y={30} stroke="#22c55e" strokeDasharray="3 3" />
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', color: '#f8fafc', borderRadius: '8px', border: '1px solid #334155' }} />
                    <Line type="monotone" name="RSI" dataKey="rsi_14" stroke="#0ea5e9" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* 6. MACD */}
            <div className="bg-slate-900 p-6 rounded-lg shadow-sm border border-slate-800">
              <h3 className="text-slate-300 font-bold mb-4 flex justify-between">
                <span>MACD (12, 26, 9)</span>
                <div className="text-sm">
                  <span className="text-blue-400 mr-2">M: {marketData.macd_line?.toFixed(2)}</span>
                  <span className="text-orange-400">S: {marketData.macd_signal?.toFixed(2)}</span>
                </div>
              </h3>
              <div className="h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={historyData} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />
                    <XAxis dataKey="timestamp" stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} minTickGap={30} />
                    <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', color: '#f8fafc', borderRadius: '8px', border: '1px solid #334155' }} />
                    <Bar name="Histogram" dataKey="macd_histogram" fill="#9ca3af" opacity={0.5} />
                    <Line name="MACD Line" type="monotone" dataKey="macd_line" stroke="#2563eb" strokeWidth={2} dot={false} />
                    <Line name="Signal Line" type="monotone" dataKey="macd_signal" stroke="#f97316" strokeWidth={2} dot={false} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: ACTION & TRACKING */}
        <div className="space-y-6">
          {/* 7. STRATEGY PANEL */}
          <div className="bg-slate-900 p-6 rounded-lg shadow-sm border border-slate-800">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-500" />
              Strategy Signal
            </h3>
            {strategyResult ? (
              <div className={`p-6 rounded-lg flex flex-col items-center justify-center border-2 border-dashed ${strategyResult.signal === 'BUY' ? 'border-emerald-500/50 bg-emerald-500/10' : strategyResult.signal === 'SELL' ? 'border-rose-500/50 bg-rose-500/10' : 'border-slate-600 bg-slate-800'}`}>
                <div className={`text-4xl font-black tracking-widest ${strategyResult.signal === 'BUY' ? 'text-emerald-400' : strategyResult.signal === 'SELL' ? 'text-rose-400' : 'text-slate-400'}`}>
                  {strategyResult.signal}
                </div>
                {strategyResult.conditions && (
                  <div className="mt-4 text-sm text-slate-300 font-medium">
                    Reason: {Object.entries(strategyResult.conditions).map(([k,v]) => `${k.toUpperCase()} ${v ? 'PASSED' : 'FAILED'}`).join(', ')}
                  </div>
                )}
              </div>
            ) : <div className="text-slate-500 text-center py-4">Evaluating...</div>}
          </div>

          {/* 8. RISK PANEL */}
          <div className="bg-slate-900 p-6 rounded-lg shadow-sm border border-slate-800">
            <h3 className="text-lg font-bold text-white mb-4">Risk Setup</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Risk %</label>
                <input type="number" step="0.1" className="w-full bg-slate-950 border border-slate-700 text-white rounded p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none" value={riskPercentage} onChange={e => setRiskPercentage(parseFloat(e.target.value) || 0)} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Stop Loss (₹)</label>
                  <input type="number" className="w-full bg-slate-950 border border-slate-700 text-white rounded p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none" value={stopLoss} onChange={e => setStopLoss(e.target.value)} />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Target (₹)</label>
                  <input type="number" className="w-full bg-slate-950 border border-slate-700 text-white rounded p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none" value={target} onChange={e => setTarget(e.target.value)} />
                </div>
              </div>
              
              {/* Risk Summary */}
              {riskData && (
                <div className="bg-slate-950 p-3 rounded border border-slate-800 grid grid-cols-2 gap-2 text-xs mt-2">
                  <div className="text-slate-400">Max Risk: <span className="text-white block font-medium">₹{riskData.maximum_risk}</span></div>
                  <div className="text-slate-400">Position: <span className="text-blue-400 block font-bold">{riskData.position_size} Shares</span></div>
                  <div className="text-slate-400">Loss: <span className="text-rose-400 block font-medium">₹{riskData.potential_loss}</span></div>
                  <div className="text-slate-400">Profit: <span className="text-emerald-400 block font-medium">₹{riskData.potential_profit}</span></div>
                  <div className="col-span-2 text-slate-400 border-t border-slate-800 pt-2 mt-1">R:R Ratio: <span className="text-emerald-300 font-bold ml-1">{riskData.risk_reward_ratio}</span></div>
                </div>
              )}
            </div>
            
            {/* 9. ALGO TRADE ACTION */}
            <div className="mt-6">
              <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-2 mb-3 rounded flex items-center justify-center gap-2 font-bold text-xs shadow-sm">
                <ShieldAlert className="w-4 h-4" /> PAPER TRADING ONLY
              </div>
              <button 
                onClick={handleExecute}
                disabled={isExecuting || !stopLoss || !target}
                className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded shadow-sm transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Play className="w-4 h-4" /> ANALYZE & EXECUTE PAPER TRADE
              </button>
            </div>
          </div>

          {/* 10. PIPELINE STATUS */}
          <div className="bg-slate-900 p-6 rounded-lg shadow-sm border border-slate-800">
            <h3 className="text-lg font-bold text-white mb-4">Pipeline Status</h3>
            {executionError && <div className="p-3 mb-4 bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded text-sm">{executionError}</div>}
            
            {!pipelineResult && !executionError && !isExecuting && (
              <div className="text-slate-500 text-sm py-4 text-center">Execute pipeline to view trace.</div>
            )}
            
            {(isExecuting || pipelineResult) && (
              <div className="space-y-3 text-sm">
                <div className="flex justify-between items-center bg-slate-950 p-2 rounded border border-slate-800">
                  <span className="text-slate-300">MARKET DATA</span>
                  {renderStatusIcon(pipelineResult ? pipelineResult.current_price > 0 : null)}
                </div>
                <div className="flex justify-between items-center bg-slate-950 p-2 rounded border border-slate-800">
                  <span className="text-slate-300">INDICATORS & STRATEGY</span>
                  <div className="flex items-center gap-2">
                    {pipelineResult?.signal && <span className={`font-bold ${pipelineResult.signal === 'HOLD' ? 'text-slate-400' : 'text-blue-400'}`}>{pipelineResult.signal}</span>}
                    {renderStatusIcon(pipelineResult ? !!pipelineResult.signal : null)}
                  </div>
                </div>
                <div className="flex justify-between items-center bg-slate-950 p-2 rounded border border-slate-800">
                  <span className="text-slate-300">RISK VALIDATION</span>
                  {renderStatusIcon(pipelineResult ? (pipelineResult.status === 'FILLED' || (pipelineResult.status === 'REJECTED' && pipelineResult.risk)) : null, pipelineResult?.status === 'REJECTED' && !pipelineResult?.risk)}
                </div>
                <div className="flex justify-between items-center bg-slate-950 p-2 rounded border border-slate-800">
                  <span className="text-slate-300">POSITION SIZING</span>
                  <div className="flex items-center gap-2">
                    {pipelineResult?.risk?.position_size > 0 && <span className="text-slate-300 font-bold">{pipelineResult.risk.position_size} SHARES</span>}
                    {renderStatusIcon(pipelineResult ? !!pipelineResult.risk : null)}
                  </div>
                </div>
                <div className="flex justify-between items-center bg-slate-950 p-2 rounded border border-slate-800">
                  <span className="text-slate-300">PAPER EXECUTION</span>
                  {renderStatusIcon(pipelineResult ? pipelineResult.status === 'FILLED' : null, pipelineResult?.status === 'REJECTED')}
                </div>
                
                {/* 11 & 12: HOLD & REJECTED STATES */}
                {pipelineResult?.status === 'REJECTED' && (
                  <div className="p-3 bg-rose-500/10 text-rose-400 rounded border border-rose-500/20 font-bold">
                    TRADE REJECTED: <span className="font-medium text-rose-300">{pipelineResult.reason}</span>
                  </div>
                )}
                {pipelineResult?.status === 'NO_TRADE' && (
                  <div className="p-3 bg-slate-800 text-slate-300 rounded border border-slate-700 font-bold">
                    HOLD: <span className="font-medium text-slate-400">{pipelineResult.reason} - {pipelineResult.strategy_reason}</span>
                  </div>
                )}
                {pipelineResult?.status === 'FILLED' && (
                  <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded border border-emerald-500/20 font-bold flex justify-between">
                    <span>POSITION OPENED</span>
                    <span>{pipelineResult.execution?.order_id}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* BOTTOM SECTION: PORTFOLIO TABLES */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* 13. OPEN POSITIONS */}
        <div className="bg-slate-900 p-6 rounded-lg shadow-sm border border-slate-800">
          <h3 className="text-lg font-bold text-white mb-4">Open Positions</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950 text-slate-400 border-b-2 border-slate-800 uppercase">
                <tr>
                  <th className="p-3">Symbol</th>
                  <th className="p-3">Side</th>
                  <th className="p-3 text-right">Qty</th>
                  <th className="p-3 text-right">Entry</th>
                  <th className="p-3 text-right">P&L</th>
                  <th className="p-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {positions.length === 0 ? (
                  <tr><td colSpan={6} className="p-6 text-center text-slate-500">No open positions</td></tr>
                ) : (
                  positions.map((p, i) => (
                    <tr key={i} className="border-b border-slate-800 hover:bg-slate-800/50">
                      <td className="p-3 font-medium text-white">{p.symbol}</td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded text-xs font-bold ${p.side === 'LONG' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
                          {p.side}
                        </span>
                      </td>
                      <td className="p-3 text-right font-medium">{p.quantity}</td>
                      <td className="p-3 text-right text-slate-400">₹{p.entry_price.toFixed(2)}</td>
                      <td className={`p-3 text-right font-bold ${p.unrealized_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        ₹{p.unrealized_pnl.toFixed(2)}
                      </td>
                      <td className="p-3 text-right">
                        <button onClick={() => handleClosePosition(p.symbol)} className="text-xs bg-slate-700 hover:bg-rose-600 text-white px-3 py-1 rounded font-bold transition-colors">CLOSE</button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* 14. ORDER HISTORY */}
        <div className="bg-slate-900 p-6 rounded-lg shadow-sm border border-slate-800">
          <h3 className="text-lg font-bold text-white mb-4">Order History</h3>
          <div className="overflow-x-auto h-64 overflow-y-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950 text-slate-400 border-b-2 border-slate-800 uppercase sticky top-0">
                <tr>
                  <th className="p-3">Order ID</th>
                  <th className="p-3">Symbol</th>
                  <th className="p-3">Side</th>
                  <th className="p-3 text-right">Qty</th>
                  <th className="p-3 text-right">Price</th>
                  <th className="p-3 text-right">Status</th>
                </tr>
              </thead>
              <tbody>
                {orders.length === 0 ? (
                  <tr><td colSpan={6} className="p-6 text-center text-slate-500">No recent orders</td></tr>
                ) : (
                  orders.map((o, i) => (
                    <tr key={i} className="border-b border-slate-800 hover:bg-slate-800/50">
                      <td className="p-3 text-xs text-slate-500">{o.order_id}</td>
                      <td className="p-3 font-medium text-white">{o.symbol}</td>
                      <td className={`p-3 font-bold ${o.side === 'BUY' ? 'text-emerald-400' : 'text-rose-400'}`}>{o.side}</td>
                      <td className="p-3 text-right font-medium">{o.quantity}</td>
                      <td className="p-3 text-right">₹{o.filled_price > 0 ? o.filled_price.toFixed(2) : o.requested_price?.toFixed(2)}</td>
                      <td className="p-3 text-right">
                        <span className={`text-xs font-bold ${o.status === 'FILLED' ? 'text-emerald-400' : 'text-slate-400'}`}>{o.status}</span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* 15. TRADE HISTORY */}
        <div className="bg-slate-900 p-6 rounded-lg shadow-sm border border-slate-800 lg:col-span-2">
          <h3 className="text-lg font-bold text-white mb-4">Trade History</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950 text-slate-400 border-b-2 border-slate-800 uppercase">
                <tr>
                  <th className="p-3">Trade ID</th>
                  <th className="p-3">Symbol</th>
                  <th className="p-3">Side</th>
                  <th className="p-3 text-right">Qty</th>
                  <th className="p-3 text-right">Entry</th>
                  <th className="p-3 text-right">Exit</th>
                  <th className="p-3 text-right">Realized P&L</th>
                  <th className="p-3 text-right">Closed At</th>
                </tr>
              </thead>
              <tbody>
                {trades.length === 0 ? (
                  <tr><td colSpan={8} className="p-6 text-center text-slate-500">No completed trades yet</td></tr>
                ) : (
                  trades.map((t, i) => (
                    <tr key={i} className="border-b border-slate-800 hover:bg-slate-800/50">
                      <td className="p-3 text-xs text-slate-500">{t.id}</td>
                      <td className="p-3 font-medium text-white">{t.symbol}</td>
                      <td className="p-3 font-bold">{t.side}</td>
                      <td className="p-3 text-right">{t.quantity}</td>
                      <td className="p-3 text-right text-slate-400">₹{t.entry_price.toFixed(2)}</td>
                      <td className="p-3 text-right text-slate-400">₹{t.exit_price.toFixed(2)}</td>
                      <td className={`p-3 text-right font-bold ${t.realized_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        ₹{t.realized_pnl.toFixed(2)}
                      </td>
                      <td className="p-3 text-right text-xs text-slate-400">{new Date(t.closed_at).toLocaleString()}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  )
}
