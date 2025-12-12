// src/pages/Backtesting.jsx
// Sinyal Geçmişi ve Backtesting Sayfası

import { useState, useEffect } from 'react'
import api from '../api'
import { formatPrice } from '../utils/formatters'

const Backtesting = ({ t, lang }) => {
  // State
  const [activeTab, setActiveTab] = useState('overview') // overview, history, coins, simulate
  const [performance, setPerformance] = useState(null)
  const [history, setHistory] = useState(null)
  const [coinPerformance, setCoinPerformance] = useState(null)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(30)

  // Simulation state
  const [simSymbol, setSimSymbol] = useState('BTC')
  const [simAmount, setSimAmount] = useState(1000)
  const [simDays, setSimDays] = useState(30)
  const [simulation, setSimulation] = useState(null)
  const [simLoading, setSimLoading] = useState(false)

  const texts = {
    tr: {
      title: 'Sinyal Backtesting',
      subtitle: 'Geçmiş sinyallerimizin performansını analiz edin',
      overview: 'Genel Bakış',
      history: 'Sinyal Geçmişi',
      byCoins: 'Coin Bazlı',
      simulate: 'Simülasyon',
      period: 'Dönem',
      days7: '7 Gün',
      days30: '30 Gün',
      days90: '90 Gün',
      totalSignals: 'Toplam Sinyal',
      successRate: 'Başarı Oranı',
      avgReturn: 'Ortalama Getiri',
      bestDay: 'En İyi Gün',
      worstDay: 'En Kötü Gün',
      trend: 'Trend',
      improving: 'Yükselişte',
      declining: 'Düşüşte',
      stable: 'Stabil',
      coin: 'Coin',
      signal: 'Sinyal',
      result: 'Sonuç',
      date: 'Tarih',
      success: 'Başarılı',
      failure: 'Başarısız',
      neutral: 'Nötr',
      bestPerformers: 'En İyi Performans',
      worstPerformers: 'En Kötü Performans',
      runSimulation: 'Simülasyonu Çalıştır',
      initialInvestment: 'Başlangıç Yatırımı',
      finalValue: 'Son Değer',
      totalReturn: 'Toplam Getiri',
      winRate: 'Kazanç Oranı',
      trades: 'İşlem Sayısı',
      noData: 'Veri bulunamadı'
    },
    en: {
      title: 'Signal Backtesting',
      subtitle: 'Analyze the performance of our past signals',
      overview: 'Overview',
      history: 'Signal History',
      byCoins: 'By Coin',
      simulate: 'Simulate',
      period: 'Period',
      days7: '7 Days',
      days30: '30 Days',
      days90: '90 Days',
      totalSignals: 'Total Signals',
      successRate: 'Success Rate',
      avgReturn: 'Avg Return',
      bestDay: 'Best Day',
      worstDay: 'Worst Day',
      trend: 'Trend',
      improving: 'Improving',
      declining: 'Declining',
      stable: 'Stable',
      coin: 'Coin',
      signal: 'Signal',
      result: 'Result',
      date: 'Date',
      success: 'Success',
      failure: 'Failure',
      neutral: 'Neutral',
      bestPerformers: 'Best Performers',
      worstPerformers: 'Worst Performers',
      runSimulation: 'Run Simulation',
      initialInvestment: 'Initial Investment',
      finalValue: 'Final Value',
      totalReturn: 'Total Return',
      winRate: 'Win Rate',
      trades: 'Total Trades',
      noData: 'No data found'
    }
  }

  const txt = texts[lang] || texts.tr

  // Fetch data
  useEffect(() => {
    fetchData()
  }, [days])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [perfResp, histResp, coinResp] = await Promise.all([
        api.get(`/api/backtesting/performance?days=${days}`),
        api.get(`/api/backtesting/history?days=${days}`),
        api.get(`/api/backtesting/by-coin?days=${days}`)
      ])

      if (perfResp.ok) setPerformance(await perfResp.json())
      if (histResp.ok) setHistory(await histResp.json())
      if (coinResp.ok) setCoinPerformance(await coinResp.json())
    } catch (e) {
      console.error('Backtesting fetch error:', e)
    } finally {
      setLoading(false)
    }
  }

  const runSimulation = async () => {
    setSimLoading(true)
    try {
      const resp = await api.get(
        `/api/backtesting/simulate?symbol=${simSymbol}&initial_investment=${simAmount}&days=${simDays}`
      )
      if (resp.ok) {
        setSimulation(await resp.json())
      }
    } catch (e) {
      console.error('Simulation error:', e)
    } finally {
      setSimLoading(false)
    }
  }

  const popularCoins = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'DOGE', 'AVAX']

  return (
    <div className="min-h-screen bg-gray-950 p-4 md:p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center justify-center gap-3">
            <span className="text-4xl">📈</span>
            {txt.title}
          </h1>
          <p className="text-gray-400">{txt.subtitle}</p>
        </div>

        {/* Period Selector */}
        <div className="flex justify-center gap-2 mb-6">
          {[
            { value: 7, label: txt.days7 },
            { value: 30, label: txt.days30 },
            { value: 90, label: txt.days90 }
          ].map(({ value, label }) => (
            <button
              key={value}
              onClick={() => setDays(value)}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                days === value
                  ? 'bg-yellow-500 text-black'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-gray-900 p-1 rounded-xl overflow-x-auto">
          {[
            { id: 'overview', icon: '📊', label: txt.overview },
            { id: 'history', icon: '📜', label: txt.history },
            { id: 'coins', icon: '🪙', label: txt.byCoins },
            { id: 'simulate', icon: '🎮', label: txt.simulate }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all whitespace-nowrap ${
                activeTab === tab.id
                  ? 'bg-yellow-500 text-black'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>

        {/* Loading */}
        {loading && activeTab !== 'simulate' ? (
          <div className="text-center py-20">
            <div className="animate-spin text-4xl mb-3">⏳</div>
            <p className="text-gray-400">Loading...</p>
          </div>
        ) : (
          <>
            {/* Overview Tab */}
            {activeTab === 'overview' && performance && (
              <div className="space-y-6">
                {/* Main Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <StatCard
                    icon="📊"
                    label={txt.totalSignals}
                    value={performance.overall?.total_signals || 0}
                  />
                  <StatCard
                    icon="🎯"
                    label={txt.successRate}
                    value={`${performance.overall?.success_rate || 0}%`}
                    valueColor={
                      performance.overall?.success_rate >= 60
                        ? 'text-green-400'
                        : performance.overall?.success_rate >= 40
                        ? 'text-yellow-400'
                        : 'text-red-400'
                    }
                  />
                  <StatCard
                    icon="💰"
                    label={txt.avgReturn}
                    value={`${performance.overall?.avg_return >= 0 ? '+' : ''}${performance.overall?.avg_return || 0}%`}
                    valueColor={performance.overall?.avg_return >= 0 ? 'text-green-400' : 'text-red-400'}
                  />
                  <StatCard
                    icon={performance.trend?.trend === 'improving' ? '📈' : performance.trend?.trend === 'declining' ? '📉' : '➡️'}
                    label={txt.trend}
                    value={
                      performance.trend?.trend === 'improving' ? txt.improving :
                      performance.trend?.trend === 'declining' ? txt.declining : txt.stable
                    }
                    valueColor={
                      performance.trend?.trend === 'improving' ? 'text-green-400' :
                      performance.trend?.trend === 'declining' ? 'text-red-400' : 'text-yellow-400'
                    }
                  />
                </div>

                {/* Trend Info */}
                {performance.trend && (
                  <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                    <h3 className="text-lg font-bold text-white mb-4">📈 Trend Analizi</h3>
                    <p className="text-gray-300">{performance.trend.description}</p>
                    <div className="mt-4 grid grid-cols-2 gap-4">
                      <div className="bg-gray-800/50 rounded-lg p-3">
                        <p className="text-gray-400 text-sm">Son 7 Gün Ort.</p>
                        <p className="text-xl font-bold text-white">{performance.trend.recent_avg}%</p>
                      </div>
                      <div className="bg-gray-800/50 rounded-lg p-3">
                        <p className="text-gray-400 text-sm">Önceki 7 Gün Ort.</p>
                        <p className="text-xl font-bold text-white">{performance.trend.previous_avg}%</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Weekly Performance */}
                {performance.weekly && performance.weekly.length > 0 && (
                  <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                    <h3 className="text-lg font-bold text-white mb-4">📅 Haftalık Performans</h3>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="text-gray-400 text-sm border-b border-gray-800">
                            <th className="py-2 text-left">Hafta</th>
                            <th className="py-2 text-right">Sinyal</th>
                            <th className="py-2 text-right">Başarılı</th>
                            <th className="py-2 text-right">Oran</th>
                            <th className="py-2 text-right">Getiri</th>
                          </tr>
                        </thead>
                        <tbody>
                          {performance.weekly.map((week, idx) => (
                            <tr key={idx} className="border-b border-gray-800/50">
                              <td className="py-3 text-white">{week.week_start}</td>
                              <td className="py-3 text-right text-gray-300">{week.total_signals}</td>
                              <td className="py-3 text-right text-green-400">{week.successful}</td>
                              <td className="py-3 text-right">
                                <span className={week.success_rate >= 50 ? 'text-green-400' : 'text-red-400'}>
                                  {week.success_rate}%
                                </span>
                              </td>
                              <td className={`py-3 text-right ${week.avg_return >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                {week.avg_return >= 0 ? '+' : ''}{week.avg_return}%
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* History Tab */}
            {activeTab === 'history' && history && (
              <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                <h3 className="text-lg font-bold text-white mb-4">
                  📜 Son {history.total_signals} Sinyal
                </h3>
                {history.signals && history.signals.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="text-gray-400 text-sm border-b border-gray-800">
                          <th className="py-2 text-left">{txt.coin}</th>
                          <th className="py-2 text-left">{txt.signal}</th>
                          <th className="py-2 text-right">Fiyat</th>
                          <th className="py-2 text-right">{txt.result}</th>
                          <th className="py-2 text-right">{txt.date}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {history.signals.slice(0, 50).map((signal, idx) => (
                          <tr key={idx} className="border-b border-gray-800/50">
                            <td className="py-3">
                              <span className="font-medium text-white">{signal.coin}</span>
                            </td>
                            <td className="py-3">
                              <span className={`px-2 py-1 rounded text-xs font-medium ${
                                signal.signal?.includes('AL') || signal.signal?.includes('BUY')
                                  ? 'bg-green-500/20 text-green-400'
                                  : signal.signal?.includes('SAT') || signal.signal?.includes('SELL')
                                  ? 'bg-red-500/20 text-red-400'
                                  : 'bg-yellow-500/20 text-yellow-400'
                              }`}>
                                {signal.signal}
                              </span>
                            </td>
                            <td className="py-3 text-right text-gray-300">
                              {formatPrice(signal.price_at_signal)}
                            </td>
                            <td className="py-3 text-right">
                              <span className={`font-medium ${
                                signal.outcome === 'success' ? 'text-green-400' :
                                signal.outcome === 'failure' ? 'text-red-400' : 'text-gray-400'
                              }`}>
                                {signal.result_pct >= 0 ? '+' : ''}{signal.result_pct?.toFixed(2)}%
                              </span>
                            </td>
                            <td className="py-3 text-right text-gray-500 text-sm">
                              {new Date(signal.created_at).toLocaleDateString(lang === 'tr' ? 'tr-TR' : 'en-US')}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-gray-400 text-center py-8">{txt.noData}</p>
                )}
              </div>
            )}

            {/* Coins Tab */}
            {activeTab === 'coins' && coinPerformance && (
              <div className="space-y-6">
                {/* Best Performers */}
                {coinPerformance.best_performers && coinPerformance.best_performers.length > 0 && (
                  <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                      🏆 {txt.bestPerformers}
                    </h3>
                    <div className="grid md:grid-cols-5 gap-4">
                      {coinPerformance.best_performers.map((coin, idx) => (
                        <CoinCard key={idx} coin={coin} rank={idx + 1} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Worst Performers */}
                {coinPerformance.worst_performers && coinPerformance.worst_performers.length > 0 && (
                  <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                      ⚠️ {txt.worstPerformers}
                    </h3>
                    <div className="grid md:grid-cols-5 gap-4">
                      {coinPerformance.worst_performers.map((coin, idx) => (
                        <CoinCard key={idx} coin={coin} isWorst />
                      ))}
                    </div>
                  </div>
                )}

                {/* All Coins Table */}
                <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                  <h3 className="text-lg font-bold text-white mb-4">
                    🪙 Tüm Coinler ({coinPerformance.total_coins})
                  </h3>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="text-gray-400 text-sm border-b border-gray-800">
                          <th className="py-2 text-left">Coin</th>
                          <th className="py-2 text-right">Sinyal</th>
                          <th className="py-2 text-right">Başarılı</th>
                          <th className="py-2 text-right">Oran</th>
                          <th className="py-2 text-right">Ort. Getiri</th>
                        </tr>
                      </thead>
                      <tbody>
                        {coinPerformance.coins?.map((coin, idx) => (
                          <tr key={idx} className="border-b border-gray-800/50">
                            <td className="py-3 font-medium text-white">{coin.symbol}</td>
                            <td className="py-3 text-right text-gray-300">{coin.total_signals}</td>
                            <td className="py-3 text-right text-green-400">{coin.successful}</td>
                            <td className="py-3 text-right">
                              <span className={coin.success_rate >= 50 ? 'text-green-400' : 'text-red-400'}>
                                {coin.success_rate}%
                              </span>
                            </td>
                            <td className={`py-3 text-right ${coin.avg_return >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {coin.avg_return >= 0 ? '+' : ''}{coin.avg_return}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* Simulate Tab */}
            {activeTab === 'simulate' && (
              <div className="space-y-6">
                {/* Simulation Form */}
                <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                  <h3 className="text-lg font-bold text-white mb-4">🎮 Strateji Simülasyonu</h3>
                  <p className="text-gray-400 text-sm mb-6">
                    Sinyallerimizi takip etseydiniz ne olurdu? Simüle edin.
                  </p>

                  <div className="grid md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-gray-400 text-sm mb-2">{txt.coin}</label>
                      <select
                        value={simSymbol}
                        onChange={(e) => setSimSymbol(e.target.value)}
                        className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white"
                      >
                        {popularCoins.map(coin => (
                          <option key={coin} value={coin}>{coin}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-gray-400 text-sm mb-2">{txt.initialInvestment} ($)</label>
                      <input
                        type="number"
                        value={simAmount}
                        onChange={(e) => setSimAmount(Number(e.target.value))}
                        className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white"
                        min="100"
                      />
                    </div>
                    <div>
                      <label className="block text-gray-400 text-sm mb-2">{txt.period}</label>
                      <select
                        value={simDays}
                        onChange={(e) => setSimDays(Number(e.target.value))}
                        className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white"
                      >
                        <option value={7}>{txt.days7}</option>
                        <option value={30}>{txt.days30}</option>
                        <option value={90}>{txt.days90}</option>
                      </select>
                    </div>
                  </div>

                  <button
                    onClick={runSimulation}
                    disabled={simLoading}
                    className="w-full mt-6 py-4 bg-yellow-500 hover:bg-yellow-600 text-black font-bold rounded-xl transition-colors disabled:opacity-50"
                  >
                    {simLoading ? '⏳ ...' : `🎮 ${txt.runSimulation}`}
                  </button>
                </div>

                {/* Simulation Results */}
                {simulation && simulation.simulation && (
                  <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                    <h3 className="text-lg font-bold text-white mb-4">
                      📊 {simulation.symbol} Simülasyon Sonuçları
                    </h3>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      <StatCard
                        icon="💵"
                        label={txt.initialInvestment}
                        value={`$${simulation.initial_investment}`}
                      />
                      <StatCard
                        icon="💰"
                        label={txt.finalValue}
                        value={`$${simulation.simulation.final_value}`}
                        valueColor={simulation.simulation.total_return >= 0 ? 'text-green-400' : 'text-red-400'}
                      />
                      <StatCard
                        icon="📈"
                        label={txt.totalReturn}
                        value={`${simulation.simulation.total_return_pct >= 0 ? '+' : ''}${simulation.simulation.total_return_pct}%`}
                        valueColor={simulation.simulation.total_return_pct >= 0 ? 'text-green-400' : 'text-red-400'}
                      />
                      <StatCard
                        icon="🎯"
                        label={txt.winRate}
                        value={`${simulation.simulation.win_rate}%`}
                      />
                    </div>

                    <div className="bg-gray-800/50 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-2">{txt.trades}: {simulation.simulation.total_trades}</p>
                      <p className="text-gray-300">
                        ✅ Kazanç: {simulation.simulation.wins} | ❌ Kayıp: {simulation.simulation.losses}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

// Stat Card Component
const StatCard = ({ icon, label, value, valueColor = 'text-white' }) => (
  <div className="bg-gray-800/50 rounded-xl p-4">
    <div className="flex items-center gap-2 mb-2">
      <span className="text-xl">{icon}</span>
      <span className="text-gray-400 text-sm">{label}</span>
    </div>
    <p className={`text-2xl font-bold ${valueColor}`}>{value}</p>
  </div>
)

// Coin Card Component
const CoinCard = ({ coin, rank, isWorst }) => (
  <div className={`bg-gray-800/50 rounded-xl p-4 border ${
    isWorst ? 'border-red-500/30' : 'border-green-500/30'
  }`}>
    <div className="flex items-center justify-between mb-2">
      <span className="font-bold text-white">{coin.symbol}</span>
      {rank && <span className="text-yellow-400 text-sm">#{rank}</span>}
    </div>
    <p className={`text-2xl font-bold ${
      coin.success_rate >= 50 ? 'text-green-400' : 'text-red-400'
    }`}>
      {coin.success_rate}%
    </p>
    <p className="text-gray-500 text-xs mt-1">{coin.total_signals} sinyal</p>
  </div>
)

export default Backtesting
