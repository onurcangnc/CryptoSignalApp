// src/components/Login.jsx
import { useState } from 'react'
import api from '../api'

const Login = ({ onLogin, t, lang }) => {
  const [isRegister, setIsRegister] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const endpoint = isRegister ? '/api/register' : '/api/login'
      const resp = await api.post(endpoint, { email, password })
      const data = await resp.json()

      if (resp.ok) {
        localStorage.setItem('token', data.access_token)
        localStorage.setItem('user', JSON.stringify(data.user))
        onLogin(data.user)
      } else {
        setError(data.detail || 'Bir hata oluştu')
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent">
            🚀 CryptoSignal AI
          </h1>
          <p className="text-gray-400 mt-2">
            {lang === 'tr' ? 'Yapay Zeka Destekli Kripto Analizi' : 'AI-Powered Crypto Analysis'}
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="bg-gray-800/50 rounded-2xl p-6 border border-gray-700/50 backdrop-blur">
          <h2 className="text-xl font-bold text-white mb-6">
            {isRegister ? t.register : t.login}
          </h2>

          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 mb-4">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          <div className="space-y-4">
            <div>
              <input
                type="email"
                placeholder={t.email}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-yellow-500 transition-colors"
                required
              />
            </div>

            <div>
              <input
                type="password"
                placeholder={t.password}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-yellow-500 transition-colors"
                required
                minLength={6}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-lg text-black font-bold hover:opacity-90 disabled:opacity-50 transition-opacity"
            >
              {loading ? '...' : isRegister ? t.register : t.login}
            </button>
          </div>

          <p className="text-center text-gray-400 mt-4">
            {isRegister ? (
              <span>
                {lang === 'tr' ? 'Hesabınız var mı?' : 'Have an account?'}{' '}
                <button
                  type="button"
                  onClick={() => setIsRegister(false)}
                  className="text-yellow-400 hover:underline"
                >
                  {t.login}
                </button>
              </span>
            ) : (
              <span>
                {lang === 'tr' ? 'Hesabınız yok mu?' : 'No account?'}{' '}
                <button
                  type="button"
                  onClick={() => setIsRegister(true)}
                  className="text-yellow-400 hover:underline"
                >
                  {t.register}
                </button>
              </span>
            )}
          </p>
        </form>

        {/* Footer */}
        <p className="text-center text-gray-600 text-xs mt-6">
          © 2025 CryptoSignal AI
        </p>
      </div>
    </div>
  )
}

export default Login