// src/components/ui/AdBanner.jsx
// Google AdSense Banner Component - Policy Compliant

import { useEffect, useRef, useState } from 'react'

/**
 * AdBanner Component
 *
 * Google AdSense compliant ad banner with proper labeling
 *
 * @param {string} slot - Ad slot ID
 * @param {string} format - Ad format (auto, rectangle, horizontal, vertical)
 * @param {string} className - Additional CSS classes
 * @param {boolean} showLabel - Show "Advertisement" label (recommended for compliance)
 */
export function AdBanner({
  slot = "4444444444",
  format = "auto",
  className = "",
  showLabel = true
}) {
  const adRef = useRef(null)
  const [adLoaded, setAdLoaded] = useState(false)
  const [adError, setAdError] = useState(false)

  useEffect(() => {
    try {
      if (window.adsbygoogle && adRef.current) {
        // Check if ad already loaded in this container
        if (adRef.current.getAttribute('data-ad-status') === 'filled') {
          setAdLoaded(true)
          return
        }

        (window.adsbygoogle = window.adsbygoogle || []).push({})

        // Check ad status after delay
        setTimeout(() => {
          if (adRef.current) {
            const status = adRef.current.getAttribute('data-ad-status')
            if (status === 'filled') {
              setAdLoaded(true)
            } else if (status === 'unfilled') {
              setAdError(true)
            }
          }
        }, 2000)
      }
    } catch (e) {
      console.error('AdSense error:', e)
      setAdError(true)
    }
  }, [])

  // Don't render anything if ad failed to load
  if (adError) return null

  const getAdStyle = () => {
    switch (format) {
      case 'rectangle':
        return { display: 'block', width: '300px', height: '250px' }
      case 'horizontal':
        return { display: 'block', width: '100%', height: '90px' }
      case 'vertical':
        return { display: 'block', width: '160px', height: '600px' }
      case 'leaderboard':
        return { display: 'block', width: '728px', maxWidth: '100%', height: '90px' }
      default:
        return { display: 'block' }
    }
  }

  return (
    <div className={`ad-container ${className}`}>
      {/* Advertisement Label - Google Policy Compliant */}
      {showLabel && (
        <div className="text-center mb-1">
          <span className="text-[10px] text-gray-500 uppercase tracking-wider">
            Advertisement
          </span>
        </div>
      )}

      {/* Ad Container */}
      <div className="flex justify-center">
        <ins
          ref={adRef}
          className="adsbygoogle"
          style={getAdStyle()}
          data-ad-client="ca-pub-5907670584730847"
          data-ad-slot={slot}
          data-ad-format={format === 'auto' ? 'auto' : undefined}
          data-full-width-responsive={format === 'auto' ? 'true' : undefined}
        />
      </div>
    </div>
  )
}

/**
 * InFeedAd Component
 *
 * In-feed native ad for lists and grids
 */
export function InFeedAd({ className = "" }) {
  const adRef = useRef(null)

  useEffect(() => {
    try {
      if (window.adsbygoogle && adRef.current) {
        (window.adsbygoogle = window.adsbygoogle || []).push({})
      }
    } catch (e) {
      console.error('InFeed AdSense error:', e)
    }
  }, [])

  return (
    <div className={`in-feed-ad ${className}`}>
      <ins
        ref={adRef}
        className="adsbygoogle"
        style={{ display: 'block' }}
        data-ad-client="ca-pub-5907670584730847"
        data-ad-slot="5555555555"
        data-ad-format="fluid"
        data-ad-layout-key="-6t+ed+2i-1n-4w"
      />
    </div>
  )
}

export default AdBanner
