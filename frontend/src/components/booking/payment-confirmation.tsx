import { useUser } from '@clerk/react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { useBookingStore } from '@/stores/booking-store'
import { useChatStore } from '@/stores/chat-store'
import { CreditCard, Plane } from 'lucide-react'

export function PaymentConfirmation() {
  const { paymentFlight: f, paymentPassengers: passengers, bookingId, send } = useBookingStore()
  const { addMessage } = useChatStore()
  const { user } = useUser()

  if (!f) return null

  const name = passengers?.[0]
    ? `${passengers[0].first_name} ${passengers[0].last_name}`
    : 'Passenger'

  function handleConfirm(approved: boolean) {
    send({
      action: 'confirm_payment',
      booking_id: bookingId,
      employee_id: user?.id ?? '',
      approved,
    })
    if (approved) {
      useBookingStore.setState({ bookingStatus: 'booking' })
      addMessage({ role: 'system', type: 'progress', text: 'Payment approved — completing booking...' })
    } else {
      useBookingStore.setState({ bookingStatus: 'cancelled', error: 'Payment cancelled by user' })
    }
  }

  return (
    <Card className="w-full max-w-md border-amber-200 bg-gradient-to-br from-amber-50 to-orange-50 dark:border-amber-800 dark:from-amber-950/40 dark:to-orange-950/40">
      <CardContent className="pt-6">
        <div className="mb-4 flex items-center gap-2">
          <CreditCard className="h-5 w-5 text-amber-600 dark:text-amber-400" />
          <h3 className="text-base font-semibold text-amber-800 dark:text-amber-200">
            Confirm Payment
          </h3>
        </div>

        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-2 text-muted-foreground">
              <Plane className="h-4 w-4" /> Flight
            </span>
            <span>{f.airline} {f.flight_number}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Route</span>
            <span>{f.departure_time} → {f.arrival_time}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Passenger</span>
            <span>{name}</span>
          </div>
          <div className="flex items-center justify-between border-t pt-2 mt-2">
            <span className="font-medium">Total</span>
            <span className="text-lg font-bold text-amber-700 dark:text-amber-300">
              ${f.price}
            </span>
          </div>
        </div>

        <div className="mt-4 flex gap-2">
          <Button onClick={() => handleConfirm(true)} className="flex-1" size="sm">
            Approve & Pay
          </Button>
          <Button onClick={() => handleConfirm(false)} variant="outline" size="sm" className="flex-1">
            Cancel
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
