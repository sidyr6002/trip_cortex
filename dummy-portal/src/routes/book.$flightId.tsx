import { useState, useMemo } from 'react';
import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { getFlightById } from '../data/helpers';
import { calculatePricing } from '../data/calculatePricing';
import Navbar from '../components/home/Navbar';
import BookingStepper from '../components/booking/BookingStepper';
import ReviewStep from '../components/booking/ReviewStep';
import PassengerStep from '../components/booking/PassengerStep';
import PaymentStep from '../components/booking/PaymentStep';
import { StripeProvider } from '../components/booking/StripeProvider';
import { createPaymentIntent } from '../server/create-payment-intent';
import { Loader2 } from 'lucide-react';
import type { PassengerData } from '../data/schema';

interface BookingSearch {
  adults: number;
  children: number;
  returnFlightId?: string;
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
    returnFlightId: search.returnFlightId as string | undefined,
  }),
  component: BookingRoute,
});

function BookingRoute() {
  const { flightId } = Route.useParams();
  const { adults, children, returnFlightId } = Route.useSearch();
  const navigate = useNavigate();

  const [currentStep, setCurrentStep] = useState(1);
  const [passengerData, setPassengerData] = useState<PassengerData[]>([]);
  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [paymentError, setPaymentError] = useState<string | null>(null);
  const [isLoadingPayment, setIsLoadingPayment] = useState(false);

  const flight = getFlightById(flightId);
  const returnFlight = returnFlightId ? getFlightById(returnFlightId) : undefined;

  // Memoize price calculations (combined for round-trip)
  const pricing = useMemo(
    () => flight ? calculatePricing(flight, adults, children, returnFlight) : { outboundSubtotal: 0, returnSubtotal: 0, subtotal: 0, taxes: 0, total: 0 },
    [flight, returnFlight, adults, children],
  );

  if (!flight) {
    return (
      <div className="min-h-screen bg-primary-100 to-white">
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
  const handleContinueToPayment = async (passengers: PassengerData[]) => {
    setPassengerData(passengers);
    setPaymentError(null);
    setIsLoadingPayment(true);
    setCurrentStep(3);

    try {
      const { clientSecret } = await createPaymentIntent({
        data: { amount: Math.round(pricing.total * 100) },
      });
      setClientSecret(clientSecret);
    } catch {
      setPaymentError('Failed to initialize payment. Please try again.');
      setCurrentStep(2);
    } finally {
      setIsLoadingPayment(false);
    }
  };

  const handleConfirmPayment = (paymentIntentId: string) => {
    // Generate deterministic booking ID based on flight and passenger data
    const bookingData = JSON.stringify({
      flightId,
      returnFlightId,
      passengers: passengerData.map(p => `${p.firstName}${p.lastName}${p.dateOfBirth}`),
      timestamp: new Date().toISOString().split('T')[0],
    });
    const bookingId = `FS-${flightId}-${hashString(bookingData)}`;

    // Store booking data in localStorage for persistence
    const bookingState = {
      flight,
      returnFlight: returnFlight ?? null,
      passengers: passengerData,
      adults,
      children,
      total: pricing.total,
      paymentIntentId,
    };
    localStorage.setItem(`booking-${bookingId}`, JSON.stringify(bookingState));

    navigate({
      to: '/confirmation/$bookingId',
      params: { bookingId },
      state: bookingState as any,
    });
  };

  return (
    <div className="min-h-screen bg-primary-100">
      <Navbar simplified />

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <BookingStepper currentStep={currentStep} />

        {currentStep === 1 && (
          <ReviewStep
            flight={flight}
            returnFlight={returnFlight}
            adults={adults}
            children={children}
            pricing={pricing}
            onContinue={handleContinueToPassengers}
          />
        )}

        {currentStep === 2 && (
          <>
            {paymentError && (
              <div className="mb-6 p-4 rounded-xl bg-monza-50 border border-monza-200 text-monza-700 text-sm font-medium">
                {paymentError}
              </div>
            )}
            <PassengerStep
              adults={adults}
              children={children}
              onContinue={handleContinueToPayment}
              onBack={() => setCurrentStep(1)}
            />
          </>
        )}

        {currentStep === 3 && isLoadingPayment && (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="w-16 h-16 text-primary animate-spin mb-6" />
            <h2 className="text-2xl font-bold text-content mb-2">Preparing payment...</h2>
          </div>
        )}

        {currentStep === 3 && !isLoadingPayment && clientSecret && (
          <StripeProvider clientSecret={clientSecret}>
            <PaymentStep
              totalAmount={pricing.total}
              onConfirm={handleConfirmPayment}
              onBack={() => setCurrentStep(2)}
            />
          </StripeProvider>
        )}
      </div>
    </div>
  );
}
