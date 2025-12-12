import { useState, useEffect } from 'react'
import api from '../api'
import { formatPrice } from '../utils/formatters'

/**
 * Price Alert Modal - Alarm Oluşturma
 */
export const CreateAlertModal = ({ coin, currentPrice, onClose, onSuccess, lang }) => {
  const [targetPrice, setTargetPrice] = useState('')
  const [condition, setCondition] = useState('above') // 'above' or 'below'
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!targetPrice || targetPrice <= 0) {
      setError(lang === 'tr' ? 'Geçerli bir fiyat girin' : 'Enter a valid price')
      return
    }

    setLoading(true)

    try {
      const resp = await api.post('/api/price-alerts', {
        symbol: coin.symbol || coin.id?.toUpperCase(),
        target_price: parseFloat(targetPrice),
        condition: condition
      })

      if (resp.ok) {
        onSuccess && onSuccess()
        onClose()
      } else {
        const data = await resp.json()
        setError(data.detail || 'Alarm oluşturulamadı')
      }
    } catch (err) {
      setError(lang === 'tr' ? 'Bir hata oluştu' : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-xl max-w-md w-full p-6 border border-gray-700">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            🔔 {lang === 'tr' ? 'Fiyat Alarmı Kur' : 'Set Price Alert'}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Coin Info */}
        <div className="bg-gray-900/50 rounded-lg p-3 mb-4">
          <div className="text-sm text-gray-400">{lang === 'tr' ? 'Coin' : 'Coin'}</div>
          <div className="text-lg font-bold text-white">{coin.symbol || coin.id?.toUpperCase()}</div>
          <div className="text-sm text-gray-400 mt-1">
            {lang === 'tr' ? 'Mevcut Fiyat' : 'Current Price'}: <span className="text-white font-mono">{formatPrice(currentPrice)}</span>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Condition Selection */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              {lang === 'tr' ? 'Alarm Koşulu' : 'Alert Condition'}
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setCondition('above')}
                className={`p-3 rounded-lg border transition-all ${
                  condition === 'above'
                    ? 'bg-green-500/20 border-green-500 text-green-400'
                    : 'bg-gray-700 border-gray-600 text-gray-400 hover:border-gray-500'
                }`}
              >
                <div className="text-2xl mb-1">📈</div>
                <div className="text-sm font-medium">
                  {lang === 'tr' ? 'Yukarı Çıkarsa' : 'Goes Above'}
                </div>
              </button>
              <button
                type="button"
                onClick={() => setCondition('below')}
                className={`p-3 rounded-lg border transition-all ${
                  condition === 'below'
                    ? 'bg-red-500/20 border-red-500 text-red-400'
                    : 'bg-gray-700 border-gray-600 text-gray-400 hover:border-gray-500'
                }`}
              >
                <div className="text-2xl mb-1">📉</div>
                <div className="text-sm font-medium">
                  {lang === 'tr' ? 'Aşağı Düşerse' : 'Goes Below'}
                </div>
              </button>
            </div>
          </div>

          {/* Target Price */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              {lang === 'tr' ? 'Hedef Fiyat ($)' : 'Target Price ($)'}
            </label>
            <input
              type="number"
              step="0.00000001"
              value={targetPrice}
              onChange={(e) => setTargetPrice(e.target.value)}
              placeholder={lang === 'tr' ? 'Örn: 50000' : 'e.g. 50000'}
              className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-yellow-500 transition-colors"
            />
          </div>

          {/* Preview */}
          {targetPrice && (
            <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-3">
              <div className="text-sm text-blue-300">
                💡 {lang === 'tr' ? 'Bildirim alacaksınız:' : 'You will be notified:'}
              </div>
              <div className="text-white mt-1">
                {coin.symbol} fiyatı <span className="font-bold">${targetPrice}</span>
                {condition === 'above'
                  ? lang === 'tr' ? " değerinin üstüne çıktığında" : " goes above"
                  : lang === 'tr' ? " değerinin altına düştüğünde" : " goes below"
                }
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="bg-red-900/20 border border-red-700/50 rounded-lg p-3 text-red-400 text-sm">
              ⚠️ {error}
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={loading || !targetPrice}
            className="w-full py-3 bg-yellow-500 hover:bg-yellow-600 text-gray-900 font-bold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? '⏳ Oluşturuluyor...' : lang === 'tr' ? '🔔 Alarmı Kur' : '🔔 Create Alert'}
          </button>
        </form>
      </div>
    </div>
  )
}

/**
 * Price Alerts List - Alarmlar Listesi
 */
export const PriceAlertsList = ({ lang, refreshKey }) => {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAlerts()
  }, [refreshKey])

  const fetchAlerts = async () => {
    try {
      const resp = await api.get('/api/price-alerts')
      if (resp.ok) {
        const data = await resp.json()
        setAlerts(data.alerts || [])
      }
    } catch (error) {
      console.error('Alerts fetch error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (alertId) => {
    try {
      const resp = await api.delete(`/api/price-alerts/${alertId}`)
      if (resp.ok) {
        setAlerts(prev => prev.filter(a => a.id !== alertId))
      }
    } catch (error) {
      console.error('Alert delete error:', error)
    }
  }

  if (loading) {
    return (
      <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
        <h3 className="text-gray-400 text-sm mb-3 flex items-center gap-2">
          🔔 {lang === 'tr' ? 'Aktif Alarmlar' : 'Active Alerts'}
        </h3>
        <div className="text-center py-4 text-gray-500">
          {lang === 'tr' ? 'Yükleniyor...' : 'Loading...'}
        </div>
      </div>
    )
  }

  if (alerts.length === 0) {
    return (
      <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
        <h3 className="text-gray-400 text-sm mb-3 flex items-center gap-2">
          🔔 {lang === 'tr' ? 'Aktif Alarmlar' : 'Active Alerts'}
        </h3>
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-2">🔕</div>
          <div className="text-sm">
            {lang === 'tr'
              ? 'Henüz alarm kurmadınız. Coin listesinden alarm ekleyin.'
              : 'No alerts yet. Add alerts from the coin list.'}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
      <h3 className="text-gray-400 text-sm mb-3 flex items-center gap-2">
        🔔 {lang === 'tr' ? 'Aktif Alarmlar' : 'Active Alerts'}
        <span className="text-xs">({alerts.length})</span>
      </h3>
      <div className="space-y-2">
        {alerts.map((alert) => {
          const isTriggered = alert.triggered === 1
          const conditionText = alert.condition === 'above'
            ? lang === 'tr' ? '📈 Yukarı' : '📈 Above'
            : lang === 'tr' ? '📉 Aşağı' : '📉 Below'

          return (
            <div
              key={alert.id}
              className={`flex items-center justify-between p-3 rounded-lg border transition-all ${
                isTriggered
                  ? 'bg-green-900/20 border-green-700/50'
                  : 'bg-gray-700/30 border-gray-700/50 hover:border-gray-600'
              }`}
            >
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-white">{alert.symbol}</span>
                  <span className="text-xs text-gray-500">{conditionText}</span>
                  {isTriggered && (
                    <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded">
                      ✅ {lang === 'tr' ? 'Tetiklendi' : 'Triggered'}
                    </span>
                  )}
                </div>
                <div className="text-sm text-gray-400 mt-1">
                  {lang === 'tr' ? 'Hedef' : 'Target'}: <span className="text-white font-mono">${alert.target_price.toFixed(2)}</span>
                </div>
                {isTriggered && alert.triggered_at && (
                  <div className="text-xs text-gray-500 mt-1">
                    {new Date(alert.triggered_at).toLocaleString(lang === 'tr' ? 'tr-TR' : 'en-US')}
                  </div>
                )}
              </div>
              <button
                onClick={() => handleDelete(alert.id)}
                className="ml-3 text-red-400 hover:text-red-300 transition-colors"
                title={lang === 'tr' ? 'Alarmı Sil' : 'Delete Alert'}
              >
                🗑️
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default PriceAlertsList
