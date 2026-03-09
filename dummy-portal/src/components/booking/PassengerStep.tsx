import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useEffect } from 'react';
import { User, Mail, Phone, CalendarDays } from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '../../lib/utils';
import { Calendar } from '../ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '../ui/popover';
import type { PassengerData } from '../../data/schema';

const passengerSchema = z.object({
  firstName: z.string().min(1, 'First name is required').trim(),
  lastName: z.string().min(1, 'Last name is required').trim(),
  dateOfBirth: z.string().min(1, 'Date of birth is required'),
  email: z.string().optional(),
  phone: z.string().optional(),
});

const formSchema = z.object({
  passengers: z.array(passengerSchema),
}).superRefine((data, ctx) => {
  // Primary passenger (index 0) must have valid email and phone
  const primary = data.passengers[0];
  if (primary) {
    if (!primary.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(primary.email)) {
      ctx.addIssue({ code: 'custom', message: 'Enter a valid email address', path: ['passengers', 0, 'email'] });
    }
    if (!primary.phone || primary.phone.replace(/\D/g, '').length < 10) {
      ctx.addIssue({ code: 'custom', message: 'Phone must be at least 10 digits', path: ['passengers', 0, 'phone'] });
    }
  }
});

type FormData = z.infer<typeof formSchema>;

interface PassengerStepProps {
  adults: number;
  children: number;
  onContinue: (passengers: PassengerData[]) => void;
  onBack: () => void;
}

