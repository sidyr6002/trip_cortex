import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { CreditCard, Smartphone, CalendarDays, Lock, User, ShieldCheck } from 'lucide-react';
import { cn } from '../../lib/utils';

type PaymentMethod = 'credit' | 'debit' | 'upi';

const paymentSchema = z.object({
  cardNumber: z.string().min(16, 'Card number must be 16 digits'),
  expiry: z.string().regex(/^\d{2}\/\d{2}$/, 'Enter a valid expiry (MM/YY)'),
  cvv: z.string().length(3, 'CVV must be 3 digits'),
  cardName: z.string().min(1, 'Cardholder name is required').trim(),
  termsAccepted: z.literal(true, { errorMap: () => ({ message: 'You must accept the terms' }) }),
});

type FormData = z.infer<typeof paymentSchema>;

interface PaymentStepProps {
  totalAmount: number;
  onConfirm: () => void;
  onBack: () => void;
}

export default function PaymentStep({ totalAmount, onConfirm, onBack }: PaymentStepProps) {
  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(paymentSchema),
    mode: 'onBlur',
    defaultValues: { cardNumber: '', expiry: '', cvv: '', cardName: '', termsAccepted: false as any },
  });

  const [selectedMethod, setSelectedMethod] = useState<PaymentMethod>('credit');

  const onSubmit = () => onConfirm();

  const inputBase = "w-full pl-11 pr-4 py-3 rounded-xl border transition-all bg-surface/30 focus:bg-white text-content placeholder:text-content-lighter shadow-sm focus:outline-none focus:ring-4";
  const inputOk = "border-divider hover:border-primary/50 focus:ring-primary/10 focus:border-primary";
  const inputErr = "border-monza-400 focus:ring-monza-100 focus:border-monza-500";

  const fieldError = (field: keyof FormData) => {
    const err = errors[field];
    return err ? <p className="text-monza-500 text-xs mt-1.5 font-medium">{err.message}</p> : null;
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h2 className="text-3xl font-bold text-content tracking-tight">Payment Details</h2>
        <p className="text-content-muted mt-2 text-lg">Securely complete your booking.</p>
      </div>

      <div className="bg-surface-gradient rounded-3xl p-6 sm:p-8 shadow-[0_4px_20px_rgb(0,0,0,0.02)] border border-divider-light/60">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-content-muted text-sm font-medium mb-1">Total to Pay</p>
            <span className="text-4xl font-black text-primary">${totalAmount.toFixed(2)}</span>
          </div>
          <div className="hidden sm:flex items-center gap-2 bg-green-50 text-green-700 px-4 py-2 rounded-full border border-green-200">
            <ShieldCheck className="w-5 h-5" />
            <span className="text-sm font-bold">Secure Payment</span>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-divider-light/60 space-y-8 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1.5 bg-linear-to-r from-primary to-primary-light" />

        {/* Payment Method Selector */}
        <div className="space-y-4">
          <label className="block text-sm font-bold text-content-muted">Select Payment Method</label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {([
              { id: 'credit', label: 'Credit Card', icon: CreditCard },
              { id: 'debit', label: 'Debit Card', icon: CreditCard },
              { id: 'upi', label: 'UPI', icon: Smartphone },
            ] as const).map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                type="button"
                onClick={() => setSelectedMethod(id)}
                className={`relative flex flex-col items-center gap-3 py-6 px-4 rounded-2xl border-2 transition-all duration-300 ${selectedMethod === id
                  ? 'border-primary bg-primary-50/50 shadow-md transform -translate-y-0.5'
                  : 'border-divider hover:border-primary/50 hover:bg-surface/50'
                }`}
                data-testid={`payment-method-${id}`}
              >
                {selectedMethod === id && <div className="absolute top-3 right-3 w-3 h-3 rounded-full bg-primary" />}
                <Icon className={`w-8 h-8 ${selectedMethod === id ? 'text-primary' : 'text-content-muted'}`} />
                <span className={`text-sm font-semibold ${selectedMethod === id ? 'text-primary' : 'text-content-muted'}`}>{label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Card Fields */}
        <div className="space-y-6 pt-6 border-t border-divider-light">
          <div>
            <label htmlFor="card-number" className="block text-sm font-semibold text-content-muted mb-1.5">
              Card Number <span className="text-monza-500">*</span>
            </label>
            <div className="relative">
              <CreditCard className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-content-lighter" />
              <input
                {...register('cardNumber')}
                id="card-number"
                onChange={(e) => setValue('cardNumber', e.target.value.replace(/\D/g, '').slice(0, 16), { shouldValidate: !!errors.cardNumber })}
                placeholder="1234 5678 9012 3456"
                className={cn(inputBase, errors.cardNumber ? inputErr : inputOk)}
                data-testid="card-number"
              />
            </div>
            {fieldError('cardNumber')}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div>
              <label htmlFor="card-expiry" className="block text-sm font-semibold text-content-muted mb-1.5">
                Expiry (MM/YY) <span className="text-monza-500">*</span>
              </label>
              <div className="relative">
                <CalendarDays className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-content-lighter" />
                <input
                  {...register('expiry')}
                  id="card-expiry"
                  onChange={(e) => {
                    let val = e.target.value.replace(/\D/g, '');
                    if (val.length >= 2) val = val.slice(0, 2) + '/' + val.slice(2, 4);
                    setValue('expiry', val, { shouldValidate: !!errors.expiry });
                  }}
                  placeholder="12/26"
                  maxLength={5}
                  className={cn(inputBase, errors.expiry ? inputErr : inputOk)}
                  data-testid="card-expiry"
                />
              </div>
              {fieldError('expiry')}
            </div>

            <div>
              <label htmlFor="card-cvv" className="block text-sm font-semibold text-content-muted mb-1.5">
                CVV <span className="text-monza-500">*</span>
              </label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-content-lighter" />
                <input
                  {...register('cvv')}
                  id="card-cvv"
                  onChange={(e) => setValue('cvv', e.target.value.replace(/\D/g, '').slice(0, 3), { shouldValidate: !!errors.cvv })}
                  placeholder="123"
                  maxLength={3}
                  className={cn(inputBase, errors.cvv ? inputErr : inputOk)}
                  data-testid="card-cvv"
                />
              </div>
              {fieldError('cvv')}
            </div>
          </div>

          <div>
            <label htmlFor="card-name" className="block text-sm font-semibold text-content-muted mb-1.5">
              Cardholder Name <span className="text-monza-500">*</span>
            </label>
            <div className="relative">
              <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-content-lighter" />
              <input
                {...register('cardName')}
                id="card-name"
                placeholder="John Doe"
                autoComplete="cc-name"
                className={cn(inputBase, errors.cardName ? inputErr : inputOk)}
                data-testid="card-name"
              />
            </div>
            {fieldError('cardName')}
          </div>
        </div>
      </div>

      {/* Terms */}
      <div>
        <div className="flex items-start gap-3 px-2">
          <input
            type="checkbox"
            id="terms"
            {...register('termsAccepted')}
            className="mt-1 w-5 h-5 accent-primary bg-surface border-divider rounded cursor-pointer transition-colors"
            data-testid="terms-checkbox"
          />
          <label htmlFor="terms" className="text-sm font-medium text-content-muted leading-relaxed cursor-pointer select-none">
            I agree to the terms and conditions, cancellation policy, and privacy policy of FlySmart.
          </label>
        </div>
        {fieldError('termsAccepted')}
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
          data-testid="confirm-payment"
        >
          Confirm & Pay ${totalAmount.toFixed(2)}
        </button>
      </div>
    </form>
  );
}
