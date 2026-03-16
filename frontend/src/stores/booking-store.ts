import { create } from 'zustand'

export interface FlightOption {
  index: number
  airline: string
  flightNumber: string
  departure: string
  arrival: string
  duration: string
  price: number
  stops: number
  cabin: string
  compliant: boolean
  policyNotes: string[]
}

type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error'
type BookingStatus =
  | 'idle'
  | 'initiated'
  | 'searching'
  | 'options_presented'
  | 'user_selected'
  | 'payment_pending'
  | 'booking'
  | 'confirmed'
  | 'failed'
  | 'cancelled'

interface BookingState {
  connectionStatus: ConnectionStatus
  bookingId: string | null
  bookingStatus: BookingStatus
  progressMessages: string[]
  flightOptions: FlightOption[]
  confirmation: {
    bookingReference: string
    paymentReference: string
    totalAmount: number
    flightNumber: string
  } | null
  paymentFlight: any | null
  paymentPassengers: any[] | null
  error: string | null
  send: (msg: object) => void
  reset: () => void
}

const initialBookingState = {
  bookingId: null,
  bookingStatus: 'idle' as BookingStatus,
  progressMessages: [],
  flightOptions: [],
  confirmation: null,
  paymentFlight: null,
  paymentPassengers: null,
  error: null,
}

export const useBookingStore = create<BookingState>()((set) => ({
  connectionStatus: 'disconnected',
  ...initialBookingState,
  send: () => {},
  reset: () => set(initialBookingState),
}))
