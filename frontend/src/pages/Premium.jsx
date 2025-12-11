import { useState } from 'react';

/**
 * Premium Ödeme Sayfası
 *
 * Solana USDT ile manuel ödeme
 * Phantom, Solflare vs. herhangi bir Solana cüzdanından gönderilebilir
 */
export default function PremiumPage({ user, setCurrent }) {
  const [loading, setLoading] = useState(false);
  const [notified, setNotified] = useState(false);

  // Solana USDT adresiniz
  const USDT_ADDRESS = "GKwGUswszYhA88zyihXDLugoReCikEA4r26tHor4TGwV";
  const PRICE = 9.99;
  const DISCOUNT_PRICE = 4.99; // İlk 100 kullanıcı için

  // Zaten Premium ise
  if (user?.tier === 'premium') {
    return (
      <div style={{ maxWidth: '800px', margin: '50px auto', padding: '20px', textAlign: 'center' }}>
        <div style={{ fontSize: '64px', marginBottom: '20px' }}>✅</div>
        <h1>Zaten Premium Kullanıcısınız!</h1>
        <p>Tüm özelliklere sınırsız erişiminiz var.</p>
        <button
          onClick={() => setCurrent('dashboard')}
          style={{
            background: '#667eea',
            color: 'white',
            padding: '12px 30px',
            border: 'none',
            borderRadius: '8px',
            fontSize: '16px',
            cursor: 'pointer',
            marginTop: '20px'
          }}
        >
          Dashboard'a Dön
        </button>
      </div>
    );
  }

  const handleCopyAddress = () => {
    navigator.clipboard.writeText(USDT_ADDRESS);
    alert('✅ Adres kopyalandı!');
  };

  const handleNotifyPayment = async () => {
    setLoading(true);

    try {
      const response = await fetch('/api/payment/manual-notification', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          tier: 'premium',
          amount: DISCOUNT_PRICE
        })
      });

      if (response.ok) {
        setNotified(true);
        alert('✅ Ödeme bildiriminiz alındı! 1-2 saat içinde Premium hesabınız aktif olacak. Email ile bilgilendirileceğiz.');
      } else {
        alert('❌ Bir hata oluştu. Lütfen tekrar deneyin.');
      }
    } catch (error) {
      console.error('Payment notification error:', error);
      alert('❌ Bağlantı hatası. Lütfen tekrar deneyin.');
    }

    setLoading(false);
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '50px auto', padding: '20px' }}>
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: '50px' }}>
        <h1 style={{ fontSize: '42px', marginBottom: '10px' }}>
          Premium - Reklamsız Deneyim
        </h1>
        <p style={{ fontSize: '18px', color: '#666' }}>
          Tüm reklamlardan kurtul + bonus özellikler
        </p>
      </div>

      {/* Plan Karşılaştırması */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '30px',
        marginBottom: '60px'
      }}>
        {/* Free Plan */}
        <div style={{
          border: '2px solid #e0e0e0',
          borderRadius: '16px',
          padding: '30px',
          background: 'white'
        }}>
          <h3 style={{ fontSize: '24px', marginBottom: '10px' }}>Free</h3>
          <div style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '20px' }}>
            $0
          </div>

          <ul style={{
            listStyle: 'none',
            padding: 0,
            marginBottom: '30px'
          }}>
            <li style={{ padding: '10px 0', borderBottom: '1px solid #f0f0f0' }}>
              📊 10 analiz/gün
            </li>
            <li style={{ padding: '10px 0', borderBottom: '1px solid #f0f0f0' }}>
              📈 Temel özellikler
            </li>
            <li style={{ padding: '10px 0', borderBottom: '1px solid #f0f0f0' }}>
              💼 Portfolio tracking
            </li>
            <li style={{ padding: '10px 0', color: '#ff6b6b' }}>
              ⚠️ Reklamlar gösteriliyor
            </li>
          </ul>

          <div style={{
            textAlign: 'center',
            color: '#999',
            fontSize: '14px'
          }}>
            Şu anki planınız
          </div>
        </div>

        {/* Premium Plan */}
        <div style={{
          border: '3px solid #667eea',
          borderRadius: '16px',
          padding: '30px',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          position: 'relative',
          boxShadow: '0 20px 40px rgba(102, 126, 234, 0.3)'
        }}>
          <div style={{
            position: 'absolute',
            top: '-15px',
            left: '50%',
            transform: 'translateX(-50%)',
            background: '#ffd700',
            color: '#333',
            padding: '5px 20px',
            borderRadius: '20px',
            fontSize: '14px',
            fontWeight: 'bold'
          }}>
            🔥 EN POPÜLER
          </div>

          <h3 style={{ fontSize: '24px', marginBottom: '10px' }}>Premium</h3>
          <div style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '5px' }}>
            <span style={{ textDecoration: 'line-through', opacity: 0.6, fontSize: '24px' }}>
              ${PRICE}
            </span>
            {' '}
            ${DISCOUNT_PRICE}
            <span style={{ fontSize: '18px', opacity: 0.8 }}>/ay</span>
          </div>
          <div style={{ fontSize: '14px', opacity: 0.9, marginBottom: '20px' }}>
            🎉 İlk 100 kullanıcıya %50 indirim
          </div>

          <ul style={{
            listStyle: 'none',
            padding: 0,
            marginBottom: '30px'
          }}>
            <li style={{ padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,0.2)' }}>
              ✅ Sınırsız analiz
            </li>
            <li style={{ padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,0.2)' }}>
              ✅ REKLAMSIZ deneyim
            </li>
            <li style={{ padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,0.2)' }}>
              ✅ Real-time bildirimler
            </li>
            <li style={{ padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,0.2)' }}>
              ✅ Gelişmiş özellikler
            </li>
            <li style={{ padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,0.2)' }}>
              ✅ Portfolio simülasyon
            </li>
            <li style={{ padding: '10px 0' }}>
              ✅ Priority support
            </li>
          </ul>

          <div style={{
            background: 'rgba(255,255,255,0.2)',
            padding: '15px',
            borderRadius: '8px',
            textAlign: 'center'
          }}>
            Aşağıdan ödeme yapın ⬇️
          </div>
        </div>
      </div>

      {/* Ödeme Bölümü */}
      <div style={{
        background: '#f8f9fa',
        padding: '40px',
        borderRadius: '16px',
        marginBottom: '40px'
      }}>
        <h2 style={{ fontSize: '28px', marginBottom: '10px' }}>
          💳 USDT ile Öde (Solana Network)
        </h2>
        <p style={{ color: '#666', marginBottom: '30px' }}>
          Phantom, Solflare veya herhangi bir Solana cüzdanından USDT gönderebilirsiniz
        </p>

        {/* Adres */}
        <div style={{ marginBottom: '25px' }}>
          <label style={{
            display: 'block',
            fontWeight: 'bold',
            marginBottom: '10px',
            fontSize: '16px'
          }}>
            Gönderilecek Adres:
          </label>
          <div style={{ display: 'flex', gap: '10px' }}>
            <input
              type="text"
              value={USDT_ADDRESS}
              readOnly
              onClick={(e) => e.target.select()}
              style={{
                flex: 1,
                padding: '15px',
                border: '2px solid #ddd',
                borderRadius: '8px',
                fontSize: '16px',
                fontFamily: 'monospace',
                background: 'white'
              }}
            />
            <button
              onClick={handleCopyAddress}
              style={{
                padding: '15px 30px',
                background: '#667eea',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '16px',
                fontWeight: 'bold',
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}
            >
              📋 Kopyala
            </button>
          </div>
        </div>

        {/* Tutar */}
        <div style={{ marginBottom: '30px' }}>
          <label style={{
            display: 'block',
            fontWeight: 'bold',
            marginBottom: '10px',
            fontSize: '16px'
          }}>
            Gönderilecek Tutar:
          </label>
          <input
            type="text"
            value={`${DISCOUNT_PRICE} USDT`}
            readOnly
            style={{
              width: '100%',
              padding: '15px',
              border: '2px solid #ddd',
              borderRadius: '8px',
              fontSize: '20px',
              fontWeight: 'bold',
              background: 'white',
              textAlign: 'center'
            }}
          />
        </div>

        {/* Uyarılar */}
        <div style={{
          background: '#fff3cd',
          border: '2px solid #ffc107',
          borderRadius: '8px',
          padding: '20px',
          marginBottom: '30px'
        }}>
          <div style={{ fontWeight: 'bold', marginBottom: '10px', fontSize: '16px' }}>
            ⚠️ Önemli Notlar:
          </div>
          <ul style={{ margin: 0, paddingLeft: '20px' }}>
            <li style={{ marginBottom: '8px' }}>
              <strong>Mutlaka Solana network kullanın!</strong> (Transfer ücreti çok düşük)
            </li>
            <li style={{ marginBottom: '8px' }}>
              Tam tutarı gönderin: <strong>{DISCOUNT_PRICE} USDT</strong>
            </li>
            <li style={{ marginBottom: '8px' }}>
              Phantom, Solflare, Trust Wallet veya herhangi bir Solana cüzdanından gönderebilirsiniz
            </li>
            <li>
              Ödeme sonrası aşağıdaki butona tıklayın
            </li>
          </ul>
        </div>

        {/* Bildirim Butonu */}
        {!notified ? (
          <button
            onClick={handleNotifyPayment}
            disabled={loading}
            style={{
              width: '100%',
              padding: '20px',
              background: loading ? '#ccc' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '12px',
              fontSize: '20px',
              fontWeight: 'bold',
              cursor: loading ? 'not-allowed' : 'pointer',
              boxShadow: '0 5px 15px rgba(102, 126, 234, 0.3)'
            }}
          >
            {loading ? 'Gönderiliyor...' : '✅ Ödeme Yaptım, Hesabımı Aktifleştir'}
          </button>
        ) : (
          <div style={{
            background: '#d4edda',
            border: '2px solid #28a745',
            borderRadius: '12px',
            padding: '20px',
            textAlign: 'center',
            color: '#155724'
          }}>
            <div style={{ fontSize: '48px', marginBottom: '10px' }}>✅</div>
            <div style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '10px' }}>
              Bildiriminiz Alındı!
            </div>
            <p style={{ margin: 0 }}>
              Ödemenizi kontrol ediyoruz. 1-2 saat içinde Premium hesabınız aktif olacak.
              Email ile bilgilendireceğiz.
            </p>
          </div>
        )}

        <p style={{
          textAlign: 'center',
          color: '#666',
          fontSize: '14px',
          marginTop: '20px'
        }}>
          Hesabınız 1-2 saat içinde onaylanmazsa <a href="mailto:onurcangencbilkent@gmail.com" style={{ color: '#667eea' }}>onurcangencbilkent@gmail.com</a> ile iletişime geçebilirsiniz.
        </p>
      </div>

      {/* SSS */}
      <div style={{ maxWidth: '700px', margin: '0 auto' }}>
        <h3 style={{ fontSize: '24px', marginBottom: '20px', textAlign: 'center' }}>
          Sık Sorulan Sorular
        </h3>

        <details style={{ marginBottom: '15px', cursor: 'pointer' }}>
          <summary style={{ fontWeight: 'bold', padding: '15px', background: '#f8f9fa', borderRadius: '8px' }}>
            USDT'yi nereden gönderebilirim?
          </summary>
          <div style={{ padding: '15px', background: 'white', borderRadius: '0 0 8px 8px' }}>
            Phantom, Solflare, Trust Wallet veya herhangi bir Solana destekleyen cüzdandan gönderebilirsiniz.
            Mutlaka Solana network'ünü seçin (SPL Token).
          </div>
        </details>

        <details style={{ marginBottom: '15px', cursor: 'pointer' }}>
          <summary style={{ fontWeight: 'bold', padding: '15px', background: '#f8f9fa', borderRadius: '8px' }}>
            Ne kadar sürede aktif olur?
          </summary>
          <div style={{ padding: '15px', background: 'white', borderRadius: '0 0 8px 8px' }}>
            Ödeme bildirimi yaptıktan sonra 1-2 saat içinde manuel olarak kontrol edip hesabınızı aktifleştiriyoruz.
            Email ile bilgilendireceğiz.
          </div>
        </details>

        <details style={{ marginBottom: '15px', cursor: 'pointer' }}>
          <summary style={{ fontWeight: 'bold', padding: '15px', background: '#f8f9fa', borderRadius: '8px' }}>
            Otomatik yenileniyor mu?
          </summary>
          <div style={{ padding: '15px', background: 'white', borderRadius: '0 0 8px 8px' }}>
            Hayır, otomatik yenilenme yok. Her ay manuel olarak yenilemeniz gerekiyor.
            Abonelik bitiminden 7 gün önce email ile hatırlatma göndereceğiz.
          </div>
        </details>

        <details style={{ marginBottom: '15px', cursor: 'pointer' }}>
          <summary style={{ fontWeight: 'bold', padding: '15px', background: '#f8f9fa', borderRadius: '8px' }}>
            İade alabilir miyim?
          </summary>
          <div style={{ padding: '15px', background: 'white', borderRadius: '0 0 8px 8px' }}>
            İlk 7 gün içinde memnun kalmazsanız tam iade yapıyoruz. Destek ekibimize email atmanız yeterli.
          </div>
        </details>
      </div>
    </div>
  );
}