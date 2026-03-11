import { useState } from 'react'
import { useStripe, useElements, PaymentElement } from '@stripe/react-stripe-js'
import { ShieldCheck } from 'lucide-react'

interface PaymentStepProps {
  totalAmount: number
  onConfirm: (paymentIntentId: string) => void
  onBack: () => void
}

export default function PaymentStep({ totalAmount, onConfirm, onBack }: PaymentStepProps) {
  const stripe = useStripe()
  const elements = useElements()
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [termsAccepted, setTermsAccepted] = useState(false)
  const [termsError, setTermsError] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!stripe || !elements) return

    if (!termsAccepted) {
      setTermsError(true)
      return
    }

    setIsProcessing(true)
    setError(null)

    const { error: stripeError, paymentIntent } = await stripe.confirmPayment({
      elements,
      redirect: 'if_required',
    })

    if (stripeError) {
      setError(stripeError.message ?? 'Payment failed. Please try again.')
      setIsProcessing(false)
    } else {
      onConfirm(paymentIntent.id)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5 sm:space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h2 className="text-2xl sm:text-3xl font-bold text-content tracking-tight">Payment Details</h2>
        <p className="text-content-muted mt-1 sm:mt-2 text-base sm:text-lg">Securely complete your booking.</p>
      </div>

      {/* Total Summary */}
      <div className="bg-surface-gradient rounded-2xl sm:rounded-3xl p-4 sm:p-8 shadow-[0_4px_20px_rgb(0,0,0,0.02)] border border-divider-light/60">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-content-muted text-xs sm:text-sm font-medium mb-1">Total to Pay</p>
            <span className="text-3xl sm:text-4xl font-black text-primary">${totalAmount.toFixed(2)}</span>
          </div>
          <div className="flex items-center gap-1.5 sm:gap-2 bg-green-50 text-green-700 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full border border-green-200">
            <ShieldCheck className="w-4 h-4 sm:w-5 sm:h-5" />
            <span className="text-xs sm:text-sm font-bold">Secure Payment</span>
          </div>
        </div>
      </div>

      {/* Stripe Payment Element */}
      <div className="bg-white rounded-2xl sm:rounded-3xl p-4 sm:p-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-divider-light/60 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1.5 bg-linear-to-r from-primary to-primary-light" />
        <PaymentElement />
        {error && (
          <p className="text-monza-500 text-sm mt-4 font-medium">{error}</p>
        )}
      </div>

      {/* Terms */}
      <div>
        <div className="flex items-start gap-2.5 sm:gap-3 px-1 sm:px-2">
          <input
            type="checkbox"
            id="terms"
            checked={termsAccepted}
            onChange={(e) => {
              setTermsAccepted(e.target.checked)
              if (e.target.checked) setTermsError(false)
            }}
            className="mt-0.5 w-5 h-5 accent-primary bg-surface border-divider rounded cursor-pointer transition-colors shrink-0"
            data-testid="terms-checkbox"
          />
          <label htmlFor="terms" className="text-xs sm:text-sm font-medium text-content-muted leading-relaxed cursor-pointer select-none">
            I agree to the terms and conditions, cancellation policy, and privacy policy of FlySmart.
          </label>
        </div>
        {termsError && (
          <p className="text-monza-500 text-xs mt-1.5 font-medium px-1 sm:px-2">You must accept the terms</p>
        )}
      </div>

      <div className="flex flex-col-reverse sm:flex-row gap-3 sm:gap-4 pt-2 sm:pt-4">
        <button
          type="button"
          onClick={onBack}
          className="w-full sm:w-1/3 py-5 rounded-2xl font-semibold text-lg border-2 border-divider bg-zinc-400 hover:bg-zinc-500 text-content hover:text-white transition-all duration-300 cursor-pointer"
        >
          Back
        </button>
        <button
          type="submit"
          disabled={!stripe || !elements || isProcessing}
          className="w-full sm:w-2/3 btn-primary-large text-base sm:text-lg py-4 sm:py-5 disabled:opacity-50 disabled:shadow-none disabled:cursor-not-allowed hover:disabled:translate-y-0"
          data-testid="confirm-payment"
        >
          {isProcessing ? 'Processing…' : `Confirm & Pay $${totalAmount.toFixed(2)}`}
        </button>
      </div>
    </form>
  )
}
