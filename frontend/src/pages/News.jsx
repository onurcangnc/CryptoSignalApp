import { useState, useEffect, useCallback } from 'react'
import api from '../api'

const News = ({ t, lang }) => {
  const [news, setNews] = useState([])
  const [stats, setStats] = useState({ bullish: 0, bearish: 0, neutral: 0 })
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')
  const [coinFilter, setCoinFilter] = useState('')
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)
  
  const ITEMS_PER_PAGE = 50

  useEffect(() => {
    loadNews(true)
  }, [filter, coinFilter])

  const loadNews = async (reset = false) => {
    try {
      if (reset) {
        setLoading(true)
        setPage(1)
      } else {
        setLoadingMore(true)
      }
      
      const currentPage = reset ? 1 : page
      const offset = (currentPage - 1) * ITEMS_PER_PAGE
      
      // Build query params
      let url = `/api/news-public?limit=${ITEMS_PER_PAGE}&offset=${offset}`
      if (filter !== 'all') url += `&sentiment=${filter}`
      if (coinFilter) url += `&coin=${coinFilter}`
      
      const resp = await api.get(url)
      if (resp.ok) {
        const data = await resp.json()
        const newNews = data.news || []
        
        if (reset) {
          setNews(newNews)
        } else {
          setNews(prev => [...prev, ...newNews])
        }
        
        setStats(data.stats || { bullish: 0, bearish: 0, neutral: 0 })
        setTotal(data.total || 0)
        setHasMore(newNews.length === ITEMS_PER_PAGE)
        
        if (!reset) {
          setPage(prev => prev + 1)
        }
      }
    } catch (e) {
      console.error('News error:', e)
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }

  const loadMore = () => {
    if (!loadingMore && hasMore) {
      setPage(prev => prev + 1)
      loadNews(false)
    }
  }

  const formatDate = (d) => {
    if (!d) return ''
    try {
      const date = new Date(d)
      const now = new Date()
      const diff = (now - date) / 1000 / 60
      if (diff < 60) return `${Math.floor(diff)} ${lang === 'tr' ? 'dk önce' : 'min ago'}`
      if (diff < 1440) return `${Math.floor(diff / 60)} ${lang === 'tr' ? 'saat önce' : 'hours ago'}`
      return date.toLocaleDateString(lang === 'tr' ? 'tr-TR' : 'en-US', { day: 'numeric', month: 'short' })
    } catch { return '' }
  }

  // Get unique coins from loaded news
  const allCoins = [...new Set(news.flatMap(n => (n.coins || []).filter(c => c !== 'GENERAL')))].sort()

  // Local search filter (doesn't trigger API call)
  const filtered = news.filter(n => {
    if (search && !n.title?.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-500">{lang === 'tr' ? 'Haberler yükleniyor...' : 'Loading news...'}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            📰 {lang === 'tr' ? 'Kripto Haberler' : 'Crypto News'}
          </h1>
          <p className="text-sm text-gray-500">
            {lang === 'tr' ? 'AI ile analiz edilmiş güncel haberler' : 'AI analyzed news'}
          </p>
        </div>
        <button
          onClick={() => loadNews(true)}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition flex items-center gap-2"
        >
          🔄 {lang === 'tr' ? 'Yenile' : 'Refresh'}
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-3">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 text-center shadow">
          <div className="text-2xl font-bold text-gray-900 dark:text-white">{total}</div>
          <div className="text-xs text-gray-500">{lang === 'tr' ? 'Toplam Haber' : 'Total News'}</div>
        </div>
        <div className="bg-green-50 dark:bg-green-900/30 rounded-xl p-4 text-center shadow">
          <div className="text-2xl font-bold text-green-600">{stats.bullish}</div>
          <div className="text-xs text-green-600">📈 {lang === 'tr' ? 'Pozitif' : 'Bullish'}</div>
        </div>
        <div className="bg-gray-100 dark:bg-gray-700 rounded-xl p-4 text-center shadow">
          <div className="text-2xl font-bold text-gray-600 dark:text-gray-300">{stats.neutral}</div>
          <div className="text-xs text-gray-500">➖ {lang === 'tr' ? 'Nötr' : 'Neutral'}</div>
        </div>
        <div className="bg-red-50 dark:bg-red-900/30 rounded-xl p-4 text-center shadow">
          <div className="text-2xl font-bold text-red-600">{stats.bearish}</div>
          <div className="text-xs text-red-600">📉 {lang === 'tr' ? 'Negatif' : 'Bearish'}</div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow">
        <div className="flex flex-wrap gap-3 items-center">
          <input
            type="text"
            placeholder={lang === 'tr' ? 'Haber ara...' : 'Search news...'}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 min-w-48 px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 focus:ring-2 focus:ring-blue-500"
          />
          
          <select
            value={coinFilter}
            onChange={(e) => setCoinFilter(e.target.value)}
            className="px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
          >
            <option value="">{lang === 'tr' ? 'Tüm Coinler' : 'All Coins'}</option>
            {allCoins.map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>

          <div className="flex gap-2">
            {[
              { key: 'all', label: lang === 'tr' ? 'Tümü' : 'All', icon: '📋' },
              { key: 'bullish', label: lang === 'tr' ? 'Pozitif' : 'Bullish', icon: '📈' },
              { key: 'bearish', label: lang === 'tr' ? 'Negatif' : 'Bearish', icon: '📉' },
            ].map(f => (
              <button
                key={f.key}
                onClick={() => setFilter(f.key)}
                className={`px-3 py-2 rounded-lg font-medium transition ${
                  filter === f.key
                    ? f.key === 'bullish' ? 'bg-green-500 text-white'
                    : f.key === 'bearish' ? 'bg-red-500 text-white'
                    : 'bg-blue-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200'
                }`}
              >
                {f.icon} {f.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* News List */}
      <div className="space-y-3">
        {filtered.length === 0 ? (
          <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-xl shadow">
            <div className="text-4xl mb-3">📭</div>
            <p className="text-gray-500">{lang === 'tr' ? 'Haber bulunamadı' : 'No news found'}</p>
            <p className="text-sm text-gray-400 mt-1">
              {lang === 'tr' ? 'Filtrelerinizi değiştirmeyi deneyin' : 'Try changing your filters'}
            </p>
          </div>
        ) : (
          filtered.map((n, i) => (
            <div key={n.id || i} className="bg-white dark:bg-gray-800 rounded-xl shadow hover:shadow-lg transition overflow-hidden">
              <div className="p-4">
                {/* Title */}
                <a 
                  href={n.source_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="block"
                >
                  <h3 className="font-bold text-gray-900 dark:text-white hover:text-blue-500 transition mb-2 line-clamp-2">
                    {n.title}
                  </h3>
                </a>
                
                {/* AI Summary if exists */}
                {n.ai_summary_tr && (
                  <div className="bg-purple-50 dark:bg-purple-900/30 border-l-4 border-purple-400 p-3 mb-3 rounded-r">
                    <div className="flex items-center gap-1 text-purple-600 text-xs font-medium mb-1">
                      🤖 AI {lang === 'tr' ? 'Özet' : 'Summary'}
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300">{n.ai_summary_tr}</p>
                  </div>
                )}
                
                {/* Content preview */}
                {!n.ai_summary_tr && n.content && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                    {n.content}
                  </p>
                )}
                
                {/* Meta */}
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  {/* Sentiment Badge */}
                  <span className={`px-2 py-1 rounded-full font-medium ${
                    n.sentiment === 'bullish' ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-400' :
                    n.sentiment === 'bearish' ? 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-400' :
                    'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                  }`}>
                    {n.sentiment === 'bullish' ? `📈 ${lang === 'tr' ? 'Pozitif' : 'Bullish'}` : 
                     n.sentiment === 'bearish' ? `📉 ${lang === 'tr' ? 'Negatif' : 'Bearish'}` : 
                     `➖ ${lang === 'tr' ? 'Nötr' : 'Neutral'}`}
                  </span>
                  
                  {/* Tier Badge */}
                  {n.tier && n.tier <= 2 && (
                    <span className="px-2 py-1 rounded-full bg-yellow-100 text-yellow-700 dark:bg-yellow-900/50 dark:text-yellow-400 font-medium">
                      ⭐ {lang === 'tr' ? 'Öne Çıkan' : 'Featured'}
                    </span>
                  )}
                  
                  {/* Source */}
                  <span className="text-gray-500 dark:text-gray-400">
                    {n.source}
                  </span>
                  
                  {/* Time */}
                  <span className="text-gray-400">
                    {formatDate(n.crawled_at || n.published_at)}
                  </span>
                  
                  {/* Coins */}
                  {(n.coins || []).filter(c => c !== 'GENERAL').slice(0, 5).map(c => (
                    <button
                      key={c}
                      onClick={() => setCoinFilter(c)}
                      className="px-2 py-1 bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-400 rounded hover:bg-blue-200 transition"
                    >
                      {c}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Load More */}
      {hasMore && filtered.length > 0 && (
        <div className="text-center py-4">
          <button
            onClick={loadMore}
            disabled={loadingMore}
            className="px-6 py-3 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl hover:bg-gray-200 dark:hover:bg-gray-600 transition disabled:opacity-50 flex items-center gap-2 mx-auto"
          >
            {loadingMore ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-500"></div>
                {lang === 'tr' ? 'Yükleniyor...' : 'Loading...'}
              </>
            ) : (
              <>
                📥 {lang === 'tr' ? 'Daha Fazla Yükle' : 'Load More'}
              </>
            )}
          </button>
          <p className="text-sm text-gray-500 mt-2">
            {filtered.length} / {total} {lang === 'tr' ? 'haber gösteriliyor' : 'news shown'}
          </p>
        </div>
      )}

      {/* End of list */}
      {!hasMore && filtered.length > 0 && (
        <div className="text-center py-4">
          <p className="text-sm text-gray-500">
            ✅ {lang === 'tr' ? 'Tüm haberler yüklendi' : 'All news loaded'} ({filtered.length})
          </p>
        </div>
      )}
    </div>
  )
}

export default News