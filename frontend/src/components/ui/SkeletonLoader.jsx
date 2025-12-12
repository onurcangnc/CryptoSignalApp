// src/components/ui/SkeletonLoader.jsx
// Modern Skeleton Loading Components

/**
 * Base Skeleton Component
 */
export function Skeleton({ className = "", animate = true }) {
  return (
    <div
      className={`bg-gray-700/50 rounded ${animate ? 'animate-pulse' : ''} ${className}`}
    />
  )
}

/**
 * Text Line Skeleton
 */
export function SkeletonText({ lines = 1, className = "" }) {
  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className={`h-4 ${i === lines - 1 ? 'w-3/4' : 'w-full'}`}
        />
      ))}
    </div>
  )
}

/**
 * Card Skeleton
 */
export function SkeletonCard({ className = "" }) {
  return (
    <div className={`bg-gray-800/50 rounded-2xl p-6 border border-gray-700/30 ${className}`}>
      <div className="flex items-center gap-4 mb-4">
        <Skeleton className="w-12 h-12 rounded-full" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-1/3" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      </div>
      <SkeletonText lines={3} />
    </div>
  )
}

/**
 * Table Row Skeleton
 */
export function SkeletonTableRow({ columns = 5, className = "" }) {
  return (
    <tr className={`border-t border-gray-700/30 ${className}`}>
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="px-4 py-4">
          <Skeleton className={`h-4 ${i === 0 ? 'w-8' : i === 1 ? 'w-20' : 'w-16'}`} />
        </td>
      ))}
    </tr>
  )
}

/**
 * Table Skeleton
 */
export function SkeletonTable({ rows = 5, columns = 5, className = "" }) {
  return (
    <div className={`bg-gray-800/50 rounded-2xl border border-gray-700/30 overflow-hidden ${className}`}>
      <table className="w-full">
        <thead className="bg-gray-900/50">
          <tr>
            {Array.from({ length: columns }).map((_, i) => (
              <th key={i} className="px-4 py-3 text-left">
                <Skeleton className="h-4 w-16" />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: rows }).map((_, i) => (
            <SkeletonTableRow key={i} columns={columns} />
          ))}
        </tbody>
      </table>
    </div>
  )
}

/**
 * Stat Card Skeleton
 */
export function SkeletonStatCard({ className = "" }) {
  return (
    <div className={`bg-gray-800/50 rounded-2xl p-5 border border-gray-700/30 ${className}`}>
      <div className="flex items-center gap-3 mb-3">
        <Skeleton className="w-10 h-10 rounded-xl" />
        <Skeleton className="h-4 w-24" />
      </div>
      <Skeleton className="h-8 w-20 mb-2" />
      <Skeleton className="h-3 w-16" />
    </div>
  )
}

/**
 * Signal Card Skeleton
 */
export function SkeletonSignalCard({ className = "" }) {
  return (
    <div className={`bg-gray-800/50 rounded-2xl p-5 border border-gray-700/30 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Skeleton className="w-10 h-10 rounded-full" />
          <div className="space-y-2">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-3 w-24" />
          </div>
        </div>
        <Skeleton className="h-8 w-20 rounded-full" />
      </div>
      <div className="space-y-3">
        <div className="flex justify-between">
          <Skeleton className="h-3 w-12" />
          <Skeleton className="h-3 w-8" />
        </div>
        <Skeleton className="h-2 w-full rounded-full" />
      </div>
      <SkeletonText lines={2} className="mt-4" />
    </div>
  )
}

/**
 * Chart Skeleton
 */
export function SkeletonChart({ height = 200, className = "" }) {
  return (
    <div className={`bg-gray-800/50 rounded-2xl p-5 border border-gray-700/30 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <Skeleton className="h-5 w-32" />
        <div className="flex gap-2">
          <Skeleton className="h-8 w-16 rounded-lg" />
          <Skeleton className="h-8 w-16 rounded-lg" />
        </div>
      </div>
      <Skeleton className={`w-full rounded-lg`} style={{ height: `${height}px` }} />
    </div>
  )
}

/**
 * Dashboard Loading Skeleton
 */
export function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <SkeletonStatCard />
        <SkeletonStatCard />
        <SkeletonStatCard />
      </div>

      {/* Second Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <SkeletonCard />
        <SkeletonCard />
      </div>

      {/* Table */}
      <SkeletonTable rows={10} columns={7} />
    </div>
  )
}

/**
 * Signals Page Loading Skeleton
 */
export function SignalsSkeleton() {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="space-y-2">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
        <Skeleton className="h-8 w-8 rounded-full" />
      </div>

      {/* Timeframe Tabs */}
      <div className="flex gap-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-20 rounded-lg" />
        ))}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonStatCard key={i} />
        ))}
      </div>

      {/* Search */}
      <Skeleton className="h-12 w-full rounded-xl" />

      {/* Signals Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 9 }).map((_, i) => (
          <SkeletonSignalCard key={i} />
        ))}
      </div>
    </div>
  )
}

export default Skeleton
