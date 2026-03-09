import { useState, useEffect } from 'react';
import { User, Mail, Phone, CalendarDays } from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '../../lib/utils';
import { Calendar } from '../ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '../ui/popover';
import { Button } from '../ui/button';

// Validation helpers
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PHONE_REGEX = /^[\d\s\-\+\(\)]+$/; // Basic phone validation

export interface PassengerData {
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  email?: string;
  phone?: string;
}

interface PassengerStepProps {
  adults: number;
  children: number;
  onContinue: (passengers: PassengerData[]) => void;
  onBack: () => void;
}

export default function PassengerStep({ adults, children, onContinue, onBack }: PassengerStepProps) {
  const totalPassengers = adults + children;

  const [passengers, setPassengers] = useState<PassengerData[]>(() => {
    return Array.from({ length: totalPassengers }, () => ({
      firstName: '',
      lastName: '',
      dateOfBirth: '',
      email: '',
      phone: '',
    }));
  });

  useEffect(() => {
    setPassengers(prev => {
      if (prev.length === totalPassengers) return prev;

      if (prev.length < totalPassengers) {
        // Add new empty passengers
        const toAdd = totalPassengers - prev.length;
        const newPassengers = Array.from({ length: toAdd }, () => ({
          firstName: '',
          lastName: '',
          dateOfBirth: '',
          email: '',
          phone: '',
        }));
        return [...prev, ...newPassengers];
      } else {
        // Remove excess passengers
        return prev.slice(0, totalPassengers);
      }
    });
  }, [totalPassengers]);

  const updatePassenger = (index: number, field: keyof PassengerData, value: string) => {
    setPassengers(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const isValid = passengers.every((p, idx) => {
    const hasBasicInfo = p.firstName.trim() && p.lastName.trim() && p.dateOfBirth;
    if (!hasBasicInfo) return false;
    
    // Primary passenger needs valid email and phone
    if (idx === 0) {
      const hasValidEmail = p.email && EMAIL_REGEX.test(p.email);
      const hasValidPhone = p.phone && PHONE_REGEX.test(p.phone) && p.phone.replace(/\D/g, '').length >= 10;
      return hasValidEmail && hasValidPhone;
    }
    
    return true;
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isValid) {
      onContinue(passengers);
    }
  };

  const inputClass = "w-full pl-11 pr-4 py-3 rounded-xl border border-divider hover:border-primary/50 focus:outline-none focus:ring-4 focus:ring-primary/10 focus:border-primary transition-all bg-surface/30 focus:bg-white text-content placeholder:text-content-lighter shadow-sm disabled:opacity-50 disabled:cursor-not-allowed";

  return (
    <form onSubmit={handleSubmit} className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h2 className="text-3xl font-bold text-content tracking-tight">Passenger Details</h2>
        <p className="text-content-muted mt-2 text-lg">Please ensure names match exactly as they appear on your government-issued ID.</p>
      </div>

      <div className="space-y-6">
        {passengers.map((passenger, idx) => {
          const isPrimary = idx === 0;
          const isChild = idx >= adults;

          return (
            <div key={idx} className="bg-white rounded-3xl p-6 sm:p-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-divider-light/60 relative overflow-hidden">
              {isPrimary && (
                <div className="absolute top-0 left-0 w-full h-1.5 bg-linear-to-r from-primary to-primary-light" />
              )}

              <div className="flex items-center gap-3 mb-6">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${isPrimary ? 'bg-primary-50 text-primary' : 'bg-surface text-content-muted'}`}>
                  <User className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-content">
                    {isPrimary ? 'Primary Passenger' : `Passenger ${idx + 1}`}
                  </h3>
                  {isChild && <span className="text-sm font-medium text-content-muted bg-surface px-2 py-0.5 rounded-full inline-block mt-1">Child</span>}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="relative">
                  <label className="block text-sm font-semibold text-content-muted mb-1.5">
                    First Name <span className="text-monza-500">*</span>
                  </label>
                  <div className="relative">
                    <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-content-lighter" />
                    <input
                      type="text"
                      value={passenger.firstName}
                      onChange={(e) => updatePassenger(idx, 'firstName', e.target.value)}
                      className={inputClass}
                      placeholder="e.g. John"
                      autoComplete="given-name"
                      required
                      data-testid={`passenger-${idx}-firstName`}
                    />
                  </div>
                </div>

                <div className="relative">
                  <label className="block text-sm font-semibold text-content-muted mb-1.5">
                    Last Name <span className="text-monza-500">*</span>
                  </label>
                  <div className="relative">
                    <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-content-lighter" />
                    <input
                      type="text"
                      value={passenger.lastName}
                      onChange={(e) => updatePassenger(idx, 'lastName', e.target.value)}
                      className={inputClass}
                      placeholder="e.g. Doe"
                      autoComplete="family-name"
                      required
                      data-testid={`passenger-${idx}-lastName`}
                    />
                  </div>
                </div>

                <div className="relative">
                  <label className="block text-sm font-semibold text-content-muted mb-1.5">
                    Date of Birth <span className="text-monza-500">*</span>
                  </label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant={"outline"}
                        className={cn(
                          "w-full flex justify-start text-left font-normal pl-11 pr-4 py-3 h-auto rounded-xl border border-divider hover:border-primary/50 focus:outline-none focus:ring-4 focus:ring-primary/10 focus:border-primary transition-all bg-surface/30 hover:bg-white focus:bg-white text-content placeholder:text-content-lighter shadow-sm",
                          !passenger.dateOfBirth && "text-content-lighter"
                        )}
                      >
                        <CalendarDays className="w-5 h-5 text-content-lighter" />
                        {passenger.dateOfBirth ? (
                          format(new Date(passenger.dateOfBirth), "PPP")
                        ) : (
                          <span>Select a date</span>
                        )}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0 rounded-2xl border-divider" align="start">
                      <Calendar
                        mode="single"
                        captionLayout="dropdown"
                        startMonth={new Date(1900, 0)}
                        endMonth={new Date()}
                        selected={passenger.dateOfBirth ? new Date(passenger.dateOfBirth) : undefined}
                        onSelect={(date) => {
                          if (date) {
                            // Format as YYYY-MM-DD to keep the PassengerData shape consistent
                            const formattedDate = format(date, 'yyyy-MM-dd');
                            updatePassenger(idx, 'dateOfBirth', formattedDate);
                          } else {
                            updatePassenger(idx, 'dateOfBirth', '');
                          }
                        }}
                        disabled={(date) =>
                          date > new Date() || date < new Date("1900-01-01")
                        }
                        initialFocus
                        className="w-full p-3"
                      />
                    </PopoverContent>
                  </Popover>
                </div>

                {isPrimary && (
                  <>
                    <div className="relative">
                      <label className="block text-sm font-semibold text-content-muted mb-1.5">
                        Email Address <span className="text-monza-500">*</span>
                      </label>
                      <div className="relative">
                        <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-content-lighter" />
                        <input
                          type="email"
                          value={passenger.email}
                          onChange={(e) => updatePassenger(idx, 'email', e.target.value)}
                          className={inputClass}
                          placeholder="john.doe@example.com"
                          autoComplete="email"
                          required
                          data-testid="primary-email"
                        />
                      </div>
                    </div>

                    <div className="relative">
                      <label className="block text-sm font-semibold text-content-muted mb-1.5">
                        Phone Number <span className="text-monza-500">*</span>
                      </label>
                      <div className="relative">
                        <Phone className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-content-lighter" />
                        <input
                          type="tel"
                          value={passenger.phone}
                          onChange={(e) => updatePassenger(idx, 'phone', e.target.value)}
                          className={inputClass}
                          placeholder="+1 (555) 000-0000"
                          autoComplete="tel"
                          required
                          data-testid="primary-phone"
                        />
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="flex flex-col-reverse sm:flex-row gap-4 pt-4">
        <button
          type="button"
          onClick={onBack}
          className="w-full sm:w-1/3 py-5 rounded-2xl font-semibold text-lg border-2 border-divider hover:border-divider-focus hover:bg-surface-muted text-content transition-all duration-300"
        >
          Back
        </button>
        <button
          type="submit"
          disabled={!isValid}
          className="w-full sm:w-2/3 btn-primary-large text-lg py-5 disabled:opacity-50 disabled:shadow-none disabled:cursor-not-allowed hover:disabled:translate-y-0"
          data-testid="continue-to-payment"
        >
          Continue to Payment
        </button>
      </div>
    </form>
  );
}
