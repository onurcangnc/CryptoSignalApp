import React from 'react'

/**
 * Başarı Oranı Kartı - Yeşil Tema
 * AL/SAT tavsiyelerinin başarı oranını gösterir (BEKLE hariç)
 */
export const SuccessRateCard = ({ stats }) => {
  if (!stats || stats.insufficient_data) {
    return null
  }

  // Trade-only metrikler (AL/SAT - BEKLE hariç)
  const tradeTotal = stats.trade_total || 0
  const tradeSuccessful = stats.trade_successful || 0
  const tradeSuccessRate = stats.trade_success_rate || 0

  // Hiç trade yoksa gösterme
  if (tradeTotal === 0) {
    return null
  }

  return (
    <div className="group bg-gradient-to-br from-green-900/20 to-emerald-900/20 rounded-xl p-5 border border-green-700/50 hover:border-green-500/70 transition-all duration-300 hover:shadow-lg hover:shadow-green-500/30 hover:-translate-y-1">
      <h3 className="text-gray-400 text-sm mb-3 flex items-center gap-2">
        <span>📊</span>
        <span>AL/SAT Tavsiye Başarısı</span>
      </h3>

      <div className="space-y-3">
        {/* Ana sayı */}
        <div className="flex items-baseline gap-2">
          <span className="text-5xl font-bold text-green-400">
            {tradeSuccessful}
          </span>
          <span className="text-2xl text-gray-400">/ {tradeTotal}</span>
        </div>

        {/* Açıklama metni */}
        <div className="text-sm text-gray-300">
          {tradeTotal} AL/SAT tavsiyesinden <span className="font-bold text-green-400">{tradeSuccessful}</span> tanesi kârlı
        </div>

        {/* Progress bar */}
        <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-green-500 to-emerald-400 transition-all duration-1000"
            style={{ width: `${tradeSuccessRate}%` }}
          />
        </div>

        {/* Yüzde gösterimi */}
        <div className="text-right text-xs text-green-400 font-medium">
          %{tradeSuccessRate.toFixed(1)} başarı oranı
        </div>
      </div>
    </div>
  )
}

/**
 * Bileşik Getiri Simülasyonu Kartı - Mor Tema
 * 100₺ ile başlasaydı ne olurdu gösterir
 */
export const CompoundReturnCard = ({ stats }) => {
  if (!stats || stats.insufficient_data || !stats.compound_return) {
    return null
  }

  const compound = stats.compound_return
  const isProfit = compound.total_return_pct > 0

  return (
    <div className="group bg-gradient-to-br from-purple-900/20 to-pink-900/20 rounded-xl p-5 border border-purple-700/50 hover:border-purple-500/70 transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/30 hover:-translate-y-1">
      <h3 className="text-gray-400 text-sm mb-3 flex items-center gap-2">
        <span>💰</span>
        <span>100₺ ile Başlasaydınız</span>
      </h3>

      <div className="space-y-3">
        {/* Başlangıç → Son durum */}
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs text-gray-500">Başlangıç</div>
            <div className="text-xl font-bold text-gray-300">
              {compound.initial_amount}₺
            </div>
          </div>

          <div className="text-3xl animate-pulse text-purple-400">→</div>

          <div>
            <div className="text-xs text-gray-500">Bugün</div>
            <div className={`text-4xl font-bold ${isProfit ? 'text-green-400' : 'text-red-400'}`}>
              {compound.final_amount}₺
            </div>
          </div>
        </div>

        {/* Toplam getiri */}
        <div className={`text-sm font-medium text-center py-2 rounded-lg ${
          isProfit ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'
        }`}>
          {isProfit ? '+' : ''}{compound.total_return_pct}% Toplam Getiri
        </div>

        {/* Açıklama */}
        <div className="text-xs text-gray-500 italic flex items-start gap-1">
          <span>💡</span>
          <span>AL/SAT tavsiyelerini takip etseydik bu kadar kazanırdık</span>
        </div>
      </div>
    </div>
  )
}

/**
 * En Başarılı Tavsiyeler Kartı - Sarı Tema
 * Top 3 kazançları gösterir (sosyal kanıt)
 */
