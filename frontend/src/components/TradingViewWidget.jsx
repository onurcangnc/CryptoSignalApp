// src/components/TradingViewWidget.jsx
// TradingView Advanced Chart Widget

import { useEffect, useRef, memo } from 'react'

/**
 * TradingView Widget Component
 * @param {string} symbol - Coin sembolü (örn: "BTC", "ETH")
 * @param {string} interval - Zaman aralığı ("1", "5", "15", "60", "240", "D", "W")
 * @param {string} theme - Tema ("dark" veya "light")
 * @param {number} height - Widget yüksekliği (px)
 */
function TradingViewWidget({
  symbol = 'BTC',
  interval = '60',
  theme = 'dark',
  height = 400,
  autosize = false
}) {
  const container = useRef(null)

  useEffect(() => {
    // TradingView widget script'ini temizle ve yeniden oluştur
    if (container.current) {
      container.current.innerHTML = ''
    }

    // Symbol'ü TradingView formatına çevir
    const tvSymbol = formatSymbol(symbol)

    const script = document.createElement('script')
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js'
    script.type = 'text/javascript'
    script.async = true
    script.innerHTML = JSON.stringify({
      "autosize": autosize,
      "symbol": tvSymbol,
      "interval": interval,
      "timezone": "Europe/Istanbul",
      "theme": theme,
      "style": "1",
      "locale": "tr",
      "enable_publishing": false,
      "backgroundColor": theme === 'dark' ? "rgba(17, 24, 39, 1)" : "rgba(255, 255, 255, 1)",
      "gridColor": theme === 'dark' ? "rgba(55, 65, 81, 0.5)" : "rgba(0, 0, 0, 0.1)",
      "hide_top_toolbar": false,
      "hide_legend": false,
      "save_image": false,
      "calendar": false,
      "hide_volume": false,
      "support_host": "https://www.tradingview.com",
      "container_id": `tradingview_${symbol}`,
      "width": "100%",
      "height": height
    })

    if (container.current) {
      container.current.appendChild(script)
    }

    return () => {
      if (container.current) {
        container.current.innerHTML = ''
      }
    }
  }, [symbol, interval, theme, height, autosize])

  return (
    <div className="tradingview-widget-container rounded-lg overflow-hidden">
      <div
        id={`tradingview_${symbol}`}
        ref={container}
        style={{ height: `${height}px` }}
      />
    </div>
  )
}

/**
 * Symbol'ü TradingView formatına çevir
 * Örn: BTC -> BINANCE:BTCUSDT
 */
