import { useState } from 'react';
import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { getFlightById } from '../data/helpers';
import Navbar from '../components/home/Navbar';
import BookingStepper from '../components/booking/BookingStepper';
import ReviewStep from '../components/booking/ReviewStep';
import PassengerStep, { type PassengerData } from '../components/booking/PassengerStep';
import PaymentStep from '../components/booking/PaymentStep';
import { Loader2 } from 'lucide-react';

interface BookingSearch {
  adults?: number;
  children?: number;
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

  const flight = getFlightById(flightId);

  if (!flight) {
    return (
      <div className="min-h-screen bg-surface">
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

  const totalPassengers = adults + children;
  const subtotal = flight.pricing.pricePerPassenger * totalPassengers;
  const taxes = subtotal * 0.12;
  const total = subtotal + taxes;

  const handleContinueToPassengers = () => setCurrentStep(2);
  const handleContinueToPayment = (passengers: PassengerData[]) => {
    setPassengerData(passengers);
    setCurrentStep(3);
  };

  const handleConfirmPayment = async () => {
    setIsProcessing(true);
    setCurrentStep(4);

    // Simulate payment processing
    await new Promise(resolve => setTimeout(resolve, 2500));

    // Generate deterministic booking ID
    const bookingId = `FS-${flightId}-${Date.now()}`;

    // Navigate to confirmation with booking data
    navigate({
      to: '/confirmation/$bookingId',
      params: { bookingId },
      state: {
        flight,
        passengers: passengerData,
        adults,
        children,
        total,
      },
    });
  };

  return (
    <div className="min-h-screen bg-surface">
      <Navbar />

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <BookingStepper currentStep={currentStep} />

        {currentStep === 1 && (
          <ReviewStep
            flight={flight}
            adults={adults}
            children={children}
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
            totalAmount={total}
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
