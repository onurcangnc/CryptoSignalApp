// src/App.jsx
// CryptoSignal AI - Main App Component v6.0
import { useState, useEffect } from 'react'

// Utils
import translations from './utils/translations'

// Components
import Nav from './components/Nav'
import Login from './components/Login'

// Pages
import Dashboard from './pages/Dashboard'
import Signals from './pages/Signals'
import AISummary from './pages/AISummary'
import News from './pages/News'
import Portfolio from './pages/Portfolio'
import Admin from './pages/Admin'
import Premium from './pages/Premium'

export default function App() {
  const [user, setUser] = useState(null)
  const [current, setCurrent] = useState('dashboard')
  const [lang, setLang] = useState('tr')
  const [loading, setLoading] = useState(true)

  const t = translations[lang]

  // Check for saved user on mount
  useEffect(() => {
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser))
      } catch (e) {
        localStorage.removeItem('user')
        localStorage.removeItem('token')
      }
    }
    setLoading(false)
  }, [])

  const handleLogin = (userData) => {
    setUser(userData)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
    setCurrent('dashboard')
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

  // Not logged in - show login
  if (!user) {
    return <Login onLogin={handleLogin} t={t} lang={lang} />
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
      </main>

      {/* Footer - Optional */}
      <footer className="text-center py-4 text-gray-600 text-xs">
        © 2025 CryptoSignal AI
      </footer>
    </div>
  )
}