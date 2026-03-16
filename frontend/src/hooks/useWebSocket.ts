import { useEffect, useRef } from 'react'
import { useClerk } from '@clerk/react'
import { useBookingStore } from '@/stores/booking-store'

const BACKOFF = [1000, 2000, 4000, 8000, 16000, 30000]
const PING_INTERVAL = 8 * 60 * 1000 // 8 minutes

export function useWebSocket(): void {
  const clerk = useClerk()
  const intentionalClose = useRef(false)
  const retryCount = useRef(0)
  const wsRef = useRef<WebSocket | null>(null)
  const pingTimer = useRef<ReturnType<typeof setInterval>>(undefined)
  const retryTimer = useRef<ReturnType<typeof setTimeout>>(undefined)

  useEffect(() => {
    if (!clerk.loaded) return

    const { setState } = useBookingStore

    function send(msg: object) {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(msg))
      }
    }

    function handleMessage(e: MessageEvent) {
      const data = JSON.parse(e.data)
      const { type, bookingId, payload } = data

      switch (type) {
        case 'booking_initiated':
          setState({ bookingId, bookingStatus: 'initiated', error: null })
          break
        case 'progress':
          setState((s) => ({
            bookingStatus: 'searching',
            progressMessages: [...s.progressMessages, payload.message],
          }))
          break
        case 'flight_options':
          setState({
            flightOptions: payload.options,
            bookingStatus: 'options_presented',
          })
          break
        case 'booking_in_progress':
          setState({ bookingStatus: 'booking' })
          break
        case 'confirmed':
          setState({
            confirmationNumber: payload.confirmationNumber,
            bookingStatus: 'confirmed',
          })
          break
        case 'error':
          setState({
            error: payload.message,
            ...(payload.fatal ? { bookingStatus: 'failed' } : {}),
          })
          break
        case 'pong':
          break
      }
    }

    async function connect() {
      const token = await clerk.session?.getToken()
      if (!token) return

      setState({ connectionStatus: 'connecting' })
      const ws = new WebSocket(`${import.meta.env.VITE_WS_URL}?token=${token}`)
      wsRef.current = ws

      ws.onopen = () => {
        retryCount.current = 0
        setState({ connectionStatus: 'connected', send })
        pingTimer.current = setInterval(
          () => send({ action: 'ping' }),
          PING_INTERVAL,
        )
      }

      ws.onmessage = handleMessage

      ws.onclose = () => {
        cleanup()
        if (intentionalClose.current) {
          setState({ connectionStatus: 'disconnected' })
          return
        }
        if (retryCount.current < BACKOFF.length) {
          setState({ connectionStatus: 'connecting' })
          retryTimer.current = setTimeout(
            connect,
            BACKOFF[retryCount.current++],
          )
        } else {
          setState({ connectionStatus: 'error' })
        }
      }

      ws.onerror = () => ws.close()
    }

    function cleanup() {
      clearInterval(pingTimer.current)
      clearTimeout(retryTimer.current)
    }

    connect()

    return () => {
      intentionalClose.current = true
      cleanup()
      wsRef.current?.close()
    }
  }, [clerk.loaded])
}
