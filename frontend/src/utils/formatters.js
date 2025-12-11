// src/utils/formatters.js

export const formatPrice = (price) => {
  if (!price || price === 0) return '$0.00'
  if (price >= 1000) {
    return `$${price.toLocaleString('en-US', { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    })}`
  }
  if (price >= 1) return `$${price.toFixed(2)}`
  if (price >= 0.01) return `$${price.toFixed(4)}`
  if (price >= 0.0001) return `$${price.toFixed(6)}`
  return `$${price.toFixed(8)}`
}

export const formatNumber = (num) => {
  if (!num) return '0'
  if (num >= 1e12) return `${(num / 1e12).toFixed(2)}T`
  if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`
  if (num >= 1e6) return `${(num / 1e6).toFixed(2)}M`
  if (num >= 1e3) return `${(num / 1e3).toFixed(2)}K`
  return num.toFixed(2)
}

export const formatChange = (change) => {
  if (change === null || change === undefined) return '0.00%'
  const sign = change >= 0 ? '+' : ''
  return `${sign}${change.toFixed(2)}%`
}

export const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString()
}

export const formatTime = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleTimeString()
}

export const getChangeColor = (change) => {
  if (change >= 0) return 'text-green-400'
  return 'text-red-400'
}

export const getRiskColor = (risk) => {
  switch (risk) {
    case 'low': return 'text-green-400'
    case 'high': return 'text-red-400'
    default: return 'text-yellow-400'
  }
}

export const getSignalColor = (signal) => {
  switch (signal) {
    case 'STRONG_BUY': return 'bg-green-500'
    case 'BUY': return 'bg-green-400/80'
    case 'STRONG_SELL': return 'bg-red-500'
    case 'SELL': return 'bg-red-400/80'
    default: return 'bg-yellow-500'
  }
}

export const getSignalText = (signal, lang = 'tr') => {
  if (lang === 'tr') {
    switch (signal) {
      case 'STRONG_BUY': return '🚀 GÜÇLÜ AL'
      case 'BUY': return '📈 AL'
      case 'STRONG_SELL': return '🔻 GÜÇLÜ SAT'
      case 'SELL': return '📉 SAT'
      default: return '⏸️ BEKLE'
    }
  }
  return signal?.replace('_', ' ') || 'HOLD'
}
