import { useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

/**
 * Google AdSense Banner Component
 *
 * Premium kullanıcılar reklam görmez
 * Free kullanıcılar için AdSense reklamları gösterir
 */
export function AdBanner({
  slot = "1234567890",
  format = "auto",
  style = {},
  className = ""
}) {
  const { user } = useAuth();

  useEffect(() => {
    // AdSense script'i yükle
    try {
      if (window.adsbygoogle && user?.tier !== 'premium') {
        (window.adsbygoogle = window.adsbygoogle || []).push({});
      }
    } catch (error) {
      console.error('AdSense loading error:', error);
    }
  }, [user]);

  // Premium kullanıcılar reklam görmez
  if (user?.tier === 'premium') {
    return null;
  }

  return (
    <div
      className={`ad-container ${className}`}
      style={{
        minHeight: '90px',
        margin: '20px 0',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#f8f9fa',
        borderRadius: '8px',
        overflow: 'hidden',
        ...style
      }}
    >
      <ins
        className="adsbygoogle"
        style={{
          display: 'block',
          width: '100%',
          height: '100%'
        }}
        data-ad-client="ca-pub-5907670584730847"
        data-ad-slot={slot}
        data-ad-format={format}
        data-full-width-responsive="true"
      />
    </div>
  );
}

/**
 * Inline Ad Banner (içerik arası)
 */
export function InlineAd({ slot = "2222222222" }) {
  return (
    <AdBanner
      slot={slot}
      format="fluid"
      style={{
        margin: '30px 0',
        minHeight: '250px'
      }}
    />
  );
}

/**
 * Sticky Bottom Ad (mobil için)
 */
export function StickyBottomAd({ slot = "3333333333" }) {
  const { user } = useAuth();

  if (user?.tier === 'premium') {
    return null;
  }

  return (
    <div style={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      zIndex: 1000,
      backgroundColor: 'white',
      boxShadow: '0 -2px 10px rgba(0,0,0,0.1)'
    }}>
      <AdBanner
        slot={slot}
        format="horizontal"
        style={{ margin: 0 }}
      />
    </div>
  );
}

export default AdBanner;