// src/components/ui/Disclaimer.jsx
// Risk Disclaimer Component - AdSense & Financial Compliance

/**
 * RiskDisclaimer Component
 *
 * Financial risk warning for AdSense and regulatory compliance
 * Must be visible on all pages showing crypto data/signals
 */
export function RiskDisclaimer({ lang = "tr", variant = "default", className = "" }) {
  const texts = {
    tr: {
      title: "Risk Uyarısı",
      short: "Bu platform yatırım tavsiyesi vermez. Kripto para yatırımları yüksek risk içerir.",
      full: "Bu platformda sunulan bilgiler yalnızca eğitim ve bilgilendirme amaçlıdır ve yatırım tavsiyesi niteliği taşımaz. Kripto para birimleri son derece volatil ve riskli yatırım araçlarıdır. Yatırımlarınızın tamamını kaybedebilirsiniz. Herhangi bir yatırım kararı vermeden önce kendi araştırmanızı yapın ve gerekirse profesyonel finansal danışmanlık alın. Geçmiş performans, gelecekteki sonuçların garantisi değildir.",
      learnMore: "Daha fazla bilgi"
    },
    en: {
      title: "Risk Warning",
      short: "This platform does not provide investment advice. Cryptocurrency investments carry high risk.",
      full: "The information provided on this platform is for educational and informational purposes only and does not constitute investment advice. Cryptocurrencies are highly volatile and risky investment instruments. You may lose your entire investment. Always do your own research before making any investment decisions and seek professional financial advice if needed. Past performance is not a guarantee of future results.",
      learnMore: "Learn more"
    }
  }

  const t = texts[lang] || texts.en

  if (variant === "compact") {
    return (
      <div className={`text-xs text-gray-500 text-center py-2 ${className}`}>
        <span className="mr-1">⚠️</span>
        {t.short}
      </div>
    )
  }

  if (variant === "banner") {
    return (
      <div className={`bg-amber-900/20 border border-amber-700/30 rounded-xl p-4 ${className}`}>
        <div className="flex items-start gap-3">
          <span className="text-xl flex-shrink-0">⚠️</span>
          <div>
            <h4 className="text-amber-400 font-semibold text-sm mb-1">{t.title}</h4>
            <p className="text-amber-200/70 text-xs leading-relaxed">{t.short}</p>
          </div>
        </div>
      </div>
    )
  }

  if (variant === "footer") {
    return (
      <div className={`bg-gray-900/50 border-t border-gray-800 py-6 px-4 ${className}`}>
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-amber-500">⚠️</span>
            <h4 className="text-amber-400 font-semibold text-sm">{t.title}</h4>
          </div>
          <p className="text-gray-400 text-xs leading-relaxed">{t.full}</p>
        </div>
      </div>
    )
  }

  // Default - Full disclaimer box
  return (
    <div className={`bg-gradient-to-r from-amber-900/20 to-orange-900/20 border border-amber-700/30 rounded-2xl p-5 ${className}`}>
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 w-12 h-12 bg-amber-500/20 rounded-xl flex items-center justify-center">
          <span className="text-2xl">⚠️</span>
        </div>
        <div className="flex-1">
          <h4 className="text-amber-400 font-bold mb-2">{t.title}</h4>
          <p className="text-amber-200/70 text-sm leading-relaxed">{t.full}</p>
        </div>
      </div>
    </div>
  )
}

/**
 * InlineDisclaimer Component
 *
 * Small inline disclaimer for signal cards
 */
export function InlineDisclaimer({ lang = "tr", className = "" }) {
  const text = lang === "tr"
    ? "Yatırım tavsiyesi değildir"
    : "Not investment advice"

  return (
    <span className={`text-[10px] text-gray-500 italic ${className}`}>
      * {text}
    </span>
  )
}

/**
 * SignalDisclaimer Component
 *
 * Disclaimer specifically for signal pages
 */
export function SignalDisclaimer({ lang = "tr", className = "" }) {
  const texts = {
    tr: {
      title: "Önemli Bilgilendirme",
      points: [
        "Sinyaller AI tarafından oluşturulur ve yatırım tavsiyesi değildir",
        "Geçmiş performans gelecek sonuçları garanti etmez",
        "Yatırım kararları tamamen sizin sorumluluğunuzdadır",
        "Sadece kaybetmeyi göze alabileceğiniz miktarla yatırım yapın"
      ]
    },
    en: {
      title: "Important Information",
      points: [
        "Signals are AI-generated and do not constitute investment advice",
        "Past performance does not guarantee future results",
        "Investment decisions are solely your responsibility",
        "Only invest what you can afford to lose"
      ]
    }
  }

  const t = texts[lang] || texts.en

  return (
    <div className={`bg-gray-800/50 border border-gray-700/50 rounded-2xl p-5 ${className}`}>
      <h4 className="text-gray-300 font-semibold mb-3 flex items-center gap-2">
        <span>ℹ️</span> {t.title}
      </h4>
      <ul className="space-y-2">
        {t.points.map((point, i) => (
          <li key={i} className="text-gray-400 text-sm flex items-start gap-2">
            <span className="text-yellow-500 mt-0.5">•</span>
            {point}
          </li>
        ))}
      </ul>
    </div>
  )
}

export default RiskDisclaimer
