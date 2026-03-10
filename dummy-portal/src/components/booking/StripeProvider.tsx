import { loadStripe } from '@stripe/stripe-js'
import { Elements } from '@stripe/react-stripe-js'
import type { ReactNode } from 'react'

if (!import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY) {
  throw new Error(
    'VITE_STRIPE_PUBLISHABLE_KEY is not set. Add it to your .env file. ' +
    'Get your test key from https://dashboard.stripe.com/test/apikeys',
  )
}

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY)

interface StripeProviderProps {
  clientSecret: string
  children: ReactNode
}

export function StripeProvider({ clientSecret, children }: StripeProviderProps) {
  return (
    <Elements
      stripe={stripePromise}
      options={{
        clientSecret,
        fonts: [
          {
            cssSrc: 'https://fonts.googleapis.com/css2?family=Geom:ital,wght@0,300..900;1,300..900&display=swap',
          },
        ],
        appearance: {
          theme: 'flat',
          variables: {
            colorPrimary: '#3957d7',
            colorBackground: '#ffffff',
            colorText: '#111827',
            colorDanger: '#ef4444',
            borderRadius: '12px',
            fontFamily: 'Geom, ui-sans-serif, system-ui, sans-serif',
            fontSizeBase: '20px',
            spacingUnit: '5px',
            spacingGridRow: '20px',
            colorTextPlaceholder: '#9ca3af',
          },
          rules: {
            '.Input': {
              backgroundColor: '#f4f7fb',
              border: '1.5px solid #e5e7eb',
              padding: '12px 14px',
              transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
              fontSize: '16px',
            },
            '.Input:focus': {
              borderColor: '#3957d7',
              boxShadow: '0 0 0 3px rgba(57, 87, 215, 0.12)',
              backgroundColor: '#ffffff',
            },
            '.Input:hover': {
              borderColor: '#7097ea',
            },
            '.Label': {
              fontWeight: '600',
              fontSize: '15px',
              color: '#374151',
              marginBottom: '6px',
            },
            '.Tab': {
              borderRadius: '12px',
              border: '1.5px solid #e5e7eb',
              padding: '12px 16px',
              backgroundColor: '#f9fafb',
              transition: 'all 0.2s ease',
            },
            '.Tab:hover': {
              borderColor: '#7097ea',
              backgroundColor: '#f1f4fd',
            },
            '.Tab--selected': {
              borderColor: '#3957d7',
              backgroundColor: '#f1f4fd',
              color: '#3957d7',
              boxShadow: '0 0 0 1px #3957d7',
            },
            '.DropdownItem': {
              padding: '10px 14px',
            },
            '.DropdownItem--highlight': {
              backgroundColor: '#f1f4fd',
            },
          },
        },
      }}
    >
      {children}
    </Elements>
  )
}
