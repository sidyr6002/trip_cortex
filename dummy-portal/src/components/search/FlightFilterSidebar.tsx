import { ChevronUp } from 'lucide-react';

export default function FlightFilterSidebar() {
    return (
        <div className="w-full shrink-0 lg:w-64 flex flex-col gap-6">
            <div className="flex items-center justify-between">
                <h3 className="font-semibold text-lg">Filter</h3>
                <button className="text-primary text-sm font-medium hover:underline cursor-pointer">Reset</button>
            </div>

            {/* Transit */}
            <div className="border-t border-divider-light pt-4">
                <div className="flex items-center justify-between mb-4 cursor-pointer">
                    <span className="font-medium text-sm text-content-muted">No. of Transit</span>
                    <ChevronUp className="w-4 h-4 text-content-muted" />
                </div>
                <div className="flex flex-col gap-3">
                    <label className="flex items-center justify-between group cursor-pointer">
                        <div className="flex items-center gap-3">
                            <input type="checkbox" defaultChecked className="w-4 h-4 rounded text-primary focus:ring-primary border-divider cursor-pointer" />
                            <span className="text-sm font-medium text-content">Direct Flight</span>
                        </div>
                        <span className="text-xs text-content-light">US$ 26.88</span>
                    </label>
                    <label className="flex items-center justify-between group cursor-pointer">
                        <div className="flex items-center gap-3">
                            <input type="checkbox" className="w-4 h-4 rounded text-primary focus:ring-primary border-divider cursor-pointer" />
                            <span className="text-sm font-medium text-content-light">1 transit(s)</span>
                        </div>
                        <span className="text-xs text-content-light">US$ 26.88</span>
                    </label>
                    <label className="flex items-center justify-between group cursor-pointer">
                        <div className="flex items-center gap-3">
                            <input type="checkbox" className="w-4 h-4 rounded text-primary focus:ring-primary border-divider cursor-pointer" />
                            <span className="text-sm font-medium text-content-light">2+ transit(s)</span>
                        </div>
                        <span className="text-xs text-content-light">US$ 26.88</span>
                    </label>
                </div>
            </div>

            {/* Price */}
            <div className="border-t border-divider-light pt-4">
                <div className="flex items-center justify-between mb-2 cursor-pointer">
                    <span className="font-medium text-sm text-content-muted">Price/passenger</span>
                    <ChevronUp className="w-4 h-4 text-content-muted" />
                </div>
                <div className="mb-4">
                    <span className="text-sm font-semibold">US$ 26.88 - US$ 1,841.63</span>
                </div>
                <div className="relative h-1 bg-divider rounded-full mt-4 mb-2">
                    <div className="absolute left-[5%] right-[20%] h-full bg-monza-400 rounded-full"></div>
                    <div className="absolute left-[5%] top-1/2 -translate-y-1/2 w-3 h-3 bg-white border-2 border-monza-400 rounded-full shadow cursor-pointer"></div>
                    <div className="absolute right-[20%] top-1/2 -translate-y-1/2 w-3 h-3 bg-white border-2 border-monza-400 rounded-full shadow cursor-pointer"></div>
                </div>
                <div className="flex justify-between text-xs text-content-light">
                    <span>US$26.88</span>
                    <span>US$1,841.63</span>
                </div>
            </div>

            {/* Facility */}
            <div className="border-t border-divider-light pt-4">
                <div className="flex items-center justify-between mb-4 cursor-pointer">
                    <span className="font-medium text-sm text-content-muted">Facility</span>
                    <ChevronUp className="w-4 h-4 text-content-muted" />
                </div>
                <div className="flex flex-col gap-3">
                    {['Baggage', 'In-flight meal', 'In-flight entertainment', 'Wifi', 'Power/USB port'].map(fac => (
                        <label key={fac} className="flex items-center justify-between group cursor-pointer">
                            <div className="flex items-center gap-3">
                                <input type="checkbox" className="w-4 h-4 rounded text-primary focus:ring-primary border-divider cursor-pointer" />
                                <span className="text-sm font-medium text-content-light">{fac}</span>
                            </div>
                        </label>
                    ))}
                </div>
            </div>
        </div>
    )
}
