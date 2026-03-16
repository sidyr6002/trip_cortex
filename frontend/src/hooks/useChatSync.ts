import { useEffect, useRef } from 'react'
import { useBookingStore } from '@/stores/booking-store'
import { useChatStore } from '@/stores/chat-store'

export function useChatSync() {
  const addMessage = useChatStore((s) => s.addMessage)
  // Track last seen progressMessages length to only append new ones
  const progressLenRef = useRef(0)

  useEffect(() => {
    return useBookingStore.subscribe((state, prev) => {
      // New progress messages
      if (state.progressMessages.length > progressLenRef.current) {
        state.progressMessages
          .slice(progressLenRef.current)
          .forEach((text) =>
            addMessage({ role: 'system', type: 'progress', text }),
          )
        progressLenRef.current = state.progressMessages.length
      }

      // Reset progress counter when store resets
      if (
        state.progressMessages.length === 0 &&
        prev.progressMessages.length > 0
      ) {
        progressLenRef.current = 0
      }

      if (state.bookingStatus === prev.bookingStatus) return

      switch (state.bookingStatus) {
        case 'initiated':
          addMessage({
            role: 'system',
            type: 'status',
            text: 'Booking initiated. Processing your request...',
          })
          break
        case 'options_presented':
          addMessage({ role: 'system', type: 'flight_options' })
          break
        case 'payment_pending':
          addMessage({ role: 'system', type: 'payment_confirmation' })
          break
        case 'booking':
          addMessage({
            role: 'system',
            type: 'status',
            text: 'Completing your booking...',
          })
          break
        case 'confirmed':
          addMessage({
            role: 'system',
            type: 'confirmed',
            text: 'Booking confirmed!',
            confirmation: state.confirmation ?? undefined,
          })
          break
        case 'failed':
        case 'cancelled':
          addMessage({
            role: 'system',
            type: 'error',
            text: state.error ?? 'Booking could not be completed.',
          })
          break
      }
    })
  }, [addMessage])
}
