import { createServerFn } from '@tanstack/react-start'
import { z } from 'zod'
import Stripe from 'stripe'

const PaymentIntentInput = z.object({
  amount: z.number().int().positive(),
  currency: z.string().default('usd'),
})

export const createPaymentIntent = createServerFn({ method: 'POST' })
  .inputValidator(PaymentIntentInput)
  .handler(async ({ data }) => {
    if (!process.env.STRIPE_SECRET_KEY) {
      throw new Error(
        'STRIPE_SECRET_KEY is not set. Add it to your .env file. ' +
        'Get your test key from https://dashboard.stripe.com/test/apikeys',
      )
    }

    const stripe = new Stripe(process.env.STRIPE_SECRET_KEY)

    const paymentIntent = await stripe.paymentIntents.create({
      amount: data.amount,
      currency: data.currency,
      automatic_payment_methods: { enabled: true },
    })

    return { clientSecret: paymentIntent.client_secret! }
  })
