// src/pages/AISummary.jsx
// AI Portfolio Intelligence Dashboard
import { useState, useEffect } from 'react'
import api from '../api'
import { formatPrice, formatChange } from '../utils/formatters'

const AISummary = ({ t, lang, user }) => {
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    fetchSummary()
  }, [])

  const fetchSummary = async () => {
    setLoading(true)
    setError(null)
    try {
      const resp = await api.get('/api/ai-summary/portfolio')
      if (resp.ok) {
        const result = await resp.json()
        // Check if it's an error response (empty portfolio)
        if (result.success === false) {
          setData(null)
          setError(result.message || result.error)
        } else {
          setData(result)
        }
      } else {
        const err = await resp.json()
        setError(err.detail || 'Failed to load summary')
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const generateFreshAnalysis = async () => {
    setGenerating(true)
    setError(null)
    try {
      const resp = await api.post('/api/ai-summary/analyze')
      if (resp.ok) {
        const result = await resp.json()
        // Check if it's an error response (empty portfolio)
        if (result.success === false) {
          setData(null)
          setError(result.message || result.error)
        } else {
          setData(result)
        }
      } else {
        const err = await resp.json()
        if (resp.status === 429) {
          setError(lang === 'tr'
            ? `⚠️ Günlük AI limiti doldu. ${err.reset_time} UTC'de sıfırlanacak.`
            : `⚠️ Daily AI limit reached. Resets at ${err.reset_time} UTC.`)
        } else {
          setError(err.detail || 'Analysis failed')
        }
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setGenerating(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-3 md:px-6 py-6">
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="animate-spin text-5xl mb-4">🤖</div>
            <p className="text-gray-400">{lang === 'tr' ? 'AI analizi yükleniyor...' : 'Loading AI analysis...'}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-3 md:px-6 py-4 md:py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white flex items-center gap-2">
            🤖 {lang === 'tr' ? 'AI Portföy İstihbaratı' : 'AI Portfolio Intelligence'}
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            {lang === 'tr' 
              ? 'Portföyünüze özel AI destekli analizler ve tahminler' 
              : 'AI-powered analysis and predictions for your portfolio'}
          </p>
        </div>
        <button
          onClick={generateFreshAnalysis}
          disabled={generating}
          className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg text-white font-medium hover:opacity-90 disabled:opacity-50 transition-opacity flex items-center gap-2"
        >
          {generating ? (
            <>
              <div className="animate-spin">⚙️</div>
              {lang === 'tr' ? 'Analiz ediliyor...' : 'Analyzing...'}
            </>
          ) : (
            <>
              ✨ {lang === 'tr' ? 'Yeni Analiz' : 'Fresh Analysis'}
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {data ? (
        <>
          {/* Tabs */}
          <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
            {[
              { id: 'overview', icon: '📊', label: lang === 'tr' ? 'Genel Bakış' : 'Overview' },
              { id: 'signals', icon: '🎯', label: lang === 'tr' ? 'Trading Sinyalleri' : 'Signals' },
              { id: 'forecasting', icon: '📈', label: lang === 'tr' ? 'Tahminler' : 'Forecasting' },
              { id: 'alerts', icon: '🔔', label: lang === 'tr' ? 'Akıllı Uyarılar' : 'Smart Alerts' },
              { id: 'technical', icon: '📉', label: lang === 'tr' ? 'Teknik Analiz' : 'Technical' },
              { id: 'predictions', icon: '🔮', label: lang === 'tr' ? 'Fiyat Hedefleri' : 'Predictions' },
              { id: 'news', icon: '📰', label: lang === 'tr' ? 'Haberler' : 'News' },
              { id: 'actions', icon: '⚡', label: lang === 'tr' ? 'Aksiyonlar' : 'Actions' },
              { id: 'risk', icon: '⚠️', label: 'Risk' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 rounded-lg font-medium transition-all whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white'
                    : 'bg-gray-800/50 text-gray-400 hover:text-white hover:bg-gray-700/50'
                }`}
              >
                <span className="mr-1">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>

          {/* Content */}
          {activeTab === 'overview' && <OverviewTab data={data} lang={lang} />}
          {activeTab === 'signals' && <SignalsTab data={data} lang={lang} />}
          {activeTab === 'forecasting' && <ForecastingTab data={data} lang={lang} />}
          {activeTab === 'alerts' && <AlertsTab data={data} lang={lang} />}
          {activeTab === 'technical' && <TechnicalTab data={data} lang={lang} />}
          {activeTab === 'predictions' && <PredictionsTab data={data} lang={lang} />}
          {activeTab === 'news' && <NewsTab data={data} lang={lang} />}
          {activeTab === 'actions' && <ActionsTab data={data} lang={lang} />}
          {activeTab === 'risk' && <RiskTab data={data} lang={lang} />}

          {/* Timestamp */}
          <div className="mt-6 text-center">
            <p className="text-gray-500 text-xs">
              {lang === 'tr' ? 'Son güncelleme' : 'Last updated'}: {new Date(data.generated_at).toLocaleString(lang === 'tr' ? 'tr-TR' : 'en-US')}
            </p>
            <p className="text-gray-600 text-xs mt-1">
              ⚡ {lang === 'tr' ? 'Gerçek zamanlı verilerle güncellenir' : 'Updates with real-time data'}
            </p>
          </div>
        </>
      ) : (
        <EmptyState lang={lang} onGenerate={generateFreshAnalysis} />
      )}
    </div>
  )
}

// ============================================================================
// OVERVIEW TAB
// ============================================================================
const OverviewTab = ({ data, lang }) => {
  const healthScore = data.portfolio_health?.score || 50
  const healthColor = healthScore >= 75 ? 'text-green-400' : healthScore >= 50 ? 'text-yellow-400' : 'text-red-400'
  const healthLabel = healthScore >= 75 
    ? (lang === 'tr' ? 'Sağlıklı' : 'Healthy')
    : healthScore >= 50 
    ? (lang === 'tr' ? 'Orta' : 'Fair')
    : (lang === 'tr' ? 'Risk Altında' : 'At Risk')

  return (
    <div className="space-y-6">
      {/* Portfolio Health Score */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-6 border border-gray-700/50">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white">
            {lang === 'tr' ? '🏥 Portföy Sağlık Skoru' : '🏥 Portfolio Health Score'}
          </h2>
          <span className={`text-3xl font-bold ${healthColor}`}>
            {healthScore}/100
          </span>
        </div>
        
        {/* Progress Bar */}
        <div className="h-3 bg-gray-700 rounded-full overflow-hidden mb-2">
          <div 
            className={`h-full transition-all duration-1000 ${
              healthScore >= 75 ? 'bg-green-500' : healthScore >= 50 ? 'bg-yellow-500' : 'bg-red-500'
            }`}
            style={{ width: `${healthScore}%` }}
          />
        </div>
        <p className={`text-center font-medium ${healthColor}`}>{healthLabel}</p>
        
        {/* Explanation */}
        {data.portfolio_health?.summary && (
          <p className="text-gray-300 mt-4 text-sm leading-relaxed">
            {data.portfolio_health.summary}
          </p>
        )}
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard
          icon="💰"
          label={lang === 'tr' ? 'Toplam Değer' : 'Total Value'}
          value={`$${data.total_value?.toLocaleString() || '0'}`}
          change={data.total_change_24h}
        />
        <MetricCard
          icon="📈"
          label={lang === 'tr' ? 'Kazanç/Kayıp' : 'Profit/Loss'}
          value={`${data.total_pnl >= 0 ? '+' : ''}$${data.total_pnl?.toLocaleString() || '0'}`}
          change={data.total_pnl_pct}
          changeLabel="%"
        />
        <MetricCard
          icon="🎯"
          label={lang === 'tr' ? 'Çeşitlendirme' : 'Diversification'}
          value={`${data.diversification_score || 50}/100`}
        />
        <MetricCard
          icon="⚠️"
          label={lang === 'tr' ? 'Risk Seviyesi' : 'Risk Level'}
          value={data.risk_level_tr || data.risk_level || 'Medium'}
        />
      </div>

      {/* Market Context */}
      {data.market_context && (
        <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700/50">
          <h3 className="text-lg font-bold text-white mb-4">
            🌍 {lang === 'tr' ? 'Piyasa Bağlamı' : 'Market Context'}
          </h3>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <p className="text-gray-400 text-sm mb-1">
                {lang === 'tr' ? 'Portföy Performansı' : 'Portfolio Performance'}
              </p>
              <p className={`text-2xl font-bold ${data.portfolio_vs_market > 0 ? 'text-green-400' : 'text-red-400'}`}>
                {data.portfolio_vs_market > 0 ? '+' : ''}{data.portfolio_vs_market?.toFixed(2)}%
              </p>
              <p className="text-gray-500 text-xs mt-1">
                {lang === 'tr' ? 'vs Piyasa Ortalaması' : 'vs Market Average'}
              </p>
            </div>
            <div>
              <p className="text-gray-400 text-sm mb-1">Fear & Greed Index</p>
              <p className="text-2xl font-bold text-yellow-400">
                {data.market_context.fear_greed}
              </p>
              <p className="text-gray-500 text-xs mt-1">
                {data.market_context.fear_greed_label}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Top Holdings */}
      {data.top_holdings && data.top_holdings.length > 0 && (
        <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700/50">
          <h3 className="text-lg font-bold text-white mb-4">
            🏆 {lang === 'tr' ? 'En Büyük Pozisyonlar' : 'Top Holdings'}
          </h3>
          <div className="space-y-3">
            {data.top_holdings.map((holding, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-gray-500 text-sm">#{i + 1}</span>
                  <div>
                    <p className="font-medium text-white">{holding.symbol}</p>
                    <p className="text-gray-400 text-xs">
                      {holding.allocation?.toFixed(1)}% {lang === 'tr' ? 'portföyden' : 'of portfolio'}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-medium text-white">{formatPrice(holding.value)}</p>
                  <p className={`text-sm ${holding.pnl_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {formatChange(holding.pnl_pct)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ============================================================================
// PREDICTIONS TAB
// ============================================================================
const PredictionsTab = ({ data, lang }) => {
  if (!data.predictions || data.predictions.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-5xl mb-4">🔮</div>
        <p className="text-gray-400">
          {lang === 'tr' ? 'Tahmin bulunamadı' : 'No predictions available'}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {data.predictions.map((pred, i) => (
        <div key={i} className="bg-gray-800/50 rounded-xl p-6 border border-gray-700/50 hover:border-gray-600/50 transition-colors">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-xl font-bold text-white">{pred.symbol}</h3>
              <p className="text-gray-400 text-sm">{pred.timeframe}</p>
            </div>
            <span className={`px-3 py-1 rounded-lg text-sm font-medium ${
              pred.direction === 'bullish' ? 'bg-green-500/20 text-green-400' :
              pred.direction === 'bearish' ? 'bg-red-500/20 text-red-400' :
              'bg-yellow-500/20 text-yellow-400'
            }`}>
              {pred.direction === 'bullish' ? '📈 Bullish' :
               pred.direction === 'bearish' ? '📉 Bearish' : '➡️ Neutral'}
            </span>
          </div>

          {/* Price Prediction */}
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="text-center">
              <p className="text-gray-500 text-xs mb-1">
                {lang === 'tr' ? 'Mevcut' : 'Current'}
              </p>
              <p className="text-white font-medium">{formatPrice(pred.current_price)}</p>
            </div>
            <div className="text-center">
              <p className="text-gray-500 text-xs mb-1">
                {lang === 'tr' ? 'Hedef' : 'Target'}
              </p>
              <p className="text-blue-400 font-bold">{formatPrice(pred.target_price)}</p>
            </div>
            <div className="text-center">
              <p className="text-gray-500 text-xs mb-1">
                {lang === 'tr' ? 'Potansiyel' : 'Potential'}
              </p>
              <p className={`font-bold ${pred.potential_gain >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {pred.potential_gain >= 0 ? '+' : ''}{pred.potential_gain?.toFixed(1)}%
              </p>
            </div>
          </div>

          {/* Confidence */}
          <div className="mb-4">
            <div className="flex justify-between mb-1">
              <span className="text-gray-400 text-sm">
                {lang === 'tr' ? 'Güven Seviyesi' : 'Confidence Level'}
              </span>
              <span className="text-white text-sm font-medium">{pred.confidence}%</span>
            </div>
            <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
              <div 
                className="h-full bg-blue-500 transition-all"
                style={{ width: `${pred.confidence}%` }}
              />
            </div>
          </div>

          {/* AI Reasoning */}
          {pred.reasoning && (
            <div className="bg-gray-900/50 rounded-lg p-4">
              <p className="text-gray-400 text-xs mb-2">
                🤖 {lang === 'tr' ? 'AI Analizi' : 'AI Analysis'}
              </p>
              <p className="text-gray-300 text-sm leading-relaxed">{pred.reasoning}</p>
            </div>
          )}

          {/* Key Factors */}
          {pred.key_factors && pred.key_factors.length > 0 && (
            <div className="mt-4">
              <p className="text-gray-400 text-xs mb-2">
                {lang === 'tr' ? 'Anahtar Faktörler' : 'Key Factors'}
              </p>
              <div className="flex flex-wrap gap-2">
                {pred.key_factors.map((factor, j) => (
                  <span key={j} className="px-2 py-1 bg-gray-700 rounded text-gray-300 text-xs">
                    {factor}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

// ============================================================================
// NEWS TAB
// ============================================================================
const NewsTab = ({ data, lang }) => {
  if (!data.personalized_news || data.personalized_news.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-5xl mb-4">📰</div>
        <p className="text-gray-400">
          {lang === 'tr' ? 'Portföyünüze özel haber bulunamadı' : 'No personalized news available'}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Summary */}
      {data.news_summary && (
        <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/30 rounded-xl p-6">
          <h3 className="text-lg font-bold text-white mb-3">
            📋 {lang === 'tr' ? 'Haber Özeti' : 'News Summary'}
          </h3>
          <p className="text-gray-200 leading-relaxed">{data.news_summary}</p>
        </div>
      )}

      {/* News Items */}
      {data.personalized_news.map((item, i) => (
        <div key={i} className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50 hover:border-gray-600/50 transition-colors">
          {/* Title */}
          <h4 className="font-bold text-white mb-2 leading-snug">{item.title}</h4>
          
          {/* AI Insight */}
          {item.ai_insight && (
            <div className="bg-purple-900/30 border-l-4 border-purple-500 p-3 mb-3 rounded-r">
              <p className="text-purple-200 text-sm leading-relaxed">
                💡 {item.ai_insight}
              </p>
            </div>
          )}

          {/* Content */}
          {item.content && (
            <p className="text-gray-400 text-sm mb-3 line-clamp-2">{item.content}</p>
          )}

          {/* Meta */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {/* Sentiment */}
            <span className={`px-2 py-1 rounded-full font-medium ${
              item.sentiment === 'bullish' ? 'bg-green-500/20 text-green-400' :
              item.sentiment === 'bearish' ? 'bg-red-500/20 text-red-400' :
              'bg-gray-700 text-gray-400'
            }`}>
              {item.sentiment === 'bullish' ? '📈 Bullish' :
               item.sentiment === 'bearish' ? '📉 Bearish' : '➡️ Neutral'}
            </span>

            {/* Relevance */}
            {item.relevance_score && (
              <span className="px-2 py-1 bg-blue-900/30 text-blue-400 rounded">
                🎯 {item.relevance_score}% {lang === 'tr' ? 'ilgili' : 'relevant'}
              </span>
            )}

            {/* Affected Coins */}
            {item.affected_coins && item.affected_coins.length > 0 && (
              <div className="flex gap-1">
                {item.affected_coins.map(coin => (
                  <span key={coin} className="px-2 py-1 bg-yellow-900/30 text-yellow-400 rounded">
                    {coin}
                  </span>
                ))}
              </div>
            )}

            {/* Source & Time */}
            <span className="text-gray-500 ml-auto">{item.source}</span>
            {item.published_at && (
              <span className="text-gray-600">
                {new Date(item.published_at).toLocaleDateString()}
              </span>
            )}
          </div>

          {/* Link */}
          {item.url && (
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 text-xs mt-2"
            >
              {lang === 'tr' ? 'Haberi Oku' : 'Read Article'} →
            </a>
          )}
        </div>
      ))}
    </div>
  )
}

// ============================================================================
// ACTIONS TAB
// ============================================================================
const ActionsTab = ({ data, lang }) => {
  if (!data.action_items || data.action_items.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-5xl mb-4">⚡</div>
        <p className="text-gray-400">
          {lang === 'tr' ? 'Aksiyon önerisi bulunamadı' : 'No action items available'}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {data.action_items.map((action, i) => (
        <div 
          key={i} 
          className={`rounded-xl p-6 border-2 ${
            action.priority === 'high' ? 'bg-red-500/10 border-red-500/50' :
            action.priority === 'medium' ? 'bg-yellow-500/10 border-yellow-500/50' :
            'bg-blue-500/10 border-blue-500/50'
          }`}
        >
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <span className="text-3xl">
                {action.type === 'buy' ? '🟢' :
                 action.type === 'sell' ? '🔴' :
                 action.type === 'hold' ? '🟡' :
                 action.type === 'rebalance' ? '⚖️' : '💡'}
              </span>
              <div>
                <h3 className="text-lg font-bold text-white">{action.title}</h3>
                <p className="text-gray-400 text-sm">{action.symbol || 'Portfolio'}</p>
              </div>
            </div>
            <span className={`px-3 py-1 rounded-lg text-xs font-bold uppercase ${
              action.priority === 'high' ? 'bg-red-500 text-white' :
              action.priority === 'medium' ? 'bg-yellow-500 text-black' :
              'bg-blue-500 text-white'
            }`}>
              {action.priority === 'high' ? (lang === 'tr' ? 'ACİL' : 'URGENT') :
               action.priority === 'medium' ? (lang === 'tr' ? 'ÖNEM' : 'MEDIUM') :
               (lang === 'tr' ? 'BİLGİ' : 'INFO')}
            </span>
          </div>

          {/* Description */}
          <p className="text-gray-300 mb-4 leading-relaxed">{action.description}</p>

          {/* Reasoning */}
          {action.reasoning && (
            <div className="bg-gray-900/50 rounded-lg p-4 mb-4">
              <p className="text-gray-400 text-xs mb-2">
                {lang === 'tr' ? 'Neden?' : 'Why?'}
              </p>
              <p className="text-gray-300 text-sm">{action.reasoning}</p>
            </div>
          )}

          {/* Expected Impact */}
          {action.expected_impact && (
            <div className="flex items-center gap-2 mb-4">
              <span className="text-gray-400 text-sm">
                {lang === 'tr' ? 'Beklenen Etki:' : 'Expected Impact:'}
              </span>
              <span className={`font-medium ${
                action.impact_direction === 'positive' ? 'text-green-400' : 'text-red-400'
              }`}>
                {action.expected_impact}
              </span>
            </div>
          )}

          {/* Timeframe */}
          {action.timeframe && (
            <div className="flex items-center gap-2">
              <span className="text-gray-400 text-sm">⏰</span>
              <span className="text-gray-300 text-sm">{action.timeframe}</span>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

// ============================================================================
// RISK TAB
// ============================================================================
const RiskTab = ({ data, lang }) => {
  return (
    <div className="space-y-6">
      {/* Overall Risk Score */}
      <div className="bg-gradient-to-br from-red-900/20 to-orange-900/20 border border-red-500/30 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white">
            ⚠️ {lang === 'tr' ? 'Toplam Risk Skoru' : 'Overall Risk Score'}
          </h2>
          <span className={`text-3xl font-bold ${
            data.risk_score >= 7 ? 'text-red-400' :
            data.risk_score >= 4 ? 'text-yellow-400' : 'text-green-400'
          }`}>
            {data.risk_score || 5}/10
          </span>
        </div>
        <p className="text-gray-300 text-sm">
          {data.risk_summary || (lang === 'tr' 
            ? 'Portföyünüzün genel risk durumu değerlendiriliyor...'
            : 'Evaluating overall portfolio risk...')}
        </p>
      </div>

      {/* Risk Factors */}
      {data.risk_factors && data.risk_factors.length > 0 && (
        <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700/50">
          <h3 className="text-lg font-bold text-white mb-4">
            🔍 {lang === 'tr' ? 'Risk Faktörleri' : 'Risk Factors'}
          </h3>
          <div className="space-y-3">
            {data.risk_factors.map((factor, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-gray-900/50 rounded-lg">
                <span className={`text-xl ${
                  factor.severity === 'high' ? 'text-red-400' :
                  factor.severity === 'medium' ? 'text-yellow-400' : 'text-blue-400'
                }`}>
                  {factor.severity === 'high' ? '🚨' :
                   factor.severity === 'medium' ? '⚠️' : 'ℹ️'}
                </span>
                <div className="flex-1">
                  <p className="font-medium text-white">{factor.title}</p>
                  <p className="text-gray-400 text-sm mt-1">{factor.description}</p>
                  {factor.mitigation && (
                    <p className="text-green-400 text-xs mt-2">
                      💡 {lang === 'tr' ? 'Öneri:' : 'Mitigation:'} {factor.mitigation}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Diversification Analysis */}
      <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700/50">
        <h3 className="text-lg font-bold text-white mb-4">
          🎯 {lang === 'tr' ? 'Çeşitlendirme Analizi' : 'Diversification Analysis'}
        </h3>
        
        <div className="space-y-4">
          {/* Score */}
          <div>
            <div className="flex justify-between mb-2">
              <span className="text-gray-400 text-sm">
                {lang === 'tr' ? 'Çeşitlendirme Skoru' : 'Diversification Score'}
              </span>
              <span className="text-white font-medium">
                {data.diversification_score || 50}/100
              </span>
            </div>
            <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all ${
                  data.diversification_score >= 70 ? 'bg-green-500' :
                  data.diversification_score >= 40 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${data.diversification_score || 50}%` }}
              />
            </div>
          </div>

          {/* Breakdown */}
          {data.asset_allocation && (
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(data.asset_allocation).map(([category, percentage]) => (
                <div key={category} className="bg-gray-900/50 rounded-lg p-3">
                  <p className="text-gray-400 text-xs mb-1">{category}</p>
                  <p className="text-white font-bold">{percentage}%</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Volatility Alert */}
      {data.high_volatility_assets && data.high_volatility_assets.length > 0 && (
        <div className="bg-orange-900/20 border border-orange-500/30 rounded-xl p-6">
          <h3 className="text-lg font-bold text-orange-400 mb-4">
            📊 {lang === 'tr' ? 'Yüksek Volatilite Uyarısı' : 'High Volatility Alert'}
          </h3>
          <p className="text-gray-300 text-sm mb-3">
            {lang === 'tr' 
              ? 'Aşağıdaki varlıklar yüksek volatilite gösteriyor:'
              : 'The following assets are showing high volatility:'}
          </p>
          <div className="flex flex-wrap gap-2">
            {data.high_volatility_assets.map(asset => (
              <span key={asset} className="px-3 py-1 bg-orange-500/20 text-orange-300 rounded-lg font-medium">
                {asset}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ============================================================================
// HELPER COMPONENTS
// ============================================================================
const MetricCard = ({ icon, label, value, change, changeLabel = '' }) => (
  <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
    <div className="flex items-center gap-2 mb-2">
      <span className="text-xl">{icon}</span>
      <span className="text-gray-400 text-xs">{label}</span>
    </div>
    <p className="text-xl font-bold text-white mb-1">{value}</p>
    {change !== undefined && change !== null && (
      <p className={`text-sm font-medium ${change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
        {change >= 0 ? '↗' : '↘'} {Math.abs(change).toFixed(2)}{changeLabel}
      </p>
    )}
  </div>
)

const EmptyState = ({ lang, onGenerate }) => (
  <div className="text-center py-12">
    <div className="text-6xl mb-4">🤖</div>
    <h3 className="text-xl font-bold text-white mb-2">
      {lang === 'tr' ? 'AI Analizi Başlatın' : 'Start AI Analysis'}
    </h3>
    <p className="text-gray-400 mb-6 max-w-md mx-auto">
      {lang === 'tr'
        ? 'Portföyünüz için özel AI destekli analizler, tahminler ve öneriler alın.'
        : 'Get personalized AI-powered analysis, predictions, and recommendations for your portfolio.'}
    </p>
    <button
      onClick={onGenerate}
      className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg text-white font-medium hover:opacity-90 transition-opacity"
    >
      ✨ {lang === 'tr' ? 'İlk Analizi Oluştur' : 'Generate First Analysis'}
    </button>
  </div>
)

// ============================================================================
// NEW CRITICAL TABS (4)
// ============================================================================

// 🎯 TRADING SIGNALS TAB
const SignalsTab = ({ data, lang }) => {
  if (!data.trading_signals || data.trading_signals.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-5xl mb-4">🎯</div>
        <p className="text-gray-400">
          {lang === 'tr' ? 'Trading sinyali bulunamadı' : 'No trading signals available'}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {data.trading_signals.map((signal, i) => (
        <div key={i} className={`rounded-xl p-6 border-2 ${
          signal.signal === 'BUY' || signal.signal === 'ACCUMULATE'
            ? 'bg-green-500/10 border-green-500/50'
            : signal.signal === 'SELL'
            ? 'bg-red-500/10 border-red-500/50'
            : 'bg-yellow-500/10 border-yellow-500/50'
        }`}>
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <span className="text-4xl">
                {signal.signal === 'BUY' ? '🟢' :
                 signal.signal === 'SELL' ? '🔴' :
                 signal.signal === 'ACCUMULATE' ? '🟡' : '⚪'}
              </span>
              <div>
                <h3 className="text-2xl font-bold text-white">{signal.coin}</h3>
                <p className="text-gray-400">${signal.current_price?.toLocaleString()}</p>
              </div>
            </div>
            <div className="text-right">
              <span className={`px-4 py-2 rounded-lg text-lg font-bold ${
                signal.signal === 'BUY' || signal.signal === 'ACCUMULATE'
                  ? 'bg-green-500 text-white'
                  : signal.signal === 'SELL'
                  ? 'bg-red-500 text-white'
                  : 'bg-yellow-500 text-black'
              }`}>
                {signal.signal}
              </span>
              <p className="text-gray-400 text-sm mt-2">
                {lang === 'tr' ? 'Güç' : 'Strength'}: {signal.strength}/10
              </p>
            </div>
          </div>

          {/* Entry Range */}
          {signal.entry_range && signal.entry_range.length > 0 && (
            <div className="bg-gray-900/50 rounded-lg p-4 mb-4">
              <p className="text-gray-400 text-sm mb-2">
                {lang === 'tr' ? '📍 Giriş Aralığı' : '📍 Entry Range'}
              </p>
              <p className="text-green-400 font-bold text-lg">
                ${signal.entry_range[0]?.toLocaleString()} - ${signal.entry_range[1]?.toLocaleString()}
              </p>
            </div>
          )}

          {/* Targets & Stop Loss */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            {signal.targets && signal.targets.map((target, idx) => (
              <div key={idx} className="bg-blue-900/30 rounded-lg p-3 text-center">
                <p className="text-gray-400 text-xs mb-1">
                  {lang === 'tr' ? 'Hedef' : 'Target'} {idx + 1}
                </p>
                <p className="text-blue-400 font-bold">${target?.toLocaleString()}</p>
              </div>
            ))}
            {signal.stop_loss && (
              <div className="bg-red-900/30 rounded-lg p-3 text-center">
                <p className="text-gray-400 text-xs mb-1">
                  {lang === 'tr' ? 'Stop Loss' : 'Stop Loss'}
                </p>
                <p className="text-red-400 font-bold">${signal.stop_loss?.toLocaleString()}</p>
              </div>
            )}
          </div>

          {/* Risk/Reward & Timeframe */}
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className="bg-gray-800/50 rounded-lg p-3 text-center">
              <p className="text-gray-400 text-xs mb-1">R/R</p>
              <p className="text-white font-bold">{signal.risk_reward}x</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3 text-center">
              <p className="text-gray-400 text-xs mb-1">
                {lang === 'tr' ? 'Güven' : 'Confidence'}
              </p>
              <p className="text-white font-bold">{signal.confidence}%</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3 text-center">
              <p className="text-gray-400 text-xs mb-1">
                {lang === 'tr' ? 'Zaman' : 'Time'}
              </p>
              <p className="text-white font-medium text-sm">{signal.timeframe}</p>
            </div>
          </div>

          {/* AI Reasoning */}
          {signal.reasoning && (
            <div className="bg-purple-900/30 border-l-4 border-purple-500 p-4 mb-3 rounded-r">
              <p className="text-purple-200 text-sm leading-relaxed">
                🤖 {signal.reasoning}
              </p>
            </div>
          )}

          {/* Key Indicators */}
          {signal.key_indicators && signal.key_indicators.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {signal.key_indicators.map((indicator, j) => (
                <span key={j} className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded-lg text-sm">
                  {indicator}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

// 📈 FORECASTING TAB
const ForecastingTab = ({ data, lang }) => {
  const forecast = data.portfolio_forecast || {}

  if (!forecast.next_7_days && !forecast.scenarios) {
    return (
      <div className="text-center py-12">
        <div className="text-5xl mb-4">📈</div>
        <p className="text-gray-400">
          {lang === 'tr' ? 'Tahmin bulunamadı' : 'No forecast available'}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 7-Day Forecast */}
      {forecast.next_7_days && (
        <div className="bg-gradient-to-br from-blue-900/20 to-purple-900/20 border border-blue-500/30 rounded-xl p-6">
          <h3 className="text-xl font-bold text-white mb-4">
            📅 {lang === 'tr' ? '7 Günlük Tahmin' : '7-Day Forecast'}
          </h3>

          <div className="grid md:grid-cols-3 gap-4 mb-4">
            <div className="bg-gray-900/50 rounded-lg p-4 text-center">
              <p className="text-gray-400 text-sm mb-2">
                {lang === 'tr' ? 'Beklenen Değer' : 'Expected Value'}
              </p>
              <p className="text-2xl font-bold text-white">
                ${forecast.next_7_days.expected_value?.toLocaleString()}
              </p>
              <p className={`text-sm mt-1 ${
                forecast.next_7_days.expected_change_pct >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {forecast.next_7_days.expected_change_pct >= 0 ? '+' : ''}
                {forecast.next_7_days.expected_change_pct?.toFixed(1)}%
              </p>
            </div>

            <div className="bg-green-900/30 rounded-lg p-4 text-center">
              <p className="text-gray-400 text-sm mb-2">
                {lang === 'tr' ? 'En İyi Durum' : 'Best Case'}
              </p>
              <p className="text-2xl font-bold text-green-400">
                ${forecast.next_7_days.best_case?.toLocaleString()}
              </p>
            </div>

            <div className="bg-red-900/30 rounded-lg p-4 text-center">
              <p className="text-gray-400 text-sm mb-2">
                {lang === 'tr' ? 'En Kötü Durum' : 'Worst Case'}
              </p>
              <p className="text-2xl font-bold text-red-400">
                ${forecast.next_7_days.worst_case?.toLocaleString()}
              </p>
            </div>
          </div>

          {forecast.next_7_days.confidence_interval && (
            <p className="text-center text-gray-400 text-sm">
              {lang === 'tr' ? 'Güven Aralığı' : 'Confidence Interval'}: {forecast.next_7_days.confidence_interval}
            </p>
          )}
        </div>
      )}

      {/* 30-Day Forecast */}
      {forecast.next_30_days && (
        <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700/50">
          <h3 className="text-xl font-bold text-white mb-4">
            📊 {lang === 'tr' ? '30 Günlük Projeksiyon' : '30-Day Projection'}
          </h3>

          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-gray-900/50 rounded-lg p-4">
              <p className="text-gray-400 text-sm mb-1">
                {lang === 'tr' ? 'Beklenen Getiri' : 'Expected Return'}
              </p>
              <p className={`text-2xl font-bold ${
                forecast.next_30_days.expected_return_pct >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {forecast.next_30_days.expected_return_pct >= 0 ? '+' : ''}
                {forecast.next_30_days.expected_return_pct?.toFixed(1)}%
              </p>
            </div>

            <div className="bg-gray-900/50 rounded-lg p-4">
              <p className="text-gray-400 text-sm mb-1">
                {lang === 'tr' ? 'Risk Ayarlı Getiri' : 'Risk-Adjusted Return'}
              </p>
              <p className="text-2xl font-bold text-blue-400">
                +{forecast.next_30_days.risk_adjusted_return_pct?.toFixed(1)}%
              </p>
            </div>

            <div className="bg-gray-900/50 rounded-lg p-4">
              <p className="text-gray-400 text-sm mb-1">Sharpe Ratio</p>
              <p className="text-2xl font-bold text-purple-400">
                {forecast.next_30_days.sharpe_ratio?.toFixed(2)}
              </p>
            </div>

            <div className="bg-gray-900/50 rounded-lg p-4">
              <p className="text-gray-400 text-sm mb-1">
                {lang === 'tr' ? 'Volatilite Tahmini' : 'Volatility Estimate'}
              </p>
              <p className="text-2xl font-bold text-yellow-400">
                {forecast.next_30_days.volatility_estimate?.toFixed(1)}%
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Scenarios */}
      {forecast.scenarios && forecast.scenarios.length > 0 && (
        <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700/50">
          <h3 className="text-xl font-bold text-white mb-4">
            🎲 {lang === 'tr' ? 'Senaryolar' : 'Scenarios'}
          </h3>

          <div className="grid md:grid-cols-3 gap-4">
            {forecast.scenarios.map((scenario, i) => (
              <div key={i} className={`rounded-lg p-4 ${
                scenario.name === 'Conservative' ? 'bg-blue-900/30 border border-blue-500/30' :
                scenario.name === 'Moderate' ? 'bg-yellow-900/30 border border-yellow-500/30' :
                'bg-green-900/30 border border-green-500/30'
              }`}>
                <h4 className="font-bold text-white mb-2">{scenario.name}</h4>
                <p className={`text-3xl font-bold mb-2 ${
                  scenario.return_pct >= 10 ? 'text-green-400' :
                  scenario.return_pct >= 0 ? 'text-yellow-400' : 'text-red-400'
                }`}>
                  +{scenario.return_pct?.toFixed(1)}%
                </p>
                <p className="text-gray-400 text-sm mb-3">
                  {lang === 'tr' ? 'Olasılık' : 'Probability'}: {scenario.probability}%
                </p>
                <p className="text-gray-300 text-xs leading-relaxed">
                  {scenario.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Key Assumptions */}
      {forecast.key_assumptions && forecast.key_assumptions.length > 0 && (
        <div className="bg-gray-900/50 border-l-4 border-gray-500 p-4 rounded-r">
          <p className="text-gray-400 text-sm mb-2">
            {lang === 'tr' ? '📌 Temel Varsayımlar' : '📌 Key Assumptions'}
          </p>
          <ul className="list-disc list-inside space-y-1">
            {forecast.key_assumptions.map((assumption, i) => (
              <li key={i} className="text-gray-300 text-sm">{assumption}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

// 🔔 SMART ALERTS TAB
const AlertsTab = ({ data, lang }) => {
  if (!data.smart_alerts || data.smart_alerts.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-5xl mb-4">🔔</div>
        <p className="text-gray-400">
          {lang === 'tr' ? 'Akıllı uyarı bulunamadı' : 'No smart alerts available'}
        </p>
        <p className="text-gray-500 text-sm mt-2">
          {lang === 'tr' ? 'Portföyünüz sağlıklı görünüyor!' : 'Your portfolio looks healthy!'}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {data.smart_alerts.map((alert, i) => (
        <div key={i} className={`rounded-xl p-6 border-2 ${
          alert.severity === 'critical' ? 'bg-red-500/20 border-red-500' :
          alert.severity === 'high' ? 'bg-orange-500/20 border-orange-500' :
          alert.severity === 'medium' ? 'bg-yellow-500/20 border-yellow-500' :
          'bg-blue-500/20 border-blue-500'
        }`}>
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <span className="text-3xl">
                {alert.type === 'price_target' ? '🎯' :
                 alert.type === 'volatility' ? '📊' :
                 alert.type === 'risk' ? '⚠️' :
                 alert.type === 'opportunity' ? '💎' :
                 alert.type === 'rebalance' ? '⚖️' : '🔔'}
              </span>
              <div>
                <h3 className="text-lg font-bold text-white">{alert.title}</h3>
                {alert.coin && (
                  <p className="text-gray-400 text-sm">{alert.coin}</p>
                )}
              </div>
            </div>
            <span className={`px-3 py-1 rounded-lg text-xs font-bold uppercase ${
              alert.severity === 'critical' ? 'bg-red-500 text-white' :
              alert.severity === 'high' ? 'bg-orange-500 text-white' :
              alert.severity === 'medium' ? 'bg-yellow-500 text-black' :
              'bg-blue-500 text-white'
            }`}>
              {alert.severity === 'critical' ? (lang === 'tr' ? 'KRİTİK' : 'CRITICAL') :
               alert.severity === 'high' ? (lang === 'tr' ? 'YÜKSEK' : 'HIGH') :
               alert.severity === 'medium' ? (lang === 'tr' ? 'ORTA' : 'MEDIUM') :
               (lang === 'tr' ? 'DÜŞÜK' : 'LOW')}
            </span>
          </div>

          {/* Trigger */}
          {alert.trigger && (
            <div className="bg-gray-900/50 rounded-lg p-3 mb-3">
              <p className="text-gray-400 text-xs mb-1">
                {lang === 'tr' ? '🎲 Tetikleyici' : '🎲 Trigger'}
              </p>
              <p className="text-white font-medium">{alert.trigger}</p>
            </div>
          )}

          {/* Recommended Action */}
          {alert.action && (
            <div className="bg-blue-900/30 border-l-4 border-blue-500 p-4 mb-3 rounded-r">
              <p className="text-gray-400 text-xs mb-1">
                {lang === 'tr' ? '💡 Önerilen Aksiyon' : '💡 Recommended Action'}
              </p>
              <p className="text-blue-200 font-medium">{alert.action}</p>
            </div>
          )}

          {/* Reasoning */}
          {alert.reasoning && (
            <p className="text-gray-300 text-sm mb-3 leading-relaxed">
              {alert.reasoning}
            </p>
          )}

          {/* Auto Action */}
          {alert.auto_action && (
            <div className="bg-green-900/30 rounded-lg p-3">
              <p className="text-gray-400 text-xs mb-1">
                {lang === 'tr' ? '🤖 Otomatik Aksiyon' : '🤖 Auto Action'}
              </p>
              <p className="text-green-300 text-sm">{alert.auto_action}</p>
            </div>
          )}

          {/* Timestamp */}
          {alert.timestamp && (
            <p className="text-gray-600 text-xs mt-3">
              {new Date(alert.timestamp).toLocaleString(lang === 'tr' ? 'tr-TR' : 'en-US')}
            </p>
          )}
        </div>
      ))}
    </div>
  )
}

// 📉 TECHNICAL ANALYSIS TAB
const TechnicalTab = ({ data, lang }) => {
  if (!data.technical_analysis || data.technical_analysis.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-5xl mb-4">📉</div>
        <p className="text-gray-400">
          {lang === 'tr' ? 'Teknik analiz bulunamadı' : 'No technical analysis available'}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {data.technical_analysis.map((analysis, i) => (
        <div key={i} className="bg-gray-800/50 rounded-xl p-6 border border-gray-700/50">
          {/* Header */}
          <div className="flex items-start justify-between mb-6">
            <div>
              <h3 className="text-2xl font-bold text-white mb-1">{analysis.coin}</h3>
              <p className="text-gray-400">${analysis.current_price?.toLocaleString()}</p>
              <p className="text-gray-500 text-sm">{analysis.timeframe}</p>
            </div>
            <div className="text-right">
              <div className={`px-4 py-2 rounded-lg text-lg font-bold ${
                analysis.trend === 'bullish' ? 'bg-green-500/20 text-green-400' :
                analysis.trend === 'bearish' ? 'bg-red-500/20 text-red-400' :
                'bg-yellow-500/20 text-yellow-400'
              }`}>
                {analysis.trend === 'bullish' ? '📈 BULLISH' :
                 analysis.trend === 'bearish' ? '📉 BEARISH' : '➡️ NEUTRAL'}
              </div>
              <p className="text-gray-400 text-sm mt-2">
                {lang === 'tr' ? 'Güç' : 'Strength'}: {analysis.trend_strength}/10
              </p>
            </div>
          </div>

          {/* Technical Score */}
          <div className="mb-6">
            <div className="flex justify-between mb-2">
              <span className="text-gray-400 text-sm">
                {lang === 'tr' ? 'Teknik Skor' : 'Technical Score'}
              </span>
              <span className="text-white font-bold">{analysis.technical_score}/100</span>
            </div>
            <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${
                  analysis.technical_score >= 70 ? 'bg-green-500' :
                  analysis.technical_score >= 40 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${analysis.technical_score}%` }}
              />
            </div>
          </div>

          {/* Support & Resistance */}
          <div className="grid md:grid-cols-2 gap-4 mb-6">
            <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-4">
              <p className="text-green-400 font-bold mb-3">
                {lang === 'tr' ? '🟢 Destek Seviyeleri' : '🟢 Support Levels'}
              </p>
              {analysis.support_levels && analysis.support_levels.map((level, idx) => (
                <div key={idx} className="flex justify-between py-1">
                  <span className="text-gray-400 text-sm">S{idx + 1}</span>
                  <span className="text-green-300 font-medium">${level?.toLocaleString()}</span>
                </div>
              ))}
            </div>

            <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4">
              <p className="text-red-400 font-bold mb-3">
                {lang === 'tr' ? '🔴 Direnç Seviyeleri' : '🔴 Resistance Levels'}
              </p>
              {analysis.resistance_levels && analysis.resistance_levels.map((level, idx) => (
                <div key={idx} className="flex justify-between py-1">
                  <span className="text-gray-400 text-sm">R{idx + 1}</span>
                  <span className="text-red-300 font-medium">${level?.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Indicators */}
          {analysis.indicators && (
            <div className="bg-gray-900/50 rounded-lg p-4 mb-4">
              <p className="text-gray-400 text-sm mb-3">
                {lang === 'tr' ? '📊 İndikatörler' : '📊 Indicators'}
              </p>
              <div className="space-y-2">
                {analysis.indicators.rsi && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-300 text-sm">RSI: {analysis.indicators.rsi.value}</span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      analysis.indicators.rsi.signal === 'oversold' ? 'bg-green-500/20 text-green-400' :
                      analysis.indicators.rsi.signal === 'overbought' ? 'bg-red-500/20 text-red-400' :
                      'bg-gray-700 text-gray-300'
                    }`}>
                      {analysis.indicators.rsi.signal}
                    </span>
                  </div>
                )}
                {analysis.indicators.macd && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-300 text-sm">MACD</span>
                    <span className="text-blue-400 text-sm">{analysis.indicators.macd.signal}</span>
                  </div>
                )}
                {analysis.indicators.moving_averages && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-300 text-sm">MA</span>
                    <span className="text-purple-400 text-sm">{analysis.indicators.moving_averages.signal}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Patterns */}
          {analysis.patterns && analysis.patterns.length > 0 && (
            <div className="mb-4">
              <p className="text-gray-400 text-sm mb-2">
                {lang === 'tr' ? '📐 Grafikal Patternler' : '📐 Chart Patterns'}
              </p>
              <div className="flex flex-wrap gap-2">
                {analysis.patterns.map((pattern, j) => (
                  <span key={j} className="px-3 py-1 bg-purple-500/20 text-purple-300 rounded-lg text-sm">
                    {pattern}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Volume Analysis */}
          {analysis.volume_analysis && (
            <div className="bg-blue-900/20 border-l-4 border-blue-500 p-3 mb-4 rounded-r">
              <p className="text-gray-400 text-xs mb-1">
                {lang === 'tr' ? '📊 Hacim Analizi' : '📊 Volume Analysis'}
              </p>
              <p className="text-blue-200 text-sm">{analysis.volume_analysis}</p>
            </div>
          )}

          {/* Recommendation */}
          {analysis.recommendation && (
            <div className="bg-gradient-to-r from-green-900/30 to-blue-900/30 border border-green-500/30 rounded-lg p-4 mb-3">
              <p className="text-gray-400 text-xs mb-1">
                {lang === 'tr' ? '💡 Öneri' : '💡 Recommendation'}
              </p>
              <p className="text-green-300 font-medium">{analysis.recommendation}</p>
              <p className="text-gray-400 text-xs mt-2">
                {lang === 'tr' ? 'Güven' : 'Confidence'}: {analysis.confidence}%
              </p>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export default AISummary