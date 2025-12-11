// src/components/PortfolioSimulator.jsx
// Portfolio Simulator - What-if scenarios and Monte Carlo simulations
import { useState } from 'react'
import api from '../api'

const PortfolioSimulator = ({ portfolio, prices, lang }) => {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [selectedScenario, setSelectedScenario] = useState('market_drop')
  const [parameters, setParameters] = useState({
    drop_percentage: 20,
    coin: 'BTC',
    sell_percentage: 50,
    amount: 1000,
    iterations: 1000,
    days: 30
  })

  const scenarios = [
    {
      id: 'market_drop',
      icon: '📉',
      title: lang === 'tr' ? 'Piyasa Düşüşü' : 'Market Drop',
      description: lang === 'tr' ? 'Piyasa %X düşerse ne olur?' : 'What if market drops X%?',
      params: ['drop_percentage']
    },
    {
      id: 'sell_position',
      icon: '💰',
      title: lang === 'tr' ? 'Pozisyon Sat' : 'Sell Position',
      description: lang === 'tr' ? 'Bir varlığın %X\'ini satarsam?' : 'What if I sell X% of an asset?',
      params: ['coin', 'sell_percentage']
    },
    {
      id: 'add_funds',
      icon: '➕',
      title: lang === 'tr' ? 'Fon Ekle' : 'Add Funds',
      description: lang === 'tr' ? '$X değerinde coin eklersem?' : 'What if I add $X worth of coin?',
      params: ['amount', 'coin']
    },
    {
      id: 'monte_carlo',
      icon: '🎲',
      title: 'Monte Carlo',
      description: lang === 'tr' ? 'Olasılık bazlı gelecek simülasyonu' : 'Probability-based future simulation',
      params: ['iterations', 'days']
    }
  ]

  const runSimulation = async () => {
    setLoading(true)
    setResults(null)

    try {
      const resp = await api.post('/api/admin/simulator/run', {
        scenario_type: selectedScenario,
        parameters
      })

      if (resp.ok) {
        const data = await resp.json()
        setResults(data)
      } else {
        const err = await resp.json()
        alert(err.detail || 'Simulation failed')
      }
    } catch (e) {
      alert('Error: ' + e.message)
    } finally {
      setLoading(false)
    }
  }

  const holdings = portfolio?.holdings || []
  const coins = holdings.map(h => h.coin).filter(Boolean)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">
          🎮 {lang === 'tr' ? 'Portföy Simülatörü' : 'Portfolio Simulator'}
        </h2>
        <p className="text-gray-400 text-sm">
          {lang === 'tr'
            ? 'Farklı senaryoları test edin ve portföyünüzün nasıl etkileneceğini görün'
            : 'Test different scenarios and see how your portfolio would be affected'}
        </p>
      </div>

      {/* Scenario Selection */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {scenarios.map(scenario => (
          <button
            key={scenario.id}
            onClick={() => setSelectedScenario(scenario.id)}
            className={`p-4 rounded-xl border-2 transition-all text-left ${
              selectedScenario === scenario.id
                ? 'bg-blue-500/20 border-blue-500 scale-105'
                : 'bg-gray-800/50 border-gray-700/50 hover:border-gray-600'
            }`}
          >
            <div className="text-3xl mb-2">{scenario.icon}</div>
            <div className="font-bold text-white text-sm">{scenario.title}</div>
            <div className="text-gray-400 text-xs mt-1">{scenario.description}</div>
          </button>
        ))}
      </div>

      {/* Parameters */}
      <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700/50">
        <h3 className="text-lg font-bold text-white mb-4">
          ⚙️ {lang === 'tr' ? 'Parametreler' : 'Parameters'}
        </h3>

        <div className="grid md:grid-cols-2 gap-4">
          {/* Market Drop */}
          {selectedScenario === 'market_drop' && (
            <div>
              <label className="block text-gray-300 text-sm mb-2">
                {lang === 'tr' ? 'Düşüş Yüzdesi (%)' : 'Drop Percentage (%)'}
              </label>
              <input
                type="number"
                value={parameters.drop_percentage}
                onChange={(e) => setParameters({ ...parameters, drop_percentage: parseFloat(e.target.value) })}
                className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                min="1"
                max="100"
              />
            </div>
          )}

          {/* Sell Position */}
          {selectedScenario === 'sell_position' && (
            <>
              <div>
                <label className="block text-gray-300 text-sm mb-2">
                  {lang === 'tr' ? 'Coin Seç' : 'Select Coin'}
                </label>
                <select
                  value={parameters.coin}
                  onChange={(e) => setParameters({ ...parameters, coin: e.target.value })}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                >
                  {coins.map(coin => (
                    <option key={coin} value={coin}>{coin}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-gray-300 text-sm mb-2">
                  {lang === 'tr' ? 'Satış Yüzdesi (%)' : 'Sell Percentage (%)'}
                </label>
                <input
                  type="number"
                  value={parameters.sell_percentage}
                  onChange={(e) => setParameters({ ...parameters, sell_percentage: parseFloat(e.target.value) })}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="100"
                />
              </div>
            </>
          )}

          {/* Add Funds */}
          {selectedScenario === 'add_funds' && (
            <>
              <div>
                <label className="block text-gray-300 text-sm mb-2">
                  {lang === 'tr' ? 'Miktar ($)' : 'Amount ($)'}
                </label>
                <input
                  type="number"
                  value={parameters.amount}
                  onChange={(e) => setParameters({ ...parameters, amount: parseFloat(e.target.value) })}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                  min="10"
                  step="10"
                />
              </div>
              <div>
                <label className="block text-gray-300 text-sm mb-2">
                  {lang === 'tr' ? 'Hangi Coin?' : 'Which Coin?'}
                </label>
                <select
                  value={parameters.coin}
                  onChange={(e) => setParameters({ ...parameters, coin: e.target.value })}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                >
                  {coins.map(coin => (
                    <option key={coin} value={coin}>{coin}</option>
                  ))}
                  <option value="BTC">BTC</option>
                  <option value="ETH">ETH</option>
                </select>
              </div>
            </>
          )}

          {/* Monte Carlo */}
          {selectedScenario === 'monte_carlo' && (
            <>
              <div>
                <label className="block text-gray-300 text-sm mb-2">
                  {lang === 'tr' ? 'Simülasyon Sayısı' : 'Iterations'}
                </label>
                <input
                  type="number"
                  value={parameters.iterations}
                  onChange={(e) => setParameters({ ...parameters, iterations: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                  min="100"
                  max="10000"
                  step="100"
                />
              </div>
              <div>
                <label className="block text-gray-300 text-sm mb-2">
                  {lang === 'tr' ? 'Gün Sayısı' : 'Days'}
                </label>
                <input
                  type="number"
                  value={parameters.days}
                  onChange={(e) => setParameters({ ...parameters, days: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="365"
                />
              </div>
            </>
          )}
        </div>

        {/* Run Button */}
        <button
          onClick={runSimulation}
          disabled={loading || !holdings.length}
          className="mt-6 w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin">⚙️</div>
              {lang === 'tr' ? 'Simüle ediliyor...' : 'Simulating...'}
            </>
          ) : (
            <>
              ▶️ {lang === 'tr' ? 'Simülasyonu Çalıştır' : 'Run Simulation'}
            </>
          )}
        </button>
      </div>

      {/* Results */}
      {results && results.success && (
        <div className="bg-gradient-to-br from-green-900/20 to-blue-900/20 border border-green-500/30 rounded-xl p-6">
          <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            📊 {lang === 'tr' ? 'Simülasyon Sonuçları' : 'Simulation Results'}
          </h3>

          {/* Scenario Description */}
          <div className="mb-4">
            <p className="text-gray-300 text-sm">{results.scenario}</p>
          </div>

          {/* Simple Scenarios */}
          {(selectedScenario === 'market_drop' || selectedScenario === 'sell_position' || selectedScenario === 'add_funds') && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="bg-gray-900/50 rounded-lg p-4">
                <p className="text-gray-400 text-xs mb-1">
                  {lang === 'tr' ? 'Mevcut Değer' : 'Current Value'}
                </p>
                <p className="text-2xl font-bold text-white">
                  ${results.current_value?.toLocaleString()}
                </p>
              </div>

              <div className="bg-gray-900/50 rounded-lg p-4">
                <p className="text-gray-400 text-xs mb-1">
                  {selectedScenario === 'market_drop'
                    ? (lang === 'tr' ? 'Yeni Değer' : 'New Value')
                    : selectedScenario === 'sell_position'
                    ? (lang === 'tr' ? 'Satış Tutarı' : 'Sell Amount')
                    : (lang === 'tr' ? 'Eklenen' : 'Added')}
                </p>
                <p className="text-2xl font-bold text-blue-400">
                  ${(results.new_value || results.sell_amount || results.added_amount)?.toLocaleString()}
                </p>
              </div>

              {selectedScenario === 'market_drop' && (
                <div className="bg-gray-900/50 rounded-lg p-4">
                  <p className="text-gray-400 text-xs mb-1">
                    {lang === 'tr' ? 'Kayıp' : 'Loss'}
                  </p>
                  <p className="text-2xl font-bold text-red-400">
                    -${results.loss?.toLocaleString()} ({results.loss_pct?.toFixed(1)}%)
                  </p>
                </div>
              )}

              {selectedScenario === 'sell_position' && (
                <div className="bg-gray-900/50 rounded-lg p-4">
                  <p className="text-gray-400 text-xs mb-1">
                    {lang === 'tr' ? 'Nakit' : 'Cash'}
                  </p>
                  <p className="text-2xl font-bold text-green-400">
                    ${results.cash_generated?.toLocaleString()}
                  </p>
                </div>
              )}

              {selectedScenario === 'add_funds' && (
                <div className="bg-gray-900/50 rounded-lg p-4">
                  <p className="text-gray-400 text-xs mb-1">
                    {lang === 'tr' ? 'Alınan Miktar' : 'Coin Quantity'}
                  </p>
                  <p className="text-2xl font-bold text-green-400">
                    {results.coin_quantity?.toLocaleString()} {parameters.coin}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Monte Carlo Results */}
          {selectedScenario === 'monte_carlo' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-gray-900/50 rounded-lg p-3">
                  <p className="text-gray-400 text-xs mb-1">
                    {lang === 'tr' ? 'Mevcut' : 'Current'}
                  </p>
                  <p className="text-lg font-bold text-white">
                    ${results.current_value?.toLocaleString()}
                  </p>
                </div>

                <div className="bg-green-900/30 rounded-lg p-3">
                  <p className="text-green-400 text-xs mb-1">
                    {lang === 'tr' ? 'En İyi Durum' : 'Best Case'}
                  </p>
                  <p className="text-lg font-bold text-green-400">
                    ${results.best_case?.toLocaleString()}
                  </p>
                </div>

                <div className="bg-red-900/30 rounded-lg p-3">
                  <p className="text-red-400 text-xs mb-1">
                    {lang === 'tr' ? 'En Kötü Durum' : 'Worst Case'}
                  </p>
                  <p className="text-lg font-bold text-red-400">
                    ${results.worst_case?.toLocaleString()}
                  </p>
                </div>

                <div className="bg-blue-900/30 rounded-lg p-3">
                  <p className="text-blue-400 text-xs mb-1">
                    {lang === 'tr' ? 'Ortalama' : 'Average'}
                  </p>
                  <p className="text-lg font-bold text-blue-400">
                    ${results.average?.toLocaleString()}
                  </p>
                </div>
              </div>

              {/* Percentiles */}
              <div className="bg-gray-900/50 rounded-lg p-4">
                <p className="text-gray-300 text-sm mb-3">
                  {lang === 'tr' ? 'Yüzdelik Dilimleri' : 'Percentiles'}
                </p>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-gray-400 text-xs">10th</p>
                    <p className="text-white font-bold">
                      ${results.percentile_10?.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs">50th (Median)</p>
                    <p className="text-white font-bold">
                      ${results.median?.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs">90th</p>
                    <p className="text-white font-bold">
                      ${results.percentile_90?.toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>

              {/* Interpretation */}
              <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
                <p className="text-blue-300 text-sm">
                  💡 {lang === 'tr'
                    ? `${parameters.iterations} simülasyonda ${parameters.days} gün sonrası: Portföyünüzün %90 ihtimalle $${results.percentile_10?.toLocaleString()} ile $${results.percentile_90?.toLocaleString()} arasında olacağı tahmin ediliyor.`
                    : `After ${parameters.days} days in ${parameters.iterations} simulations: Your portfolio has a 90% chance of being between $${results.percentile_10?.toLocaleString()} and $${results.percentile_90?.toLocaleString()}.`
                  }
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default PortfolioSimulator