export const TopWinsCard = ({ stats }) => {
  if (!stats || stats.insufficient_data || !stats.top_signals || stats.top_signals.length === 0) {
    return null
  }

  const medals = ['🥇', '🥈', '🥉']

  return (
    <div className="group bg-gradient-to-br from-yellow-900/20 to-orange-900/20 rounded-xl p-5 border border-yellow-700/50 hover:border-yellow-500/70 transition-all duration-300 hover:shadow-lg hover:shadow-yellow-500/30 hover:-translate-y-1">
      <h3 className="text-gray-400 text-sm mb-3 flex items-center gap-2">
        <span>🏆</span>
        <span>En Başarılı Tavsiyeler</span>
      </h3>

      <div className="space-y-2">
        {stats.top_signals.map((sig, idx) => (
          <div
            key={idx}
            className="flex items-center justify-between p-2 bg-gray-800/50 rounded-lg hover:bg-gray-700/50 transition"
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">{medals[idx]}</span>
              <div>
                <div className="font-medium text-white">{sig.symbol}</div>
                <div className="text-xs text-gray-500">
                  {new Date(sig.date).toLocaleDateString('tr-TR')}
                </div>
              </div>
            </div>
            <div className="text-lg font-bold text-green-400">
              +{sig.profit_pct.toFixed(1)}%
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/**
 * Şeffaflık & Risk Kartı - Gri Tema
 * Kayıpları ve riskleri gösterir
 */
export const TransparencyCard = ({ stats }) => {
  if (!stats || stats.insufficient_data) {
    return null
  }

  const worstLoss = stats.worst_signal
  const avgLoss = stats.avg_loss_pct || 0

  return (
    <div className="group bg-gradient-to-br from-gray-800/50 to-gray-900/50 rounded-xl p-5 border border-gray-700/50 hover:border-gray-600/70 transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
      <h3 className="text-gray-400 text-sm mb-3 flex items-center gap-2">
        <span>⚠️</span>
        <span>Şeffaflık & Risk</span>
      </h3>

      <div className="space-y-3">
        {/* En büyük kayıp */}
        {worstLoss && (
          <div className="p-2 bg-red-900/20 border border-red-700/30 rounded-lg">
            <div className="text-xs text-gray-400 mb-1">En Büyük Kayıp:</div>
            <div className="flex justify-between items-center">
              <span className="font-medium text-white">{worstLoss.symbol}</span>
              <span className="text-red-400 font-bold">
                {worstLoss.loss_pct.toFixed(1)}%
              </span>
            </div>
          </div>
        )}

        {/* Ortalama kayıp */}
        <div className="text-sm text-gray-400 flex justify-between">
          <span className="text-gray-500">Ortalama Kayıp:</span>
          <span className="font-bold text-red-400">
            {avgLoss.toFixed(1)}%
          </span>
        </div>

        {/* Risk uyarısı */}
        <div className="text-xs text-yellow-200 bg-yellow-900/20 p-3 rounded border border-yellow-700/30 leading-relaxed">
          ⚠️ Her tavsiye kârlı olmaz. Risk yönetimi önemlidir. Kaybetmeyi göze alamayacağınız parayla yatırım yapmayın.
        </div>
      </div>
    </div>
  )
}

/**
 * Yetersiz Veri Durumu - Mavi Tema
 * < 30 sinyal varsa gösterilir
 */
export const InsufficientDataState = ({ stats }) => {
  if (!stats || !stats.insufficient_data) {
    return null
  }

  const progressPct = stats.progress_pct || 0

  return (
    <div className="col-span-1 md:col-span-2 bg-blue-900/20 border border-blue-700/50 rounded-xl p-6 text-center">
      <div className="text-6xl mb-4">🤖</div>

      <h3 className="text-2xl font-bold text-white mb-2">
        AI Hala Öğreniyor
      </h3>

      <p className="text-gray-400 mb-4">
        {stats.total_signals} tavsiye tamamlandı. En az {stats.min_required} gerekiyor.
      </p>

      {/* Progress bar */}
      <div className="max-w-md mx-auto mb-3">
        <div className="h-4 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 transition-all duration-500"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      <div className="text-sm text-gray-500">
        %{progressPct.toFixed(0)} Tamamlandı
      </div>

      <div className="mt-4 text-xs text-blue-300 italic">
        Her gün yeni veriler ekleniyor. Birkaç gün içinde performans verilerini göreceksiniz.
      </div>
    </div>
  )
}

/**
 * Ana Grid Container
 * 4 kartı veya yetersiz veri durumunu gösterir
 */
export const SignalPerformanceGrid = ({ stats }) => {
  // Veri yükleniyor
  if (!stats) {
    return (
      <div className="col-span-1 md:col-span-2 bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 text-center">
        <div className="text-4xl mb-3">⏳</div>
        <p className="text-gray-400">Performans verileri yükleniyor...</p>
      </div>
    )
  }

  // Yetersiz veri
  if (stats.insufficient_data) {
    return <InsufficientDataState stats={stats} />
  }

  // Yeterli veri var - 4 kartı göster
  return (
    <>
      <SuccessRateCard stats={stats} />
      <CompoundReturnCard stats={stats} />
      <TopWinsCard stats={stats} />
      <TransparencyCard stats={stats} />
    </>
  )
}

export default SignalPerformanceGrid
