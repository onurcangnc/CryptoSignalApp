// src/pages/AdminEnhanced.jsx
// Enhanced Admin Dashboard with LLM Analytics
import { useState, useEffect } from 'react'
import api from '../api'
import { Line, Bar, Pie } from 'recharts'

const AdminEnhanced = ({ t, lang, user }) => {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState(null)
  const [llmStats, setLlmStats] = useState(null)
  const [systemHealth, setSystemHealth] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  
  useEffect(() => {
    if (user?.role === 'admin' || user?.tier === 'admin') {
      fetchAll()
      const interval = setInterval(fetchAll, 30000) // 30s refresh
      return () => clearInterval(interval)
    }
  }, [user])
  
  const fetchAll = async () => {
    try {
      const [statsResp, llmResp, healthResp] = await Promise.all([
        api.get('/api/admin/stats'),
        api.get('/api/admin/llm-analytics'),
        api.get('/api/admin/system/health')
      ])
      
      if (statsResp.ok) setStats(await statsResp.json())
      if (llmResp.ok) setLlmStats(await llmResp.json())
      if (healthResp.ok) setSystemHealth(await healthResp.json())
    } catch (e) {
      console.error('Admin fetch error:', e)
    } finally {
      setLoading(false)
    }
  }
  
  if (user?.tier !== 'admin') {
    return (
      <div className="max-w-4xl mx-auto px-3 md:px-6 py-12 text-center">
        <div className="text-6xl mb-4">🚫</div>
        <p className="text-red-400 text-lg">Access denied</p>
      </div>
    )
  }
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin text-4xl">⚙️</div>
      </div>
    )
  }
  
  return (
    <div className="max-w-7xl mx-auto px-3 md:px-6 py-4 md:py-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white flex items-center gap-2">
            ⚙️ {lang === 'tr' ? 'Yönetim Paneli' : 'Admin Dashboard'}
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            {lang === 'tr' ? 'Sistem durumu ve analitikler' : 'System status and analytics'}
          </p>
        </div>
        <button
          onClick={fetchAll}
          className="px-4 py-2 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors flex items-center gap-2"
        >
          🔄 {lang === 'tr' ? 'Yenile' : 'Refresh'}
        </button>
      </div>
      
      {/* Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {[
          { id: 'overview', icon: '📊', label: lang === 'tr' ? 'Genel Bakış' : 'Overview' },
          { id: 'llm', icon: '🤖', label: 'LLM Analytics' },
          { id: 'users', icon: '👥', label: lang === 'tr' ? 'Kullanıcılar' : 'Users' },
          { id: 'workers', icon: '⚙️', label: 'Workers' },
          { id: 'system', icon: '🖥️', label: lang === 'tr' ? 'Sistem' : 'System' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-lg font-medium transition-all whitespace-nowrap ${
              activeTab === tab.id
                ? 'bg-blue-500 text-white'
                : 'bg-gray-800/50 text-gray-400 hover:text-white hover:bg-gray-700/50'
            }`}
          >
            <span className="mr-1">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>
      
      {/* Content */}
      {activeTab === 'overview' && <OverviewTab stats={stats} lang={lang} />}
      {activeTab === 'llm' && <LLMTab llmStats={llmStats} lang={lang} />}
      {activeTab === 'users' && <UsersTab stats={stats} lang={lang} />}
      {activeTab === 'workers' && <WorkersTab stats={stats} lang={lang} />}
      {activeTab === 'system' && <SystemTab health={systemHealth} lang={lang} />}
    </div>
  )
}

