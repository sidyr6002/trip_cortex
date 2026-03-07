import type { FlightListing } from '../../data/schema';

interface Props {
    flight: FlightListing;
}

export default function PriceDetailsTab({ flight }: Props) {
    const adults = 1; // Assuming 1 adult for now, this could be passed as a prop from SearchWidget state
    const child = 0;

    const basePrice = flight.pricing.pricePerPassenger;
    const taxes = basePrice * 0.12; // Mock 12% tax
    const total = basePrice + taxes;

    return (
        <div className="pt-6 border-t border-divider-light mt-6 flex flex-col lg:flex-row gap-8">
            <div className="flex-1 max-w-lg">
                <h4 className="font-semibold text-lg mb-4 text-content">Price Details</h4>

                <div className="space-y-3 mb-4">
                    <div className="flex items-center justify-between text-sm">
                        <span className="text-content-muted">Adult x {adults}</span>
                        <span className="font-medium">{flight.pricing.currency} {(basePrice * adults).toFixed(2)}</span>
                    </div>
                    {child > 0 && (
                        <div className="flex items-center justify-between text-sm">
                            <span className="text-content-muted">Child x {child}</span>
                            <span className="font-medium">{flight.pricing.currency} {(basePrice * 0.75 * child).toFixed(2)}</span>
                        </div>
                    )}
                    <div className="flex items-center justify-between text-sm">
                        <span className="text-content-muted">Taxes & Fees</span>
                        <span className="font-medium">{flight.pricing.currency} {taxes.toFixed(2)}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm text-green-600">
                        <span>Discount</span>
                        <span>- {flight.pricing.currency} 0.00</span>
                    </div>
                </div>

                <hr className="border-divider-light mb-4" />

                <div className="flex items-center justify-between">
                    <span className="font-semibold text-content">Total Price</span>
                    <span className="font-bold text-xl text-monza-500">{flight.pricing.currency} {total.toFixed(2)}</span>
                </div>

                <p className="text-xs text-content-light mt-2">* This is the final price including all applicable taxes and fees.</p>
            </div>
        </div>
    );
}
