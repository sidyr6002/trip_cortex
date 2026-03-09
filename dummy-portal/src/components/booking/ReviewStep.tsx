import type { FlightListing } from '../../data/schema';
import { formatDuration } from '../../data/mockData';
import { Plane, Calendar, Users, Briefcase } from 'lucide-react';

interface ReviewStepProps {
  flight: FlightListing;
  adults: number;
  children: number;
  pricing: { subtotal: number; taxes: number; total: number };
  onContinue: () => void;
}

export default function ReviewStep({ flight, adults, children, pricing, onContinue }: ReviewStepProps) {
  const totalPassengers = adults + children;
  const { subtotal, taxes, total } = pricing;

  const departureDate = new Date(flight.segments[0].departureTime).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h2 className="text-3xl font-bold text-content tracking-tight">Review Your Flight</h2>
        <p className="text-content-muted mt-2 text-lg">Double check your flight details before continuing.</p>
      </div>

      {/* Flight Summary Card */}
      <div className="bg-white rounded-3xl p-1 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-divider-light/60 overflow-hidden relative">
        <div className="absolute top-0 left-0 w-full h-2 bg-linear-to-r from-primary to-primary-light" />

        <div className="p-6 sm:p-8 space-y-8 mt-2">
          {/* Header */}
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-full bg-surface flex items-center justify-center border border-divider-light shadow-sm">
                <div className="text-sm font-black text-primary tracking-wider">
                  {flight.segments[0].airline.name.split(' ').map(w => w[0]).join('')}
                </div>
              </div>
              <div>
                <h3 className="text-lg font-bold text-content">{flight.segments[0].airline.name}</h3>
                <p className="text-sm font-medium text-content-muted">{flight.segments.map(s => s.flightNumber).join(' • ')}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 bg-primary-50 text-primary-700 px-4 py-2 rounded-full text-sm font-semibold border border-primary-100">
              <Calendar className="w-4 h-4" />
              {departureDate}
            </div>
          </div>

          {/* Time Route */}
          <div className="flex items-center justify-between relative px-2 sm:px-4">
            <div className="text-left relative z-10 bg-white pr-4">
              <div className="text-3xl sm:text-4xl font-black text-content tracking-tight">
                {flight.segments[0].departureTime.split('T')[1].substring(0, 5)}
              </div>
              <div className="text-lg font-semibold text-content-muted mt-1">{flight.departureAirport.code}</div>
              <div className="text-sm text-content-lighter">{flight.departureAirport.cityName}</div>
            </div>

            <div className="flex-1 flex flex-col items-center absolute left-0 right-0 z-0">
              <div className="text-xs font-bold text-primary-600 mb-2 bg-primary-50 px-3 py-1 rounded-full border border-primary-100">
                {formatDuration(flight.totalDurationMinutes)}
              </div>
              <div className="w-full flex items-center">
                <div className="h-[2px] w-full bg-divider" />
                <Plane className="w-6 h-6 text-primary mx-2 shrink-0 fill-primary/20" />
                <div className="h-[2px] w-full bg-divider" />
              </div>
              <div className="text-xs font-medium text-content-muted mt-2 bg-white px-2">
                {flight.transitType}
              </div>
            </div>

            <div className="text-right flex flex-col items-end relative z-10 bg-white pl-4">
              <div className="text-3xl sm:text-4xl font-black text-content tracking-tight">
                {flight.segments[flight.segments.length - 1].arrivalTime.split('T')[1].substring(0, 5)}
              </div>
              <div className="text-lg font-semibold text-content-muted mt-1">{flight.arrivalAirport.code}</div>
              <div className="text-sm text-content-lighter">{flight.arrivalAirport.cityName}</div>
            </div>
          </div>

          {/* Amenities/Info */}
          <div className="grid grid-cols-2 gap-4 pt-6 border-t border-divider-light">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-surface flex items-center justify-center shrink-0">
                <Briefcase className="w-5 h-5 text-content-muted" />
              </div>
              <div>
                <div className="text-xs text-content-muted mb-0.5">Cabin Class</div>
                <div className="text-sm font-bold text-content">{flight.flightClass.name}</div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-surface flex items-center justify-center shrink-0">
                <Users className="w-5 h-5 text-content-muted" />
              </div>
              <div>
                <div className="text-xs text-content-muted mb-0.5">Passengers</div>
                <div className="text-sm font-bold text-content">
                  {adults} Adult{adults > 1 ? 's' : ''}{children > 0 ? `, ${children} Child${children > 1 ? 'ren' : ''}` : ''}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Price Breakdown */}
      <div className="bg-surface-gradient rounded-3xl p-6 sm:p-8 border border-divider-light/60 shadow-[0_4px_20px_rgb(0,0,0,0.02)]">
        <h3 className="text-xl font-bold text-content mb-6 flex items-center gap-2">
          Price Breakdown
        </h3>

        <div className="space-y-4">
          <div className="flex justify-between items-center text-content-muted">
            <span className="font-medium">Base Fare ({totalPassengers} × ${flight.pricing.pricePerPassenger})</span>
            <span className="font-semibold text-content">${subtotal.toFixed(2)}</span>
          </div>
          <div className="flex justify-between items-center text-content-muted">
            <span className="font-medium">Taxes & Fees</span>
            <span className="font-semibold text-content">${taxes.toFixed(2)}</span>
          </div>

          <div className="pt-6 border-t border-divider flex justify-between items-end">
            <div>
              <div className="text-sm font-medium text-content-muted mb-1">Total Amount</div>
              <div className="text-xs text-content-lighter">Includes all taxes and fees</div>
            </div>
            <div className="text-3xl font-black text-primary">${total.toFixed(2)}</div>
          </div>
        </div>
      </div>

      <div className="pt-4">
        <button
          onClick={onContinue}
          className="btn-primary-large w-full text-lg py-5"
          data-testid="continue-to-passengers"
        >
          Continue to Passenger Details
        </button>
      </div>
    </div>
  );
}
