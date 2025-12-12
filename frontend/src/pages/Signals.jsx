import { useState, useEffect } from 'react'
import api from '../api'
import { SignalPerformanceGrid } from '../components/SignalPerformance'
import { SignalsSkeleton, EmptyState, AdBanner, SignalDisclaimer } from '../components/ui'

const Signals = ({ t, lang }) => {
  const [signals, setSignals] = useState({})
  const [stats, setStats] = useState({ total: 0, buy: 0, sell: 0, hold: 0 })
  const [signalPerf, setSignalPerf] = useState(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')
  const [timeframe, setTimeframe] = useState('1d')
  const [lastUpdate, setLastUpdate] = useState('')
  const [expanded, setExpanded] = useState(null)

  // Timeframe değiştiğinde yeniden yükle
  useEffect(() => {
    loadSignals()
    loadPerformance()
  }, [timeframe])

  // Her 60 saniyede bir güncelle
  useEffect(() => {
    const interval = setInterval(loadSignals, 60000)
    return () => clearInterval(interval)
  }, [timeframe])

  const loadPerformance = async () => {
    try {
      const resp = await api.get('/api/signal-stats?days=30')
      if (resp.ok) {
        const data = await resp.json()
        setSignalPerf(data)
      }
    } catch (err) {
      console.error('Performance error:', err)
    }
  }

  const loadSignals = async () => {
    try {
      setLoading(true)
      
      // Timeframe parametresi ile API çağrısı
      const resp = await api.get(`/api/signals?timeframe=${timeframe}&limit=500`)
      
      if (resp.ok) {
        const data = await resp.json()
        
        // API'den gelen veriyi işle
        if (data.signals) {
          // Eğer signals bir array ise, objeye çevir
          if (Array.isArray(data.signals)) {
            const signalsObj = {}
            data.signals.forEach(s => {
              signalsObj[s.symbol] = s
            })
            setSignals(signalsObj)
          } else {
            setSignals(data.signals)
          }
        }
        
        // Stats'ı API'den al veya hesapla
        if (data.stats) {
          setStats({
            total: data.count || data.total || Object.keys(data.signals || {}).length,
            buy: (data.stats.STRONG_BUY || 0) + (data.stats.BUY || 0),
            hold: data.stats.HOLD || 0,
            sell: (data.stats.STRONG_SELL || 0) + (data.stats.SELL || 0)
          })
        }
        
        setLastUpdate(data.updated_at || data.updated || '')
      }
    } catch (err) {
      console.error('Signals error:', err)
    } finally {
      setLoading(false)
    }
  }

  const getSignalColor = (signal) => {
    if (!signal) return 'bg-gray-500'
    const s = signal.toUpperCase()
    if (s.includes('GÜÇLÜ AL') || s === 'STRONG_BUY') return 'bg-emerald-500'
    if (s.includes('AL') || s === 'BUY') return 'bg-green-500'
    if (s.includes('GÜÇLÜ SAT') || s === 'STRONG_SELL') return 'bg-red-600'
    if (s.includes('SAT') || s === 'SELL') return 'bg-red-500'
    return 'bg-yellow-500'
  }

  const getSignalText = (signal) => {
    if (!signal) return 'BEKLE'
    const s = signal.toUpperCase()
    if (s.includes('GÜÇLÜ AL') || s === 'STRONG_BUY') return 'GÜÇLÜ AL'
    if (s.includes('AL') || s === 'BUY') return 'AL'
    if (s.includes('GÜÇLÜ SAT') || s === 'STRONG_SELL') return 'GÜÇLÜ SAT'
    if (s.includes('SAT') || s === 'SELL') return 'SAT'
    return 'BEKLE'
  }

  const getSignalIcon = (signal) => {
    if (!signal) return '⏸️'
    const s = signal.toUpperCase()
    if (s.includes('GÜÇLÜ AL') || s === 'STRONG_BUY') return '🚀'
    if (s.includes('AL') || s === 'BUY') return '📈'
    if (s.includes('GÜÇLÜ SAT') || s === 'STRONG_SELL') return '🔻'
    if (s.includes('SAT') || s === 'SELL') return '📉'
    return '⏸️'
  }

  const formatPrice = (price) => {
    if (!price) return '$0'
    if (price >= 1000) return `$${price.toLocaleString('en-US', { maximumFractionDigits: 0 })}`
    if (price >= 1) return `$${price.toFixed(2)}`
    if (price >= 0.01) return `$${price.toFixed(4)}`
    return `$${price.toFixed(8)}`
  }

  const getRiskColor = (risk) => {
    if (!risk) return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
    const r = risk.toUpperCase()
    if (r === 'LOW' || r === 'DÜŞÜK') return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
    if (r === 'HIGH' || r === 'YÜKSEK') return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
    return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
  }

  const getRiskText = (risk) => {
    if (!risk) return 'MEDIUM'
    const r = risk.toUpperCase()
    if (r === 'LOW') return 'DÜŞÜK'
    if (r === 'HIGH') return 'YÜKSEK'
    if (r === 'MEDIUM') return 'ORTA'
    return risk
  }

  // Timeframe seçenekleri - 1m eklendi
  const timeframes = [
    { key: '1d', label: '1 Gün' },
    { key: '1w', label: '1 Hafta' },
    { key: '1m', label: '1 Ay' },
    { key: '3m', label: '3 Ay' },
    { key: '6m', label: '6 Ay' },
    { key: '1y', label: '1 Yıl' },
  ]

  // Filter signals
  const filteredSignals = Object.entries(signals)
    .filter(([symbol, data]) => {
      if (search && !symbol.toLowerCase().includes(search.toLowerCase())) return false
      
      const signal = data.signal_tr || data.signal || ''
      const s = signal.toUpperCase()
      
      if (filter === 'buy' && !s.includes('AL') && s !== 'BUY' && s !== 'STRONG_BUY') return false
      if (filter === 'sell' && !s.includes('SAT') && s !== 'SELL' && s !== 'STRONG_SELL') return false
      if (filter === 'hold' && !s.includes('BEKLE') && s !== 'HOLD') return false
      
      return true
    })
    .sort((a, b) => {
      // Market cap'e göre sırala (varsayılan)
      const mcapA = a[1].market_cap || 0
      const mcapB = b[1].market_cap || 0
      return mcapB - mcapA
    })

  // Use skeleton loader instead of spinner
  if (loading && Object.keys(signals).length === 0) {
    return <SignalsSkeleton />
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            💡 {lang === 'tr' ? 'Yatırım Sinyalleri' : 'Investment Signals'}
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {lang === 'tr' ? 'Tüm coinler için AI destekli öneriler' : 'AI-powered recommendations for all coins'}
          </p>
          {lastUpdate && (
            <p className="text-xs text-gray-400 mt-1">
              Son güncelleme: {new Date(lastUpdate).toLocaleTimeString('tr-TR')}
            </p>
          )}
        </div>
        {loading && (
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
        )}
      </div>

      {/* Timeframe Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {timeframes.map(tf => (
          <button
            key={tf.key}
            onClick={() => setTimeframe(tf.key)}
            className={`px-4 py-2 rounded-lg font-medium whitespace-nowrap transition ${
              timeframe === tf.key
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            {tf.label}
          </button>
        ))}
      </div>

      {/* Timeframe Warning - Same data notice */}
      {timeframe !== '1d' && (
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700/30 rounded-lg px-3 py-2 flex items-center gap-2 text-xs">
          <span className="text-amber-500">ℹ️</span>
          <span className="text-amber-700 dark:text-amber-400">
            {lang === 'tr'
              ? 'Not: Şu an tüm zaman dilimleri aynı günlük veriyi kullanmaktadır. Farklı periyot analizleri yakında eklenecek.'
              : 'Note: All timeframes currently use the same daily data. Different period analysis coming soon.'}
          </span>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-4 gap-3">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-3 text-center shadow">
          <div className="text-xl font-bold text-gray-900 dark:text-white">{stats.total}</div>
          <div className="text-xs text-gray-500">Toplam</div>
        </div>
        <div className="bg-green-50 dark:bg-green-900/30 rounded-xl p-3 text-center shadow">
          <div className="text-xl font-bold text-green-600">{stats.buy}</div>
          <div className="text-xs text-green-600">AL</div>
        </div>
        <div className="bg-yellow-50 dark:bg-yellow-900/30 rounded-xl p-3 text-center shadow">
          <div className="text-xl font-bold text-yellow-600">{stats.hold}</div>
          <div className="text-xs text-yellow-600">BEKLE</div>
        </div>
        <div className="bg-red-50 dark:bg-red-900/30 rounded-xl p-3 text-center shadow">
          <div className="text-xl font-bold text-red-600">{stats.sell}</div>
          <div className="text-xs text-red-600">SAT</div>
        </div>
      </div>

      {/* Signal Performance (30 days) - NEW 4-CARD GRID */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SignalPerformanceGrid stats={signalPerf} />
      </div>

      {/* Search & Filter */}
      <div className="flex flex-wrap gap-3">
        <input
          type="text"
          placeholder="Coin ara..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 min-w-48 px-4 py-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500 text-gray-900 dark:text-white"
        />
        <div className="flex gap-2">
          {[
            { key: 'all', label: 'Tümü' },
            { key: 'buy', label: 'AL', color: 'green' },
            { key: 'hold', label: 'BEKLE', color: 'yellow' },
            { key: 'sell', label: 'SAT', color: 'red' },
          ].map(f => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`px-3 py-2 rounded-lg font-medium transition ${
                filter === f.key
                  ? f.color === 'green' ? 'bg-green-500 text-white'
                  : f.color === 'red' ? 'bg-red-500 text-white'
                  : f.color === 'yellow' ? 'bg-yellow-500 text-white'
                  : 'bg-blue-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Signals Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredSignals.map(([symbol, data]) => {
          const signal = data.signal_tr || data.signal || 'BEKLE'
          const confidence = data.confidence || 50
          const price = data.price || data.current_price || 0
          const change24h = data.change_24h || 0
          const riskLevel = data.risk_level || 'MEDIUM'
          const simpleReason = data.simple_reason || data.simple_summary || 'Analiz tamamlandı'
          const reasons = data.reasons || []
          const newsCount = data.news_sentiment?.count || data.news_count || 0

          return (
            <div 
              key={symbol}
              className="bg-white dark:bg-gray-800 rounded-xl shadow overflow-hidden cursor-pointer hover:shadow-lg transition"
              onClick={() => setExpanded(expanded === symbol ? null : symbol)}
            >
              {/* Header */}
              <div className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{getSignalIcon(signal)}</span>
                    <div>
                      <h3 className="font-bold text-gray-900 dark:text-white">{symbol}</h3>
                      <p className="text-sm text-gray-500">{formatPrice(price)}</p>
                    </div>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-white font-bold text-sm ${getSignalColor(signal)}`}>
                    {getSignalText(signal)}
                  </span>
                </div>

                {/* Confidence - Multi-Factor */}
                <div className="mb-3">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-500 flex items-center gap-1 group relative">
                      Güven Skoru
                      {data.confidence_details && (
                        <>
                          <span className="text-gray-400 cursor-help">ⓘ</span>
                          {/* Tooltip */}
                          <div className="absolute left-0 bottom-full mb-2 w-64 p-2 bg-gray-900 text-white text-xs rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
                            <p className="font-semibold mb-1">Güven = Faktör Uyum Gücü</p>
                            <p className="text-gray-300">Teknik, futures ve haber göstergelerinin ne kadar aynı yönü işaret ettiğini ölçer. Yüksek güven = faktörler uyumlu.</p>
                            <p className="text-yellow-400 mt-1 text-[10px]">⚠️ Bu bir tutturma olasılığı değildir.</p>
                          </div>
                        </>
                      )}
                    </span>
                    <span className={`font-bold ${
                      confidence >= 70 ? 'text-green-600' : confidence >= 50 ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      {confidence}%
                    </span>
                  </div>
                  <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        confidence >= 70 ? 'bg-green-500' : confidence >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${confidence}%` }}
                    />
                  </div>
                  {/* Confidence Factors Mini Summary */}
                  {data.confidence_details && (
                    <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                      <span className="flex items-center gap-0.5">
                        <span className="text-green-500">▲</span>{data.confidence_details.factors_buy || 0}
                      </span>
                      <span className="flex items-center gap-0.5">
                        <span className="text-red-500">▼</span>{data.confidence_details.factors_sell || 0}
                      </span>
                      <span className="flex items-center gap-0.5">
                        <span className="text-gray-400">◆</span>{data.confidence_details.factors_neutral || 0}
                      </span>
                      {data.confidence_details.volatility_penalty < 0 && (
                        <span className="text-orange-500 text-xs">
                          (vol: {data.confidence_details.volatility_penalty})
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Quick Info */}
                <div className="flex items-center justify-between text-sm">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskColor(riskLevel)}`}>
                    Risk: {getRiskText(riskLevel)}
                  </span>
                  <div className="flex items-center gap-2">
                    {newsCount > 0 && (
                      <span className="text-gray-500 text-xs">📰 {newsCount}</span>
                    )}
                    <span className={`text-xs font-medium ${change24h >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                      {change24h >= 0 ? '+' : ''}{change24h?.toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* Reason */}
                <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                  {simpleReason}
                </p>
              </div>

              {/* Expanded Details */}
              {expanded === symbol && (
                <div className="border-t border-gray-100 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-900">
                  {/* Confidence Breakdown - NEW */}
                  {data.confidence_details && (
                    <div className="mb-4">
                      <div className="text-xs text-gray-500 mb-2">Güven Skoru Detayları</div>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                        <div className="bg-white dark:bg-gray-800 p-2 rounded">
                          <div className="text-gray-500">Faktör Uyumu</div>
                          <div className="font-bold text-blue-600">{data.confidence_details.alignment_ratio}%</div>
                        </div>
                        <div className="bg-white dark:bg-gray-800 p-2 rounded">
                          <div className="text-gray-500">Veri Kalitesi</div>
                          <div className="font-bold text-purple-600">+{data.confidence_details.data_quality}</div>
                        </div>
                        <div className="bg-white dark:bg-gray-800 p-2 rounded">
                          <div className="text-gray-500">Sinyal Gücü</div>
                          <div className="font-bold text-indigo-600">+{data.confidence_details.signal_strength}</div>
                        </div>
                        <div className="bg-white dark:bg-gray-800 p-2 rounded">
                          <div className="text-gray-500">Trend Netliği</div>
                          <div className="font-bold text-cyan-600">+{data.confidence_details.trend_clarity}</div>
                        </div>
                        <div className="bg-white dark:bg-gray-800 p-2 rounded">
                          <div className="text-gray-500">Volatilite</div>
                          <div className={`font-bold ${data.confidence_details.volatility_penalty < 0 ? 'text-orange-500' : 'text-green-500'}`}>
                            {data.confidence_details.volatility_penalty}
                          </div>
                        </div>
                        <div className="bg-white dark:bg-gray-800 p-2 rounded">
                          <div className="text-gray-500">Faktörler</div>
                          <div className="font-bold">
                            <span className="text-green-500">{data.confidence_details.factors_buy}↑</span>
                            {' '}
                            <span className="text-red-500">{data.confidence_details.factors_sell}↓</span>
                            {' '}
                            <span className="text-gray-400">{data.confidence_details.factors_neutral}○</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Technical Indicators */}
                  {data.technical && (
                    <div className="mb-4">
                      <div className="text-xs text-gray-500 mb-2">Teknik Göstergeler</div>
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        {data.technical.rsi && (
                          <div className="bg-white dark:bg-gray-800 p-2 rounded">
                            <div className="text-gray-500">RSI</div>
                            <div className={`font-bold ${
                              data.technical.rsi < 30 ? 'text-green-500' : 
                              data.technical.rsi > 70 ? 'text-red-500' : 'text-gray-900 dark:text-white'
                            }`}>
                              {data.technical.rsi?.toFixed(0)}
                            </div>
                          </div>
                        )}
                        {data.technical.macd_signal && (
                          <div className="bg-white dark:bg-gray-800 p-2 rounded">
                            <div className="text-gray-500">MACD</div>
                            <div className={`font-bold ${
                              data.technical.macd_signal.includes('BULLISH') ? 'text-green-500' : 
                              data.technical.macd_signal.includes('BEARISH') ? 'text-red-500' : 'text-gray-900 dark:text-white'
                            }`}>
                              {data.technical.macd_signal.replace('_', ' ')}
                            </div>
                          </div>
                        )}
                        {data.technical.trend && (
                          <div className="bg-white dark:bg-gray-800 p-2 rounded">
                            <div className="text-gray-500">Trend</div>
                            <div className={`font-bold ${
                              data.technical.trend.includes('UP') ? 'text-green-500' : 
                              data.technical.trend.includes('DOWN') ? 'text-red-500' : 'text-gray-900 dark:text-white'
                            }`}>
                              {data.technical.trend.replace('_', ' ')}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Futures Data */}
                  {(data.funding || data.futures) && (
                    <div className="mb-4">
                      <div className="text-xs text-gray-500 mb-2">Vadeli Veriler</div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        {data.funding?.rate !== undefined && (
                          <div className="bg-white dark:bg-gray-800 p-2 rounded">
                            <div className="text-gray-500">Funding</div>
                            <div className={`font-bold ${
                              data.funding.rate > 0.05 ? 'text-red-500' : 
                              data.funding.rate < -0.02 ? 'text-green-500' : 'text-gray-900 dark:text-white'
                            }`}>
                              {data.funding.rate?.toFixed(3)}%
                            </div>
                          </div>
                        )}
                        {data.futures?.long_short_ratio && (
                          <div className="bg-white dark:bg-gray-800 p-2 rounded">
                            <div className="text-gray-500">L/S Ratio</div>
                            <div className={`font-bold ${
                              data.futures.long_short_ratio > 2 ? 'text-red-500' : 
                              data.futures.long_short_ratio < 0.7 ? 'text-green-500' : 'text-gray-900 dark:text-white'
                            }`}>
                              {data.futures.long_short_ratio?.toFixed(2)}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Reasons */}
                  {reasons.length > 0 && (
                    <div>
                      <div className="text-xs text-gray-500 mb-2">Analiz Detayları</div>
                      {reasons.slice(0, 5).map((r, i) => (
                        <div key={i} className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-1 mb-1">
                          <span className="text-blue-500">•</span> {r}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Risk Factors */}
                  {data.risk_factors && data.risk_factors.length > 0 && (
                    <div className="mt-3 p-2 bg-red-50 dark:bg-red-900/20 rounded">
                      <div className="text-xs text-red-500 mb-1">⚠️ Risk Faktörleri</div>
                      {data.risk_factors.slice(0, 3).map((r, i) => (
                        <div key={i} className="text-xs text-red-600 dark:text-red-400">• {r}</div>
                      ))}
                    </div>
                  )}

                  {/* Data Source & Category Info */}
                  <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700 flex flex-wrap items-center gap-2 text-[10px]">
                    {data.source && (
                      <span className={`px-2 py-0.5 rounded-full ${
                        data.source === 'binance_ws'
                          ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                          : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                      }`}>
                        📡 {data.source === 'binance_ws' ? 'Binance Real-time' : 'CoinGecko'}
                      </span>
                    )}
                    {data.category && (
                      <span className={`px-2 py-0.5 rounded-full ${
                        data.category === 'MEGA_CAP' ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400' :
                        data.category === 'LARGE_CAP' ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400' :
                        data.category === 'HIGH_RISK' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                        'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                      }`}>
                        {data.category === 'MEGA_CAP' ? '👑 Mega Cap' :
                         data.category === 'LARGE_CAP' ? '💎 Large Cap' :
                         data.category === 'HIGH_RISK' ? '🎰 Meme/High Risk' :
                         data.category === 'STABLECOIN' ? '🔒 Stablecoin' : '🪙 Altcoin'}
                      </span>
                    )}
                    {data.news_sentiment?.news_count > 0 && (
                      <span className="px-2 py-0.5 rounded-full bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-400">
                        📰 {data.news_sentiment.news_count} haber (sent: {data.news_sentiment.score > 0 ? '+' : ''}{(data.news_sentiment.score * 100).toFixed(0)}%)
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Empty */}
      {filteredSignals.length === 0 && (
        <EmptyState
          type="no-signals"
          lang={lang}
          actionLabel={search ? (lang === 'tr' ? 'Aramayı Temizle' : 'Clear Search') : undefined}
          onAction={search ? () => setSearch('') : undefined}
        />
      )}

      {/* Ad Banner */}
      <AdBanner format="horizontal" slot="7777777777" className="my-6" />

      {/* Disclaimer - Enhanced */}
      <SignalDisclaimer lang={lang} />
    </div>
  )
}

export default Signals