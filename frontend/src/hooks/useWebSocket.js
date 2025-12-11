import { useEffect, useRef, useState } from 'react'

const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws'

export const useWebSocket = (onMessage) => {
  const ws = useRef(null)
  const [isConnected, setIsConnected] = useState(false)
  const reconnectTimeout = useRef(null)
  const reconnectAttempts = useRef(0)

  const connect = () => {
    try {
      ws.current = new WebSocket(WS_URL)

      ws.current.onopen = () => {
        console.log('[WS] Connected')
        setIsConnected(true)
        reconnectAttempts.current = 0
      }

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (onMessage) {
            onMessage(data)
          }
        } catch (e) {
          console.error('[WS] Parse error:', e)
        }
      }

      ws.current.onerror = (error) => {
        console.error('[WS] Error:', error)
      }

      ws.current.onclose = () => {
        console.log('[WS] Disconnected')
        setIsConnected(false)

        // Reconnect with exponential backoff
        if (reconnectAttempts.current < 10) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000)
          console.log(`[WS] Reconnecting in ${delay}ms...`)

          reconnectTimeout.current = setTimeout(() => {
            reconnectAttempts.current += 1
            connect()
          }, delay)
        }
      }
    } catch (error) {
      console.error('[WS] Connection error:', error)
    }
  }

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current)
      }
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [])

  const send = (data) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(data))
    }
  }

  return { isConnected, send }
}