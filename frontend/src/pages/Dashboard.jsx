// src/pages/Dashboard.jsx
import { useState, useEffect } from 'react'
import api from '../api'
import { formatPrice, formatNumber, formatChange } from '../utils/formatters'
import AnalysisModal from '../components/modals/AnalysisModal'
import { useWebSocket } from '../hooks/useWebSocket'

const Dashboard = ({ t, lang, user }) => {
  const [coins, setCoins] = useState([])
  const [prices, setPrices] = useState({})
  const [fearGreed, setFearGreed] = useState(null)
  const [signalStats, setSignalStats] = useState(null)
  const [recentSignals, setRecentSignals] = useState([])
  const [portfolio, setPortfolio] = useState(null)
  const [marketData, setMarketData] = useState(null)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)

  // Telegram bot username (user bot, not admin bot)
  const TELEGRAM_BOT_USERNAME = 'cryptosignalanalyzer_bot'

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
      const requests = [
        api.get('/api/coins'),
        api.get('/api/prices'),
        api.get('/api/fear-greed'),
        api.get('/api/signal-stats?days=30'),
        api.get('/api/signals?limit=5'),
        api.get('/api/portfolio')
      ]

      const [coinsResp, pricesResp, fgResp, statsResp, signalsResp, portfolioResp] = await Promise.all(requests)

      if (coinsResp.ok) {
        const data = await coinsResp.json()
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
      if (signalsResp.ok) {
        const data = await signalsResp.json()
        setRecentSignals(data.signals || [])
      }
      if (portfolioResp.ok) {
        const data = await portfolioResp.json()
        if (data.holdings && data.holdings.length > 0) {
          setPortfolio(data)
        }
      }

      // Calculate market data from coins
      if (coinsResp.ok) {
        const data = await coinsResp.json()
        const allCoins = data.details || []
        const totalMarketCap = allCoins.reduce((sum, c) => sum + (c.market_cap || 0), 0)
        const btcCoin = allCoins.find(c => c.symbol === 'BTC' || c.id === 'bitcoin')
        const btcDominance = btcCoin && totalMarketCap > 0
          ? ((btcCoin.market_cap || 0) / totalMarketCap * 100).toFixed(1)
          : 0
        const totalVolume = allCoins.reduce((sum, c) => sum + (c.volume || 0), 0)

        setMarketData({
          total_market_cap: totalMarketCap,
          btc_dominance: btcDominance,
          total_volume_24h: totalVolume
        })
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

  // Get trending coins (top 5 movers by 24h change)
  const trending = [...coins]
    .sort((a, b) => Math.abs(b.change_24h || 0) - Math.abs(a.change_24h || 0))
    .slice(0, 5)

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
      {/* Top Stats Grid - 3 columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Fear & Greed */}
        {fearGreed && (
          <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
            <h3 className="text-gray-400 text-sm mb-2 flex items-center gap-2">
              😱 {lang === 'tr' ? 'Piyasa Duygusu' : 'Market Sentiment'}
            </h3>
            <div className="space-y-2">
              <div className="flex items-center gap-4">
                <span className={`text-4xl font-bold ${getFearGreedColor(fearGreed.value)}`}>
                  {fearGreed.value}
                </span>
                <span className={`text-lg font-semibold ${getFearGreedColor(fearGreed.value)}`}>
                  {getFearGreedLabel(fearGreed.value)}
                </span>
              </div>
              <div className="text-xs text-gray-500 leading-relaxed">
                {lang === 'tr'
                  ? fearGreed.value <= 45
                    ? '📉 Yatırımcılar endişeli, fiyatlar düşebilir. Alım fırsatı olabilir.'
                    : fearGreed.value <= 55
                    ? '⚖️ Piyasa dengede, yön belirsiz.'
                    : '📈 Yatırımcılar iyimser, fiyatlar yükselebilir. Dikkatli olun!'
                  : fearGreed.value <= 45
                  ? '📉 Investors worried, prices may drop. Could be buying opportunity.'
                  : fearGreed.value <= 55
                  ? '⚖️ Market balanced, direction unclear.'
                  : '📈 Investors optimistic, prices may rise. Be careful!'
                }
              </div>
            </div>
          </div>
        )}

        {/* AI Signal Stats - IMPROVED */}
        {signalStats && (
          <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
            <h3 className="text-gray-400 text-sm mb-2 flex items-center gap-2">
              🎯 {lang === 'tr' ? 'AI Performansı' : 'AI Performance'}
              <span className="text-xs text-gray-500">
                ({lang === 'tr' ? '30 Gün' : '30 Days'})
              </span>
            </h3>
            <div className="space-y-2">
              <div className="flex items-baseline justify-between">
                <span className="text-3xl font-bold text-green-500">
                  {signalStats.success_rate ? `${signalStats.success_rate.toFixed(1)}%` : 'N/A'}
                </span>
                <span className="text-sm text-gray-400">
                  {lang === 'tr' ? 'Başarı Oranı' : 'Success Rate'}
                </span>
              </div>
              <div className="text-xs text-gray-500 leading-relaxed">
                {lang === 'tr'
                  ? `${signalStats.profitable || 0}/${signalStats.total || 0} sinyal kârlı, ortalama %${(signalStats.avg_profit_pct || 0).toFixed(1)} kazanç`
                  : `${signalStats.profitable || 0}/${signalStats.total || 0} signals profitable, avg ${(signalStats.avg_profit_pct || 0).toFixed(1)}% gain`
                }
              </div>
              <div className="text-xs text-gray-600 italic mt-2 pt-2 border-t border-gray-700">
                💡 {lang === 'tr'
                  ? 'AI her 10 sinyalden ~' + Math.round((signalStats.success_rate || 0) / 10) + "'inde doğru tahmin yapıyor"
                  : 'AI predicts correctly ~' + Math.round((signalStats.success_rate || 0) / 10) + ' out of 10 signals'
                }
              </div>
            </div>
          </div>
        )}

        {/* Telegram Notification */}
        <a
          href={`https://t.me/${TELEGRAM_BOT_USERNAME}?start=connect_${user?.id || ''}`}
          target="_blank"
          rel="noopener noreferrer"
          className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-4 border border-blue-400/50 hover:from-blue-600 hover:to-blue-700 transition-all cursor-pointer shadow-lg hover:shadow-blue-500/20"
        >
          <h3 className="text-white text-sm mb-2 flex items-center gap-2">
            📱 {lang === 'tr' ? 'Telegram Bildirimleri' : 'Telegram Notifications'}
          </h3>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white mb-1">
                @{TELEGRAM_BOT_USERNAME}
              </div>
              <div className="text-sm text-blue-100 opacity-90">
                {lang === 'tr' ? 'Portföy bildirimlerini al' : 'Get portfolio alerts'}
              </div>
            </div>
            <div className="text-4xl">
              💬
            </div>
          </div>
        </a>
      </div>

      {/* Second Row - 2 columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Trending Coins */}
        <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
          <h3 className="text-gray-400 text-sm mb-3 flex items-center gap-2">
            🔥 {lang === 'tr' ? 'Trend Coinler' : 'Trending Coins'}
            <span className="text-xs text-gray-500">
              ({lang === 'tr' ? 'En Çok Hareket Edenler' : 'Biggest Movers'})
            </span>
          </h3>
          <div className="space-y-2">
            {trending.map((coin, idx) => {
              const symbol = coin.symbol || coin.id?.toUpperCase() || '?'
              const priceData = prices[symbol] || {}
              const price = priceData.price || coin.price || 0
              const change24h = priceData.change_24h ?? coin.change_24h ?? 0
              const isPositive = change24h >= 0

              return (
                <div
                  key={symbol}
                  onClick={() => setSelected(coin)}
                  className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-700/30 cursor-pointer transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-500">#{idx + 1}</span>
                    <div>
                      <div className="font-medium text-white text-sm">{symbol}</div>
                      <div className="text-xs text-gray-500">{formatPrice(price)}</div>
                    </div>
                  </div>
                  <div className={`text-sm font-mono font-bold ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
                    {formatChange(change24h)}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Recent Signals */}
        <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
          <h3 className="text-gray-400 text-sm mb-3 flex items-center gap-2">
            ⚡ {lang === 'tr' ? 'Son Sinyaller' : 'Recent Signals'}
          </h3>
          <div className="space-y-2">
            {recentSignals.length > 0 ? (
              recentSignals.slice(0, 5).map((signal, idx) => {
                // Format date properly
                const formatDate = (dateStr) => {
                  if (!dateStr) return '-'
                  try {
                    const date = new Date(dateStr)
                    if (isNaN(date.getTime())) return '-'

                    const now = new Date()
                    const diffMs = now - date
                    const diffMins = Math.floor(diffMs / 60000)
                    const diffHours = Math.floor(diffMs / 3600000)
                    const diffDays = Math.floor(diffMs / 86400000)

                    if (diffMins < 60) {
                      return lang === 'tr' ? `${diffMins} dk önce` : `${diffMins}m ago`
                    } else if (diffHours < 24) {
                      return lang === 'tr' ? `${diffHours} saat önce` : `${diffHours}h ago`
                    } else if (diffDays < 7) {
                      return lang === 'tr' ? `${diffDays} gün önce` : `${diffDays}d ago`
                    } else {
                      return date.toLocaleDateString(lang === 'tr' ? 'tr-TR' : 'en-US')
                    }
                  } catch {
                    return '-'
                  }
                }

                // Format confidence
                const getConfidence = () => {
                  const conf = signal.confidence || signal.confidence_pct || signal.score
                  if (!conf) return null
                  const num = parseFloat(conf)
                  if (isNaN(num)) return null
                  return Math.round(num)
                }

                const confidence = getConfidence()
                const signalType = signal.signal_type || signal.signal || signal.action || '?'

                return (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-700/30 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                        signalType === 'BUY' || signalType === 'AL'
                          ? 'bg-green-500/20 text-green-400'
                          : signalType === 'SELL' || signalType === 'SAT'
                          ? 'bg-red-500/20 text-red-400'
                          : 'bg-yellow-500/20 text-yellow-400'
                      }`}>
                        {signalType}
                      </span>
                      <div>
                        <div className="font-medium text-white text-sm">{signal.coin || signal.symbol || '?'}</div>
                        <div className="text-xs text-gray-500">
                          {formatDate(signal.created_at || signal.timestamp || signal.date)}
                        </div>
                      </div>
                    </div>
                    {confidence && (
                      <div className="text-right">
                        <div className="text-xs font-medium text-gray-400">{confidence}%</div>
                        <div className="text-xs text-gray-600">
                          {lang === 'tr' ? 'güven' : 'conf.'}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })
            ) : (
              <div className="text-center py-8 text-gray-500 text-sm">
                {lang === 'tr' ? 'Henüz sinyal yok' : 'No signals yet'}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Third Row - Portfolio & Market Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Portfolio Summary */}
        {portfolio && (
          <div className="bg-gradient-to-br from-purple-900/20 to-purple-800/20 rounded-xl p-4 border border-purple-700/50">
            <h3 className="text-gray-400 text-sm mb-3 flex items-center gap-2">
              📈 {lang === 'tr' ? 'Portföy Özeti' : 'Portfolio Summary'}
            </h3>
            <div className="space-y-3">
              <div>
                <div className="text-sm text-gray-400">
                  {lang === 'tr' ? 'Toplam Değer' : 'Total Value'}
                </div>
                <div className="text-3xl font-bold text-white">
                  ${formatNumber(portfolio.total_value || 0)}
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-gray-500">
                    {lang === 'tr' ? 'Günlük Değişim' : 'Daily P&L'}
                  </div>
                  <div className={`text-lg font-bold ${(portfolio.daily_pnl_pct || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {(portfolio.daily_pnl_pct || 0) >= 0 ? '+' : ''}{(portfolio.daily_pnl_pct || 0).toFixed(2)}%
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-gray-500">
                    {lang === 'tr' ? 'Toplam Kar/Zarar' : 'Total P&L'}
                  </div>
                  <div className={`text-lg font-bold ${(portfolio.total_pnl_pct || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {(portfolio.total_pnl_pct || 0) >= 0 ? '+' : ''}{(portfolio.total_pnl_pct || 0).toFixed(2)}%
                  </div>
                </div>
              </div>
              <div className="pt-2 border-t border-purple-700/50">
                <div className="text-xs text-gray-500">
                  {lang === 'tr' ? 'En İyi Performans' : 'Best Performer'}
                </div>
                <div className="text-sm text-white font-medium">
                  {portfolio.best_performer || '-'}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Market Overview */}
        {marketData && (
          <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
            <h3 className="text-gray-400 text-sm mb-3 flex items-center gap-2">
              📊 {lang === 'tr' ? 'Piyasa Görünümü' : 'Market Overview'}
            </h3>
            <div className="space-y-3">
              <div>
                <div className="text-xs text-gray-500">
                  {lang === 'tr' ? 'Toplam Piyasa Değeri' : 'Total Market Cap'}
                </div>
                <div className="text-2xl font-bold text-white">
                  ${(marketData.total_market_cap / 1e12).toFixed(2)}T
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-gray-500">BTC Dominance</div>
                  <div className="text-xl font-bold text-orange-400">
                    {marketData.btc_dominance}%
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-gray-500">
                    {lang === 'tr' ? '24s Hacim' : '24h Volume'}
                  </div>
                  <div className="text-xl font-bold text-blue-400">
                    ${(marketData.total_volume_24h / 1e9).toFixed(1)}B
                  </div>
                </div>
              </div>
              <div className="pt-2 border-t border-gray-700 text-xs text-gray-600">
                💡 {lang === 'tr'
                  ? 'Piyasa verisi tüm coinlerin toplamından hesaplanır'
                  : 'Market data calculated from all tracked coins'
                }
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