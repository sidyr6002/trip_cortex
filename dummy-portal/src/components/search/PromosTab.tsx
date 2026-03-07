import type { FlightListing } from '../../data/schema';
import { Tag } from 'lucide-react';

interface Props {
    flight: FlightListing;
}

export default function PromosTab({ flight }: Props) {
    return (
        <div className="pt-6 border-t border-divider-light mt-6 flex flex-col gap-6">
            <h4 className="font-semibold text-lg text-content">Available Promos</h4>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Mock Promo 1 */}
                <div className="border border-green-200 bg-green-50 rounded-xl p-4 flex gap-4 items-start">
                    <div className="w-10 h-10 rounded-full bg-green-100 text-green-600 flex items-center justify-center shrink-0">
                        <Tag className="w-5 h-5" />
                    </div>
                    <div className="flex-1">
                        <div className="font-bold text-green-800 text-sm mb-1 uppercase tracking-wide">FLYSMART20</div>
                        <h5 className="font-semibold text-content text-sm mb-1">Get 20% Off on your first booking</h5>
                        <p className="text-xs text-content-muted mb-3">Valid until 31 Dec 2026. Max discount US$ 50.00.</p>
                        <button className="text-sm font-medium text-green-700 hover:text-green-800 transition-colors">Apply Promo</button>
                    </div>
                </div>

                {/* Mock Promo 2 */}
                <div className="border border-divider-light bg-surface-muted/30 rounded-xl p-4 flex gap-4 items-start">
                    <div className="w-10 h-10 rounded-full bg-surface-muted text-content-muted flex items-center justify-center shrink-0">
                        <Tag className="w-5 h-5" />
                    </div>
                    <div className="flex-1">
                        <div className="font-bold text-content text-sm mb-1 uppercase tracking-wide">BANK PROMO</div>
                        <h5 className="font-semibold text-content text-sm mb-1">Save US$ 25 on {flight.airline.name}</h5>
                        <p className="text-xs text-content-muted mb-3">Minimum transaction US$ 200.00. Limited quota daily.</p>
                        <button className="text-sm font-medium text-primary hover:text-primary-hover transition-colors">Apply Promo</button>
                    </div>
                </div>
            </div>
            <p className="text-xs text-content-light">You can only apply one promo code per transaction. Terms and conditions apply.</p>
        </div>
    );
}
