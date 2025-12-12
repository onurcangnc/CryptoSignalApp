// src/App.jsx
// CryptoSignal AI - Main App Component v7.0
import { useState, useEffect } from 'react'

// Utils
import translations from './utils/translations'

// Components
import Nav from './components/Nav'
import Login from './components/Login'
import Toast from './components/Toast'
import { RiskDisclaimer } from './components/ui'

// Pages
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import Signals from './pages/Signals'
import AISummary from './pages/AISummary'
import News from './pages/News'
import Portfolio from './pages/Portfolio'
import Admin from './pages/Admin'
import Premium from './pages/Premium'
import DCACalculator from './pages/DCACalculator'
import Backtesting from './pages/Backtesting'

export default function App() {
  const [user, setUser] = useState(null)
  const [current, setCurrent] = useState('dashboard')
  const [lang, setLang] = useState('tr')
  const [loading, setLoading] = useState(true)
  const [showLanding, setShowLanding] = useState(true)

  const t = translations[lang]

  // Check for saved user on mount
  useEffect(() => {
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser))
        setShowLanding(false) // User logged in, skip landing
      } catch (e) {
        localStorage.removeItem('user')
        localStorage.removeItem('token')
      }
    }
    setLoading(false)
  }, [])

  const handleLogin = (userData) => {
    setUser(userData)
    setShowLanding(false)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
    setCurrent('dashboard')
    setShowLanding(true)
  }

  const handleGetStarted = () => {
    setShowLanding(false)
  }

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-3">🚀</div>
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    )
  }

  // Show landing page if not logged in and showLanding is true
  if (showLanding && !user) {
    return <Landing onGetStarted={handleGetStarted} lang={lang} setLang={setLang} />
  }

  // Not logged in - show login
  if (!user) {
    return (
      <div>
        <div className="absolute top-4 left-4 z-50">
          <button
            onClick={() => setShowLanding(true)}
            className="px-4 py-2 rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 transition-all flex items-center gap-2"
          >
            ← {lang === 'tr' ? 'Ana Sayfa' : 'Home'}
          </button>
        </div>
        <Login onLogin={handleLogin} t={t} lang={lang} />
      </div>
    )
  }

  // Main app
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Navigation */}
      <Nav
        current={current}
        setCurrent={setCurrent}
        user={user}
        logout={handleLogout}
        lang={lang}
        setLang={setLang}
        t={t}
      />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-3 md:px-6 py-4 md:py-6">
        {current === 'dashboard' && <Dashboard t={t} lang={lang} user={user} />}
        {current === 'signals' && <Signals t={t} lang={lang} />}
        {current === 'ai-summary' && <AISummary t={t} lang={lang} user={user} />}
        {current === 'news' && <News t={t} lang={lang} />}
        {current === 'portfolio' && <Portfolio t={t} lang={lang} user={user} />}
        {current === 'premium' && <Premium user={user} setCurrent={setCurrent} />}
        {current === 'admin' && <Admin t={t} lang={lang} user={user} />}
        {current === 'dca' && <DCACalculator t={t} lang={lang} />}
        {current === 'backtesting' && <Backtesting t={t} lang={lang} />}
      </main>

      {/* Footer with Risk Disclaimer */}
      <RiskDisclaimer lang={lang} variant="footer" />
      <footer className="text-center py-4 text-gray-600 text-xs border-t border-gray-800">
        © 2025 CryptoSignal AI - {lang === 'tr' ? 'Tüm hakları saklıdır' : 'All rights reserved'}
      </footer>

      {/* Toast Notifications */}
      <Toast />
    </div>
  )
}