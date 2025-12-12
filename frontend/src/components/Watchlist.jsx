import { useState, useEffect } from 'react'
import api from '../api'
import { formatPrice, formatChange } from '../utils/formatters'

/**
 * Watchlist Component - Favori Coinler
 * Kullanıcının favori coin listesini gösterir
 */
export const Watchlist = ({ prices, onCoinClick, lang }) => {
  const [watchlist, setWatchlist] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchWatchlist()
  }, [])

  const fetchWatchlist = async () => {
    try {
      const resp = await api.get('/api/watchlist')
      if (resp.ok) {
        const data = await resp.json()
        setWatchlist(data.watchlist || [])
      }
    } catch (error) {
      console.error('Watchlist fetch error:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleFavorite = async (symbol) => {
    const isInList = watchlist.some(item => item.symbol === symbol)

    try {
      if (isInList) {
        // Remove from watchlist
        const resp = await api.delete(`/api/watchlist/remove/${symbol}`)
        if (resp.ok) {
          setWatchlist(prev => prev.filter(item => item.symbol !== symbol))
        }
      } else {
        // Add to watchlist
        const resp = await api.post('/api/watchlist/add', { symbol })
        if (resp.ok) {
          const data = await resp.json()
          setWatchlist(prev => [{
            symbol: data.symbol,
            added_at: new Date().toISOString()
          }, ...prev])
        }
      }
    } catch (error) {
      console.error('Watchlist toggle error:', error)
    }
  }

  if (loading) {
    return (
      <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-4 border border-gray-700/50">
        <h3 className="text-gray-400 text-sm mb-3 flex items-center gap-2">
          ⭐ {lang === 'tr' ? 'Favorilerim' : 'My Favorites'}
        </h3>
        <div className="text-center py-4 text-gray-500">
          {lang === 'tr' ? 'Yükleniyor...' : 'Loading...'}
        </div>
      </div>
    )
  }

  if (watchlist.length === 0) {
    return (
      <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-4 border border-gray-700/50">
        <h3 className="text-gray-400 text-sm mb-3 flex items-center gap-2">
          ⭐ {lang === 'tr' ? 'Favorilerim' : 'My Favorites'}
        </h3>
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-2">📌</div>
          <div className="text-sm">
            {lang === 'tr'
              ? 'Henüz favori coin eklemediniz. Coin listesinden ⭐ ikonuna tıklayarak ekleyin.'
              : 'No favorites yet. Click the ⭐ icon in the coin list to add favorites.'}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="group bg-gray-800/50 backdrop-blur-sm rounded-xl p-4 border border-gray-700/50 hover:border-yellow-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-yellow-500/20 hover:-translate-y-1">
      <h3 className="text-gray-400 text-sm mb-3 flex items-center gap-2 group-hover:text-gray-300 transition-colors">
        ⭐ {lang === 'tr' ? 'Favorilerim' : 'My Favorites'}
        <span className="text-xs text-gray-500">
          ({watchlist.length})
        </span>
      </h3>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {watchlist.map((item, idx) => {
          const symbol = item.symbol
          const priceData = prices[symbol] || {}
          const price = priceData.price || 0
          const change24h = priceData.change_24h || 0
          const isPositive = change24h >= 0

          return (
            <div
              key={symbol}
              className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-700/50 cursor-pointer transition-all duration-200 group/item"
            >
              <div
                onClick={() => onCoinClick && onCoinClick({ symbol, id: symbol.toLowerCase() })}
                className="flex-1 flex items-center gap-3"
              >
                <div>
                  <div className="font-medium text-white text-sm">{symbol}</div>
                  <div className="text-xs text-gray-500">{formatPrice(price)}</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`text-sm font-medium ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                  {formatChange(change24h)}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    toggleFavorite(symbol)
                  }}
                  className="text-yellow-400 hover:text-yellow-500 transition-colors opacity-0 group-hover/item:opacity-100"
                >
                  ⭐
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

/**
 * Star Icon Component - Favori İkonu
 * Coin listesinde kullanılır
 */
export const FavoriteButton = ({ symbol, onToggle }) => {
  const [isFavorite, setIsFavorite] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkFavorite()
  }, [symbol])

  const checkFavorite = async () => {
    try {
      const resp = await api.get(`/api/watchlist/check/${symbol}`)
      if (resp.ok) {
        const data = await resp.json()
        setIsFavorite(data.in_watchlist)
      }
    } catch (error) {
      console.error('Favorite check error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleClick = async (e) => {
    e.stopPropagation()
    setLoading(true)

    try {
      if (isFavorite) {
        const resp = await api.delete(`/api/watchlist/remove/${symbol}`)
        if (resp.ok) {
          setIsFavorite(false)
          onToggle && onToggle(symbol, false)
        }
      } else {
        const resp = await api.post('/api/watchlist/add', { symbol })
        if (resp.ok) {
          setIsFavorite(true)
          onToggle && onToggle(symbol, true)
        }
      }
    } catch (error) {
      console.error('Favorite toggle error:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <span className="text-gray-600">⭐</span>
  }

  return (
    <button
      onClick={handleClick}
      className={`transition-all duration-200 hover:scale-110 ${
        isFavorite ? 'text-yellow-400 hover:text-yellow-500' : 'text-gray-600 hover:text-yellow-400'
      }`}
      title={isFavorite ? 'Favorilerden çıkar' : 'Favorilere ekle'}
    >
      {isFavorite ? '⭐' : '☆'}
    </button>
  )
}

export default Watchlist
