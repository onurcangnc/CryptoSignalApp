// src/pages/Dashboard.jsx
import { useState, useEffect } from 'react'
import api from '../api'
import { formatPrice, formatNumber, formatChange } from '../utils/formatters'
import AnalysisModal from '../components/modals/AnalysisModal'
import { useWebSocket } from '../hooks/useWebSocket'
import { SignalPerformanceGrid } from '../components/SignalPerformance'
import { Watchlist, FavoriteButton } from '../components/Watchlist'
import { CreateAlertModal, PriceAlertsList } from '../components/PriceAlerts'

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
  const [alertModal, setAlertModal] = useState(null)
  const [alertsRefreshKey, setAlertsRefreshKey] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const ITEMS_PER_PAGE = 100

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

      // Parse all responses once
      let coinsData = null
      if (coinsResp.ok) {
        coinsData = await coinsResp.json()
        setCoins(coinsData.details || [])
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

      // Calculate market data from coins (reuse already parsed data)
      if (coinsData) {
        const allCoins = coinsData.details || []
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

  // Pagination
  const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE)
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE
  const endIndex = startIndex + ITEMS_PER_PAGE
  const paginatedCoins = filtered.slice(startIndex, endIndex)

  // Reset to page 1 when search changes
  useEffect(() => {
    setCurrentPage(1)
  }, [search])

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
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="relative">
            <div className="animate-spin rounded-full h-20 w-20 border-b-4 border-t-4 border-yellow-500 mx-auto"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-4xl animate-pulse">🚀</div>
            </div>
          </div>
          <p className="mt-6 text-gray-400 font-medium animate-pulse">
            {lang === 'tr' ? 'Yükleniyor...' : 'Loading...'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Stats Grid - 3 columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Fear & Greed */}
        {fearGreed && (
          <div className="group bg-gray-800/50 backdrop-blur-sm rounded-xl p-4 border border-gray-700/50 hover:border-gray-600/50 transition-all duration-300 hover:shadow-lg hover:shadow-gray-900/50 hover:-translate-y-1">
            <h3 className="text-gray-400 text-sm mb-2 flex items-center gap-2 group-hover:text-gray-300 transition-colors">
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

        {/* AI Performance - NEW 4-CARD GRID */}
        <SignalPerformanceGrid stats={signalStats} />

        {/* Telegram Notification */}
        <a
          href={`https://t.me/${TELEGRAM_BOT_USERNAME}?start=connect_${user?.id || ''}`}
          target="_blank"
          rel="noopener noreferrer"
          className="group bg-gradient-to-br from-blue-500 to-blue-600 backdrop-blur-sm rounded-xl p-4 border border-blue-400/50 hover:border-blue-300/70 hover:from-blue-600 hover:to-blue-700 transition-all duration-300 cursor-pointer shadow-lg hover:shadow-blue-500/40 hover:-translate-y-1 hover:scale-[1.02] animate-fade-in"
        >
          <h3 className="text-white text-sm mb-2 flex items-center gap-2 group-hover:scale-105 transition-transform">
            📱 {lang === 'tr' ? 'Telegram Bildirimleri' : 'Telegram Notifications'}
          </h3>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white mb-1 group-hover:text-blue-50 transition-colors">
                @{TELEGRAM_BOT_USERNAME}
              </div>
              <div className="text-sm text-blue-100 opacity-90 group-hover:opacity-100 transition-opacity">
                {lang === 'tr' ? 'Portföy bildirimlerini al' : 'Get portfolio alerts'}
              </div>
            </div>
            <div className="text-4xl group-hover:scale-110 group-hover:rotate-12 transition-all duration-300">
              💬
            </div>
          </div>
        </a>
      </div>

      {/* Second Row - 2 columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Trending Coins */}
        <div className="group bg-gray-800/50 backdrop-blur-sm rounded-xl p-4 border border-gray-700/50 hover:border-orange-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-orange-500/20 hover:-translate-y-1">
          <h3 className="text-gray-400 text-sm mb-3 flex items-center gap-2 group-hover:text-gray-300 transition-colors">
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
                  className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-700/50 cursor-pointer transition-all duration-200 hover:scale-[1.02] hover:shadow-md hover:shadow-gray-900/50"
                  style={{ animationDelay: `${idx * 50}ms` }}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-500 font-bold bg-gray-700/50 px-2 py-1 rounded">
                      #{idx + 1}
                    </span>
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
        <div className="group bg-gray-800/50 backdrop-blur-sm rounded-xl p-4 border border-gray-700/50 hover:border-yellow-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-yellow-500/20 hover:-translate-y-1">
          <h3 className="text-gray-400 text-sm mb-3 flex items-center gap-2 group-hover:text-gray-300 transition-colors">
            ⚡ {lang === 'tr' ? 'Son Sinyaller' : 'Recent Signals'}
          </h3>
          <div className="space-y-2">
            {recentSignals.length > 0 ? (
              recentSignals.slice(0, 5).map((signal, idx) => {
                // Get coin symbol and price
                const coinSymbol = signal.coin || signal.symbol || '?'
                const priceData = prices[coinSymbol] || {}
                const coinPrice = priceData.price || signal.price || 0

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
                    className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-700/50 transition-all duration-200 hover:scale-[1.02] hover:shadow-md hover:shadow-gray-900/50 cursor-pointer"
                    style={{ animationDelay: `${idx * 50}ms` }}
                  >
                    <div className="flex items-center gap-3">
                      <span className={`px-2 py-1 rounded text-xs font-bold shadow-md transition-all duration-200 hover:scale-105 ${
                        signalType === 'BUY' || signalType === 'AL' || signalType === 'STRONG_BUY'
                          ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30 hover:shadow-green-500/50'
                          : signalType === 'SELL' || signalType === 'SAT' || signalType === 'STRONG_SELL'
                          ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30 hover:shadow-red-500/50'
                          : 'bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30 hover:shadow-yellow-500/50'
                      }`}>
                        {signalType === 'STRONG_BUY' ? 'BUY' : signalType === 'STRONG_SELL' ? 'SELL' : signalType}
                      </span>
                      <div>
                        <div className="font-medium text-white text-sm">{coinSymbol}</div>
                        <div className="text-xs text-gray-500">
                          {coinPrice > 0 ? formatPrice(coinPrice) : '-'}
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

      {/* Watchlist Section */}
      <Watchlist prices={prices} onCoinClick={setSelected} lang={lang} />

      {/* Price Alerts Section */}
      <PriceAlertsList lang={lang} refreshKey={alertsRefreshKey} />

      {/* Third Row - Portfolio & Market Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Portfolio Summary */}
        {portfolio && (
          <div className="group bg-gradient-to-br from-purple-900/20 to-purple-800/20 backdrop-blur-sm rounded-xl p-4 border border-purple-700/50 hover:border-purple-500/70 transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/30 hover:-translate-y-1">
            <h3 className="text-gray-400 text-sm mb-3 flex items-center gap-2 group-hover:text-gray-300 transition-colors">
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
          <div className="group bg-gray-800/50 backdrop-blur-sm rounded-xl p-4 border border-gray-700/50 hover:border-blue-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/20 hover:-translate-y-1">
            <h3 className="text-gray-400 text-sm mb-3 flex items-center gap-2 group-hover:text-gray-300 transition-colors">
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
      <div className="relative group">
        <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
          <span className="text-gray-500 group-focus-within:text-yellow-500 transition-colors">🔍</span>
        </div>
        <input
          type="text"
          placeholder={lang === 'tr' ? 'Coin ara...' : 'Search coin...'}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-yellow-500 focus:shadow-lg focus:shadow-yellow-500/30 transition-all duration-300"
        />
        {search && (
          <button
            onClick={() => setSearch('')}
            className="absolute inset-y-0 right-3 flex items-center text-gray-500 hover:text-red-400 transition-colors"
          >
            ✕
          </button>
        )}
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
              <th className="px-4 py-3 text-center">⭐</th>
              <th className="px-4 py-3 text-center">🔔</th>
            </tr>
          </thead>
          <tbody>
            {paginatedCoins.map((coin, idx) => {
              const symbol = coin.symbol || coin.id?.toUpperCase() || '?'
              const priceData = prices[symbol] || {}
              const price = priceData.price || coin.price || 0
              const change24h = priceData.change_24h ?? coin.change_24h ?? 0
              const change7d = coin.change_7d ?? 0
              const actualIndex = startIndex + idx

              return (
                <tr
                  key={symbol}
                  onClick={() => setSelected(coin)}
                  className={`border-t border-gray-700/50 hover:bg-gradient-to-r hover:from-gray-700/50 hover:to-gray-700/20 cursor-pointer transition-all duration-200 hover:scale-[1.01] hover:shadow-md hover:shadow-gray-900/50 ${
                    idx % 2 === 0 ? 'bg-gray-800/20' : 'bg-gray-800/40'
                  }`}
                >
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-gradient-to-br from-yellow-500/20 to-yellow-600/20 text-yellow-500 font-bold text-sm">
                      {coin.rank || actualIndex + 1}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-white">{symbol}</span>
                      <span className="text-gray-500 text-sm hidden sm:inline">{coin.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right text-white font-mono font-bold">
                    {formatPrice(price)}
                  </td>
                  <td className={`px-4 py-3 text-right font-mono font-bold transition-colors ${change24h >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                    <span className="inline-flex items-center gap-1">
                      {change24h >= 0 ? '↗' : '↘'}
                      {formatChange(change24h)}
                    </span>
                  </td>
                  <td className={`px-4 py-3 text-right font-mono font-bold hidden md:table-cell transition-colors ${change7d >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                    <span className="inline-flex items-center gap-1">
                      {change7d >= 0 ? '↗' : '↘'}
                      {formatChange(change7d)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-gray-400 hidden lg:table-cell">
                    {formatNumber(coin.market_cap)}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-400 hidden lg:table-cell">
                    {formatNumber(coin.volume || priceData.volume_24h)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <FavoriteButton symbol={symbol} />
                  </td>
                  <td className="px-4 py-3 text-center">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setAlertModal({ coin, price })
                      }}
                      className="text-gray-400 hover:text-yellow-500 transition-colors"
                      title={lang === 'tr' ? 'Fiyat Alarmı Kur' : 'Set Price Alert'}
                    >
                      🔔
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        </div>

        {paginatedCoins.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            {lang === 'tr' ? 'Coin bulunamadı' : 'No coins found'}
          </div>
        )}
      </div>

      {/* Pagination */}
      {filtered.length > ITEMS_PER_PAGE && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-4">
          {/* Info */}
          <div className="text-sm text-gray-400">
            {lang === 'tr'
              ? `${startIndex + 1}-${Math.min(endIndex, filtered.length)} arası gösteriliyor (Toplam ${filtered.length})`
              : `Showing ${startIndex + 1}-${Math.min(endIndex, filtered.length)} of ${filtered.length}`
            }
          </div>

          {/* Page buttons */}
          <div className="flex items-center gap-2">
            {/* Previous button */}
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-4 py-2 rounded-lg bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200 hover:shadow-lg hover:shadow-gray-900/50 hover:-translate-x-1 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-x-0 transition-all duration-200"
            >
              {lang === 'tr' ? '← Önceki' : '← Previous'}
            </button>

            {/* Page numbers */}
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum
                if (totalPages <= 5) {
                  pageNum = i + 1
                } else if (currentPage <= 3) {
                  pageNum = i + 1
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + i
                } else {
                  pageNum = currentPage - 2 + i
                }

                return (
                  <button
                    key={pageNum}
                    onClick={() => setCurrentPage(pageNum)}
                    className={`w-10 h-10 rounded-lg transition-all duration-200 font-bold ${
                      currentPage === pageNum
                        ? 'bg-yellow-500 text-gray-900 shadow-lg shadow-yellow-500/50 animate-glow-pulse scale-110'
                        : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200 hover:scale-105 hover:shadow-md hover:shadow-gray-900/50'
                    }`}
                  >
                    {pageNum}
                  </button>
                )
              })}
            </div>

            {/* Next button */}
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-4 py-2 rounded-lg bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200 hover:shadow-lg hover:shadow-gray-900/50 hover:translate-x-1 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-x-0 transition-all duration-200"
            >
              {lang === 'tr' ? 'Sonraki →' : 'Next →'}
            </button>
          </div>
        </div>
      )}

      {/* Analysis Modal */}
      {selected && (
        <AnalysisModal
          coin={selected}
          onClose={() => setSelected(null)}
          t={t}
          lang={lang}
        />
      )}

      {/* Price Alert Modal */}
      {alertModal && (
        <CreateAlertModal
          coin={alertModal.coin}
          currentPrice={alertModal.price}
          onClose={() => setAlertModal(null)}
          onSuccess={() => {
            // Refresh alerts list by incrementing the key
            setAlertsRefreshKey(prev => prev + 1)
            setAlertModal(null)
          }}
          lang={lang}
        />
      )}
    </div>
  )
}

export default Dashboard