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
      console.log('[WS] send() called', msg)
      console.log('[WS] readyState:', wsRef.current?.readyState, '(1=OPEN)')
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(msg))
        console.log('[WS] message sent')
      } else {
        console.warn('[WS] socket not open, message dropped')
      }
    }

    function handleMessage(e: MessageEvent) {
      console.log('[WS] received:', e.data)
      const data = JSON.parse(e.data)

      // API Gateway error (no type field) — ignore for pings, show for active bookings
      if (!data.type && data.message) {
        console.warn('[WS] API Gateway error:', data.message)
        return
      }

      const { type, booking_id, payload } = data
      const bookingId = booking_id

      switch (type) {
        case 'booking_initiated':
          setState({ bookingId, bookingStatus: 'initiated', error: null })
          break
        case 'progress':
          setState((s) => ({
            bookingId: bookingId ?? s.bookingId,
            bookingStatus: 'searching',
            progressMessages: [...s.progressMessages, payload.message],
          }))
          break
        case 'flight_options':
          setState({
            bookingId,
            flightOptions: data.flights,
            bookingStatus: 'options_presented',
          })
          break
        case 'booking_in_progress':
          setState({ bookingStatus: 'booking' })
          break
        case 'booking_complete':
        case 'confirmed':
          setState({
            confirmation: payload?.confirmation
              ? {
                  bookingReference: payload.confirmation.booking_reference,
                  paymentReference: payload.confirmation.payment_reference,
                  totalAmount: payload.confirmation.total_amount,
                  flightNumber: payload.confirmation.flight_number,
                }
              : null,
            bookingStatus: 'confirmed',
          })
          break
        case 'fallback':
          setState({
            error: payload?.message ?? 'Booking could not be completed. A fallback URL has been provided.',
            bookingStatus: 'failed',
          })
          break
        case 'error':
          setState({
            error: payload?.message ?? 'An unexpected error occurred.',
            ...(payload?.fatal !== false ? { bookingStatus: 'failed' } : {}),
          })
          break
        case 'pong':
          break
        default:
          console.warn('[WS] unhandled message type:', type, data)
      }
    }

    async function connect() {
      const token = await clerk.session?.getToken()
      console.log('[WS] token:', token ? `${token.slice(0, 20)}...` : 'NULL')
      if (!token) return

      const url = `${import.meta.env.VITE_WS_URL}?token=${token}`
      console.log('[WS] connecting to:', import.meta.env.VITE_WS_URL)
      setState({ connectionStatus: 'connecting' })
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('[WS] connected')
        retryCount.current = 0
        setState({ connectionStatus: 'connected', send })
        pingTimer.current = setInterval(
          () => send({ action: 'ping' }),
          PING_INTERVAL,
        )
      }

      ws.onmessage = handleMessage

      ws.onclose = (ev) => {
        console.log('[WS] closed, code:', ev.code, 'reason:', ev.reason)
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

      ws.onerror = (ev) => {
        console.error('[WS] error', ev)
        ws.close()
      }
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
