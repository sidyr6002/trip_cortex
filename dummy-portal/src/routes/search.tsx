import { useState, useRef, useEffect } from 'react'
import { createFileRoute, redirect } from '@tanstack/react-router'
import { format } from 'date-fns'
import Navbar from '../components/home/Navbar'
import SearchWidget from '../components/home/search-widget/SearchWidget'
import FlightFilterSidebar, { SORT_LABELS } from '../components/search/FlightFilterSidebar'
import type { SortOption } from '../components/search/FlightFilterSidebar'
import MobileFilterBar from '../components/search/MobileFilterBar'
import DateTabs from '../components/search/DateTabs'
import FlightCard from '../components/search/FlightCard'
import { useFlightSearch } from '../hooks/useFlightSearch'

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

export const Route = createFileRoute('/search')({
    validateSearch: (search: Record<string, unknown>): SearchParams => ({
        from: search.from as string | undefined,
        to: search.to as string | undefined,
        date: search.date as string | undefined,
        returnDate: search.returnDate as string | undefined,
        tripType: search.tripType as string | undefined,
        class: search.class as string | undefined,
        adults: Number(search.adults) || 1,
        children: Number(search.children) || 0,
    }),
    beforeLoad: ({ search }) => {
        if (!search.from || !search.to || !search.date) {
            throw redirect({
                to: '/search',
                search: {
                    from: search.from || 'DEL',
                    to: search.to || 'BOM',
                    date: search.date || format(new Date(), 'yyyy-MM-dd'),
                    tripType: search.tripType || 'one-way',
                    class: search.class || 'economy',
                    ...(search.returnDate ? { returnDate: search.returnDate } : {}),
                },
            })
        }
    },
    component: SearchRoute,
})

