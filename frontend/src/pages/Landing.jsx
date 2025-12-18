// src/pages/Landing.jsx
// Public Landing Page for SEO and AdSense

const Landing = ({ onGetStarted, setLang, lang }) => {
  const t = {
    tr: {
      hero_title: "Kripto Para AI Sinyal Platformu",
      hero_subtitle: "Yapay zeka destekli analizlerle kripto para yatırımlarınızı optimize edin",
      hero_cta: "Hemen Başla",
      hero_cta_secondary: "Daha Fazla Bilgi",

      features_title: "Neden Bizi Seçmelisiniz?",
      feature1_title: "🤖 AI Destekli Sinyaller",
      feature1_desc: "Makine öğrenimi algoritmaları ile %70+ başarı oranı",
      feature2_title: "📊 Gerçek Zamanlı Analiz",
      feature2_desc: "1000+ kripto paranın anlık fiyat ve trend analizi",
      feature3_title: "📱 Telegram Entegrasyonu",
      feature3_desc: "Önemli sinyalleri anında Telegram'dan alın",
      feature4_title: "💼 Portföy Yönetimi",
      feature4_desc: "Yatırımlarınızı tek yerden takip edin",

      stats_title: "Rakamlarla Biz",
      stats_users: "Aktif Kullanıcı",
      stats_signals: "Günlük Sinyal",
      stats_accuracy: "Başarı Oranı",
      stats_coins: "Takip Edilen Coin",

      pricing_title: "Fiyatlandırma",
      pricing_free: "Ücretsiz",
      pricing_free_desc: "Temel özellikler",
      pricing_premium: "Premium",
      pricing_premium_desc: "Tüm özellikler",
      pricing_month: "ay",
      pricing_feature1: "Sınırlı sinyaller",
      pricing_feature2: "Temel analiz",
      pricing_feature3: "Günlük güncelleme",
      pricing_premium_feature1: "Sınırsız sinyaller",
      pricing_premium_feature2: "Gelişmiş AI analizi",
      pricing_premium_feature3: "Gerçek zamanlı bildirimler",
      pricing_premium_feature4: "Portföy yönetimi",
      pricing_premium_feature5: "Öncelikli destek",

      blog_title: "Son Blog Yazıları",
      footer_about: "Hakkımızda",
      footer_about_text: "Kripto para yatırımcılarına AI destekli sinyal ve analiz hizmeti sunan lider platformuz.",
      footer_links: "Hızlı Linkler",
      footer_features: "Özellikler",
      footer_pricing: "Fiyatlandırma",
      footer_blog: "Blog",
      footer_contact: "İletişim",
      footer_legal: "Yasal",
      footer_privacy: "Gizlilik",
      footer_terms: "Şartlar",
      footer_rights: "Tüm hakları saklıdır.",
    },
    en: {
      hero_title: "Crypto AI Signal Platform",
      hero_subtitle: "Optimize your crypto investments with AI-powered analysis",
      hero_cta: "Get Started",
      hero_cta_secondary: "Learn More",

      features_title: "Why Choose Us?",
      feature1_title: "🤖 AI-Powered Signals",
      feature1_desc: "70%+ success rate with machine learning algorithms",
      feature2_title: "📊 Real-Time Analysis",
      feature2_desc: "Live price and trend analysis for 1000+ cryptocurrencies",
      feature3_title: "📱 Telegram Integration",
      feature3_desc: "Get important signals instantly via Telegram",
      feature4_title: "💼 Portfolio Management",
      feature4_desc: "Track your investments from one place",

      stats_title: "By The Numbers",
      stats_users: "Active Users",
      stats_signals: "Daily Signals",
      stats_accuracy: "Success Rate",
      stats_coins: "Tracked Coins",

      pricing_title: "Pricing",
      pricing_free: "Free",
      pricing_free_desc: "Basic features",
      pricing_premium: "Premium",
      pricing_premium_desc: "All features",
      pricing_month: "month",
      pricing_feature1: "Limited signals",
      pricing_feature2: "Basic analysis",
      pricing_feature3: "Daily updates",
      pricing_premium_feature1: "Unlimited signals",
      pricing_premium_feature2: "Advanced AI analysis",
      pricing_premium_feature3: "Real-time notifications",
      pricing_premium_feature4: "Portfolio management",
      pricing_premium_feature5: "Priority support",

      blog_title: "Latest Blog Posts",
      footer_about: "About Us",
      footer_about_text: "We are the leading platform providing AI-powered signal and analysis services to crypto investors.",
      footer_links: "Quick Links",
      footer_features: "Features",
      footer_pricing: "Pricing",
      footer_blog: "Blog",
      footer_contact: "Contact",
      footer_legal: "Legal",
      footer_privacy: "Privacy",
      footer_terms: "Terms",
      footer_rights: "All rights reserved.",
    }
  }

  const text = t[lang]

  const blogPosts = [
    {
      id: 1,
      title: lang === 'tr' ? 'Bitcoin 2025 Fiyat Tahminleri' : 'Bitcoin 2025 Price Predictions',
      excerpt: lang === 'tr'
        ? 'Yapay zeka analizleri ışığında Bitcoin\'in 2025 yılında hangi seviyelere ulaşabileceğini inceliyoruz.'
        : 'Analyzing potential Bitcoin price levels in 2025 using AI-powered analysis.',
      date: '12 Ara 2025',
      image: '🚀',
      url: '/blog-bitcoin-2025.html'
    },
    {
      id: 2,
      title: lang === 'tr' ? 'Altcoin Sezonu Yaklaşıyor mu?' : 'Is Altcoin Season Coming?',
      excerpt: lang === 'tr'
        ? 'Piyasa verileri ve göstergeler ışığında altcoin sezonunun zamanlamasını değerlendiriyoruz.'
        : 'Evaluating altcoin season timing based on market data and indicators.',
      date: '10 Ara 2025',
      image: '📊',
      url: '/blog-altcoin-season.html'
    },
    {
      id: 3,
      title: lang === 'tr' ? 'Risk Yönetimi: Kripto Yatırımlarında Temel Kurallar' : 'Risk Management: Core Rules in Crypto Investing',
      excerpt: lang === 'tr'
        ? 'Portföy değerinizi korumak için uygulamanız gereken risk yönetimi stratejileri.'
        : 'Risk management strategies you need to apply to protect your portfolio value.',
      date: '8 Ara 2025',
      image: '🛡️',
      url: '/blog-risk-management.html'
    },
    {
      id: 4,
      title: lang === 'tr' ? 'Ethereum Staking Rehberi' : 'Ethereum Staking Guide',
      excerpt: lang === 'tr'
        ? 'ETH staking ile pasif gelir kazanmanın yolları, riskleri ve en iyi stratejiler.'
        : 'Ways to earn passive income with ETH staking, risks and best strategies.',
      date: '7 Ara 2025',
      image: '💎',
      url: '/blog-ethereum-merge.html'
    },
    {
      id: 5,
      title: lang === 'tr' ? 'DeFi Başlangıç Rehberi' : 'DeFi Beginners Guide',
      excerpt: lang === 'tr'
        ? 'Lending, yield farming ve likidite sağlama ile DeFi dünyasına giriş yapın.'
        : 'Enter the DeFi world with lending, yield farming and liquidity provision.',
      date: '5 Ara 2025',
      image: '🏦',
      url: '/blog-defi-guide.html'
    },
    {
      id: 6,
      title: lang === 'tr' ? 'Teknik Analiz 101' : 'Technical Analysis 101',
      excerpt: lang === 'tr'
        ? 'Grafik okuma, göstergeler ve trading stratejileri için temel rehber.'
        : 'Essential guide for chart reading, indicators and trading strategies.',
      date: '3 Ara 2025',
      image: '📈',
      url: '/blog-technical-analysis.html'
    }
  ]

  const scrollToSection = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 bg-gray-900/80 backdrop-blur-lg border-b border-gray-700/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <span className="text-3xl">🚀</span>
              <span className="text-xl font-bold text-white">CryptoSignal AI</span>
            </div>

            <div className="hidden md:flex items-center gap-6">
              <button onClick={() => scrollToSection('features')} className="text-gray-300 hover:text-white transition-colors">
                {text.footer_features}
              </button>
              <button onClick={() => scrollToSection('pricing')} className="text-gray-300 hover:text-white transition-colors">
                {text.footer_pricing}
              </button>
              <button onClick={() => scrollToSection('blog')} className="text-gray-300 hover:text-white transition-colors">
                {text.footer_blog}
              </button>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setLang(lang === 'tr' ? 'en' : 'tr')}
                className="px-3 py-1 rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 transition-colors text-sm"
              >
                {lang === 'tr' ? '🇬🇧 EN' : '🇹🇷 TR'}
              </button>
              <button
                onClick={onGetStarted}
                className="px-4 py-2 rounded-lg bg-yellow-500 text-gray-900 font-bold hover:bg-yellow-400 transition-all hover:scale-105"
              >
                {text.hero_cta}
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-6 animate-fade-in">
            {text.hero_title}
          </h1>
          <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto animate-slide-up">
            {text.hero_subtitle}
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-scale-in">
            <button
              onClick={onGetStarted}
              className="px-8 py-4 rounded-lg bg-yellow-500 text-gray-900 font-bold text-lg hover:bg-yellow-400 transition-all hover:scale-105 shadow-lg hover:shadow-yellow-500/50"
            >
              {text.hero_cta}
            </button>
            <button
              onClick={() => scrollToSection('features')}
              className="px-8 py-4 rounded-lg bg-gray-800 text-white font-bold text-lg hover:bg-gray-700 transition-all hover:scale-105"
            >
              {text.hero_cta_secondary}
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-16 max-w-4xl mx-auto">
            {[
              { value: '10K+', label: text.stats_users },
              { value: '500+', label: text.stats_signals },
              { value: '73%', label: text.stats_accuracy },
              { value: '1000+', label: text.stats_coins }
            ].map((stat, idx) => (
              <div key={idx} className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50 hover:border-yellow-500/50 transition-all hover:-translate-y-1">
                <div className="text-3xl font-bold text-yellow-500 mb-2">{stat.value}</div>
                <div className="text-sm text-gray-400">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 bg-gray-900/50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-white text-center mb-12">
            {text.features_title}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { title: text.feature1_title, desc: text.feature1_desc },
              { title: text.feature2_title, desc: text.feature2_desc },
              { title: text.feature3_title, desc: text.feature3_desc },
              { title: text.feature4_title, desc: text.feature4_desc }
            ].map((feature, idx) => (
              <div
                key={idx}
                className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50 hover:border-yellow-500/50 transition-all hover:-translate-y-2 hover:shadow-lg hover:shadow-yellow-500/20"
              >
                <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
                <p className="text-gray-400 text-sm leading-relaxed">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-white text-center mb-12">
            {text.pricing_title}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {/* Free Plan */}
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-8 border border-gray-700/50 hover:border-gray-600/50 transition-all">
              <h3 className="text-2xl font-bold text-white mb-2">{text.pricing_free}</h3>
              <p className="text-gray-400 text-sm mb-6">{text.pricing_free_desc}</p>
              <div className="text-4xl font-bold text-white mb-6">$0<span className="text-lg text-gray-400">/{text.pricing_month}</span></div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center gap-2 text-gray-300">
                  <span className="text-green-500">✓</span> {text.pricing_feature1}
                </li>
                <li className="flex items-center gap-2 text-gray-300">
                  <span className="text-green-500">✓</span> {text.pricing_feature2}
                </li>
                <li className="flex items-center gap-2 text-gray-300">
                  <span className="text-green-500">✓</span> {text.pricing_feature3}
                </li>
              </ul>
              <button
                onClick={onGetStarted}
                className="w-full px-6 py-3 rounded-lg bg-gray-700 text-white font-bold hover:bg-gray-600 transition-all"
              >
                {text.hero_cta}
              </button>
            </div>

            {/* Premium Plan */}
            <div className="bg-gradient-to-br from-yellow-500/20 to-yellow-600/20 backdrop-blur-sm rounded-xl p-8 border border-yellow-500/50 hover:border-yellow-400/70 transition-all hover:-translate-y-2 hover:shadow-lg hover:shadow-yellow-500/30 relative">
              <div className="absolute -top-4 right-4 bg-yellow-500 text-gray-900 px-4 py-1 rounded-full text-sm font-bold">
                {text.pricing_premium_desc}
              </div>
              <h3 className="text-2xl font-bold text-white mb-2">{text.pricing_premium}</h3>
              <p className="text-gray-300 text-sm mb-6">{text.pricing_premium_desc}</p>
              <div className="text-4xl font-bold text-white mb-6">$49<span className="text-lg text-gray-300">/{text.pricing_month}</span></div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center gap-2 text-gray-200">
                  <span className="text-yellow-500">✓</span> {text.pricing_premium_feature1}
                </li>
                <li className="flex items-center gap-2 text-gray-200">
                  <span className="text-yellow-500">✓</span> {text.pricing_premium_feature2}
                </li>
                <li className="flex items-center gap-2 text-gray-200">
                  <span className="text-yellow-500">✓</span> {text.pricing_premium_feature3}
                </li>
                <li className="flex items-center gap-2 text-gray-200">
                  <span className="text-yellow-500">✓</span> {text.pricing_premium_feature4}
                </li>
                <li className="flex items-center gap-2 text-gray-200">
                  <span className="text-yellow-500">✓</span> {text.pricing_premium_feature5}
                </li>
              </ul>
              <button
                onClick={onGetStarted}
                className="w-full px-6 py-3 rounded-lg bg-yellow-500 text-gray-900 font-bold hover:bg-yellow-400 transition-all hover:scale-105"
              >
                {text.hero_cta}
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Blog Section */}
      <section id="blog" className="py-20 px-4 bg-gray-900/50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-white text-center mb-12">
            {text.blog_title}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {blogPosts.map((post) => (
              <div
                key={post.id}
                className="bg-gray-800/50 backdrop-blur-sm rounded-xl overflow-hidden border border-gray-700/50 hover:border-yellow-500/50 transition-all hover:-translate-y-2 hover:shadow-lg hover:shadow-yellow-500/20"
              >
                <div className="h-48 bg-gradient-to-br from-yellow-500/20 to-yellow-600/20 flex items-center justify-center text-6xl">
                  {post.image}
                </div>
                <div className="p-6">
                  <div className="text-sm text-gray-500 mb-2">{post.date}</div>
                  <h3 className="text-xl font-bold text-white mb-3">{post.title}</h3>
                  <p className="text-gray-400 text-sm leading-relaxed mb-4">{post.excerpt}</p>
                  <a
                    href={post.url}
                    className="text-yellow-500 hover:text-yellow-400 font-medium text-sm transition-colors inline-block"
                  >
                    {lang === 'tr' ? 'Devamını Oku →' : 'Read More →'}
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 bg-gray-900 border-t border-gray-800">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <span className="text-3xl">🚀</span>
                <span className="text-xl font-bold text-white">CryptoSignal AI</span>
              </div>
              <p className="text-gray-400 text-sm leading-relaxed">
                {text.footer_about_text}
              </p>
            </div>

            <div>
              <h4 className="text-white font-bold mb-4">{text.footer_links}</h4>
              <ul className="space-y-2">
                <li><button onClick={() => scrollToSection('features')} className="text-gray-400 hover:text-white transition-colors text-sm">{text.footer_features}</button></li>
                <li><button onClick={() => scrollToSection('pricing')} className="text-gray-400 hover:text-white transition-colors text-sm">{text.footer_pricing}</button></li>
                <li><button onClick={() => scrollToSection('blog')} className="text-gray-400 hover:text-white transition-colors text-sm">{text.footer_blog}</button></li>
              </ul>
            </div>

            <div>
              <h4 className="text-white font-bold mb-4">{text.footer_legal}</h4>
              <ul className="space-y-2">
                <li><a href="/privacy-policy.html" className="text-gray-400 hover:text-white transition-colors text-sm">{text.footer_privacy}</a></li>
                <li><a href="/terms.html" className="text-gray-400 hover:text-white transition-colors text-sm">{text.footer_terms}</a></li>
              </ul>
            </div>

            <div>
              <h4 className="text-white font-bold mb-4">{text.footer_contact}</h4>
              <p className="text-gray-400 text-sm">
                contact@cryptosignal.ai<br/>
                support@cryptosignal.ai
              </p>
            </div>
          </div>

          <div className="pt-8 border-t border-gray-800 text-center text-gray-500 text-sm">
            © 2025 CryptoSignal AI. {text.footer_rights}
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Landing