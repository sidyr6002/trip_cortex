import { createFileRoute } from '@tanstack/react-router'
import Navbar from '../components/home/Navbar'
import SearchWidget from '../components/home/SearchWidget'
import FlightFilterSidebar from '../components/search/FlightFilterSidebar'
import DateTabs from '../components/search/DateTabs'
import FlightCard from '../components/search/FlightCard'
import { searchFlights } from '../data/searchFlights'
import { getClassIdByName } from '../data/helpers'

interface SearchParams {
    from?: string;
    to?: string;
    date?: string;
    class?: string;
}

export const Route = createFileRoute('/search')({
    validateSearch: (search: Record<string, unknown>): SearchParams => {
        return {
            from: search.from as string | undefined,
            to: search.to as string | undefined,
            date: search.date as string | undefined,
            class: search.class as string | undefined,
        }
    },
    component: SearchRoute,
})

function SearchRoute() {
    const searchParams = Route.useSearch();
    
    const classId = searchParams.class ? getClassIdByName(searchParams.class) : undefined;

    const flights = searchFlights({
        originAirportCode: searchParams.from,
        destinationAirportCode: searchParams.to,
        departureDate: searchParams.date,
        classId,
    });

    return (
        <div className="min-h-screen bg-surface-gradient font-sans text-content overflow-x-hidden">
            <Navbar simplified />

            <div className="max-w-[1400px] mx-auto px-4 pt-12 pb-6">
                <SearchWidget />
            </div>

            <div className="max-w-[1400px] mx-auto px-4 py-6">
                <div className="flex flex-col lg:flex-row gap-8 items-start">

                    {/* Left Sidebar */}
                    <div className="w-full lg:w-72 shrink-0 space-y-6">
                        {/* Your Flight Summary Widget (mock visual) */}
                        <div className="bg-white rounded-2xl shadow-sm border border-divider-light p-5">
                            <h3 className="font-semibold text-lg flex items-center gap-2 mb-4">
                                Your Flight
                            </h3>
                            <div className="space-y-4 relative before:absolute before:left-3.5 before:top-8 before:bottom-8 before:w-px before:bg-divider-light">
                                <div className="flex gap-4 relative z-10 bg-white group cursor-pointer">
                                    <div className="w-7 h-7 bg-primary rounded-full flex items-center justify-center text-white shrink-0 mt-0.5 shadow-sm shadow-primary/30">
                                        <svg viewBox="0 0 24 24" fill="none" className="w-3.5 h-3.5" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.2-1.1.6L3 8l6 4-4 4-2.8-.9c-.4-.1-.8.1-1 .5L1 17l4 2 2 4 .7-.1c.4-.2.6-.6.5-1L7.3 19l4-4 4 6h1.2c.4 0 .7-.4.6-.9z" /></svg>
                                    </div>
                                    <div>
                                        <div className="font-medium text-sm text-content-muted">Sun, 20 Aug 2023</div>
                                        <div className="font-semibold text-content mt-0.5 group-hover:text-primary transition-colors">Jakarta → Singapore</div>
                                    </div>
                                </div>
                                <div className="flex gap-4 relative z-10 bg-white group cursor-pointer opacity-60 hover:opacity-100 transition-opacity">
                                    <div className="w-7 h-7 bg-surface-muted rounded-full flex items-center justify-center text-content-muted shrink-0 mt-0.5">
                                        <svg viewBox="0 0 24 24" fill="none" className="w-3.5 h-3.5" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.2-1.1.6L3 8l6 4-4 4-2.8-.9c-.4-.1-.8.1-1 .5L1 17l4 2 2 4 .7-.1c.4-.2.6-.6.5-1L7.3 19l4-4 4 6h1.2c.4 0 .7-.4.6-.9z" /></svg>
                                    </div>
                                    <div>
                                        <div className="font-medium text-sm text-content-muted">Mon, 21 Aug 2023</div>
                                        <div className="font-semibold text-content mt-0.5 group-hover:text-primary transition-colors">Singapore → Jakarta</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="bg-white rounded-2xl shadow-sm border border-divider-light p-5">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-content-muted">Sort by:</span>
                            </div>
                            <div className="font-semibold text-content flex items-center justify-between cursor-pointer group">
                                <span className="group-hover:text-primary transition-colors">Direct Flight First</span>
                                <svg className="w-4 h-4 text-content-muted group-hover:text-primary transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" /></svg>
                            </div>
                        </div>

                        <div className="bg-white rounded-2xl shadow-sm border border-divider-light p-5">
                            <FlightFilterSidebar />
                        </div>
                    </div>

                    {/* Main Content Area */}
                    <div className="flex-1 w-full min-w-0">
                        <DateTabs
                            departureDate={searchParams.date}
                            from={searchParams.from}
                            to={searchParams.to}
                            flightClass={classId}
                        />

                        <div className="space-y-4">
                            {flights.length > 0 ? flights.map((flight) => (
                                <FlightCard key={flight.id} flight={flight} />
                            )) : (
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
