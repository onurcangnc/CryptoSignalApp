// src/components/Nav.jsx
// AI Stats entegreli Navigation Bar

import { useState, useEffect } from 'react'
import api from '../api'

const Nav = ({ current, setCurrent, user, logout, lang, setLang, t }) => {
  const [menuOpen, setMenuOpen] = useState(false)
  const [aiStats, setAiStats] = useState(null)
  
  const navItems = [
    { id: 'dashboard', icon: '📊', label: t.dashboard },
    { id: 'signals', icon: '💡', label: t.signals },
    { id: 'ai-summary', icon: '🤖', label: t.digest },
    { id: 'news', icon: '📰', label: t.news },
    { id: 'portfolio', icon: '💼', label: t.portfolio },
    { id: 'dca', icon: '🧮', label: lang === 'tr' ? 'DCA' : 'DCA' },
    { id: 'backtesting', icon: '📈', label: lang === 'tr' ? 'Backtest' : 'Backtest' },
  ]

  // Premium butonu (sadece free kullanıcılar için)
  if (user?.tier === 'free' || !user?.tier) {
    navItems.push({ id: 'premium', icon: '⭐', label: lang === 'tr' ? 'Premium' : 'Premium', isPremium: true })
  }

  if (user?.tier === 'admin') {
    navItems.push({ id: 'admin', icon: '⚙️', label: t.admin })
  }

  // AI Stats'ı yükle
  useEffect(() => {
    fetchAIStats()
    const interval = setInterval(fetchAIStats, 60000) // Her dakika güncelle
    return () => clearInterval(interval)
  }, [])

  const fetchAIStats = async () => {
    try {
      const resp = await api.get('/api/ai/stats')
      if (resp.ok) {
        const data = await resp.json()
        setAiStats(data.user_stats)
      }
    } catch (e) {}
  }

  const handleNavClick = (id) => {
    setCurrent(id)
    setMenuOpen(false)
  }

  // AI kullanım rengi
  const getAIColor = () => {
    if (!aiStats) return 'text-gray-400'
    const remaining = aiStats.remaining || 0
    if (remaining === 0) return 'text-red-400'
    if (remaining <= 2) return 'text-yellow-400'
    return 'text-green-400'
  }

  return (
    <nav className="bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 border-b border-gray-700 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-3 md:px-6">
        <div className="flex items-center justify-between h-14 md:h-16">
          {/* Logo */}
          <div className="flex items-center">
            <span className="text-xl md:text-2xl font-bold bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent">
              🚀 CryptoSignal
            </span>
            <span className="hidden md:inline ml-2 text-xs text-gray-500">AI</span>
          </div>
          
          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-1">
            {navItems.map(item => (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  item.isPremium
                    ? 'bg-gradient-to-r from-yellow-500 to-orange-500 text-white hover:from-yellow-600 hover:to-orange-600 shadow-lg'
                    : current === item.id
                    ? 'bg-yellow-500/20 text-yellow-400'
                    : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
                }`}
              >
                <span className="mr-1">{item.icon}</span>
                {item.label}
              </button>
            ))}
          </div>
          
          {/* Right Side - Desktop */}
          <div className="hidden md:flex items-center space-x-3">
            {/* AI Stats Badge */}
            {aiStats && (
              <div 
                className="flex items-center gap-2 px-3 py-1.5 bg-gray-800/80 rounded-lg border border-gray-700/50 cursor-pointer hover:bg-gray-700/50 transition"
                title={`${lang === 'tr' ? 'AI Kullanımı' : 'AI Usage'}: ${aiStats.used_today}/${aiStats.daily_limit}`}
              >
                <span className="text-base">🤖</span>
                <div className="flex items-center gap-1">
                  <span className={`text-sm font-bold ${getAIColor()}`}>
                    {aiStats.remaining || 0}
                  </span>
                  <span className="text-gray-500 text-xs">/ {aiStats.daily_limit || 3}</span>
                </div>
                {/* Mini progress bar */}
                <div className="w-10 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    className={`h-full rounded-full transition-all ${
                      (aiStats.remaining || 0) === 0 ? 'bg-red-500' :
                      (aiStats.remaining || 0) <= 2 ? 'bg-yellow-500' : 'bg-green-500'
                    }`}
                    style={{ width: `${((aiStats.remaining || 0) / (aiStats.daily_limit || 3)) * 100}%` }}
                  />
                </div>
              </div>
            )}

            {/* Language Toggle */}
            <button
              onClick={() => setLang(lang === 'tr' ? 'en' : 'tr')}
              className="px-2 py-1 text-xs rounded bg-gray-700 text-gray-300 hover:bg-gray-600 transition-colors"
            >
              {lang === 'tr' ? '🇬🇧 EN' : '🇹🇷 TR'}
            </button>

            {/* User Info */}
            {user && (
              <>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-400">{user.email}</span>
                  {user.tier && user.tier !== 'free' && (
                    <span className={`text-xs px-1.5 py-0.5 rounded ${
                      user.tier === 'admin' ? 'bg-purple-500/30 text-purple-300' : 'bg-blue-500/30 text-blue-300'
                    }`}>
                      {user.tier.toUpperCase()}
                    </span>
                  )}
                </div>
                <button
                  onClick={logout}
                  className="px-3 py-1 text-sm rounded bg-red-600/20 text-red-400 hover:bg-red-600/30 transition-colors"
                >
                  {t.logout}
                </button>
              </>
            )}
          </div>
          
          {/* Mobile Menu Button */}
          <div className="flex md:hidden items-center space-x-2">
            {/* Mobile AI Stats */}
            {aiStats && (
              <div className={`flex items-center gap-1 px-2 py-1 bg-gray-800 rounded text-sm ${getAIColor()}`}>
                <span>🤖</span>
                <span className="font-bold">{aiStats.remaining || 0}</span>
              </div>
            )}
            
            <button
              onClick={() => setLang(lang === 'tr' ? 'en' : 'tr')}
              className="px-2 py-1 text-xs rounded bg-gray-700 text-gray-300"
            >
              {lang === 'tr' ? '🇬🇧' : '🇹🇷'}
            </button>
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="p-2 rounded-lg bg-gray-700 text-white hover:bg-gray-600 transition-colors"
            >
              {menuOpen ? '✕' : '☰'}
            </button>
          </div>
        </div>
        
        {/* Mobile Menu Dropdown */}
        {menuOpen && (
          <div className="md:hidden pb-4 border-t border-gray-700 mt-2 pt-3 animate-fadeIn">
            {/* Mobile AI Stats Expanded */}
            {aiStats && (
              <div className="mb-3 p-3 bg-gray-800/50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-400 text-sm">🤖 AI Kullanımı</span>
                  <span className={`font-bold ${getAIColor()}`}>
                    {aiStats.used_today || 0} / {aiStats.daily_limit || 3}
                  </span>
                </div>
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    className={`h-full rounded-full ${
                      (aiStats.remaining || 0) === 0 ? 'bg-red-500' :
                      (aiStats.remaining || 0) <= 2 ? 'bg-yellow-500' : 'bg-green-500'
                    }`}
                    style={{ width: `${((aiStats.remaining || 0) / (aiStats.daily_limit || 3)) * 100}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {(aiStats.remaining || 0) > 0 
                    ? `${aiStats.remaining} kullanım kaldı`
                    : '⚠️ Günlük limit doldu'
                  }
                </p>
              </div>
            )}

            <div className="grid grid-cols-3 gap-2">
              {navItems.map(item => (
                <button
                  key={item.id}
                  onClick={() => handleNavClick(item.id)}
                  className={`flex flex-col items-center justify-center p-3 rounded-lg text-xs font-medium transition-all ${
                    item.isPremium
                      ? 'bg-gradient-to-r from-yellow-500 to-orange-500 text-white shadow-lg'
                      : current === item.id
                      ? 'bg-yellow-500/20 text-yellow-400'
                      : 'bg-gray-700/50 text-gray-400 hover:bg-gray-700'
                  }`}
                >
                  <span className="text-xl mb-1">{item.icon}</span>
                  {item.label}
                </button>
              ))}
            </div>
            {user && (
              <div className="mt-3 pt-3 border-t border-gray-700 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-400 truncate">{user.email}</span>
                  {user.tier && user.tier !== 'free' && (
                    <span className={`text-xs px-1.5 py-0.5 rounded ${
                      user.tier === 'admin' ? 'bg-purple-500/30 text-purple-300' : 'bg-blue-500/30 text-blue-300'
                    }`}>
                      {user.tier.toUpperCase()}
                    </span>
                  )}
                </div>
                <button
                  onClick={() => {
                    logout()
                    setMenuOpen(false)
                  }}
                  className="px-3 py-1 text-sm rounded bg-red-600/20 text-red-400"
                >
                  {t.logout}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </nav>
  )
}

export default Nav