function formatSymbol(symbol) {
  // Yaygın coin sembolleri için mapping
  const symbolMap = {
    'BTC': 'BINANCE:BTCUSDT',
    'ETH': 'BINANCE:ETHUSDT',
    'BNB': 'BINANCE:BNBUSDT',
    'SOL': 'BINANCE:SOLUSDT',
    'XRP': 'BINANCE:XRPUSDT',
    'ADA': 'BINANCE:ADAUSDT',
    'DOGE': 'BINANCE:DOGEUSDT',
    'DOT': 'BINANCE:DOTUSDT',
    'AVAX': 'BINANCE:AVAXUSDT',
    'MATIC': 'BINANCE:MATICUSDT',
    'LINK': 'BINANCE:LINKUSDT',
    'UNI': 'BINANCE:UNIUSDT',
    'ATOM': 'BINANCE:ATOMUSDT',
    'LTC': 'BINANCE:LTCUSDT',
    'ETC': 'BINANCE:ETCUSDT',
    'XLM': 'BINANCE:XLMUSDT',
    'TRX': 'BINANCE:TRXUSDT',
    'NEAR': 'BINANCE:NEARUSDT',
    'APT': 'BINANCE:APTUSDT',
    'ARB': 'BINANCE:ARBUSDT',
    'OP': 'BINANCE:OPUSDT',
    'SHIB': 'BINANCE:SHIBUSDT',
    'PEPE': 'BINANCE:PEPEUSDT',
    'FIL': 'BINANCE:FILUSDT',
    'ICP': 'BINANCE:ICPUSDT',
    'RENDER': 'BINANCE:RENDERUSDT',
    'INJ': 'BINANCE:INJUSDT',
    'IMX': 'BINANCE:IMXUSDT',
    'SUI': 'BINANCE:SUIUSDT',
    'SEI': 'BINANCE:SEIUSDT',
    'TIA': 'BINANCE:TIAUSDT',
    'FET': 'BINANCE:FETUSDT',
    'AAVE': 'BINANCE:AAVEUSDT',
    'ALGO': 'BINANCE:ALGOUSDT',
    'VET': 'BINANCE:VETUSDT',
    'SAND': 'BINANCE:SANDUSDT',
    'MANA': 'BINANCE:MANAUSDT',
    'GALA': 'BINANCE:GALAUSDT',
    'AXS': 'BINANCE:AXSUSDT',
    'CRV': 'BINANCE:CRVUSDT',
    'MKR': 'BINANCE:MKRUSDT',
    'LDO': 'BINANCE:LDOUSDT',
    'RUNE': 'BINANCE:RUNEUSDT',
    'GRT': 'BINANCE:GRTUSDT',
    'SNX': 'BINANCE:SNXUSDT',
    'ENS': 'BINANCE:ENSUSDT',
    'QNT': 'BINANCE:QNTUSDT',
    'EGLD': 'BINANCE:EGLDUSDT',
    'FTM': 'BINANCE:FTMUSDT',
    'FLOW': 'BINANCE:FLOWUSDT',
    'THETA': 'BINANCE:THETAUSDT',
    'XTZ': 'BINANCE:XTZUSDT',
    'HBAR': 'BINANCE:HBARUSDT',
    'EOS': 'BINANCE:EOSUSDT',
    'KAVA': 'BINANCE:KAVAUSDT',
    'ZEC': 'BINANCE:ZECUSDT',
    'XMR': 'BINANCE:XMRUSDT',
    'NEO': 'BINANCE:NEOUSDT',
    'DASH': 'BINANCE:DASHUSDT',
    'WAVES': 'BINANCE:WAVESUSDT',
    'ZIL': 'BINANCE:ZILUSDT',
    'ENJ': 'BINANCE:ENJUSDT',
    'BAT': 'BINANCE:BATUSDT',
    'COMP': 'BINANCE:COMPUSDT',
    'YFI': 'BINANCE:YFIUSDT',
    'SUSHI': 'BINANCE:SUSHIUSDT',
    '1INCH': 'BINANCE:1INCHUSDT',
    'CAKE': 'BINANCE:CAKEUSDT',
    'CELO': 'BINANCE:CELOUSDT',
    'CHZ': 'BINANCE:CHZUSDT',
    'HOT': 'BINANCE:HOTUSDT',
    'IOTA': 'BINANCE:IOTAUSDT',
    'KSM': 'BINANCE:KSMUSDT',
    'LUNA': 'BINANCE:LUNAUSDT',
    'LUNC': 'BINANCE:LUNCUSDT',
    'ONE': 'BINANCE:ONEUSDT',
    'ONT': 'BINANCE:ONTUSDT',
    'QTUM': 'BINANCE:QTUMUSDT',
    'RVN': 'BINANCE:RVNUSDT',
    'SC': 'BINANCE:SCUSDT',
    'STORJ': 'BINANCE:STORJUSDT',
    'ZRX': 'BINANCE:ZRXUSDT'
  }

  // Eğer mapping'de varsa kullan, yoksa BINANCE:SYMBOLUSDT formatını dene
  const upperSymbol = symbol?.toUpperCase()
  return symbolMap[upperSymbol] || `BINANCE:${upperSymbol}USDT`
}

/**
 * Mini Chart Widget - Küçük grafik için
 */
export function TradingViewMiniWidget({
  symbol = 'BTC',
  theme = 'dark',
  height = 200
}) {
  const container = useRef(null)

  useEffect(() => {
    if (container.current) {
      container.current.innerHTML = ''
    }

    const tvSymbol = formatSymbol(symbol)

    const script = document.createElement('script')
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js'
    script.type = 'text/javascript'
    script.async = true
    script.innerHTML = JSON.stringify({
      "symbol": tvSymbol,
      "width": "100%",
      "height": height,
      "locale": "tr",
      "dateRange": "1M",
      "colorTheme": theme,
      "isTransparent": true,
      "autosize": false,
      "largeChartUrl": ""
    })

    if (container.current) {
      container.current.appendChild(script)
    }

    return () => {
      if (container.current) {
        container.current.innerHTML = ''
      }
    }
  }, [symbol, theme, height])

  return (
    <div className="tradingview-mini-widget rounded-lg overflow-hidden">
      <div ref={container} style={{ height: `${height}px` }} />
    </div>
  )
}

export default memo(TradingViewWidget)
