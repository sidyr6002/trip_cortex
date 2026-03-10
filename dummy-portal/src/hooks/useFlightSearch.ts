import { useState, useMemo, useEffect } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { searchFlights } from '../data/searchFlights';
import { getClassIdByName, getAirportByCode } from '../data/helpers';
import type { FlightListing } from '../data/schema';
import type { FilterState, SortOption } from '../components/search/FlightFilterSidebar';
import { DEFAULT_SORT } from '../constants';

interface SearchParams {
    from?: string;
    to?: string;
    date?: string;
    returnDate?: string;
    tripType?: string;
    class?: string;
    adults?: number;
    children?: number;
}

function applyFilters(flights: FlightListing[], filters: FilterState): FlightListing[] {
    return flights.filter(f => {
        if (filters.transitTypes.length > 0 && !filters.transitTypes.includes(f.transitType as any)) return false;
        if (f.pricing.pricePerPassenger < filters.priceRange[0] || f.pricing.pricePerPassenger > filters.priceRange[1]) return false;
        if (filters.facilities.length > 0) {
            const ids = new Set(f.segments.flatMap(s => s.facilities.map(fac => fac.id)));
            if (!filters.facilities.every(id => ids.has(id))) return false;
        }
        return true;
    });
}

function applySorting(flights: FlightListing[], sort: SortOption): FlightListing[] {
    return [...flights].sort((a, b) => {
        if (a.status === 'sold-out' && b.status !== 'sold-out') return 1;
        if (a.status !== 'sold-out' && b.status === 'sold-out') return -1;
        switch (sort) {
            case 'price-asc': return a.pricing.pricePerPassenger - b.pricing.pricePerPassenger;
            case 'price-desc': return b.pricing.pricePerPassenger - a.pricing.pricePerPassenger;
            case 'duration-asc': return a.totalDurationMinutes - b.totalDurationMinutes;
            case 'departure-asc': return a.segments[0].departureTime.localeCompare(b.segments[0].departureTime);
            case 'direct-first': {
                const order: Record<string, number> = { 'Direct': 0, '1 transit': 1, '2+ transit': 2 };
                return (order[a.transitType] ?? 9) - (order[b.transitType] ?? 9) || a.pricing.pricePerPassenger - b.pricing.pricePerPassenger;
            }
            default: return 0;
        }
    });
}

export function useFlightSearch(searchParams: SearchParams) {
    const navigate = useNavigate();
    const isRoundTrip = searchParams.tripType === 'round-trip';
    const [activeLeg, setActiveLeg] = useState<'outbound' | 'return'>('outbound');
    const [selectedOutbound, setSelectedOutbound] = useState<FlightListing | null>(null);
    const [sortBy, setSortBy] = useState<SortOption>(DEFAULT_SORT);
    const [searchError, setSearchError] = useState<string | null>(null);

    const classId = searchParams.class ? getClassIdByName(searchParams.class) : undefined;
    const isReturnLeg = isRoundTrip && activeLeg === 'return';

    const effectiveFrom = isReturnLeg ? searchParams.to : searchParams.from;
    const effectiveTo = isReturnLeg ? searchParams.from : searchParams.to;
    const effectiveDate = isReturnLeg ? searchParams.returnDate : searchParams.date;

    const allFlights = useMemo(() => {
        try {
            setSearchError(null);
            return searchFlights({
                originAirportCode: effectiveFrom,
                destinationAirportCode: effectiveTo,
                departureDate: effectiveDate,
                classId,
                excludeSoldOut: false,
            });
        } catch {
            setSearchError('Failed to load flights. Please try again.');
            return [] as FlightListing[];
        }
    }, [effectiveFrom, effectiveTo, effectiveDate, classId]);

    const prices = allFlights.map(f => f.pricing.pricePerPassenger);
    const minPrice = prices.length > 0 ? Math.min(...prices) : 0;
    const maxPrice = prices.length > 0 ? Math.max(...prices) : 0;

    const [filters, setFilters] = useState<FilterState>({
        transitTypes: [],
        priceRange: [minPrice, maxPrice],
        facilities: [],
    });

    useEffect(() => {
        setFilters({ transitTypes: [], priceRange: [minPrice, maxPrice], facilities: [] });
    }, [minPrice, maxPrice]);

    const filteredFlights = useMemo(() => applyFilters(allFlights, filters), [allFlights, filters]);
    const sortedFlights = useMemo(() => applySorting(filteredFlights, sortBy), [filteredFlights, sortBy]);

    const fromAirport = searchParams.from ? getAirportByCode(searchParams.from) : undefined;
    const toAirport = searchParams.to ? getAirportByCode(searchParams.to) : undefined;

    const handleFlightSelect = (flight: FlightListing) => {
        if (isRoundTrip && activeLeg === 'outbound') {
            setSelectedOutbound(flight);
            setActiveLeg('return');
        } else if (isRoundTrip && activeLeg === 'return' && selectedOutbound) {
            navigate({
                to: '/book/$flightId',
                params: { flightId: selectedOutbound.id },
                search: { adults: searchParams.adults || 1, children: searchParams.children || 0, returnFlightId: flight.id },
            });
        } else {
            navigate({
                to: '/book/$flightId',
                params: { flightId: flight.id },
                search: { adults: searchParams.adults || 1, children: searchParams.children || 0 },
            });
        }
    };

    return {
        allFlights,
        sortedFlights,
        filters,
        setFilters,
        sortBy,
        setSortBy,
        searchError,
        isRoundTrip,
        activeLeg,
        setActiveLeg,
        selectedOutbound,
        setSelectedOutbound,
        effectiveFrom,
        effectiveTo,
        effectiveDate,
        isReturnLeg,
        classId,
        fromAirport,
        toAirport,
        handleFlightSelect,
    };
}
