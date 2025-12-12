// src/components/ui/EmptyState.jsx
// Empty State Components with Illustrations

/**
 * EmptyState Component
 *
 * Shows a friendly empty state with illustration and action
 *
 * @param {string} type - Type of empty state (no-data, no-results, error, no-signals, etc.)
 * @param {string} title - Custom title
 * @param {string} description - Custom description
 * @param {string} actionLabel - Button label
 * @param {function} onAction - Button click handler
 * @param {string} lang - Language (tr/en)
 */
export function EmptyState({
  type = "no-data",
  title,
  description,
  actionLabel,
  onAction,
  lang = "tr",
  className = ""
}) {
  const configs = {
    "no-data": {
      illustration: "📭",
      title: {
        tr: "Henüz Veri Yok",
        en: "No Data Yet"
      },
      description: {
        tr: "Bu alanda henüz gösterilecek veri bulunmuyor.",
        en: "There's no data to display in this area yet."
      }
    },
    "no-results": {
      illustration: "🔍",
      title: {
        tr: "Sonuç Bulunamadı",
        en: "No Results Found"
      },
      description: {
        tr: "Arama kriterlerinize uygun sonuç bulunamadı. Farklı terimler deneyin.",
        en: "No results match your search criteria. Try different terms."
      }
    },
    "no-signals": {
      illustration: "📡",
      title: {
        tr: "Sinyal Bulunamadı",
        en: "No Signals Found"
      },
      description: {
        tr: "Şu anda aktif sinyal bulunmuyor. Kısa süre sonra yeni sinyaller oluşturulacak.",
        en: "No active signals at the moment. New signals will be generated shortly."
      }
    },
    "no-portfolio": {
      illustration: "💼",
      title: {
        tr: "Portföyünüz Boş",
        en: "Your Portfolio is Empty"
      },
      description: {
        tr: "Henüz portföyünüze coin eklemediniz. Takip etmek istediğiniz coinleri ekleyin.",
        en: "You haven't added any coins yet. Add coins you want to track."
      }
    },
    "no-alerts": {
      illustration: "🔔",
      title: {
        tr: "Alarm Yok",
        en: "No Alerts"
      },
      description: {
        tr: "Henüz fiyat alarmı oluşturmadınız. Fiyat değişikliklerinden haberdar olmak için alarm kurun.",
        en: "You haven't set any price alerts. Set alerts to be notified of price changes."
      }
    },
    "no-watchlist": {
      illustration: "⭐",
      title: {
        tr: "İzleme Listeniz Boş",
        en: "Your Watchlist is Empty"
      },
      description: {
        tr: "Favori coinlerinizi buraya ekleyin ve kolayca takip edin.",
        en: "Add your favorite coins here to track them easily."
      }
    },
    "no-news": {
      illustration: "📰",
      title: {
        tr: "Haber Bulunamadı",
        en: "No News Found"
      },
      description: {
        tr: "Şu anda gösterilecek haber bulunmuyor. Daha sonra tekrar kontrol edin.",
        en: "No news available at the moment. Check back later."
      }
    },
    "error": {
      illustration: "⚠️",
      title: {
        tr: "Bir Hata Oluştu",
        en: "Something Went Wrong"
      },
      description: {
        tr: "Veriler yüklenirken bir sorun oluştu. Lütfen tekrar deneyin.",
        en: "There was a problem loading the data. Please try again."
      }
    },
    "offline": {
      illustration: "📶",
      title: {
        tr: "Bağlantı Yok",
        en: "No Connection"
      },
      description: {
        tr: "İnternet bağlantınızı kontrol edin ve tekrar deneyin.",
        en: "Check your internet connection and try again."
      }
    },
    "maintenance": {
      illustration: "🔧",
      title: {
        tr: "Bakım Yapılıyor",
        en: "Under Maintenance"
      },
      description: {
        tr: "Sistem bakımda. Kısa süre sonra tekrar çevrimiçi olacağız.",
        en: "System is under maintenance. We'll be back online shortly."
      }
    },
    "coming-soon": {
      illustration: "🚀",
      title: {
        tr: "Yakında",
        en: "Coming Soon"
      },
      description: {
        tr: "Bu özellik üzerinde çalışıyoruz. Çok yakında sizlerle!",
        en: "We're working on this feature. Coming to you very soon!"
      }
    }
  }

  const config = configs[type] || configs["no-data"]
  const finalTitle = title || config.title[lang] || config.title.en
  const finalDescription = description || config.description[lang] || config.description.en

  return (
    <div className={`flex flex-col items-center justify-center py-16 px-6 ${className}`}>
      {/* Illustration Container */}
      <div className="relative mb-6">
        {/* Background Glow */}
        <div className="absolute inset-0 bg-gradient-to-br from-yellow-500/10 to-orange-500/10 rounded-full blur-2xl scale-150" />

        {/* Main Illustration */}
        <div className="relative w-24 h-24 flex items-center justify-center bg-gradient-to-br from-gray-800 to-gray-900 rounded-3xl border border-gray-700/50 shadow-xl">
          <span className="text-5xl">{config.illustration}</span>
        </div>

        {/* Decorative Elements */}
        <div className="absolute -top-2 -right-2 w-4 h-4 bg-yellow-500/30 rounded-full animate-pulse" />
        <div className="absolute -bottom-1 -left-1 w-3 h-3 bg-orange-500/30 rounded-full animate-pulse delay-300" />
      </div>

      {/* Title */}
      <h3 className="text-xl font-bold text-white mb-2 text-center">
        {finalTitle}
      </h3>

      {/* Description */}
      <p className="text-gray-400 text-center max-w-md mb-6 leading-relaxed">
        {finalDescription}
      </p>

      {/* Action Button */}
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="px-6 py-3 bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 text-black font-semibold rounded-xl transition-all duration-200 transform hover:scale-105 hover:shadow-lg hover:shadow-yellow-500/25"
        >
          {actionLabel}
        </button>
      )}
    </div>
  )
}

/**
 * CompactEmptyState Component
 *
 * Smaller empty state for inline use
 */
export function CompactEmptyState({
  icon = "📭",
  message,
  actionLabel,
  onAction,
  className = ""
}) {
  return (
    <div className={`flex flex-col items-center justify-center py-8 px-4 ${className}`}>
      <span className="text-3xl mb-3 opacity-50">{icon}</span>
      <p className="text-gray-500 text-sm text-center mb-3">{message}</p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="text-sm text-yellow-500 hover:text-yellow-400 font-medium transition-colors"
        >
          {actionLabel}
        </button>
      )}
    </div>
  )
}

export default EmptyState
