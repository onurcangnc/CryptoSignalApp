import { useState, useEffect } from 'react'
import api from '../api'

const Portfolio = ({ t, lang }) => {
  const [portfolio, setPortfolio] = useState(null)
  const [aiAnalysis, setAiAnalysis] = useState(null)
  const [prices, setPrices] = useState({})
  const [fxRates, setFxRates] = useState({ USD: 1, TRY: 34.5, EUR: 0.92, GBP: 0.79 })
  const [loading, setLoading] = useState(true)
  const [aiLoading, setAiLoading] = useState(false)
  const [showAdd, setShowAdd] = useState(false)
  const [coins, setCoins] = useState([])
  
  // Yeni varlık ekleme state'i
  const [newHolding, setNewHolding] = useState({
    coin: '',
    amount: '',           // Girilen miktar
    currency: 'USD',      // Para birimi (USD, TRY, EUR)
    inputMode: 'fiat'     // fiat veya crypto
  })
  const [coinSearch, setCoinSearch] = useState('')
  
  // Hesaplanan değerler
  const [calculated, setCalculated] = useState({
    cryptoAmount: 0,
    usdValue: 0
  })

  useEffect(() => {
    loadData()
  }, [])

  // Otomatik hesaplama - amount, currency veya coin değişince
  useEffect(() => {
    if (!newHolding.coin || !newHolding.amount || !prices[newHolding.coin]) {
      setCalculated({ cryptoAmount: 0, usdValue: 0 })
      return
    }

    const coinPrice = prices[newHolding.coin]?.price || 0
    const amount = parseFloat(newHolding.amount) || 0
    const fxRate = fxRates[newHolding.currency] || 1

    if (newHolding.inputMode === 'fiat') {
      // Fiat girişi: TRY/EUR -> USD -> Crypto miktarı
      const usdValue = newHolding.currency === 'USD' ? amount : amount / fxRate
      const cryptoAmount = coinPrice > 0 ? usdValue / coinPrice : 0
      setCalculated({ cryptoAmount, usdValue })
    } else {
      // Crypto girişi: Crypto miktarı -> USD değeri
      const usdValue = amount * coinPrice
      setCalculated({ cryptoAmount: amount, usdValue })
    }
  }, [newHolding.coin, newHolding.amount, newHolding.currency, newHolding.inputMode, prices, fxRates])

  const loadData = async () => {
    try {
      setLoading(true)
      const [portResp, priceResp, coinsResp] = await Promise.all([
        api.get('/api/portfolio'),
        api.get('/api/prices'),
        api.get('/api/coins?limit=1000')  // Tüm coinleri al
      ])
      
      if (portResp.ok) {
        const data = await portResp.json()
        setPortfolio(data)
        if (data.fx) setFxRates(data.fx)
      }
      
      if (priceResp.ok) {
        const data = await priceResp.json()
        setPrices(data.prices || {})
        if (data.fx) setFxRates(data.fx)
      }

      if (coinsResp.ok) {
        const data = await coinsResp.json()
        setCoins(data.coins || [])
      }
      
      // AI analizi varsa yükle
      try {
        const aiResp = await api.get('/api/portfolio/ai-analysis')
        if (aiResp.ok) {
          const data = await aiResp.json()
          if (!data.error) setAiAnalysis(data)
        }
      } catch (e) {}
    } catch (err) {
      console.error('Portfolio error:', err)
    } finally {
      setLoading(false)
    }
  }

  const requestAI = async () => {
    try {
      setAiLoading(true)
      const resp = await api.post('/api/portfolio/analyze', {})
      if (resp.ok) {
        const data = await resp.json()
        setAiAnalysis(data)
      } else {
        const err = await resp.json()
        alert(err.detail || 'AI analizi başarısız')
      }
    } catch (e) {
      alert('Hata: ' + e.message)
    } finally {
      setAiLoading(false)
    }
  }

  const addHolding = async () => {
    if (!newHolding.coin || !newHolding.amount) {
      alert('Coin ve miktar gerekli')
      return
    }

    const holdings = [...(portfolio?.holdings || [])]
    
    // Aynı coin varsa güncelle, yoksa ekle
    const existingIndex = holdings.findIndex(h => h.coin === newHolding.coin.toUpperCase())
    
    const holdingData = {
      coin: newHolding.coin.toUpperCase(),
      weight: 0,
      quantity: calculated.cryptoAmount,
      invested_amount: parseFloat(newHolding.amount),
      invested_currency: newHolding.currency,
      invested_usd: calculated.usdValue,
      input_mode: newHolding.inputMode
    }

    if (existingIndex >= 0) {
      // Mevcut varlığı güncelle (miktarları topla)
      holdings[existingIndex].quantity += calculated.cryptoAmount
      holdings[existingIndex].invested_usd += calculated.usdValue
    } else {
      holdings.push(holdingData)
    }

    try {
      const resp = await api.put('/api/portfolio', { holdings })
      if (resp.ok) {
        setShowAdd(false)
        setNewHolding({ coin: '', amount: '', currency: 'USD', inputMode: 'fiat' })
        loadData()
      }
    } catch (e) {
      alert('Ekleme başarısız')
    }
  }

  const removeHolding = async (coin) => {
    if (!confirm(`${coin} silinsin mi?`)) return
    const holdings = (portfolio?.holdings || []).filter(h => h.coin !== coin)
    try {
      await api.put('/api/portfolio', { holdings })
      loadData()
    } catch (e) {}
  }

  const formatMoney = (val, currency = 'USD') => {
    if (currency === 'TRY') return `₺${val.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    if (currency === 'EUR') return `€${val.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    return `$${val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const formatCrypto = (val) => {
    if (val >= 1) return val.toLocaleString('en-US', { minimumFractionDigits: 4, maximumFractionDigits: 4 })
    if (val >= 0.0001) return val.toLocaleString('en-US', { minimumFractionDigits: 6, maximumFractionDigits: 6 })
    return val.toLocaleString('en-US', { minimumFractionDigits: 8, maximumFractionDigits: 8 })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-500">Portföy yükleniyor...</p>
        </div>
      </div>
    )
  }

  const holdings = portfolio?.holdings || []
  const totalValue = portfolio?.total_value_usd || 0
  const totalInvested = portfolio?.total_invested_usd || 0
  const totalPnL = portfolio?.total_profit_loss_usd || 0
  const totalPnLPct = portfolio?.total_profit_loss_pct || 0

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            💼 {lang === 'tr' ? 'Portföyüm' : 'My Portfolio'}
          </h1>
          <p className="text-sm text-gray-500">
            {holdings.length} varlık
          </p>
        </div>
        <button
          onClick={() => setShowAdd(true)}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition flex items-center gap-2"
        >
          ➕ Varlık Ekle
        </button>
      </div>

      {/* Özet Kartlar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow">
          <div className="text-xs text-gray-500 mb-1">Toplam Değer</div>
          <div className="text-xl font-bold text-gray-900 dark:text-white">
            {formatMoney(totalValue)}
          </div>
          <div className="text-xs text-gray-400">
            ≈ {formatMoney(totalValue * fxRates.TRY, 'TRY')}
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow">
          <div className="text-xs text-gray-500 mb-1">Yatırılan</div>
          <div className="text-xl font-bold text-gray-900 dark:text-white">
            {formatMoney(totalInvested)}
          </div>
        </div>
        
        <div className={`rounded-xl p-4 shadow ${totalPnL >= 0 ? 'bg-green-50 dark:bg-green-900/30' : 'bg-red-50 dark:bg-red-900/30'}`}>
          <div className="text-xs text-gray-500 mb-1">Kar/Zarar</div>
          <div className={`text-xl font-bold ${totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {totalPnL >= 0 ? '+' : ''}{formatMoney(totalPnL)}
          </div>
          <div className={`text-xs ${totalPnL >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            {totalPnLPct >= 0 ? '+' : ''}{totalPnLPct.toFixed(2)}%
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow">
          <div className="text-xs text-gray-500 mb-1">Döviz Kurları</div>
          <div className="text-sm font-medium text-gray-700 dark:text-gray-300">
            1 USD = ₺{fxRates.TRY?.toFixed(2)}
          </div>
          <div className="text-xs text-gray-400">
            1 USD = €{fxRates.EUR?.toFixed(2)}
          </div>
        </div>
      </div>

      {/* AI Analizi */}
      <div className="bg-gradient-to-r from-purple-500/10 to-blue-500/10 rounded-xl p-4 shadow">
        <div className="flex justify-between items-center mb-3">
          <h2 className="font-bold text-gray-900 dark:text-white flex items-center gap-2">
            🤖 AI Portföy Analizi
          </h2>
          <button
            onClick={requestAI}
            disabled={aiLoading || holdings.length === 0}
            className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center gap-2"
          >
            {aiLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Analiz ediliyor...
              </>
            ) : (
              <>✨ Analiz Et</>
            )}
          </button>
        </div>

        {aiAnalysis && !aiAnalysis.error ? (
          <div className="space-y-3">
            {/* Genel Durum */}
            <div className="flex items-center gap-3">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                aiAnalysis.portfolio_health === 'sağlıklı' ? 'bg-green-100 text-green-700' :
                aiAnalysis.portfolio_health === 'riskli' ? 'bg-yellow-100 text-yellow-700' :
                'bg-red-100 text-red-700'
              }`}>
                {aiAnalysis.portfolio_health === 'sağlıklı' ? '✅' : aiAnalysis.portfolio_health === 'riskli' ? '⚠️' : '🔴'} 
                {' '}{aiAnalysis.portfolio_health}
              </span>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Risk Skoru: {aiAnalysis.risk_score}/10
              </span>
            </div>

            {/* Özet */}
            <p className="text-gray-700 dark:text-gray-300 text-sm">
              {aiAnalysis.general_summary}
            </p>

            {/* Coin Tavsiyeleri */}
            {aiAnalysis.coin_analysis && aiAnalysis.coin_analysis.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {aiAnalysis.coin_analysis.map((ca, i) => (
                  <div key={i} className="flex items-center justify-between bg-white/50 dark:bg-gray-800/50 rounded-lg px-3 py-2">
                    <span className="font-medium">{ca.coin}</span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      ca.action === 'AL' ? 'bg-green-100 text-green-700' :
                      ca.action === 'SAT' || ca.action === 'AZALT' ? 'bg-red-100 text-red-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {ca.action}
                    </span>
                    <span className="text-xs text-gray-500">{ca.reason}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Öneriler */}
            {aiAnalysis.recommendations && aiAnalysis.recommendations.length > 0 && (
              <div className="mt-2">
                <div className="text-xs text-gray-500 mb-1">Öneriler:</div>
                <ul className="text-sm text-gray-600 dark:text-gray-400 list-disc list-inside">
                  {aiAnalysis.recommendations.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">
            {holdings.length === 0 
              ? 'Önce portföyünüze varlık ekleyin'
              : 'AI analizi için butona tıklayın'}
          </p>
        )}
      </div>

      {/* Varlık Listesi */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow overflow-hidden">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="font-bold text-gray-900 dark:text-white">Varlıklarım</h2>
        </div>

        {holdings.length === 0 ? (
          <div className="p-8 text-center">
            <div className="text-4xl mb-3">📭</div>
            <p className="text-gray-500">Henüz varlık eklenmemiş</p>
            <button
              onClick={() => setShowAdd(true)}
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              İlk Varlığını Ekle
            </button>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {holdings.map((h, i) => {
              const price = prices[h.coin]?.price || 0
              const value = (h.quantity || 0) * price
              const pnl = value - (h.invested_usd || 0)
              const pnlPct = h.invested_usd > 0 ? (pnl / h.invested_usd * 100) : 0

              return (
                <div key={i} className="p-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                      {h.coin.slice(0, 2)}
                    </div>
                    <div>
                      <div className="font-bold text-gray-900 dark:text-white">{h.coin}</div>
                      <div className="text-xs text-gray-500">
                        {formatCrypto(h.quantity || 0)} {h.coin}
                      </div>
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="font-bold text-gray-900 dark:text-white">
                      {formatMoney(value)}
                    </div>
                    <div className={`text-xs ${pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                      {pnl >= 0 ? '+' : ''}{formatMoney(pnl)} ({pnlPct >= 0 ? '+' : ''}{pnlPct.toFixed(1)}%)
                    </div>
                  </div>

                  <button
                    onClick={() => removeHolding(h.coin)}
                    className="ml-4 p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition"
                  >
                    🗑️
                  </button>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Varlık Ekleme Modal */}
      {showAdd && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md shadow-xl">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
              <h3 className="font-bold text-lg text-gray-900 dark:text-white">Varlık Ekle</h3>
              <button 
                onClick={() => setShowAdd(false)}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ✕
              </button>
            </div>

            <div className="p-4 space-y-4">
              {/* Coin Seçimi - Arama destekli */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Kripto Varlık
                </label>
                {/* Arama input'u */}
                <input
                  type="text"
                  value={coinSearch}
                  onChange={(e) => setCoinSearch(e.target.value)}
                  placeholder="Coin ara... (BTC, ETH, RNDR...)"
                  className="w-full px-4 py-2 mb-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 focus:ring-2 focus:ring-blue-500 text-sm"
                />
                {/* Seçili coin göstergesi */}
                {newHolding.coin && (
                  <div className="flex items-center justify-between mb-2 px-3 py-2 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
                    <span className="font-medium text-blue-700 dark:text-blue-300">
                      {newHolding.coin} {prices[newHolding.coin]?.price ? `- $${prices[newHolding.coin].price.toLocaleString()}` : ''}
                    </span>
                    <button
                      onClick={() => setNewHolding({ ...newHolding, coin: '' })}
                      className="text-red-500 hover:text-red-700 text-sm"
                    >
                      ✕ Kaldır
                    </button>
                  </div>
                )}
                {/* Coin listesi */}
                <div className="max-h-48 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg">
                  {coins
                    .filter(c => {
                      if (!coinSearch) return true
                      const search = coinSearch.toLowerCase()
                      const name = (prices[c]?.name || '').toLowerCase()
                      return c.toLowerCase().includes(search) || name.includes(search)
                    })
                    .slice(0, 100)  // Performans için görüntüde max 100
                    .map(c => (
                      <button
                        key={c}
                        onClick={() => {
                          setNewHolding({ ...newHolding, coin: c })
                          setCoinSearch('')
                        }}
                        className={`w-full text-left px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 border-b border-gray-100 dark:border-gray-700 last:border-0 transition ${
                          newHolding.coin === c ? 'bg-blue-50 dark:bg-blue-900/30' : ''
                        }`}
                      >
                        <span className="font-medium">{c}</span>
                        <span className="text-gray-500 text-sm ml-2">
                          {prices[c]?.name || ''}
                          {prices[c]?.price ? ` - $${prices[c].price.toLocaleString()}` : ''}
                        </span>
                      </button>
                    ))
                  }
                  {coins.filter(c => {
                    if (!coinSearch) return true
                    const search = coinSearch.toLowerCase()
                    return c.toLowerCase().includes(search) || (prices[c]?.name || '').toLowerCase().includes(search)
                  }).length === 0 && (
                    <div className="px-3 py-4 text-center text-gray-500">
                      "{coinSearch}" bulunamadı
                    </div>
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {coins.length} coin mevcut - arama yaparak filtreleyin
                </p>
              </div>

              {/* Giriş Modu */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Nasıl girmek istiyorsunuz?
                </label>
                <div className="flex gap-2">
                  <button
                    onClick={() => setNewHolding({ ...newHolding, inputMode: 'fiat', amount: '' })}
                    className={`flex-1 py-2 px-4 rounded-lg font-medium transition ${
                      newHolding.inputMode === 'fiat'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                    }`}
                  >
                    💵 Para Birimi
                  </button>
                  <button
                    onClick={() => setNewHolding({ ...newHolding, inputMode: 'crypto', amount: '', currency: 'USD' })}
                    className={`flex-1 py-2 px-4 rounded-lg font-medium transition ${
                      newHolding.inputMode === 'crypto'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                    }`}
                  >
                    🪙 Kripto Miktarı
                  </button>
                </div>
              </div>

              {/* Para Birimi Seçimi (sadece fiat modunda) */}
              {newHolding.inputMode === 'fiat' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Para Birimi
                  </label>
                  <div className="flex gap-2">
                    {[
                      { code: 'USD', symbol: '$', label: 'Dolar' },
                      { code: 'TRY', symbol: '₺', label: 'TL' },
                      { code: 'EUR', symbol: '€', label: 'Euro' },
                    ].map(curr => (
                      <button
                        key={curr.code}
                        onClick={() => setNewHolding({ ...newHolding, currency: curr.code })}
                        className={`flex-1 py-2 px-3 rounded-lg font-medium transition ${
                          newHolding.currency === curr.code
                            ? 'bg-green-500 text-white'
                            : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                        }`}
                      >
                        {curr.symbol} {curr.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Miktar Girişi */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {newHolding.inputMode === 'fiat' 
                    ? `Yatırım Miktarı (${newHolding.currency})`
                    : `${newHolding.coin || 'Kripto'} Miktarı`
                  }
                </label>
                <div className="relative">
                  <input
                    type="number"
                    value={newHolding.amount}
                    onChange={(e) => setNewHolding({ ...newHolding, amount: e.target.value })}
                    placeholder={newHolding.inputMode === 'fiat' ? '1000' : '0.5'}
                    className="w-full px-4 py-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400">
                    {newHolding.inputMode === 'fiat' 
                      ? (newHolding.currency === 'TRY' ? '₺' : newHolding.currency === 'EUR' ? '€' : '$')
                      : newHolding.coin || 'COIN'
                    }
                  </span>
                </div>
              </div>

              {/* Hesaplama Sonucu */}
              {newHolding.coin && newHolding.amount && calculated.cryptoAmount > 0 && (
                <div className="bg-blue-50 dark:bg-blue-900/30 rounded-lg p-4">
                  <div className="text-sm text-blue-600 dark:text-blue-400 font-medium mb-2">
                    📊 Hesaplanan Değerler
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-xs text-gray-500">Kripto Miktarı</div>
                      <div className="font-bold text-gray-900 dark:text-white">
                        {formatCrypto(calculated.cryptoAmount)} {newHolding.coin}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">USD Değeri</div>
                      <div className="font-bold text-gray-900 dark:text-white">
                        {formatMoney(calculated.usdValue)}
                      </div>
                    </div>
                  </div>
                  
                  {/* Dönüşüm detayı */}
                  {newHolding.inputMode === 'fiat' && newHolding.currency !== 'USD' && (
                    <div className="mt-2 text-xs text-gray-500">
                      {newHolding.currency === 'TRY' ? '₺' : '€'}{newHolding.amount} 
                      {' '}÷ {fxRates[newHolding.currency]?.toFixed(2)} 
                      {' '}= ${calculated.usdValue.toFixed(2)}
                    </div>
                  )}
                  
                  <div className="mt-2 text-xs text-gray-500">
                    1 {newHolding.coin} = ${prices[newHolding.coin]?.price?.toLocaleString() || '?'}
                  </div>
                </div>
              )}
            </div>

            <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex gap-3">
              <button
                onClick={() => setShowAdd(false)}
                className="flex-1 py-3 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg font-medium hover:bg-gray-200 transition"
              >
                İptal
              </button>
              <button
                onClick={addHolding}
                disabled={!newHolding.coin || !newHolding.amount || calculated.cryptoAmount <= 0}
                className="flex-1 py-3 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                ✓ Ekle
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Portfolio
