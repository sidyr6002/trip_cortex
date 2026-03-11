import { createFileRoute, Link } from '@tanstack/react-router';
import { useEffect, useState } from 'react';
import { SignedIn } from '@clerk/tanstack-react-start';
import Navbar from '../components/home/Navbar';
import { Download, Calendar, Users, DollarSign, Plane, ArrowLeft, ArrowRightLeft } from 'lucide-react';
import type { FlightListing, PassengerData } from '../data/schema';

interface StoredBooking {
  bookingId: string;
  flight: FlightListing;
  returnFlight?: FlightListing | null;
  passengers: PassengerData[];
  adults: number;
  children: number;
  total: number;
  paymentIntentId?: string;
}

export const Route = createFileRoute('/bookings')({
  component: BookingsRoute,
});

function BookingsRoute() {
  const [bookings, setBookings] = useState<StoredBooking[]>([]);

  useEffect(() => {
    const stored: StoredBooking[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key?.startsWith('booking-')) {
        const bookingId = key.replace('booking-', '');
        const data = localStorage.getItem(key);
        if (data) {
          try {
            stored.push({
              bookingId,
              ...JSON.parse(data),
            });
          } catch (e) {
            console.error(`Failed to parse booking ${bookingId}:`, e);
          }
        }
      }
    }
    // Sort by most recent first (reverse order of insertion)
    setBookings(stored.reverse());
  }, []);

  const handleDownload = async (booking: StoredBooking) => {
    const { generateTicketPdf } = await import('../utils/generateTicketPdf');
    await generateTicketPdf({
      bookingId: booking.bookingId,
      flight: booking.flight,
      returnFlight: booking.returnFlight,
      passengers: booking.passengers,
      adults: booking.adults,
      children: booking.children,
      total: booking.total,
      paymentIntentId: booking.paymentIntentId,
    });
  };

  return (
    <SignedIn>
      <div className="min-h-screen bg-primary-100">
        <Navbar simplified />

        <div className="container mx-auto px-4 py-12 max-w-6xl">
          <Link to="/search" className="inline-flex items-center gap-2 text-primary hover:text-primary/80 font-medium mb-4">
            <ArrowLeft className="w-4 h-4" />
            Go to Search
          </Link>
          <h1 className="text-3xl font-bold text-content mb-2">My Bookings</h1>
          <p className="text-content-muted mb-8">View and manage your flight bookings</p>

          {bookings.length === 0 ? (
            <div className="bg-white rounded-xl border border-divider-light p-12 text-center">
              <Plane className="w-16 h-16 text-content-muted mx-auto mb-4 opacity-50" />
              <h2 className="text-xl font-semibold text-content mb-2">No bookings yet</h2>
              <p className="text-content-muted mb-6">Start your journey by booking a flight</p>
              <a
                href="/search"
                className="inline-block bg-primary text-white px-6 py-3 rounded-xl font-semibold hover:bg-primary/90"
              >
                Search Flights
              </a>
            </div>
          ) : (
            <div className="grid gap-4">
              {bookings.map((booking) => {
                const departureTime = new Date(booking.flight.segments[0].departureTime);
                const isRoundTrip = !!booking.returnFlight;
                const returnDepartureTime = isRoundTrip
                  ? new Date(booking.returnFlight!.segments[0].departureTime)
                  : null;
                const totalPassengers = booking.adults + booking.children;

                return (
                  <a
                    key={booking.bookingId}
                    href={`/confirmation/${booking.bookingId}`}
                    className="bg-white rounded-xl border border-divider-light p-6 hover:shadow-lg transition-shadow cursor-pointer"
                  >
                    {/* Trip type badge */}
                    {isRoundTrip && (
                      <div className="flex items-center gap-1.5 mb-3">
                        <ArrowRightLeft className="w-3.5 h-3.5 text-accent" />
                        <span className="text-xs font-semibold text-accent">Round Trip</span>
                      </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-start">
                      {/* Route */}
                      <div className="md:col-span-2 space-y-3">
                        {/* Outbound */}
                        <div>
                          <div className="text-xs text-content-muted mb-1">
                            {isRoundTrip ? 'Outbound' : 'Route'}
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="text-lg font-bold text-primary">
                              {booking.flight.departureAirport.code}
                            </div>
                            <Plane className="w-4 h-4 text-content-muted" />
                            <div className="text-lg font-bold text-primary">
                              {booking.flight.arrivalAirport.code}
                            </div>
                          </div>
                          <div className="text-xs text-content-muted">
                            {booking.flight.segments[0].airline.name}
                          </div>
                        </div>

                        {/* Return */}
                        {isRoundTrip && booking.returnFlight && (
                          <div>
                            <div className="text-xs text-content-muted mb-1">Return</div>
                            <div className="flex items-center gap-2">
                              <div className="text-lg font-bold text-primary">
                                {booking.returnFlight.departureAirport.code}
                              </div>
                              <Plane className="w-4 h-4 text-content-muted rotate-180" />
                              <div className="text-lg font-bold text-primary">
                                {booking.returnFlight.arrivalAirport.code}
                              </div>
                            </div>
                            <div className="text-xs text-content-muted">
                              {booking.returnFlight.segments[0].airline.name}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Date */}
                      <div className="space-y-3">
                        <div>
                          <div className="text-sm text-content-muted mb-1 flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            {isRoundTrip ? 'Departure' : 'Date'}
                          </div>
                          <div className="font-semibold text-content">
                            {departureTime.toLocaleDateString('en-US', {
                              month: 'short',
                              day: 'numeric',
                              year: 'numeric',
                            })}
                          </div>
                          <div className="text-xs text-content-muted">
                            {departureTime.toLocaleTimeString('en-US', {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </div>
                        </div>

                        {isRoundTrip && returnDepartureTime && (
                          <div>
                            <div className="text-sm text-content-muted mb-1 flex items-center gap-1">
                              <Calendar className="w-4 h-4" />
                              Return
                            </div>
                            <div className="font-semibold text-content">
                              {returnDepartureTime.toLocaleDateString('en-US', {
                                month: 'short',
                                day: 'numeric',
                                year: 'numeric',
                              })}
                            </div>
                            <div className="text-xs text-content-muted">
                              {returnDepartureTime.toLocaleTimeString('en-US', {
                                hour: '2-digit',
                                minute: '2-digit',
                              })}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Passengers */}
                      <div>
                        <div className="text-sm text-content-muted mb-1 flex items-center gap-1">
                          <Users className="w-4 h-4" />
                          Passengers
                        </div>
                        <div className="font-semibold text-content">{totalPassengers}</div>
                        <div className="text-xs text-content-muted">
                          {booking.adults} adult{booking.adults !== 1 ? 's' : ''}
                          {booking.children > 0 && `, ${booking.children} child${booking.children !== 1 ? 'ren' : ''}`}
                        </div>
                      </div>

                      {/* Price & Action */}
                      <div className="flex items-end justify-between md:flex-col md:items-end gap-2">
                        <div>
                          <div className="text-sm text-content-muted mb-1 flex items-center gap-1">
                            <DollarSign className="w-4 h-4" />
                            Total
                          </div>
                          <div className="text-lg font-bold text-primary">
                            ${booking.total.toFixed(2)}
                          </div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.preventDefault();
                            handleDownload(booking);
                          }}
                          className="bg-primary/10 text-primary px-3 py-2 rounded-lg hover:bg-primary/20 transition-colors flex items-center gap-2 text-sm font-medium"
                        >
                          <Download className="w-4 h-4" />
                          PDF
                        </button>
                      </div>
                    </div>

                    {/* Booking ID */}
                    <div className="mt-4 pt-4 border-t border-divider-light">
                      <div className="text-xs text-content-muted">
                        Booking ID: <span className="font-mono text-content">{booking.bookingId}</span>
                      </div>
                    </div>
                  </a>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </SignedIn>
  );
}
