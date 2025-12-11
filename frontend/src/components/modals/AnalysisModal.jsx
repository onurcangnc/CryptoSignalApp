// src/components/modals/AnalysisModal.jsx
import { useState, useEffect } from 'react'
import api from '../../api'
import { formatPrice, formatChange } from '../../utils/formatters'

const AnalysisModal = ({ symbol, onClose, t, lang }) => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (symbol) {
      fetchAnalysis()
    }
  }, [symbol])

  const fetchAnalysis = async () => {
    setLoading(true)
    setError(null)
    try {
      const resp = await api.get(`/api/analyze/${symbol}?timeframe=1m`)
      if (resp.ok) {
        setData(await resp.json())
      } else {
        setError('Analiz yapılamadı')
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  if (!symbol) return null

  return (
    <div 
      className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div 
        className="bg-gray-900 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-gray-900 p-4 border-b border-gray-800 flex items-center justify-between">
          <span className="text-xl font-bold text-white">
            {symbol} {lang === 'tr' ? 'Analizi' : 'Analysis'}
          </span>
          <button 
            onClick={onClose} 
            className="text-gray-400 hover:text-white text-2xl transition-colors"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          {loading ? (
            <div className="flex items-center justify-center h-48">
              <div className="text-center">
                <div className="animate-spin text-4xl mb-3">🔄</div>
                <p className="text-gray-400">{t.analyzing}</p>
              </div>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-400 mb-4">{error}</p>
              <button 
                onClick={fetchAnalysis}
                className="px-4 py-2 bg-yellow-500 text-black rounded-lg font-medium hover:bg-yellow-400 transition-colors"
              >
                {t.retry}
              </button>
            </div>
          ) : data ? (
            <div className="space-y-4">
              {/* Signal */}
              <div className={`p-4 rounded-xl text-center ${
                data.recommendation?.includes('AL') || data.recommendation?.includes('BUY') 
                  ? 'bg-green-500/20 border border-green-500/50' 
                  : data.recommendation?.includes('SAT') || data.recommendation?.includes('SELL')
                  ? 'bg-red-500/20 border border-red-500/50'
                  : 'bg-yellow-500/20 border border-yellow-500/50'
              }`}>
                <p className="text-2xl font-bold text-white">{data.recommendation}</p>
                {data.confidence && (
                  <p className="text-gray-300 mt-1">{t.confidence}: {data.confidence}%</p>
                )}
              </div>

              {/* Price Info */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gray-800/50 rounded-xl p-4">
                  <p className="text-gray-400 text-sm">{t.price}</p>
                  <p className="text-xl font-bold text-white">{formatPrice(data.price)}</p>
                </div>
                <div className="bg-gray-800/50 rounded-xl p-4">
                  <p className="text-gray-400 text-sm">{t.change24h}</p>
                  <p className={`text-xl font-bold ${data.change_24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {formatChange(data.change_24h)}
                  </p>
                </div>
              </div>

              {/* Technical Indicators */}
              {data.technical && (
                <div className="bg-gray-800/50 rounded-xl p-4">
                  <p className="text-gray-400 text-sm mb-3">
                    {lang === 'tr' ? 'Teknik Göstergeler' : 'Technical Indicators'}
                  </p>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {data.technical.rsi !== undefined && (
                      <div>
                        <p className="text-gray-500 text-xs">RSI</p>
                        <p className={`font-medium ${
                          data.technical.rsi < 30 ? 'text-green-400' : 
                          data.technical.rsi > 70 ? 'text-red-400' : 'text-white'
                        }`}>
                          {data.technical.rsi?.toFixed(1)}
                        </p>
                      </div>
                    )}
                    {data.technical.macd !== undefined && (
                      <div>
                        <p className="text-gray-500 text-xs">MACD</p>
                        <p className={`font-medium ${data.technical.macd > 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {data.technical.macd?.toFixed(4)}
                        </p>
                      </div>
                    )}
                    {data.technical.ma_50 !== undefined && (
                      <div>
                        <p className="text-gray-500 text-xs">MA50</p>
                        <p className="font-medium text-white">{formatPrice(data.technical.ma_50)}</p>
                      </div>
                    )}
                    {data.technical.ma_200 !== undefined && (
                      <div>
                        <p className="text-gray-500 text-xs">MA200</p>
                        <p className="font-medium text-white">{formatPrice(data.technical.ma_200)}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* AI Analysis */}
              {data.ai_analysis && (
                <div className="bg-gray-800/50 rounded-xl p-4">
                  <p className="text-gray-400 text-sm mb-2">
                    🤖 AI {lang === 'tr' ? 'Analizi' : 'Analysis'}
                  </p>
                  <p className="text-gray-200 whitespace-pre-wrap text-sm leading-relaxed">
                    {data.ai_analysis}
                  </p>
                </div>
              )}

              {/* Futures Data */}
              {data.futures && (
                <div className="bg-gray-800/50 rounded-xl p-4">
                  <p className="text-gray-400 text-sm mb-3">
                    {lang === 'tr' ? 'Vadeli Piyasa' : 'Futures Market'}
                  </p>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <p className="text-gray-500 text-xs">{t.fundingRate}</p>
                      <p className={`font-medium ${
                        data.futures.funding_rate > 0.05 ? 'text-red-400' : 
                        data.futures.funding_rate < -0.02 ? 'text-green-400' : 'text-white'
                      }`}>
                        {data.futures.funding_rate?.toFixed(4)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500 text-xs">{t.longShort}</p>
                      <p className="font-medium text-white">
                        {data.futures.long_short_ratio?.toFixed(2)}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500 text-xs">Open Interest</p>
                      <p className="font-medium text-white">
                        ${(data.futures.open_interest_usd / 1e6)?.toFixed(1)}M
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* News Summary */}
              {data.news_summary && (
                <div className="bg-gray-800/50 rounded-xl p-4">
                  <p className="text-gray-400 text-sm mb-2">
                    📰 {lang === 'tr' ? 'Haber Özeti' : 'News Summary'}
                  </p>
                  <p className="text-gray-300 text-sm">{data.news_summary}</p>
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}

export default AnalysisModal
