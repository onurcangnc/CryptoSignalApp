import { useState, useEffect } from 'react'

/**
 * Toast Notification Component
 *
 * Usage:
 * import { showToast } from './components/Toast'
 *
 * In your component:
 * showToast('Success!', 'success')
 * showToast('Error occurred', 'error')
 * showToast('Warning!', 'warning')
 * showToast('Info message', 'info')
 */

// Toast store
let toastListeners = []
let toastId = 0

export const showToast = (message, type = 'info', duration = 3000) => {
  const id = toastId++
  const toast = { id, message, type, duration }

  toastListeners.forEach(listener => listener(toast))

  return id
}

export const Toast = () => {
  const [toasts, setToasts] = useState([])

  useEffect(() => {
    const listener = (toast) => {
      setToasts(prev => [...prev, toast])

      // Auto remove after duration
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== toast.id))
      }, toast.duration)
    }

    toastListeners.push(listener)

    return () => {
      toastListeners = toastListeners.filter(l => l !== listener)
    }
  }, [])

  const removeToast = (id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map(toast => (
        <ToastItem
          key={toast.id}
          toast={toast}
          onClose={() => removeToast(toast.id)}
        />
      ))}
    </div>
  )
}

const ToastItem = ({ toast, onClose }) => {
  const typeStyles = {
    success: {
      bg: 'bg-green-500/90',
      border: 'border-green-400',
      shadow: 'shadow-green-500/50',
      icon: '✓'
    },
    error: {
      bg: 'bg-red-500/90',
      border: 'border-red-400',
      shadow: 'shadow-red-500/50',
      icon: '✕'
    },
    warning: {
      bg: 'bg-yellow-500/90',
      border: 'border-yellow-400',
      shadow: 'shadow-yellow-500/50',
      icon: '⚠'
    },
    info: {
      bg: 'bg-blue-500/90',
      border: 'border-blue-400',
      shadow: 'shadow-blue-500/50',
      icon: 'ℹ'
    }
  }

  const style = typeStyles[toast.type] || typeStyles.info

  return (
    <div
      className={`${style.bg} ${style.border} backdrop-blur-md border rounded-lg p-4 shadow-lg ${style.shadow} min-w-[300px] max-w-md pointer-events-auto animate-slide-down`}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-full bg-white/20 text-white font-bold text-sm">
          {style.icon}
        </div>
        <div className="flex-1">
          <p className="text-white font-medium text-sm leading-relaxed">
            {toast.message}
          </p>
        </div>
        <button
          onClick={onClose}
          className="flex-shrink-0 text-white/80 hover:text-white transition-colors"
        >
          ✕
        </button>
      </div>

      {/* Progress bar */}
      <div className="mt-2 h-1 bg-white/20 rounded-full overflow-hidden">
        <div
          className="h-full bg-white/40 animate-progress"
          style={{
            animation: `progress ${toast.duration}ms linear forwards`
          }}
        />
      </div>
    </div>
  )
}

export default Toast
