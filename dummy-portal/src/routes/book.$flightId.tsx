import { useState, useMemo, useEffect, useRef } from 'react';
import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { getFlightById } from '../data/helpers';
import Navbar from '../components/home/Navbar';
import BookingStepper from '../components/booking/BookingStepper';
import ReviewStep from '../components/booking/ReviewStep';
import PassengerStep from '../components/booking/PassengerStep';
import PaymentStep from '../components/booking/PaymentStep';
import { Loader2 } from 'lucide-react';
import { TAX_RATE } from '../data/helpers';
import type { PassengerData } from '../data/schema';
// TODO: Replace with actual Stripe payment processing time
const MOCK_PAYMENT_DELAY_MS = 2500;

interface BookingSearch {
  adults: number;
  children: number;
}

// Simple hash function for deterministic booking IDs
function hashString(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash).toString(36).toUpperCase();
}

export const Route = createFileRoute('/book/$flightId')({
  validateSearch: (search: Record<string, unknown>): BookingSearch => ({
    adults: Number(search.adults) || 1,
    children: Number(search.children) || 0,
  }),
  component: BookingRoute,
});

function BookingRoute() {
  const { flightId } = Route.useParams();
  const { adults, children } = Route.useSearch();
  const navigate = useNavigate();

  const [currentStep, setCurrentStep] = useState(1);
  const [passengerData, setPassengerData] = useState<PassengerData[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const flight = getFlightById(flightId);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Memoize price calculations
  const pricing = useMemo(() => {
    if (!flight) return { subtotal: 0, taxes: 0, total: 0 };
    const totalPassengers = adults + children;
    const subtotal = flight.pricing.pricePerPassenger * totalPassengers;
    const taxes = subtotal * TAX_RATE;
    return { subtotal, taxes, total: subtotal + taxes };
  }, [flight, adults, children]);

  if (!flight) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-primary-100 via-primary-50 to-white">
        <Navbar />
        <div className="container mx-auto px-4 py-12 text-center">
          <h1 className="text-2xl font-bold text-content mb-4">Flight Not Found</h1>
          <p className="text-content-muted mb-6">The flight you're looking for doesn't exist.</p>
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

  const handleContinueToPassengers = () => setCurrentStep(2);
  const handleContinueToPayment = (passengers: PassengerData[]) => {
    setPassengerData(passengers);
    setCurrentStep(3);
  };

  const handleConfirmPayment = async () => {
    setIsProcessing(true);
    setCurrentStep(4);

    // Create abort controller for cleanup
    abortControllerRef.current = new AbortController();

    try {
      // TODO: Replace with actual Stripe payment processing
      await new Promise((resolve, reject) => {
        const timeout = setTimeout(resolve, MOCK_PAYMENT_DELAY_MS);
        abortControllerRef.current?.signal.addEventListener('abort', () => {
          clearTimeout(timeout);
          reject(new Error('Payment cancelled'));
        });
      });

      // Generate deterministic booking ID based on flight and passenger data
      const bookingData = JSON.stringify({
        flightId,
        passengers: passengerData.map(p => `${p.firstName}${p.lastName}${p.dateOfBirth}`),
        timestamp: new Date().toISOString().split('T')[0], // Date only for determinism
      });
      const bookingId = `FS-${flightId}-${hashString(bookingData)}`;

      // Store booking data in localStorage for persistence
      const bookingState = {
        flight,
        passengers: passengerData,
        adults,
        children,
        total: pricing.total,
      };
      localStorage.setItem(`booking-${bookingId}`, JSON.stringify(bookingState));

      // Navigate to confirmation
      navigate({
        to: '/confirmation/$bookingId',
        params: { bookingId },
        state: bookingState as any,
      });
    } catch (error) {
      // Handle payment cancellation/error
      if ((error as Error).message !== 'Payment cancelled') {
        console.error('Payment error:', error);
        // TODO: Show error message to user
      }
      setIsProcessing(false);
      setCurrentStep(3);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-100 via-primary-50 to-white">
      <Navbar />

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <BookingStepper currentStep={currentStep} />

        {currentStep === 1 && (
          <ReviewStep
            flight={flight}
            adults={adults}
            children={children}
            pricing={pricing}
            onContinue={handleContinueToPassengers}
          />
        )}

        {currentStep === 2 && (
          <PassengerStep
            adults={adults}
            children={children}
            onContinue={handleContinueToPayment}
            onBack={() => setCurrentStep(1)}
          />
        )}

        {currentStep === 3 && (
          <PaymentStep
            totalAmount={pricing.total}
            onConfirm={handleConfirmPayment}
            onBack={() => setCurrentStep(2)}
          />
        )}

        {currentStep === 4 && isProcessing && (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="w-16 h-16 text-primary animate-spin mb-6" />
            <h2 className="text-2xl font-bold text-content mb-2">Processing your booking...</h2>
            <p className="text-content-muted">Please wait while we confirm your reservation</p>
          </div>
        )}
      </div>
    </div>
  );
}
