// src/pages/Dashboard.jsx
import { useState, useEffect } from 'react'
import api from '../api'
import { formatPrice, formatNumber, formatChange } from '../utils/formatters'
import AnalysisModal from '../components/modals/AnalysisModal'
import { useWebSocket } from '../hooks/useWebSocket'

const Dashboard = ({ t, lang }) => {
  const [coins, setCoins] = useState([])
  const [prices, setPrices] = useState({})
  const [fearGreed, setFearGreed] = useState(null)
  const [signalStats, setSignalStats] = useState(null)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)

  // WebSocket connection for real-time price updates
  const { isConnected } = useWebSocket((data) => {
    if (data.type === 'init' && data.prices) {
      // Initial data from WebSocket
      setPrices(data.prices)
      if (data.fear_greed) setFearGreed(data.fear_greed)
    } else if (data.type === 'price_update' && data.prices) {
      // Real-time price updates
      setPrices(prevPrices => ({
        ...prevPrices,
        ...data.prices
      }))
    }
  })

  useEffect(() => {
    fetchData()
    // Fallback: Still poll if WebSocket disconnects
    const interval = setInterval(() => {
      if (!isConnected) {
        fetchPrices()
      }
    }, 5000)
    return () => clearInterval(interval)
  }, [isConnected])

  const fetchData = async () => {
    try {
      const [coinsResp, pricesResp, fgResp, statsResp] = await Promise.all([
        api.get('/api/coins'),
        api.get('/api/prices'),
        api.get('/api/fear-greed'),
        api.get('/api/signal-stats?days=30')
      ])
      if (coinsResp.ok) {
        const data = await coinsResp.json()
        // Use details array which has full coin objects
        setCoins(data.details || [])
      }
      if (pricesResp.ok) {
        const data = await pricesResp.json()
        setPrices(data.prices || {})
      }
      if (fgResp.ok) {
        const data = await fgResp.json()
        setFearGreed(data)
      }
      if (statsResp.ok) {
        const data = await statsResp.json()
        setSignalStats(data)
      }
    } catch (e) {
      console.error('Dashboard fetch error:', e)
    } finally {
      setLoading(false)
    }
  }

  const fetchPrices = async () => {
    try {
      const resp = await api.get('/api/prices')
      if (resp.ok) {
        const data = await resp.json()
        setPrices(data.prices || {})
      }
    } catch (e) {}
  }

  const filtered = coins
    .filter(c => {
      const symbol = c.symbol || c.id || ''
      const name = c.name || ''
      return symbol.toLowerCase().includes(search.toLowerCase()) ||
             name.toLowerCase().includes(search.toLowerCase())
    })
    .slice(0, 50)

  const getFearGreedColor = (value) => {
    if (value <= 25) return 'text-red-500'
    if (value <= 45) return 'text-orange-500'
    if (value <= 55) return 'text-yellow-500'
    if (value <= 75) return 'text-lime-500'
    return 'text-green-500'
  }

  const getFearGreedLabel = (value) => {
    if (value <= 25) return lang === 'tr' ? 'Aşırı Korku' : 'Extreme Fear'
    if (value <= 45) return lang === 'tr' ? 'Korku' : 'Fear'
    if (value <= 55) return lang === 'tr' ? 'Nötr' : 'Neutral'
    if (value <= 75) return lang === 'tr' ? 'Açgözlülük' : 'Greed'
    return lang === 'tr' ? 'Aşırı Açgözlülük' : 'Extreme Greed'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-500"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Fear & Greed */}
        {fearGreed && (
          <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
            <h3 className="text-gray-400 text-sm mb-2">{lang === 'tr' ? 'Korku & Açgözlülük' : 'Fear & Greed'}</h3>
            <div className="flex items-center gap-4">
              <span className={`text-4xl font-bold ${getFearGreedColor(fearGreed.value)}`}>
                {fearGreed.value}
              </span>
              <span className={`text-lg ${getFearGreedColor(fearGreed.value)}`}>
                {getFearGreedLabel(fearGreed.value)}
              </span>
            </div>
          </div>
        )}

        {/* AI Signal Stats */}
        {signalStats && (
          <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
            <h3 className="text-gray-400 text-sm mb-2 flex items-center gap-2">
              🎯 {lang === 'tr' ? 'AI Sinyal Doğruluğu' : 'AI Signal Accuracy'}
              <span className="text-xs text-gray-500">(30 gün)</span>
            </h3>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-4xl font-bold text-green-500">
                  {signalStats.success_rate ? `${signalStats.success_rate.toFixed(1)}%` : 'N/A'}
                </div>
                <div className="text-sm text-gray-400 mt-1">
                  {signalStats.profitable || 0}/{signalStats.total || 0} {lang === 'tr' ? 'kârlı' : 'profitable'}
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-400">
                  {lang === 'tr' ? 'Ort. Kazanç' : 'Avg Profit'}
                </div>
                <div className="text-lg font-bold text-green-400">
                  +{signalStats.avg_profit_pct ? signalStats.avg_profit_pct.toFixed(1) : '0'}%
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Search */}
      <div className="relative">
        <input
          type="text"
          placeholder={lang === 'tr' ? 'Coin ara...' : 'Search coin...'}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-yellow-500"
        />
      </div>

      {/* Coins Table */}
      <div className="bg-gray-800/50 rounded-xl border border-gray-700/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
          <thead className="bg-gray-900/50">
            <tr className="text-left text-gray-400 text-sm">
              <th className="px-4 py-3">#</th>
              <th className="px-4 py-3">{lang === 'tr' ? 'İsim' : 'Name'}</th>
              <th className="px-4 py-3 text-right">{lang === 'tr' ? 'Fiyat' : 'Price'}</th>
              <th className="px-4 py-3 text-right">{lang === 'tr' ? '24s Değişim' : '24h Change'}</th>
              <th className="px-4 py-3 text-right hidden md:table-cell">{lang === 'tr' ? '7g Değişim' : '7d Change'}</th>
              <th className="px-4 py-3 text-right hidden lg:table-cell">{lang === 'tr' ? 'Piyasa Değeri' : 'Market Cap'}</th>
              <th className="px-4 py-3 text-right hidden lg:table-cell">{lang === 'tr' ? 'Hacim' : 'Volume'}</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((coin, idx) => {
              const symbol = coin.symbol || coin.id?.toUpperCase() || '?'
              const priceData = prices[symbol] || {}
              const price = priceData.price || coin.price || 0
              const change24h = priceData.change_24h ?? coin.change_24h ?? 0
              const change7d = coin.change_7d ?? 0
              
              return (
                <tr 
                  key={symbol}
                  onClick={() => setSelected(coin)}
                  className="border-t border-gray-700/50 hover:bg-gray-700/30 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3 text-gray-500">{coin.rank || idx + 1}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-white">{symbol}</span>
                      <span className="text-gray-500 text-sm hidden sm:inline">{coin.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right text-white font-mono">
                    {formatPrice(price)}
                  </td>
                  <td className={`px-4 py-3 text-right font-mono ${change24h >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {formatChange(change24h)}
                  </td>
                  <td className={`px-4 py-3 text-right font-mono hidden md:table-cell ${change7d >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {formatChange(change7d)}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-400 hidden lg:table-cell">
                    {formatNumber(coin.market_cap)}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-400 hidden lg:table-cell">
                    {formatNumber(coin.volume || priceData.volume_24h)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        </div>

        {filtered.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            {lang === 'tr' ? 'Coin bulunamadı' : 'No coins found'}
          </div>
        )}
      </div>

      {/* Analysis Modal */}
      {selected && (
        <AnalysisModal
          coin={selected}
          onClose={() => setSelected(null)}
          t={t}
          lang={lang}
        />
      )}
    </div>
  )
}

export default Dashboard