export default function PassengerStep({ adults, children, onContinue, onBack }: PassengerStepProps) {
  const totalPassengers = adults + children;

  const { register, control, handleSubmit, setValue, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: 'onBlur',
    defaultValues: {
      passengers: Array.from({ length: totalPassengers }, () => ({
        firstName: '', lastName: '', dateOfBirth: '', email: '', phone: '',
      })),
    },
  });

  const { fields } = useFieldArray({ control, name: 'passengers' });

  // Sync field count if passenger count changes
  useEffect(() => {
    if (fields.length !== totalPassengers) {
      setValue('passengers', Array.from({ length: totalPassengers }, (_, i) =>
        watch(`passengers.${i}`) || { firstName: '', lastName: '', dateOfBirth: '', email: '', phone: '' }
      ));
    }
  }, [totalPassengers]);

  const onSubmit = (data: FormData) => onContinue(data.passengers);

  const inputBase = "w-full pl-11 pr-4 py-3 rounded-xl border transition-all bg-surface/30 focus:bg-white text-content placeholder:text-content-lighter shadow-sm focus:outline-none focus:ring-4";
  const inputOk = "border-divider hover:border-primary/50 focus:ring-primary/10 focus:border-primary";
  const inputErr = "border-monza-400 focus:ring-monza-100 focus:border-monza-500";

  const fieldError = (idx: number, field: string) => {
    const err = (errors.passengers as any)?.[idx]?.[field];
    return err ? <p className="text-monza-500 text-xs mt-1.5 font-medium">{err.message}</p> : null;
  };

  const hasError = (idx: number, field: string) => !!(errors.passengers as any)?.[idx]?.[field];

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h2 className="text-3xl font-bold text-content tracking-tight">Passenger Details</h2>
        <p className="text-content-muted mt-2 text-lg">Please ensure names match exactly as they appear on your government-issued ID.</p>
      </div>

      <div className="space-y-6">
        {fields.map((field, idx) => {
          const isPrimary = idx === 0;
          const isChild = idx >= adults;

          return (
            <div key={field.id} className="bg-white rounded-3xl p-6 sm:p-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-divider-light/60 relative overflow-hidden">
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
                {/* First Name */}
                <div>
                  <label htmlFor={`passenger-${idx}-firstName`} className="block text-sm font-semibold text-content-muted mb-1.5">
                    First Name <span className="text-monza-500">*</span>
                  </label>
                  <div className="relative">
                    <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-content-lighter" />
                    <input
                      {...register(`passengers.${idx}.firstName`)}
                      id={`passenger-${idx}-firstName`}
                      className={cn(inputBase, hasError(idx, 'firstName') ? inputErr : inputOk)}
                      placeholder="e.g. John"
                      autoComplete="given-name"
                      data-testid={`passenger-${idx}-firstName`}
                    />
                  </div>
                  {fieldError(idx, 'firstName')}
                </div>

                {/* Last Name */}
                <div>
                  <label htmlFor={`passenger-${idx}-lastName`} className="block text-sm font-semibold text-content-muted mb-1.5">
                    Last Name <span className="text-monza-500">*</span>
                  </label>
                  <div className="relative">
                    <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-content-lighter" />
                    <input
                      {...register(`passengers.${idx}.lastName`)}
                      id={`passenger-${idx}-lastName`}
                      className={cn(inputBase, hasError(idx, 'lastName') ? inputErr : inputOk)}
                      placeholder="e.g. Doe"
                      autoComplete="family-name"
                      data-testid={`passenger-${idx}-lastName`}
                    />
                  </div>
                  {fieldError(idx, 'lastName')}
                </div>

                {/* Date of Birth */}
                <div>
                  <label htmlFor={`passenger-${idx}-dob`} className="block text-sm font-semibold text-content-muted mb-1.5">
                    Date of Birth <span className="text-monza-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      id={`passenger-${idx}-dob`}
                      type="text"
                      placeholder="DD-MM-YYYY"
                      value={watch(`passengers.${idx}.dateOfBirth`) ? format(new Date(watch(`passengers.${idx}.dateOfBirth`)), 'dd-MM-yyyy') : ''}
                      onChange={(e) => {
                        const val = e.target.value;
                        const match = val.match(/^(\d{2})-(\d{2})-(\d{4})$/);
                        if (match) {
                          setValue(`passengers.${idx}.dateOfBirth`, `${match[3]}-${match[2]}-${match[1]}`, { shouldValidate: true });
                        } else {
                          // Store raw input temporarily so user can keep typing
                          setValue(`passengers.${idx}.dateOfBirth`, val, { shouldValidate: false });
                        }
                      }}
                      className={cn(inputBase, hasError(idx, 'dateOfBirth') ? inputErr : inputOk)}
                      data-testid={`passenger-${idx}-dob`}
                    />
                    <Popover>
                      <PopoverTrigger asChild>
                        <button
                          type="button"
                          className="absolute left-3 top-1/2 -translate-y-1/2 text-content-lighter hover:text-primary transition-colors"
                          aria-label="Open calendar"
                        >
                          <CalendarDays className="w-5 h-5" />
                        </button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0 rounded-2xl border-divider" align="start">
                        <Calendar
                          mode="single"
                          captionLayout="dropdown"
                          startMonth={new Date(1900, 0)}
                          endMonth={new Date()}
                          selected={watch(`passengers.${idx}.dateOfBirth`) ? new Date(watch(`passengers.${idx}.dateOfBirth`)) : undefined}
                          onSelect={(date) => {
                            setValue(`passengers.${idx}.dateOfBirth`, date ? format(date, 'yyyy-MM-dd') : '', { shouldValidate: true });
                          }}
                          disabled={(date) => date > new Date() || date < new Date("1900-01-01")}
                          initialFocus
                          className="w-full p-3"
                        />
                      </PopoverContent>
                    </Popover>
                  </div>
                  {fieldError(idx, 'dateOfBirth')}
                </div>

                {/* Email & Phone — primary passenger only */}
                {isPrimary && (
                  <>
                    <div>
                      <label htmlFor="primary-email" className="block text-sm font-semibold text-content-muted mb-1.5">
                        Email Address <span className="text-monza-500">*</span>
                      </label>
                      <div className="relative">
                        <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-content-lighter" />
                        <input
                          {...register(`passengers.${idx}.email`)}
                          id="primary-email"
                          type="email"
                          className={cn(inputBase, hasError(idx, 'email') ? inputErr : inputOk)}
                          placeholder="john.doe@example.com"
                          autoComplete="email"
                          data-testid="primary-email"
                        />
                      </div>
                      {fieldError(idx, 'email')}
                    </div>

                    <div>
                      <label htmlFor="primary-phone" className="block text-sm font-semibold text-content-muted mb-1.5">
                        Phone Number <span className="text-monza-500">*</span>
                      </label>
                      <div className="relative">
                        <Phone className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-content-lighter" />
                        <input
                          {...register(`passengers.${idx}.phone`)}
                          id="primary-phone"
                          type="tel"
                          className={cn(inputBase, hasError(idx, 'phone') ? inputErr : inputOk)}
                          placeholder="+1 (555) 000-0000"
                          autoComplete="tel"
                          data-testid="primary-phone"
                        />
                      </div>
                      {fieldError(idx, 'phone')}
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
          className="w-full sm:w-2/3 btn-primary-large text-lg py-5 disabled:opacity-50 disabled:shadow-none disabled:cursor-not-allowed hover:disabled:translate-y-0"
          data-testid="continue-to-payment"
        >
          Continue to Payment
        </button>
      </div>
    </form>
  );
}
