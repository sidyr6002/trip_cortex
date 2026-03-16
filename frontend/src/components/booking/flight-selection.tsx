import { useState } from 'react'
import { useUser } from '@clerk/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useBookingStore } from '@/stores/booking-store'
import { useChatStore } from '@/stores/chat-store'

export function FlightSelection() {
  const { flightOptions, bookingId, send } = useBookingStore()
  const { addMessage } = useChatStore()
  const { user } = useUser()
  const [selected, setSelected] = useState<number | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [passenger, setPassenger] = useState({
    first_name: '',
    last_name: '',
    date_of_birth: '',
    email: '',
    phone: '',
  })

  function handleSelect(idx: number) {
    setSelected(idx)
    setShowForm(true)
  }

  function handleConfirm() {
    if (selected === null) return
    const flight = flightOptions[selected]
    send({
      action: 'select_flight',
      booking_id: bookingId,
      employee_id: user?.id ?? '',
      flight: {
        airline: (flight as any).airline,
        flight_number: (flight as any).flight_number ?? (flight as any).flightNumber,
        price: flight.price,
        departure_time: (flight as any).departure_time ?? (flight as any).departure,
        arrival_time: (flight as any).arrival_time ?? (flight as any).arrival,
        stops: flight.stops,
        cabin_class: (flight as any).cabin_class ?? flight.cabin,
        duration: (flight as any).duration,
      },
      passengers: [passenger],
      search_url: `https://flysmart.dportal.workers.dev/search?from=DEL&to=BOM`,
    })
    useBookingStore.setState({ bookingStatus: 'booking' })
    addMessage({
      role: 'system',
      type: 'progress',
      text: `Selected ${(flight as any).airline} ${(flight as any).flight_number ?? (flight as any).flightNumber} — booking in progress...`,
    })
  }

  return (
    <div className="space-y-2 px-1">
      <p className="text-sm font-medium text-muted-foreground">
        {flightOptions.length} flights found — select one:
      </p>
      <div className="space-y-2">
        {flightOptions.map((f: any, i: number) => (
          <button
            key={i}
            onClick={() => handleSelect(i)}
            className={cn(
              'w-full rounded-lg border p-3 text-left text-sm transition-colors',
              selected === i
                ? 'border-primary bg-primary/5'
                : 'border-border hover:border-primary/50',
            )}
          >
            <div className="flex items-center justify-between">
              <div>
                <span className="font-medium">{f.airline}</span>
                <span className="ml-2 text-muted-foreground">
                  {f.flight_number ?? f.flightNumber}
                </span>
              </div>
              <span className="font-semibold text-primary">
                ${f.price}
              </span>
            </div>
            <div className="mt-1 text-xs text-muted-foreground">
              {f.departure_time ?? f.departure} → {f.arrival_time ?? f.arrival}
              {' · '}
              {f.duration}
              {' · '}
              {f.stops === 0 ? 'Direct' : `${f.stops} stop${f.stops > 1 ? 's' : ''}`}
              {' · '}
              {f.cabin_class ?? f.cabin}
            </div>
          </button>
        ))}
      </div>

      {showForm && (
        <div className="space-y-3 rounded-lg border border-border p-3">
          <p className="text-sm font-medium">Passenger Details</p>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <Label className="text-xs">First Name</Label>
              <Input
                value={passenger.first_name}
                onChange={(e) => setPassenger({ ...passenger, first_name: e.target.value })}
                placeholder="John"
                className="h-8 text-sm"
              />
            </div>
            <div>
              <Label className="text-xs">Last Name</Label>
              <Input
                value={passenger.last_name}
                onChange={(e) => setPassenger({ ...passenger, last_name: e.target.value })}
                placeholder="Doe"
                className="h-8 text-sm"
              />
            </div>
            <div>
              <Label className="text-xs">Date of Birth</Label>
              <Input
                value={passenger.date_of_birth}
                onChange={(e) => setPassenger({ ...passenger, date_of_birth: e.target.value })}
                placeholder="DD-MM-YYYY"
                className="h-8 text-sm"
              />
            </div>
            <div>
              <Label className="text-xs">Email</Label>
              <Input
                value={passenger.email}
                onChange={(e) => setPassenger({ ...passenger, email: e.target.value })}
                placeholder="john@example.com"
                className="h-8 text-sm"
              />
            </div>
            <div className="col-span-2">
              <Label className="text-xs">Phone</Label>
              <Input
                value={passenger.phone}
                onChange={(e) => setPassenger({ ...passenger, phone: e.target.value })}
                placeholder="+91 9999999999"
                className="h-8 text-sm"
              />
            </div>
          </div>
          <Button
            onClick={handleConfirm}
            disabled={!passenger.first_name || !passenger.last_name || !passenger.email}
            className="w-full"
            size="sm"
          >
            Confirm & Book
          </Button>
        </div>
      )}
    </div>
  )
}
