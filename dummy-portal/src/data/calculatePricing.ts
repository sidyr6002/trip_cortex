import type { FlightListing } from './schema';
import { TAX_RATE } from './helpers';

export interface PricingBreakdown {
  outboundSubtotal: number;
  returnSubtotal: number;
  subtotal: number;
  taxes: number;
  total: number;
}

export function calculatePricing(
  flight: FlightListing,
  adults: number,
  children: number,
  returnFlight?: FlightListing | null,
): PricingBreakdown {
  const totalPassengers = adults + children;
  const outboundSubtotal = flight.pricing.pricePerPassenger * totalPassengers;
  const returnSubtotal = returnFlight ? returnFlight.pricing.pricePerPassenger * totalPassengers : 0;
  const subtotal = outboundSubtotal + returnSubtotal;
  const taxes = subtotal * TAX_RATE;
  return { outboundSubtotal, returnSubtotal, subtotal, taxes, total: subtotal + taxes };
}
