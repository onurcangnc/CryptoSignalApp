// src/pages/DCACalculator.jsx
// DCA (Dollar Cost Averaging) Hesaplayıcı Sayfası

import { useState } from 'react'
import api from '../api'
import { formatPrice } from '../utils/formatters'

const DCACalculator = ({ t, lang }) => {
  // Form state
  const [symbol, setSymbol] = useState('BTC')
  const [totalInvestment, setTotalInvestment] = useState(1000)
  const [frequency, setFrequency] = useState('weekly')
  const [duration, setDuration] = useState(12)

  // Comparison form
  const [compareSymbol, setCompareSymbol] = useState('BTC')
  const [compareAmount, setCompareAmount] = useState(1000)
  const [compareMonths, setCompareMonths] = useState(12)

  // Results
  const [result, setResult] = useState(null)
  const [comparison, setComparison] = useState(null)
  const [loading, setLoading] = useState(false)
  const [compareLoading, setCompareLoading] = useState(false)
  const [error, setError] = useState(null)

  // Tab state
  const [activeTab, setActiveTab] = useState('calculator') // calculator, compare

  const texts = {
    tr: {
      title: 'DCA Hesaplayıcı',
      subtitle: 'Dollar Cost Averaging stratejinizi planlayın',
      calculator: 'Hesaplayıcı',
      compare: 'Karşılaştır',
      coin: 'Coin',
      totalInvestment: 'Toplam Yatırım',
      frequency: 'Alım Sıklığı',
      duration: 'Süre (Ay)',
      calculate: 'Hesapla',
      daily: 'Günlük',
      weekly: 'Haftalık',
      biweekly: 'İki Haftada Bir',
      monthly: 'Aylık',
      results: 'Sonuçlar',
      totalCoins: 'Toplam Coin',
      avgPrice: 'Ortalama Alış Fiyatı',
      currentPrice: 'Mevcut Fiyat',
      currentValue: 'Mevcut Değer',
      profitLoss: 'Kar/Zarar',
      amountPerPurchase: 'Alım Başına Miktar',
      totalPurchases: 'Toplam Alım Sayısı',
      projections: 'Fiyat Senaryoları',
      compareTitle: 'DCA vs Tek Seferde Alım',
      compareSubtitle: 'Hangi strateji daha iyi performans gösterirdi?',
      monthsAgo: 'Kaç Ay Önce Başlasaydı',
      investmentAmount: 'Yatırım Miktarı',
      lumpSum: 'Tek Seferde Alım',
      dcaStrategy: 'DCA Stratejisi',
      winner: 'Kazanan',
      purchasePrice: 'Alış Fiyatı',
      coinsBought: 'Alınan Coin',
      returnPct: 'Getiri',
      insight: 'Değerlendirme',
      breakEven: 'Başabaş Fiyatı',
      error: 'Bir hata oluştu'
    },
    en: {
      title: 'DCA Calculator',
      subtitle: 'Plan your Dollar Cost Averaging strategy',
      calculator: 'Calculator',
      compare: 'Compare',
      coin: 'Coin',
      totalInvestment: 'Total Investment',
      frequency: 'Purchase Frequency',
      duration: 'Duration (Months)',
      calculate: 'Calculate',
      daily: 'Daily',
      weekly: 'Weekly',
      biweekly: 'Bi-weekly',
      monthly: 'Monthly',
      results: 'Results',
      totalCoins: 'Total Coins',
      avgPrice: 'Average Purchase Price',
      currentPrice: 'Current Price',
      currentValue: 'Current Value',
      profitLoss: 'Profit/Loss',
      amountPerPurchase: 'Amount per Purchase',
      totalPurchases: 'Total Purchases',
      projections: 'Price Scenarios',
      compareTitle: 'DCA vs Lump Sum',
      compareSubtitle: 'Which strategy would have performed better?',
      monthsAgo: 'Months Ago',
      investmentAmount: 'Investment Amount',
      lumpSum: 'Lump Sum',
      dcaStrategy: 'DCA Strategy',
      winner: 'Winner',
      purchasePrice: 'Purchase Price',
      coinsBought: 'Coins Bought',
      returnPct: 'Return',
      insight: 'Insight',
      breakEven: 'Break-even Price',
      error: 'An error occurred'
    }
  }

  const txt = texts[lang] || texts.tr

  // Popüler coinler
  const popularCoins = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'DOGE', 'AVAX', 'DOT', 'MATIC']

  const handleCalculate = async () => {
    setLoading(true)
    setError(null)

    try {
      const resp = await api.post('/api/dca/calculate', {
        symbol,
        total_investment: totalInvestment,
        frequency,
        duration_months: duration
      })

      if (resp.ok) {
        setResult(await resp.json())
      } else {
        const err = await resp.json()
        setError(err.detail || txt.error)
      }
    } catch (e) {
      setError(txt.error)
    } finally {
      setLoading(false)
    }
  }

  const handleCompare = async () => {
    setCompareLoading(true)
    setError(null)

    try {
      const resp = await api.post('/api/dca/compare', {
        symbol: compareSymbol,
        investment_amount: compareAmount,
        months_ago: compareMonths
      })

      if (resp.ok) {
        setComparison(await resp.json())
      } else {
        const err = await resp.json()
        setError(err.detail || txt.error)
      }
    } catch (e) {
      setError(txt.error)
    } finally {
      setCompareLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 p-4 md:p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center justify-center gap-3">
            <span className="text-4xl">🧮</span>
            {txt.title}
          </h1>
          <p className="text-gray-400">{txt.subtitle}</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 bg-gray-900 p-1 rounded-xl">
          <button
            onClick={() => setActiveTab('calculator')}
            className={`flex-1 py-3 rounded-lg font-medium transition-all ${
              activeTab === 'calculator'
                ? 'bg-yellow-500 text-black'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            📊 {txt.calculator}
          </button>
          <button
            onClick={() => setActiveTab('compare')}
            className={`flex-1 py-3 rounded-lg font-medium transition-all ${
              activeTab === 'compare'
                ? 'bg-yellow-500 text-black'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            ⚖️ {txt.compare}
          </button>
        </div>

        {/* Calculator Tab */}
        {activeTab === 'calculator' && (
          <div className="space-y-6">
            {/* Calculator Form */}
            <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
              <div className="grid md:grid-cols-2 gap-4">
                {/* Coin Select */}
                <div>
                  <label className="block text-gray-400 text-sm mb-2">{txt.coin}</label>
                  <select
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-yellow-500"
                  >
                    {popularCoins.map(coin => (
                      <option key={coin} value={coin}>{coin}</option>
                    ))}
                  </select>
                </div>

                {/* Total Investment */}
                <div>
                  <label className="block text-gray-400 text-sm mb-2">{txt.totalInvestment} ($)</label>
                  <input
                    type="number"
                    value={totalInvestment}
                    onChange={(e) => setTotalInvestment(Number(e.target.value))}
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-yellow-500"
                    min="10"
                  />
                </div>

                {/* Frequency */}
                <div>
                  <label className="block text-gray-400 text-sm mb-2">{txt.frequency}</label>
                  <select
                    value={frequency}
                    onChange={(e) => setFrequency(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-yellow-500"
                  >
                    <option value="daily">{txt.daily}</option>
                    <option value="weekly">{txt.weekly}</option>
                    <option value="biweekly">{txt.biweekly}</option>
                    <option value="monthly">{txt.monthly}</option>
                  </select>
                </div>

                {/* Duration */}
                <div>
                  <label className="block text-gray-400 text-sm mb-2">{txt.duration}</label>
                  <input
                    type="number"
                    value={duration}
                    onChange={(e) => setDuration(Number(e.target.value))}
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-yellow-500"
                    min="1"
                    max="120"
                  />
                </div>
              </div>

              {/* Calculate Button */}
              <button
                onClick={handleCalculate}
                disabled={loading}
                className="w-full mt-6 py-4 bg-yellow-500 hover:bg-yellow-600 text-black font-bold rounded-xl transition-colors disabled:opacity-50"
              >
                {loading ? '⏳ ...' : `🧮 ${txt.calculate}`}
              </button>
            </div>

            {/* Results */}
            {result && (
              <div className="space-y-4">
                {/* Main Results */}
                <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                  <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    📈 {txt.results}
                  </h3>

                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <ResultCard
                      label={txt.totalCoins}
                      value={result.results.total_coins.toFixed(6)}
                      symbol={result.symbol}
                    />
                    <ResultCard
                      label={txt.avgPrice}
                      value={formatPrice(result.results.average_price)}
                    />
                    <ResultCard
                      label={txt.currentPrice}
                      value={formatPrice(result.results.current_price)}
                    />
                    <ResultCard
                      label={txt.currentValue}
                      value={formatPrice(result.results.current_value)}
                    />
                    <ResultCard
                      label={txt.profitLoss}
                      value={`${result.results.profit_loss >= 0 ? '+' : ''}${formatPrice(result.results.profit_loss)}`}
                      valueColor={result.results.profit_loss >= 0 ? 'text-green-400' : 'text-red-400'}
                      subValue={`${result.results.profit_loss_pct >= 0 ? '+' : ''}${result.results.profit_loss_pct.toFixed(2)}%`}
                    />
                    <ResultCard
                      label={txt.amountPerPurchase}
                      value={formatPrice(result.input.amount_per_purchase)}
                      subValue={`${result.input.total_purchases} ${txt.totalPurchases.toLowerCase()}`}
                    />
                  </div>
                </div>

                {/* Projections */}
                <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                  <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    🔮 {txt.projections}
                  </h3>

                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="text-gray-400 text-sm border-b border-gray-800">
                          <th className="py-2 text-left">Senaryo</th>
                          <th className="py-2 text-right">Fiyat</th>
                          <th className="py-2 text-right">Değer</th>
                          <th className="py-2 text-right">Kar/Zarar</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.projections.map((proj, idx) => (
                          <tr key={idx} className="border-b border-gray-800/50">
                            <td className="py-3 text-white font-medium">{proj.scenario}</td>
                            <td className="py-3 text-right text-gray-300">{formatPrice(proj.price)}</td>
                            <td className="py-3 text-right text-white">{formatPrice(proj.value)}</td>
                            <td className={`py-3 text-right font-medium ${
                              proj.profit_loss >= 0 ? 'text-green-400' : 'text-red-400'
                            }`}>
                              {proj.profit_loss >= 0 ? '+' : ''}{proj.profit_loss_pct.toFixed(1)}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Compare Tab */}
        {activeTab === 'compare' && (
          <div className="space-y-6">
            {/* Compare Form */}
            <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
              <h3 className="text-lg font-bold text-white mb-4">{txt.compareTitle}</h3>
              <p className="text-gray-400 text-sm mb-6">{txt.compareSubtitle}</p>

              <div className="grid md:grid-cols-3 gap-4">
                {/* Coin */}
                <div>
                  <label className="block text-gray-400 text-sm mb-2">{txt.coin}</label>
                  <select
                    value={compareSymbol}
                    onChange={(e) => setCompareSymbol(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-yellow-500"
                  >
                    {popularCoins.map(coin => (
                      <option key={coin} value={coin}>{coin}</option>
                    ))}
                  </select>
                </div>

                {/* Amount */}
                <div>
                  <label className="block text-gray-400 text-sm mb-2">{txt.investmentAmount} ($)</label>
                  <input
                    type="number"
                    value={compareAmount}
                    onChange={(e) => setCompareAmount(Number(e.target.value))}
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-yellow-500"
                    min="10"
                  />
                </div>

                {/* Months Ago */}
                <div>
                  <label className="block text-gray-400 text-sm mb-2">{txt.monthsAgo}</label>
                  <input
                    type="number"
                    value={compareMonths}
                    onChange={(e) => setCompareMonths(Number(e.target.value))}
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-yellow-500"
                    min="1"
                    max="60"
                  />
                </div>
              </div>

              <button
                onClick={handleCompare}
                disabled={compareLoading}
                className="w-full mt-6 py-4 bg-yellow-500 hover:bg-yellow-600 text-black font-bold rounded-xl transition-colors disabled:opacity-50"
              >
                {compareLoading ? '⏳ ...' : `⚖️ ${txt.compare}`}
              </button>
            </div>

            {/* Comparison Results */}
            {comparison && (
              <div className="space-y-4">
                {/* Winner Banner */}
                <div className={`p-6 rounded-2xl text-center ${
                  comparison.comparison.winner === 'lumpsum'
                    ? 'bg-blue-900/30 border border-blue-500/50'
                    : comparison.comparison.winner === 'dca'
                    ? 'bg-green-900/30 border border-green-500/50'
                    : 'bg-yellow-900/30 border border-yellow-500/50'
                }`}>
                  <p className="text-gray-400 text-sm mb-1">{txt.winner}</p>
                  <p className="text-2xl font-bold text-white">
                    {comparison.comparison.winner === 'lumpsum' ? `💰 ${txt.lumpSum}` :
                     comparison.comparison.winner === 'dca' ? `📊 ${txt.dcaStrategy}` : '🤝 Berabere'}
                  </p>
                  <p className="text-gray-300 mt-2">
                    {lang === 'tr' ? 'Fark' : 'Difference'}: {comparison.comparison.difference_pct.toFixed(2)}%
                  </p>
                </div>

                {/* Side by Side Comparison */}
                <div className="grid md:grid-cols-2 gap-4">
                  {/* Lump Sum */}
                  <div className={`bg-gray-900 rounded-2xl p-6 border ${
                    comparison.comparison.winner === 'lumpsum' ? 'border-blue-500' : 'border-gray-800'
                  }`}>
                    <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                      💰 {txt.lumpSum}
                      {comparison.comparison.winner === 'lumpsum' && (
                        <span className="text-xs bg-blue-500 text-white px-2 py-1 rounded">WINNER</span>
                      )}
                    </h4>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-400">{txt.purchasePrice}</span>
                        <span className="text-white">{formatPrice(comparison.lump_sum.purchase_price)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">{txt.coinsBought}</span>
                        <span className="text-white">{comparison.lump_sum.coins_bought.toFixed(6)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">{txt.currentValue}</span>
                        <span className="text-white">{formatPrice(comparison.lump_sum.current_value)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">{txt.returnPct}</span>
                        <span className={comparison.lump_sum.return_pct >= 0 ? 'text-green-400' : 'text-red-400'}>
                          {comparison.lump_sum.return_pct >= 0 ? '+' : ''}{comparison.lump_sum.return_pct.toFixed(2)}%
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* DCA */}
                  <div className={`bg-gray-900 rounded-2xl p-6 border ${
                    comparison.comparison.winner === 'dca' ? 'border-green-500' : 'border-gray-800'
                  }`}>
                    <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                      📊 {txt.dcaStrategy}
                      {comparison.comparison.winner === 'dca' && (
                        <span className="text-xs bg-green-500 text-white px-2 py-1 rounded">WINNER</span>
                      )}
                    </h4>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-400">{txt.avgPrice}</span>
                        <span className="text-white">{formatPrice(comparison.dca.average_price)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">{txt.coinsBought}</span>
                        <span className="text-white">{comparison.dca.coins_bought.toFixed(6)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">{txt.currentValue}</span>
                        <span className="text-white">{formatPrice(comparison.dca.current_value)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">{txt.returnPct}</span>
                        <span className={comparison.dca.return_pct >= 0 ? 'text-green-400' : 'text-red-400'}>
                          {comparison.dca.return_pct >= 0 ? '+' : ''}{comparison.dca.return_pct.toFixed(2)}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Insight */}
                <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                  <h4 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                    💡 {txt.insight}
                  </h4>
                  <p className="text-gray-300 leading-relaxed">{comparison.insight}</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mt-4 p-4 bg-red-900/30 border border-red-500/50 rounded-xl text-red-300">
            ⚠️ {error}
          </div>
        )}
      </div>
    </div>
  )
}

// Result Card Component
const ResultCard = ({ label, value, symbol, subValue, valueColor = 'text-white' }) => (
  <div className="bg-gray-800/50 rounded-xl p-4">
    <p className="text-gray-400 text-xs mb-1">{label}</p>
    <p className={`text-lg font-bold ${valueColor}`}>
      {value} {symbol && <span className="text-gray-500 text-sm">{symbol}</span>}
    </p>
    {subValue && <p className="text-gray-500 text-xs mt-1">{subValue}</p>}
  </div>
)

export default DCACalculator