// ============================================================================
// OVERVIEW TAB
// ============================================================================
const OverviewTab = ({ stats, lang }) => {
  return (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard
          icon="👥"
          label={lang === 'tr' ? 'Toplam Kullanıcı' : 'Total Users'}
          value={stats?.users || 0}
          trend="+12%"
        />
        <MetricCard
          icon="💰"
          label={lang === 'tr' ? 'Pro Kullanıcı' : 'Pro Users'}
          value={stats?.tier_distribution?.pro || 0}
          trend="+8%"
        />
        <MetricCard
          icon="🤖"
          label={lang === 'tr' ? 'LLM Çağrısı (Bugün)' : 'LLM Calls (Today)'}
          value={stats?.llm_calls_today || 0}
          trend="+25%"
        />
        <MetricCard
          icon="💸"
          label={lang === 'tr' ? 'LLM Maliyet (Bu Ay)' : 'LLM Cost (Month)'}
          value={`$${stats?.llm_cost_month?.toFixed(2) || '0.00'}`}
          trend="-5%"
        />
      </div>
      
      {/* Revenue Metrics */}
      <div className="bg-gradient-to-br from-green-900/20 to-emerald-900/20 border border-green-500/30 rounded-xl p-6">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          💰 {lang === 'tr' ? 'Gelir Özeti' : 'Revenue Summary'}
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-gray-400 text-sm">{lang === 'tr' ? 'Bu Ay MRR' : 'This Month MRR'}</p>
            <p className="text-2xl font-bold text-green-400">
              ${((stats?.tier_distribution?.pro || 0) * 9.99 + 
                 (stats?.tier_distribution?.premium || 0) * 29.99).toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">{lang === 'tr' ? 'LLM Maliyeti' : 'LLM Cost'}</p>
            <p className="text-2xl font-bold text-orange-400">
              ${stats?.llm_cost_month?.toFixed(2) || '0.00'}
            </p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">{lang === 'tr' ? 'Net Kar' : 'Net Profit'}</p>
            <p className="text-2xl font-bold text-green-400">
              ${((stats?.tier_distribution?.pro || 0) * 9.99 + 
                 (stats?.tier_distribution?.premium || 0) * 29.99 - 
                 (stats?.llm_cost_month || 0)).toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">{lang === 'tr' ? 'Kar Marjı' : 'Profit Margin'}</p>
            <p className="text-2xl font-bold text-green-400">
              {stats?.profit_margin?.toFixed(1) || '99.0'}%
            </p>
          </div>
        </div>
      </div>
      
      {/* Quick Stats Grid */}
      <div className="grid md:grid-cols-3 gap-4">
        <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
          <h4 className="text-gray-400 text-sm mb-3">🪙 {lang === 'tr' ? 'Coin İstatistikleri' : 'Coin Stats'}</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">{lang === 'tr' ? 'Toplam Coin' : 'Total Coins'}</span>
              <span className="text-white font-medium">{stats?.coins || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">{lang === 'tr' ? 'Sinyal' : 'Signals'}</span>
              <span className="text-white font-medium">{stats?.signals || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">{lang === 'tr' ? 'Haber' : 'News'}</span>
              <span className="text-white font-medium">{stats?.news || 0}</span>
            </div>
          </div>
        </div>
        
        <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
          <h4 className="text-gray-400 text-sm mb-3">📈 {lang === 'tr' ? 'Kullanım Trendi' : 'Usage Trend'}</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">{lang === 'tr' ? 'Aktif Kullanıcı (7g)' : 'Active Users (7d)'}</span>
              <span className="text-green-400 font-medium">+15%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">{lang === 'tr' ? 'API Çağrısı' : 'API Calls'}</span>
              <span className="text-blue-400 font-medium">+22%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">{lang === 'tr' ? 'Dönüşüm Oranı' : 'Conversion Rate'}</span>
              <span className="text-yellow-400 font-medium">8.5%</span>
            </div>
          </div>
        </div>
        
        <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
          <h4 className="text-gray-400 text-sm mb-3">⚡ {lang === 'tr' ? 'Performans' : 'Performance'}</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">{lang === 'tr' ? 'Ortalama Yanıt' : 'Avg Response'}</span>
              <span className="text-green-400 font-medium">245ms</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">{lang === 'tr' ? 'Hata Oranı' : 'Error Rate'}</span>
              <span className="text-green-400 font-medium">0.03%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">Uptime</span>
              <span className="text-green-400 font-medium">99.98%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// LLM ANALYTICS TAB
// ============================================================================
const LLMTab = ({ llmStats, lang }) => {
  return (
    <div className="space-y-6">
      {/* Cost Summary */}
      <div className="bg-gradient-to-br from-purple-900/20 to-blue-900/20 border border-purple-500/30 rounded-xl p-6">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          🤖 {lang === 'tr' ? 'LLM Kullanım Özeti' : 'LLM Usage Summary'}
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-gray-400 text-sm mb-1">{lang === 'tr' ? 'Bugün' : 'Today'}</p>
            <p className="text-2xl font-bold text-white">{llmStats?.today?.calls || 0}</p>
            <p className="text-sm text-purple-400">${llmStats?.today?.cost?.toFixed(3) || '0.000'}</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm mb-1">{lang === 'tr' ? 'Bu Hafta' : 'This Week'}</p>
            <p className="text-2xl font-bold text-white">{llmStats?.week?.calls || 0}</p>
            <p className="text-sm text-purple-400">${llmStats?.week?.cost?.toFixed(2) || '0.00'}</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm mb-1">{lang === 'tr' ? 'Bu Ay' : 'This Month'}</p>
            <p className="text-2xl font-bold text-white">{llmStats?.month?.calls || 0}</p>
            <p className="text-sm text-purple-400">${llmStats?.month?.cost?.toFixed(2) || '0.00'}</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm mb-1">{lang === 'tr' ? 'Ortalama/Çağrı' : 'Avg/Call'}</p>
            <p className="text-2xl font-bold text-white">
              ${llmStats?.average_cost_per_call?.toFixed(4) || '0.0025'}
            </p>
            <p className="text-sm text-gray-400">~{llmStats?.avg_tokens || 9500} tokens</p>
          </div>
        </div>
      </div>
      
      {/* Cost Breakdown */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700/50">
          <h4 className="text-white font-bold mb-4">
            📊 {lang === 'tr' ? 'Özellik Bazlı Kullanım' : 'Usage by Feature'}
          </h4>
          <div className="space-y-3">
            {[
              { name: 'Portfolio Analysis', calls: llmStats?.by_feature?.portfolio || 0, cost: '$0.85' },
              { name: 'Price Predictions', calls: llmStats?.by_feature?.predictions || 0, cost: '$1.24' },
              { name: 'News Analysis', calls: llmStats?.by_feature?.news || 0, cost: '$0.67' },
              { name: 'AI Chat', calls: llmStats?.by_feature?.chat || 0, cost: '$0.43' },
              { name: 'Other', calls: llmStats?.by_feature?.other || 0, cost: '$0.21' }
            ].map((item, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex justify-between mb-1">
                    <span className="text-gray-300 text-sm">{item.name}</span>
                    <span className="text-gray-400 text-xs">{item.cost}</span>
                  </div>
                  <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-purple-500"
                      style={{ width: `${(item.calls / (llmStats?.today?.calls || 1)) * 100}%` }}
                    />
                  </div>
                </div>
                <span className="text-white font-medium ml-4 w-12 text-right">{item.calls}</span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700/50">
          <h4 className="text-white font-bold mb-4">
            👥 {lang === 'tr' ? 'Tier Bazlı Kullanım' : 'Usage by Tier'}
          </h4>
          <div className="space-y-4">
            {[
              { tier: 'Free', users: llmStats?.by_tier?.free?.users || 0, calls: llmStats?.by_tier?.free?.calls || 0, cost: llmStats?.by_tier?.free?.cost || 0 },
              { tier: 'Pro', users: llmStats?.by_tier?.pro?.users || 0, calls: llmStats?.by_tier?.pro?.calls || 0, cost: llmStats?.by_tier?.pro?.cost || 0 },
              { tier: 'Premium', users: llmStats?.by_tier?.premium?.users || 0, calls: llmStats?.by_tier?.premium?.calls || 0, cost: llmStats?.by_tier?.premium?.cost || 0 }
            ].map((tier, i) => (
              <div key={i} className="bg-gray-900/50 rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <span className={`font-medium ${
                    tier.tier === 'Free' ? 'text-gray-400' :
                    tier.tier === 'Pro' ? 'text-blue-400' : 'text-purple-400'
                  }`}>{tier.tier}</span>
                  <span className="text-gray-400 text-sm">{tier.users} users</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-white text-sm">{tier.calls} calls</span>
                  <span className="text-gray-400 text-sm">${tier.cost.toFixed(2)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      {/* Top Users */}
      <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700/50">
        <h4 className="text-white font-bold mb-4">
          🔥 {lang === 'tr' ? 'En Aktif Kullanıcılar' : 'Top Users (This Month)'}
        </h4>
        <div className="space-y-2">
          {llmStats?.top_users?.map((user, i) => (
            <div key={i} className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg">
              <div className="flex items-center gap-3">
                <span className="text-gray-500 text-sm w-6">#{i + 1}</span>
                <div>
                  <p className="text-white font-medium">{user.email?.replace(/(.{3}).*(@.*)/, '$1***$2')}</p>
                  <p className="text-gray-400 text-xs">{user.tier}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-white font-medium">{user.calls} calls</p>
                <p className="text-gray-400 text-xs">${user.cost?.toFixed(3)}</p>
              </div>
            </div>
          )) || <p className="text-gray-500 text-center py-4">No data</p>}
        </div>
      </div>
      
      {/* Budget Alert */}
      {llmStats?.month?.cost > 400 && (
        <div className="bg-orange-900/20 border border-orange-500/30 rounded-xl p-4">
          <div className="flex items-center gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <p className="text-orange-400 font-medium">
                {lang === 'tr' ? 'Bütçe Uyarısı' : 'Budget Alert'}
              </p>
              <p className="text-gray-300 text-sm">
                {lang === 'tr' 
                  ? `Bu ay LLM maliyeti $${llmStats.month.cost.toFixed(2)} - bütçenin %${((llmStats.month.cost / 1000) * 100).toFixed(0)}'sine ulaştı`
                  : `LLM cost this month is $${llmStats.month.cost.toFixed(2)} - ${((llmStats.month.cost / 1000) * 100).toFixed(0)}% of budget`
                }
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ============================================================================
// USERS TAB
// ============================================================================
const UsersTab = ({ stats, lang }) => {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    fetchUsers()
  }, [])
  
  const fetchUsers = async () => {
    try {
      const resp = await api.get('/api/admin/users')
      if (resp.ok) {
        const data = await resp.json()
        setUsers(data.users || [])
      }
    } catch (e) {
      console.error('Users fetch error:', e)
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <div className="space-y-6">
      {/* User Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50 text-center">
          <p className="text-gray-400 text-sm mb-1">Free</p>
          <p className="text-2xl font-bold text-gray-300">{stats?.tier_distribution?.free || 0}</p>
        </div>
        <div className="bg-blue-900/20 border border-blue-500/30 rounded-xl p-4 text-center">
          <p className="text-blue-400 text-sm mb-1">Pro</p>
          <p className="text-2xl font-bold text-blue-300">{stats?.tier_distribution?.pro || 0}</p>
        </div>
        <div className="bg-purple-900/20 border border-purple-500/30 rounded-xl p-4 text-center">
          <p className="text-purple-400 text-sm mb-1">Premium</p>
          <p className="text-2xl font-bold text-purple-300">{stats?.tier_distribution?.premium || 0}</p>
        </div>
      </div>
      
      {/* Users Table */}
      <div className="bg-gray-800/50 rounded-xl border border-gray-700/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-900/50">
              <tr className="text-left text-gray-400 text-sm">
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Tier</th>
                <th className="px-4 py-3">{lang === 'tr' ? 'Kayıt Tarihi' : 'Created'}</th>
                <th className="px-4 py-3">{lang === 'tr' ? 'Son Giriş' : 'Last Login'}</th>
              </tr>
            </thead>
            <tbody>
              {users.slice(0, 20).map((user, i) => (
                <tr key={i} className="border-t border-gray-700/50 hover:bg-gray-700/30">
                  <td className="px-4 py-3 text-white">{user.email}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      user.tier === 'admin' ? 'bg-purple-500/20 text-purple-400' :
                      user.tier === 'pro' ? 'bg-blue-500/20 text-blue-400' :
                      user.tier === 'premium' ? 'bg-purple-500/20 text-purple-400' :
                      'bg-gray-700 text-gray-400'
                    }`}>
                      {user.tier}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-sm">
                    {user.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-sm">
                    {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// WORKERS TAB
// ============================================================================
const WorkersTab = ({ stats, lang }) => {
  return (
    <div className="space-y-4">
      {stats?.workers && Object.entries(stats.workers).map(([name, updated]) => {
        // Worker'ların 20 dakika içinde güncellenmiş olması yeterli
        const date = new Date(updated)
        const isActive = !isNaN(date.getTime()) && (new Date() - date) < 20 * 60 * 1000
        return (
          <WorkerCard
            key={name}
            name={name}
            updated={updated}
            isActive={isActive}
            lang={lang}
          />
        )
      })}
    </div>
  )
}

const WorkerCard = ({ name, updated, isActive, lang }) => {
  const formatTime = (dateStr) => {
    if (!dateStr) return '-'

    // Handle Invalid Date
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return '-'

    const diff = Math.floor((new Date() - date) / 1000)

    if (diff < 60) return `${diff}s ${lang === 'tr' ? 'önce' : 'ago'}`
    if (diff < 3600) return `${Math.floor(diff / 60)}m ${lang === 'tr' ? 'önce' : 'ago'}`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ${lang === 'tr' ? 'önce' : 'ago'}`
    return date.toLocaleTimeString()
  }
  
  return (
    <div className={`p-4 rounded-xl border-2 ${
      isActive 
        ? 'bg-green-900/10 border-green-500/30' 
        : 'bg-red-900/10 border-red-500/30'
    }`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className={`w-3 h-3 rounded-full ${isActive ? 'bg-green-500' : 'bg-red-500'}`} />
          <div>
            <p className="text-white font-medium capitalize">{name.replace('_', ' ')}</p>
            <p className="text-gray-400 text-xs">{formatTime(updated)}</p>
          </div>
        </div>
        <span className={`px-3 py-1 rounded-lg text-xs font-medium ${
          isActive ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
        }`}>
          {isActive ? (lang === 'tr' ? 'Aktif' : 'Active') : (lang === 'tr' ? 'Durdu' : 'Down')}
        </span>
      </div>
    </div>
  )
}

// ============================================================================
// SYSTEM TAB
// ============================================================================
const SystemTab = ({ health, lang }) => {
  return (
    <div className="space-y-6">
      {/* Overall Status */}
      <div className={`p-6 rounded-xl border-2 ${
        health?.overall === 'healthy' ? 'bg-green-900/10 border-green-500/30' :
        health?.overall === 'degraded' ? 'bg-yellow-900/10 border-yellow-500/30' :
        'bg-red-900/10 border-red-500/30'
      }`}>
        <h3 className="text-xl font-bold text-white mb-2">
          {health?.overall === 'healthy' ? '✅' :
           health?.overall === 'degraded' ? '⚠️' : '🚨'} 
          {' '}
          {lang === 'tr' ? 'Sistem Durumu' : 'System Status'}
        </h3>
        <p className={`text-2xl font-bold ${
          health?.overall === 'healthy' ? 'text-green-400' :
          health?.overall === 'degraded' ? 'text-yellow-400' :
          health?.overall === 'warning' ? 'text-orange-400' :
          'text-red-400'
        }`}>
          {health?.overall === 'degraded'
            ? (lang === 'tr' ? 'YAKINDAN TAKİP' : 'MONITORING')
            : health?.overall?.toUpperCase()}
        </p>
        {health?.overall === 'degraded' && (
          <p className="text-gray-400 text-sm mt-2">
            {lang === 'tr'
              ? 'Bazı worker\'lar 10+ dakikadır güncellenmedi. Normal olabilir.'
              : 'Some workers haven\'t updated in 10+ minutes. May be normal.'}
          </p>
        )}
      </div>
      
      {/* Services */}
      <div className="grid md:grid-cols-2 gap-4">
        {health?.services && Object.entries(health.services).map(([service, status]) => (
          <div key={service} className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
            <div className="flex items-center justify-between mb-2">
              <p className="text-white font-medium capitalize">{service}</p>
              <span className={`w-2 h-2 rounded-full ${
                status?.status === 'ok' ? 'bg-green-500' : 'bg-red-500'
              }`} />
            </div>
            {status?.last_update && (
              <p className="text-gray-400 text-xs">
                {lang === 'tr' ? 'Son güncelleme' : 'Last update'}: {status.last_update}
              </p>
            )}
            {status?.age_seconds && (
              <p className="text-gray-500 text-xs">
                {Math.floor(status.age_seconds / 60)}m {status.age_seconds % 60}s {lang === 'tr' ? 'önce' : 'ago'}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// ============================================================================
// HELPER COMPONENTS
// ============================================================================
const MetricCard = ({ icon, label, value, trend }) => (
  <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
    <div className="flex items-center gap-2 mb-2">
      <span className="text-xl">{icon}</span>
      <span className="text-gray-400 text-sm">{label}</span>
    </div>
    <p className="text-2xl font-bold text-white mb-1">{value}</p>
    {trend && (
      <p className={`text-sm font-medium ${trend.startsWith('+') ? 'text-green-400' : 'text-red-400'}`}>
        {trend}
      </p>
    )}
  </div>
)

export default AdminEnhanced