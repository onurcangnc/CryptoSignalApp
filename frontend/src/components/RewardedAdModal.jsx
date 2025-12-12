// src/components/RewardedAdModal.jsx
// Rewarded Ad Modal - Watch ad to earn AI credits

import { useState, useEffect, useCallback } from 'react'
import api from '../api'

/**
 * RewardedAdModal Component
 *
 * Shows an ad for a specified duration, then allows user to claim reward
 *
 * @param {boolean} isOpen - Whether modal is open
 * @param {function} onClose - Close handler
 * @param {function} onRewardClaimed - Called when reward is successfully claimed
 * @param {string} lang - Language ('tr' or 'en')
 */
export function RewardedAdModal({ isOpen, onClose, onRewardClaimed, lang = 'tr' }) {
  const [countdown, setCountdown] = useState(15)
  const [canClaim, setCanClaim] = useState(false)
  const [claiming, setClaiming] = useState(false)
  const [error, setError] = useState(null)
  const [adLoaded, setAdLoaded] = useState(false)

  const texts = {
    tr: {
      title: 'AI Kredisi Kazan',
      subtitle: 'Reklamı izleyerek 1 AI analiz kredisi kazanın',
      watching: 'Reklam izleniyor...',
      secondsLeft: 'saniye kaldı',
      claim: 'Kredimi Al',
      claiming: 'Alınıyor...',
      close: 'Kapat',
      error: 'Bir hata oluştu',
      adPlaceholder: 'Reklam Alanı',
      success: 'Kredi kazanıldı!'
    },
    en: {
      title: 'Earn AI Credit',
      subtitle: 'Watch the ad to earn 1 AI analysis credit',
      watching: 'Watching ad...',
      secondsLeft: 'seconds left',
      claim: 'Claim Credit',
      claiming: 'Claiming...',
      close: 'Close',
      error: 'An error occurred',
      adPlaceholder: 'Ad Space',
      success: 'Credit earned!'
    }
  }

  const t = texts[lang] || texts.tr

  // Start countdown when modal opens
  useEffect(() => {
    if (!isOpen) {
      setCountdown(15)
      setCanClaim(false)
      setError(null)
      return
    }

    // Try to load AdSense
    try {
      if (window.adsbygoogle) {
        (window.adsbygoogle = window.adsbygoogle || []).push({})
        setAdLoaded(true)
      }
    } catch (e) {
      console.error('AdSense error:', e)
    }

    // Countdown timer
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(timer)
          setCanClaim(true)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [isOpen])

  const handleClaim = useCallback(async () => {
    if (!canClaim || claiming) return

    setClaiming(true)
    setError(null)

    try {
      const resp = await api.post('/api/ads/reward')

      if (resp.ok) {
        const data = await resp.json()
        onRewardClaimed?.(data.credits)
        onClose()
      } else {
        const err = await resp.json()
        setError(err.detail || t.error)
      }
    } catch (e) {
      setError(t.error)
    } finally {
      setClaiming(false)
    }
  }, [canClaim, claiming, onRewardClaimed, onClose, t.error])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-gray-900 rounded-2xl w-full max-w-md border border-gray-700 shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-blue-600 px-6 py-4">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span className="text-2xl">🎬</span>
            {t.title}
          </h2>
          <p className="text-purple-100 text-sm mt-1">{t.subtitle}</p>
        </div>

        {/* Ad Container */}
        <div className="p-6">
          <div
            className="bg-gray-800 rounded-lg overflow-hidden mb-4"
            style={{ minHeight: '250px' }}
          >
            {/* AdSense Container */}
            <ins
              className="adsbygoogle"
              style={{
                display: 'block',
                width: '100%',
                height: '250px'
              }}
              data-ad-client="ca-pub-5907670584730847"
              data-ad-slot="4444444444"
              data-ad-format="rectangle"
            />

            {/* Fallback if no ad */}
            {!adLoaded && (
              <div className="flex items-center justify-center h-full bg-gradient-to-br from-gray-800 to-gray-900">
                <div className="text-center">
                  <div className="text-4xl mb-2">📺</div>
                  <p className="text-gray-400">{t.adPlaceholder}</p>
                </div>
              </div>
            )}
          </div>

          {/* Countdown / Claim Button */}
          <div className="text-center">
            {!canClaim ? (
              <div className="space-y-3">
                <div className="flex items-center justify-center gap-2">
                  <div className="animate-spin text-2xl">⏳</div>
                  <span className="text-gray-300">{t.watching}</span>
                </div>
                <div className="text-4xl font-bold text-purple-400">
                  {countdown}
                </div>
                <p className="text-gray-500 text-sm">{t.secondsLeft}</p>

                {/* Progress bar */}
                <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-purple-500 to-blue-500 h-full transition-all duration-1000"
                    style={{ width: `${((15 - countdown) / 15) * 100}%` }}
                  />
                </div>
              </div>
            ) : (
              <button
                onClick={handleClaim}
                disabled={claiming}
                className="w-full py-4 px-6 bg-gradient-to-r from-green-500 to-emerald-600
                           text-white font-bold rounded-xl text-lg
                           hover:from-green-600 hover:to-emerald-700
                           disabled:opacity-50 disabled:cursor-not-allowed
                           transition-all duration-200 transform hover:scale-105
                           flex items-center justify-center gap-2"
              >
                {claiming ? (
                  <>
                    <div className="animate-spin">⏳</div>
                    {t.claiming}
                  </>
                ) : (
                  <>
                    <span className="text-xl">🎁</span>
                    {t.claim}
                  </>
                )}
              </button>
            )}

            {/* Error */}
            {error && (
              <div className="mt-4 p-3 bg-red-900/50 border border-red-500 rounded-lg text-red-300 text-sm">
                {error}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 pb-6">
          <button
            onClick={onClose}
            disabled={!canClaim && countdown > 0}
            className="w-full py-3 text-gray-400 hover:text-white
                       disabled:opacity-30 disabled:cursor-not-allowed
                       transition-colors"
          >
            {t.close}
          </button>
        </div>
      </div>
    </div>
  )
}

export default RewardedAdModal
