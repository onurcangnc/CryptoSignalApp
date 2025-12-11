import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

/**
 * Premium Call-to-Action Component
 *
 * Free kullanıcıları Premium'a yönlendirir
 * "Reklamlardan kurtul" mesajı
 */
export function PremiumCTA() {
  const navigate = useNavigate();
  const { user } = useAuth();

  // Premium kullanıcılara gösterme
  if (user?.tier === 'premium') {
    return null;
  }

  return (
    <div
      style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        padding: '40px 30px',
        borderRadius: '16px',
        margin: '40px 0',
        textAlign: 'center',
        boxShadow: '0 10px 30px rgba(102, 126, 234, 0.3)'
      }}
    >
      {/* Başlık */}
      <div style={{ fontSize: '32px', marginBottom: '10px' }}>
        🚀
      </div>
      <h2 style={{
        fontSize: '28px',
        fontWeight: 'bold',
        margin: '0 0 15px 0',
        color: 'white'
      }}>
        Reklamlardan Kurtul!
      </h2>

      <p style={{
        fontSize: '18px',
        opacity: 0.95,
        marginBottom: '30px',
        maxWidth: '600px',
        margin: '0 auto 30px'
      }}>
        Premium'a geç, tüm reklamları kaldır + bonus özellikler kazan
      </p>

      {/* Özellikler */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '15px',
        maxWidth: '800px',
        margin: '0 auto 30px',
        textAlign: 'left'
      }}>
        <div style={{
          background: 'rgba(255,255,255,0.1)',
          padding: '15px',
          borderRadius: '8px'
        }}>
          <div style={{ fontSize: '20px', marginBottom: '5px' }}>✅</div>
          <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>Reklamsız Deneyim</div>
          <div style={{ fontSize: '14px', opacity: 0.9 }}>Tüm reklamlar kaldırılır</div>
        </div>

        <div style={{
          background: 'rgba(255,255,255,0.1)',
          padding: '15px',
          borderRadius: '8px'
        }}>
          <div style={{ fontSize: '20px', marginBottom: '5px' }}>🔄</div>
          <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>Sınırsız Analiz</div>
          <div style={{ fontSize: '14px', opacity: 0.9 }}>Günlük limit yok</div>
        </div>

        <div style={{
          background: 'rgba(255,255,255,0.1)',
          padding: '15px',
          borderRadius: '8px'
        }}>
          <div style={{ fontSize: '20px', marginBottom: '5px' }}>🔔</div>
          <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>Real-time Bildirimler</div>
          <div style={{ fontSize: '14px', opacity: 0.9 }}>Anında fiyat alarmları</div>
        </div>

        <div style={{
          background: 'rgba(255,255,255,0.1)',
          padding: '15px',
          borderRadius: '8px'
        }}>
          <div style={{ fontSize: '20px', marginBottom: '5px' }}>⚡</div>
          <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>Gelişmiş Özellikler</div>
          <div style={{ fontSize: '14px', opacity: 0.9 }}>Portfolio simülasyon vs.</div>
        </div>
      </div>

      {/* Fiyat */}
      <div style={{
        fontSize: '36px',
        fontWeight: 'bold',
        margin: '20px 0',
        color: 'white'
      }}>
        $9.99<span style={{ fontSize: '18px', opacity: 0.8 }}>/ay</span>
      </div>

      <div style={{
        fontSize: '14px',
        opacity: 0.85,
        marginBottom: '25px'
      }}>
        TRC-20 USDT ile kolay ödeme
      </div>

      {/* CTA Butonu */}
      <button
        onClick={() => navigate('/premium')}
        style={{
          background: 'white',
          color: '#667eea',
          padding: '18px 50px',
          border: 'none',
          borderRadius: '12px',
          fontSize: '20px',
          fontWeight: 'bold',
          cursor: 'pointer',
          boxShadow: '0 5px 15px rgba(0,0,0,0.2)',
          transition: 'transform 0.2s, box-shadow 0.2s'
        }}
        onMouseEnter={(e) => {
          e.target.style.transform = 'translateY(-2px)';
          e.target.style.boxShadow = '0 8px 20px rgba(0,0,0,0.3)';
        }}
        onMouseLeave={(e) => {
          e.target.style.transform = 'translateY(0)';
          e.target.style.boxShadow = '0 5px 15px rgba(0,0,0,0.2)';
        }}
      >
        Premium'a Geç 🚀
      </button>

      {/* İndirim Badge */}
      <div style={{
        marginTop: '20px',
        fontSize: '13px',
        opacity: 0.9,
        fontStyle: 'italic'
      }}>
        🎉 İlk 100 kullanıcıya %50 indirim: sadece $4.99/ay
      </div>
    </div>
  );
}

/**
 * Compact Premium Banner (küçük versiyon)
 */
export function CompactPremiumBanner() {
  const navigate = useNavigate();
  const { user } = useAuth();

  if (user?.tier === 'premium') {
    return null;
  }

  return (
    <div
      onClick={() => navigate('/premium')}
      style={{
        background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        padding: '15px 20px',
        borderRadius: '8px',
        margin: '20px 0',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        transition: 'transform 0.2s'
      }}
      onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.02)'}
      onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
    >
      <div>
        <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>
          🚀 Reklamlardan Kurtul
        </div>
        <div style={{ fontSize: '14px', opacity: 0.9 }}>
          $9.99/ay - Sınırsız analiz + Reklamsız
        </div>
      </div>
      <div style={{
        background: 'white',
        color: '#667eea',
        padding: '8px 20px',
        borderRadius: '6px',
        fontWeight: 'bold',
        fontSize: '14px'
      }}>
        Premium'a Geç →
      </div>
    </div>
  );
}

export default PremiumCTA;
