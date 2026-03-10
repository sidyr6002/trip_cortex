import { ChevronUp } from 'lucide-react';
import type { FlightListing } from '../../data/schema';
import { FACILITY_TABLE } from '../../data/mockData';
import { Slider } from '../ui/slider';

export type TransitFilter = 'Direct' | '1 transit' | '2+ transit';
export type SortOption = 'price-asc' | 'price-desc' | 'duration-asc' | 'departure-asc' | 'direct-first';

export const SORT_LABELS: Record<SortOption, string> = {
    'direct-first': 'Direct Flight First',
    'price-asc': 'Lowest Price',
    'price-desc': 'Highest Price',
    'duration-asc': 'Shortest Duration',
    'departure-asc': 'Earliest Departure',
};

export interface FilterState {
    transitTypes: TransitFilter[];
    priceRange: [number, number];
    facilities: string[]; // facility IDs
}

interface Props {
    filters: FilterState;
    onFiltersChange: (filters: FilterState) => void;
    flights: FlightListing[]; // unfiltered flights to derive available options
}

export default function FlightFilterSidebar({ filters, onFiltersChange, flights }: Props) {
    // Exclude sold-out flights from all derived filter values
    const bookableFlights = flights.filter(f => f.status !== 'sold-out');

    // Derive which transit types exist in the current flight results
    const availableTransitTypes = new Set(bookableFlights.map(f => f.transitType));

    // Derive price range from flights
    const prices = bookableFlights.map(f => f.pricing.pricePerPassenger);
    const minPrice = prices.length > 0 ? Math.min(...prices) : 0;
    const maxPrice = prices.length > 0 ? Math.max(...prices) : 0;

    // Derive which facilities exist across all flights
    const availableFacilityIds = new Set(
        bookableFlights.flatMap(f => f.segments.flatMap(s => s.facilities.map(fac => fac.id)))
    );

    // Get cheapest price per transit type
    const cheapestByTransit: { [key: string]: number | undefined } = {};
    for (const f of bookableFlights) {
        const current = cheapestByTransit[f.transitType];
        if (current === undefined || f.pricing.pricePerPassenger < current) {
            cheapestByTransit[f.transitType] = f.pricing.pricePerPassenger;
        }
    }

    const transitOptions: { value: TransitFilter; label: string }[] = [
        { value: 'Direct', label: 'Direct Flight' },
        { value: '1 transit', label: '1 transit(s)' },
        { value: '2+ transit', label: '2+ transit(s)' },
    ];

    const toggleTransit = (type: TransitFilter) => {
        const current = filters.transitTypes;
        const next = current.includes(type)
            ? current.filter(t => t !== type)
            : [...current, type];
        onFiltersChange({ ...filters, transitTypes: next });
    };

    const toggleFacility = (facilityId: string) => {
        const current = filters.facilities;
        const next = current.includes(facilityId)
            ? current.filter(id => id !== facilityId)
            : [...current, facilityId];
        onFiltersChange({ ...filters, facilities: next });
    };

    const resetFilters = () => {
        onFiltersChange({
            transitTypes: [],
            priceRange: [minPrice, maxPrice],
            facilities: [],
        });
    };

    const formatPrice = (p: number) => `US$ ${p.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

    return (
        <div className="w-full shrink-0 lg:w-64 flex flex-col gap-6">
            <div className="flex items-center justify-between">
                <h3 className="font-semibold text-lg">Filter</h3>
                <button onClick={resetFilters} className="text-primary text-sm font-medium hover:underline cursor-pointer">Reset</button>
            </div>

            {/* Transit */}
            <div className="border-t border-divider-light pt-4">
                <div className="flex items-center justify-between mb-4 cursor-pointer">
                    <span className="font-medium text-sm text-content-muted">No. of Transit</span>
                    <ChevronUp className="w-4 h-4 text-content-muted" />
                </div>
                <div className="flex flex-col gap-3">
                    {transitOptions.map(opt => {
                        const isAvailable = availableTransitTypes.has(opt.value);
                        const isChecked = filters.transitTypes.includes(opt.value);
                        const cheapest = cheapestByTransit[opt.value];
                        return (
                            <label key={opt.value} className={`flex items-center justify-between group ${isAvailable ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'}`}>
                                <div className="flex items-center gap-3">
                                    <input
                                        type="checkbox"
                                        checked={isChecked}
                                        disabled={!isAvailable}
                                        onChange={() => toggleTransit(opt.value)}
                                        className="w-4 h-4 rounded text-primary focus:ring-primary border-divider cursor-pointer disabled:cursor-not-allowed"
                                    />
                                    <span className={`text-sm font-medium ${isAvailable ? 'text-content' : 'text-content-lighter'}`}>{opt.label}</span>
                                </div>
                                {cheapest !== undefined && (
                                    <span className="text-xs text-content-light">{formatPrice(cheapest)}</span>
                                )}
                            </label>
                        );
                    })}
                </div>
            </div>

            {/* Price */}
            <div className="border-t border-divider-light pt-4">
                <div className="flex items-center justify-between mb-2 cursor-pointer">
                    <span className="font-medium text-sm text-content-muted">Price/passenger</span>
                    <ChevronUp className="w-4 h-4 text-content-muted" />
                </div>
                <div className="mb-4">
                    <span className="text-sm font-semibold">{formatPrice(filters.priceRange[0])} - {formatPrice(filters.priceRange[1])}</span>
                </div>
                <div className="px-1">
                    <Slider
                        min={minPrice}
                        max={maxPrice}
                        step={1}
                        value={[filters.priceRange[0], filters.priceRange[1]]}
                        onValueChange={([low, high]) => onFiltersChange({ ...filters, priceRange: [low, high] })}
                    />
                </div>
                <div className="flex justify-between text-xs text-content-light mt-1">
                    <span>{formatPrice(minPrice)}</span>
                    <span>{formatPrice(maxPrice)}</span>
                </div>
            </div>

            {/* Facility */}
            <div className="border-t border-divider-light pt-4">
                <div className="flex items-center justify-between mb-4 cursor-pointer">
                    <span className="font-medium text-sm text-content-muted">Facility</span>
                    <ChevronUp className="w-4 h-4 text-content-muted" />
                </div>
                <div className="flex flex-col gap-3">
                    {FACILITY_TABLE.map(fac => {
                        const isAvailable = availableFacilityIds.has(fac.id);
                        const isChecked = filters.facilities.includes(fac.id);
                        return (
                            <label key={fac.id} className={`flex items-center justify-between group ${isAvailable ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'}`}>
                                <div className="flex items-center gap-3">
                                    <input
                                        type="checkbox"
                                        checked={isChecked}
                                        disabled={!isAvailable}
                                        onChange={() => toggleFacility(fac.id)}
                                        className="w-4 h-4 rounded text-primary focus:ring-primary border-divider cursor-pointer disabled:cursor-not-allowed"
                                    />
                                    <span className={`text-sm font-medium ${isAvailable ? 'text-content' : 'text-content-lighter'}`}>{fac.name}</span>
                                </div>
                            </label>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
