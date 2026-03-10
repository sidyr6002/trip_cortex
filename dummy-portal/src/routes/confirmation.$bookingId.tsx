import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { useEffect, useState } from 'react';
import Navbar from '../components/home/Navbar';
import { CheckCircle, Download, Printer } from 'lucide-react';
import type { FlightListing, PassengerData } from '../data/schema';
import { formatDuration } from '../data/mockData';
import { TAX_RATE } from '../data/helpers';
import { generateTicketPdf } from '../utils/generateTicketPdf';

interface ConfirmationState {
  flight: FlightListing;
  returnFlight?: FlightListing | null;
  passengers: PassengerData[];
  adults: number;
  children: number;
  total: number;
  paymentIntentId?: string;
}

export const Route = createFileRoute('/confirmation/$bookingId')({
  component: ConfirmationRoute,
});

function FlightDetailBlock({ flight }: { flight: FlightListing }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 pb-4 border-b border-divider-light">
        <div className="w-12 h-12 rounded-full bg-surface-muted flex items-center justify-center">
          <div className="text-xs font-bold text-primary">
            {flight.segments[0].airline.name.split(' ').map(w => w[0]).join('')}
          </div>
        </div>
        <div>
          <h3 className="font-semibold text-content">{flight.segments[0].airline.name}</h3>
          <p className="text-sm text-content-muted">
            {flight.segments.map(s => s.flightNumber).join(' → ')} · {flight.flightClass.name}
          </p>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <div className="text-content-muted mb-1">Departure</div>
          <div className="font-semibold text-content">{flight.departureAirport.name} ({flight.departureAirport.code})</div>
          <div className="text-content-muted">
            {new Date(flight.segments[0].departureTime).toLocaleString('en-US', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
        <div>
          <div className="text-content-muted mb-1">Arrival</div>
          <div className="font-semibold text-content">{flight.arrivalAirport.name} ({flight.arrivalAirport.code})</div>
          <div className="text-content-muted">
            {new Date(flight.segments[flight.segments.length - 1].arrivalTime).toLocaleString('en-US', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
        <div>
          <div className="text-content-muted mb-1">Duration</div>
          <div className="font-semibold text-content">{formatDuration(flight.totalDurationMinutes)}</div>
        </div>
        <div>
          <div className="text-content-muted mb-1">Transit</div>
          <div className="font-semibold text-content">{flight.transitType}</div>
        </div>
      </div>
    </div>
  );
}

function ConfirmationRoute() {
  const { bookingId } = Route.useParams();
  const navigate = useNavigate();

  // Try to get state from navigation or localStorage
  const [bookingState, setBookingState] = useState<ConfirmationState | null>(null);

  useEffect(() => {
    // First try navigation state
    const navState = window.history.state?.usr as ConfirmationState | undefined;

    if (navState) {
      setBookingState(navState);
    } else {
      // Fallback to localStorage
      const stored = localStorage.getItem(`booking-${bookingId}`);
      if (stored) {
        try {
          setBookingState(JSON.parse(stored));
        } catch (error) {
          console.error('Failed to parse booking data:', error);
        }
      }
    }
  }, [bookingId]);

  if (!bookingState) {
    return (
      <div className="min-h-screen bg-linear-to-b from-primary-100 via-primary-50 to-white">
        <Navbar />
        <div className="container mx-auto px-4 py-12 text-center">
          <h1 className="text-2xl font-bold text-content mb-4">Booking Not Found</h1>
          <p className="text-content-muted mb-6">We couldn't find this booking.</p>
          <button
            onClick={() => navigate({ to: '/search' })}
            className="bg-primary text-white px-6 py-3 rounded-xl font-semibold hover:bg-primary/90"
          >
            Back to Search
          </button>
        </div>
      </div>
    );
  }

  const { flight, returnFlight, passengers, adults, children, total } = bookingState;
  const totalPassengers = adults + children;
  const outboundSubtotal = flight.pricing.pricePerPassenger * totalPassengers;
  const returnSubtotal = returnFlight ? returnFlight.pricing.pricePerPassenger * totalPassengers : 0;
  const subtotal = outboundSubtotal + returnSubtotal;
  const taxes = subtotal * TAX_RATE;

  const handleDownload = () => {
    generateTicketPdf({
      bookingId,
      flight,
      passengers,
      adults,
      children,
      total,
      paymentIntentId: bookingState.paymentIntentId,
    });
  };

  return (
    <div className="min-h-screen bg-primary-100">
      <Navbar />

      <div className="container mx-auto px-4 py-12 max-w-4xl">
        {/* Success Header */}
        <div className="text-center mb-8">
          <CheckCircle className="w-20 h-20 text-green-500 mx-auto mb-4" />
          <h1 className="text-3xl font-bold text-content mb-2">Booking Confirmed!</h1>
          <p className="text-content-muted">Your flight has been successfully booked</p>
        </div>

        {/* Booking Reference */}
        <div className="bg-primary/10 border-2 border-primary rounded-xl p-6 mb-6 text-center">
          <div className="text-sm font-medium text-content-muted mb-1">Booking Reference</div>
          <div
            className="text-3xl font-bold text-primary font-mono tracking-wider"
            data-testid="booking-reference"
          >
            {bookingId}
          </div>
          {bookingState.paymentIntentId && (
            <div className="mt-3 pt-3 border-t border-primary/20">
              <div className="text-sm font-medium text-content-muted mb-1">Payment Reference</div>
              <div className="text-sm font-mono text-content-muted" data-testid="payment-reference">
                {bookingState.paymentIntentId}
              </div>
            </div>
          )}
        </div>

        {/* Flight Summary */}
        <div className="bg-white rounded-xl border border-divider-light p-6 mb-6">
          <h2 className="text-xl font-bold text-content mb-4">Flight Details</h2>

          {returnFlight && (
            <div className="text-xs font-semibold text-primary uppercase tracking-wider mb-3">Outbound</div>
          )}
          <FlightDetailBlock flight={flight} />

          {returnFlight && (
            <>
              <div className="my-4 border-t border-divider-light" />
              <div className="text-xs font-semibold text-primary uppercase tracking-wider mb-3">Return</div>
              <FlightDetailBlock flight={returnFlight} />
            </>
          )}
        </div>

        {/* Passenger Details */}
        <div className="bg-white rounded-xl border border-divider-light p-6 mb-6">
          <h2 className="text-xl font-bold text-content mb-4">Passenger Details</h2>
          <div className="space-y-3">
            {passengers.map((passenger, idx) => (
              <div
                key={idx}
                className="flex justify-between items-center py-2 border-b border-divider-light last:border-0"
                data-testid={`passenger-${idx}`}
              >
                <div>
                  <div className="font-semibold text-content">
                    {passenger.firstName} {passenger.lastName}
                  </div>
                  <div className="text-sm text-content-muted">
                    DOB: {passenger.dateOfBirth}
                    {idx === 0 && ` · ${passenger.email} · ${passenger.phone}`}
                  </div>
                </div>
                <div className="text-sm text-content-muted">
                  {idx < adults ? 'Adult' : 'Child'}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Price Breakdown */}
        <div className="bg-white rounded-xl border border-divider-light p-6 mb-6">
          <h2 className="text-xl font-bold text-content mb-4">Price Breakdown</h2>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-content-muted">
                {returnFlight ? 'Outbound' : 'Base Fare'} ({totalPassengers} × ${flight.pricing.pricePerPassenger})
              </span>
              <span className="text-content">${outboundSubtotal.toFixed(2)}</span>
            </div>
            {returnFlight && (
              <div className="flex justify-between text-sm">
                <span className="text-content-muted">
                  Return ({totalPassengers} × ${returnFlight.pricing.pricePerPassenger})
                </span>
                <span className="text-content">${returnSubtotal.toFixed(2)}</span>
              </div>
            )}
            <div className="flex justify-between text-sm">
              <span className="text-content-muted">Taxes & Fees</span>
              <span className="text-content">${taxes.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-lg font-bold pt-3 border-t border-divider-light">
              <span className="text-content">Total Paid{returnFlight ? ' (Round Trip)' : ''}</span>
              <span className="text-primary" data-testid="total-amount">${total.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-4">
          <button
            onClick={handleDownload}
            className="flex-1 bg-primary text-white py-4 rounded-xl font-semibold hover:bg-primary-hover transition-colors flex items-center justify-center gap-2"
            data-testid="download-itinerary"
          >
            <Download className="w-5 h-5" />
            Download PDF Ticket
          </button>
          <button
            onClick={() => window.print()}
            className="flex-1 bg-surface-muted text-content py-4 rounded-xl font-semibold hover:bg-divider-light transition-colors flex items-center justify-center gap-2"
            data-testid="print-itinerary"
          >
            <Printer className="w-5 h-5" />
            Print
          </button>
        </div>

        <div className="text-center mt-8">
          <button
            onClick={() => navigate({ to: '/search' })}
            className="text-primary hover:underline font-medium"
          >
            Book Another Flight
          </button>
        </div>
      </div>
    </div>
  );
}
