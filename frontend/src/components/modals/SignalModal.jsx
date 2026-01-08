// src/components/modals/SignalModal.jsx
import { formatPrice, formatChange, getSignalColor } from '../../utils/formatters'

const SignalModal = ({ signal, onClose, t, lang }) => {
  if (!signal) return null

  return (
    <div 
      className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div 
        className="bg-gray-900 rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-gray-900 p-4 border-b border-gray-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-2xl font-bold text-white">{signal.symbol}</span>
            <span className={`px-3 py-1 rounded-lg text-sm font-medium text-white ${getSignalColor(signal.signal)}`}>
              {signal.signal_tr || signal.signal}
            </span>
          </div>
          <button 
            onClick={onClose} 
            className="text-gray-400 hover:text-white text-2xl transition-colors"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* Price & Change */}
          <div className="bg-gray-800/50 rounded-xl p-4">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-gray-400 text-sm">{t.price}</p>
                <p className="text-2xl font-bold text-white">{formatPrice(signal.price)}</p>
              </div>
              <div className="text-right">
                <p className="text-gray-400 text-sm">{t.change24h}</p>
                <p className={`text-xl font-bold ${signal.change_24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {formatChange(signal.change_24h)}
                </p>
              </div>
            </div>
          </div>

          {/* Exit Strategy */}
          {signal.take_profit && signal.stop_loss && (
            <div className="bg-gradient-to-r from-green-500/10 to-red-500/10 rounded-xl p-4 border border-gray-700/50">
              <p className="text-gray-400 text-sm mb-3">🎯 Çıkış Stratejisi</p>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">🟢</span>
                    <span className="text-gray-300">Kâr Al (Take Profit)</span>
                  </div>
                  <div className="text-right">
                    <p className="text-green-400 font-bold">{formatPrice(signal.take_profit)}</p>
                    <p className="text-green-400/70 text-xs">+{signal.take_profit_pct?.toFixed(1)}%</p>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">🔴</span>
                    <span className="text-gray-300">Zarar Kes (Stop Loss)</span>
                  </div>
                  <div className="text-right">
                    <p className="text-red-400 font-bold">{formatPrice(signal.stop_loss)}</p>
                    <p className="text-red-400/70 text-xs">-{signal.stop_loss_pct?.toFixed(1)}%</p>
                  </div>
                </div>
                {signal.risk_reward_ratio && (
                  <div className="pt-2 border-t border-gray-700 flex justify-between items-center">
                    <span className="text-gray-500 text-sm">Risk/Reward Oranı</span>
                    <span className="text-blue-400 font-bold">{signal.risk_reward_ratio}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Confidence & Risk */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-800/50 rounded-xl p-4 text-center">
              <p className="text-gray-400 text-sm mb-1">{t.confidence}</p>
              <p className="text-3xl font-bold text-yellow-400">{signal.confidence}%</p>
            </div>
            <div className="bg-gray-800/50 rounded-xl p-4 text-center">
              <p className="text-gray-400 text-sm mb-1">{t.risk}</p>
              <p className={`text-xl font-bold ${
                signal.risk_level === 'low' ? 'text-green-400' :
                signal.risk_level === 'high' ? 'text-red-400' : 'text-yellow-400'
              }`}>
                {signal.risk_tr || signal.risk_level}
              </p>
            </div>
          </div>

          {/* Simple Explanation */}
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
            <p className="text-blue-400 font-medium mb-2">
              💡 {lang === 'tr' ? 'Ne Anlama Geliyor?' : 'What Does This Mean?'}
            </p>
            <p className="text-white">{signal.simple_reason || signal.simple_tr}</p>
          </div>

          {/* Reasons */}
          {signal.reasons && signal.reasons.length > 0 && (
            <div className="bg-gray-800/50 rounded-xl p-4">
              <p className="text-gray-400 text-sm mb-3">
                {lang === 'tr' ? 'Analiz Detayları' : 'Analysis Details'}
              </p>
              <div className="space-y-2">
                {signal.reasons.map((reason, i) => (
                  <p key={i} className="text-gray-300 text-sm">• {reason}</p>
                ))}
              </div>
            </div>
          )}

          {/* Futures Data */}
          {signal.futures && (signal.futures.funding_rate !== undefined || signal.futures.long_short_ratio !== undefined) && (
            <div className="bg-gray-800/50 rounded-xl p-4">
              <p className="text-gray-400 text-sm mb-3">
                {lang === 'tr' ? 'Vadeli İşlem Verileri' : 'Futures Data'}
              </p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-gray-500 text-xs">{t.fundingRate}</p>
                  <p className={`font-medium ${
                    signal.futures.funding_rate > 0.05 ? 'text-red-400' : 
                    signal.futures.funding_rate < -0.02 ? 'text-green-400' : 'text-white'
                  }`}>
                    {signal.futures.funding_rate?.toFixed(4)}%
                  </p>
                </div>
                <div>
                  <p className="text-gray-500 text-xs">{t.longShort}</p>
                  <p className={`font-medium ${
                    signal.futures.long_short_ratio > 2 ? 'text-red-400' : 
                    signal.futures.long_short_ratio < 0.7 ? 'text-green-400' : 'text-white'
                  }`}>
                    {signal.futures.long_short_ratio?.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Component Scores */}
          {signal.components && (
            <div className="bg-gray-800/50 rounded-xl p-4">
              <p className="text-gray-400 text-sm mb-3">
                {lang === 'tr' ? 'Analiz Skorları' : 'Analysis Scores'}
              </p>
              <div className="space-y-2">
                {Object.entries(signal.components).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between">
                    <span className="text-gray-400 text-sm capitalize">
                      {key === 'technical' ? (lang === 'tr' ? 'Teknik' : 'Technical') :
                       key === 'momentum' ? 'Momentum' :
                       key === 'futures' ? (lang === 'tr' ? 'Vadeli' : 'Futures') :
                       key === 'sentiment' ? (lang === 'tr' ? 'Duygu' : 'Sentiment') :
                       key === 'structure' ? (lang === 'tr' ? 'Yapı' : 'Structure') : key}
                    </span>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div 
                          className={`h-full transition-all ${
                            value >= 60 ? 'bg-green-500' : 
                            value >= 40 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${value}%` }}
                        />
                      </div>
                      <span className="text-white text-sm w-8">{Math.round(value)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Risk Factors */}
          {signal.risk_factors && signal.risk_factors.length > 0 && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4">
              <p className="text-red-400 font-medium mb-2">
                ⚠️ {lang === 'tr' ? 'Risk Faktörleri' : 'Risk Factors'}
              </p>
              <div className="space-y-1">
                {signal.risk_factors.map((risk, i) => (
                  <p key={i} className="text-red-300 text-sm">• {risk}</p>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-900 p-4 border-t border-gray-800">
          <button
            onClick={onClose}
            className="w-full py-3 bg-gray-700 hover:bg-gray-600 rounded-xl text-white font-medium transition-colors"
          >
            {t.close}
          </button>
        </div>
      </div>
    </div>
  )
}

export default SignalModal
