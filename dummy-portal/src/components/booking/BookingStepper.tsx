import { cn } from '../../lib/utils';
import { Check } from 'lucide-react';

interface BookingStepperProps {
  currentStep: number; // 1-4
}

const STEPS = [
  { number: 1, label: 'Review' },
  { number: 2, label: 'Passengers' },
  { number: 3, label: 'Payment' },
  { number: 4, label: 'Confirm' },
];

export default function BookingStepper({ currentStep }: BookingStepperProps) {
  return (
    <div className="w-full mb-12 px-4">
      <div className="relative hidden md:flex justify-between items-center z-0">
        {/* Background track */}
        <div className="absolute top-1/2 left-0 w-full h-1 bg-divider-light -translate-y-1/2 -z-10 rounded-full" />

        {/* Active track */}
        <div
          className="absolute top-1/2 left-0 h-1 bg-primary -translate-y-1/2 -z-10 rounded-full transition-all duration-500 ease-in-out"
          style={{ width: `${((currentStep - 1) / (STEPS.length - 1)) * 100}%` }}
        />

        {STEPS.map((step) => {
          const isCompleted = step.number < currentStep;
          const isActive = step.number === currentStep;

          return (
            <div key={step.number} className="flex flex-col items-center relative z-10 w-24">
              <div
                className={cn(
                  'w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all duration-500',
                  isCompleted ? 'bg-primary text-white ring-4 ring-primary/20 shadow-md' :
                    isActive ? 'bg-white text-primary border-2 border-primary ring-4 ring-primary/20 shadow-[0_0_15px_rgba(57,87,215,0.3)] scale-110' :
                      'bg-white text-content-lighter border-2 border-divider ring-4 ring-white'
                )}
                data-testid={`booking-step-${step.number}`}
              >
                {isCompleted ? <Check className="w-5 h-5 stroke-[3]" /> : step.number}
              </div>

              <div
                className={cn(
                  'absolute top-14 text-xs font-semibold text-center whitespace-nowrap transition-colors duration-300',
                  isActive ? 'text-primary' : isCompleted ? 'text-content' : 'text-content-lighter'
                )}
              >
                {step.label}
              </div>
            </div>
          );
        })}
      </div>
      {/* Mobile: Show current step name */}
      <div className="md:hidden text-center mt-8 text-sm font-semibold text-primary">
        Step {currentStep} of 4: {STEPS[currentStep - 1].label}
      </div>
    </div>
  );
}
