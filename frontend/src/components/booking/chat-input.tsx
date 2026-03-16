import { useState } from 'react'
import { useUser } from '@clerk/react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { useBookingStore } from '@/stores/booking-store'
import { useChatStore } from '@/stores/chat-store'

const IN_FLIGHT: string[] = [
  'initiated',
  'searching',
  'options_presented',
  'user_selected',
  'booking',
]

const TERMINAL: string[] = ['confirmed', 'failed', 'cancelled']

export function ChatInput() {
  const [text, setText] = useState('')
  const { user } = useUser()
  const { bookingStatus, connectionStatus, send } = useBookingStore()
  const { addMessage, clear } = useChatStore()
  const reset = useBookingStore((s) => s.reset)

  const isInFlight = IN_FLIGHT.includes(bookingStatus)
  const isTerminal = TERMINAL.includes(bookingStatus)
  const disabled = connectionStatus !== 'connected' || isInFlight

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const msg = text.trim()
    console.log('[ChatInput] submit', { msg, disabled, hasUser: !!user, connectionStatus, bookingStatus })
    if (!msg || disabled || !user) return
    const bookingId = crypto.randomUUID()
    addMessage({ role: 'user', type: 'request', text: msg })
    const payload = {
      action: 'booking_request',
      employee_id: user.id,
      booking_id: bookingId,
      user_query: msg,
    }
    console.log('[ChatInput] sending payload:', payload)
    send(payload)
    setText('')
  }

  function handleNewBooking() {
    reset()
    clear()
  }

  if (isTerminal) {
    return (
      <div className="px-4 py-3">
        <Button onClick={handleNewBooking} className="w-full">
          New Booking
        </Button>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 px-4 py-3">
      <Input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={
          connectionStatus !== 'connected'
            ? 'Connecting...'
            : 'Type your booking request...'
        }
        disabled={disabled}
        className="flex-1"
      />
      <Button type="submit" disabled={disabled || !text.trim()}>
        Send
      </Button>
    </form>
  )
}