function formatSidebarDate(dateStr: string) {
    const d = new Date(dateStr + 'T00:00:00Z');
    return d.toLocaleDateString('en-US', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
}

function SearchRoute() {
    const searchParams = Route.useSearch();
    const [sortOpen, setSortOpen] = useState(false);
    const sortRef = useRef<HTMLDivElement>(null);

    const {
        allFlights, sortedFlights,
        filters, setFilters,
        sortBy, setSortBy,
        searchError,
        isRoundTrip, activeLeg, setActiveLeg,
        selectedOutbound, setSelectedOutbound,
        effectiveFrom, effectiveTo, effectiveDate,
        isReturnLeg, classId,
        fromAirport, toAirport,
        handleFlightSelect,
    } = useFlightSearch(searchParams);

    useEffect(() => {
        const handler = (e: MouseEvent) => {
            if (sortRef.current && !sortRef.current.contains(e.target as Node)) setSortOpen(false);
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, []);

    return (
        <div className="min-h-screen bg-primary-100 font-sans text-content overflow-x-hidden">
            <Navbar simplified />

            <div className="max-w-[1400px] mx-auto px-4 pt-12 pb-6">
                <SearchWidget />
            </div>

            <div className="max-w-[1400px] mx-auto px-4 py-6">
                <div className="flex flex-col lg:flex-row gap-8 items-start">

                    {/* Left Sidebar — desktop only */}
                    <div className="hidden lg:block w-72 shrink-0 space-y-6">
                        {isRoundTrip && fromAirport && toAirport && (
                            <div className="bg-white rounded-2xl shadow-sm border border-divider-light p-5">
                                <h3 className="font-semibold text-lg flex items-center gap-2 mb-4">Your Flight</h3>
                                <div className="space-y-4 relative before:absolute before:left-3.5 before:top-8 before:bottom-8 before:w-px before:bg-divider-light">
                                    <button
                                        onClick={() => { setActiveLeg('outbound'); setSelectedOutbound(null); }}
                                        className={`flex gap-4 relative z-10 bg-white group cursor-pointer w-full text-left transition-opacity ${activeLeg === 'return' ? 'opacity-60 hover:opacity-100' : ''}`}
                                    >
                                        <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${activeLeg === 'outbound' ? 'bg-primary text-white shadow-sm shadow-primary/30' : selectedOutbound ? 'bg-green-500 text-white' : 'bg-surface-muted text-content-muted'}`}>
                                            {selectedOutbound && activeLeg !== 'outbound' ? (
                                                <svg viewBox="0 0 24 24" fill="none" className="w-3.5 h-3.5" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6L9 17l-5-5" /></svg>
                                            ) : (
                                                <svg viewBox="0 0 24 24" fill="none" className="w-3.5 h-3.5" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.2-1.1.6L3 8l6 4-4 4-2.8-.9c-.4-.1-.8.1-1 .5L1 17l4 2 2 4 .7-.1c.4-.2.6-.6.5-1L7.3 19l4-4 4 6h1.2c.4 0 .7-.4.6-.9z" /></svg>
                                            )}
                                        </div>
                                        <div>
                                            <div className="font-medium text-sm text-content-muted">{searchParams.date ? formatSidebarDate(searchParams.date) : 'Departure'}</div>
                                            <div className="font-semibold text-content mt-0.5 group-hover:text-primary transition-colors">{fromAirport.cityName} → {toAirport.cityName}</div>
                                            {selectedOutbound && (
                                                <div className="text-sm font-semibold text-green-600 mt-1">
                                                    {selectedOutbound.segments[0].airline.name} · {selectedOutbound.pricing.currency} {selectedOutbound.pricing.pricePerPassenger.toFixed(2)}/pax
                                                </div>
                                            )}
                                        </div>
                                    </button>
                                    <button
                                        onClick={() => { if (selectedOutbound) setActiveLeg('return'); }}
                                        className={`flex gap-4 relative z-10 bg-white group w-full text-left transition-opacity ${!selectedOutbound ? 'opacity-40 cursor-not-allowed' : activeLeg === 'outbound' ? 'opacity-60 hover:opacity-100 cursor-pointer' : 'cursor-pointer'}`}
                                    >
                                        <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${activeLeg === 'return' ? 'bg-primary text-white shadow-sm shadow-primary/30' : 'bg-surface-muted text-content-muted'}`}>
                                            <svg viewBox="0 0 24 24" fill="none" className="w-3.5 h-3.5" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.2-1.1.6L3 8l6 4-4 4-2.8-.9c-.4-.1-.8.1-1 .5L1 17l4 2 2 4 .7-.1c.4-.2.6-.6.5-1L7.3 19l4-4 4 6h1.2c.4 0 .7-.4.6-.9z" /></svg>
                                        </div>
                                        <div>
                                            <div className="font-medium text-sm text-content-muted">{searchParams.returnDate ? formatSidebarDate(searchParams.returnDate) : 'Return'}</div>
                                            <div className="font-semibold text-content mt-0.5 group-hover:text-primary transition-colors">{toAirport.cityName} → {fromAirport.cityName}</div>
                                            {!selectedOutbound && <div className="text-xs text-content-muted mt-1">Select outbound first</div>}
                                        </div>
                                    </button>
                                </div>
                                {selectedOutbound && (
                                    <div className="mt-4 pt-4 border-t border-divider-light">
                                        <div className="flex justify-between text-sm text-content-muted">
                                            <span>Outbound</span>
                                            <span className="font-semibold text-content">{selectedOutbound.pricing.currency} {selectedOutbound.pricing.pricePerPassenger.toFixed(2)}/pax</span>
                                        </div>
                                        {activeLeg === 'return' && <div className="text-xs text-primary mt-2 font-medium">Select a return flight to see total</div>}
                                    </div>
                                )}
                            </div>
                        )}

                        <div className="bg-white rounded-2xl shadow-sm border border-divider-light p-5">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-content-muted">Sort by:</span>
                            </div>
                            <div ref={sortRef} className="relative">
                                <button
                                    onClick={() => setSortOpen(!sortOpen)}
                                    className="font-semibold text-content flex items-center justify-between cursor-pointer group w-full"
                                >
                                    <span className="group-hover:text-primary transition-colors">{SORT_LABELS[sortBy]}</span>
                                    <svg className="w-4 h-4 text-content-muted group-hover:text-primary transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" /></svg>
                                </button>
                                {sortOpen && (
                                    <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-lg border border-divider-light z-50 py-1 overflow-hidden">
                                        {(Object.keys(SORT_LABELS) as SortOption[]).map(option => (
                                            <button
                                                key={option}
                                                onClick={() => { setSortBy(option); setSortOpen(false); }}
                                                className={`w-full text-left px-4 py-2.5 text-sm cursor-pointer transition-colors ${sortBy === option ? 'bg-primary-50 text-primary font-semibold' : 'text-content hover:bg-surface-muted'}`}
                                            >
                                                {SORT_LABELS[option]}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="bg-white rounded-2xl shadow-sm border border-divider-light p-5">
                            <FlightFilterSidebar filters={filters} onFiltersChange={setFilters} flights={allFlights} />
                        </div>
                    </div>

                    {/* Main Content Area */}
                    <div className="flex-1 w-full min-w-0">
                        <MobileFilterBar
                            filters={filters}
                            onFiltersChange={setFilters}
                            flights={allFlights}
                            sortBy={sortBy}
                            onSortChange={setSortBy}
                        />
                        <DateTabs
                            departureDate={effectiveDate}
                            from={effectiveFrom}
                            to={effectiveTo}
                            flightClass={classId}
                            isReturnLeg={isReturnLeg}
                        />
                        <div className="space-y-4">
                            {searchError ? (
                                <div className="bg-white rounded-2xl shadow-sm border border-red-100 p-12 text-center">
                                    <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-4">
                                        <svg className="w-8 h-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                                    </div>
                                    <h3 className="font-bold text-lg mb-2 text-content">Search Failed</h3>
                                    <p className="text-content-muted max-w-sm mx-auto">{searchError}</p>
                                </div>
                            ) : sortedFlights.length > 0 ? (
                                sortedFlights.map((flight) => (
                                    <FlightCard
                                        key={flight.id}
                                        flight={flight}
                                        adults={searchParams.adults || 1}
                                        children={searchParams.children || 0}
                                        onSelect={handleFlightSelect}
                                    />
                                ))
                            ) : (
                                <div className="bg-white rounded-2xl shadow-sm border border-divider-light p-12 text-center">
                                    <div className="w-16 h-16 bg-surface-muted rounded-full flex items-center justify-center mx-auto mb-4 text-content-muted">
                                        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                                    </div>
                                    <h3 className="font-bold text-lg mb-2">No Flights Found</h3>
                                    <p className="text-content-muted max-w-sm mx-auto">We couldn't find any flights matching your criteria. Try adjusting your filters or dates.</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
