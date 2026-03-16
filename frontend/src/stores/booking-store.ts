import { create } from 'zustand'

interface BookingState {
  connectionStatus: 'disconnected' | 'connecting' | 'connected'
}

export const useBookingStore = create<BookingState>()(() => ({
  connectionStatus: 'disconnected',
}))
