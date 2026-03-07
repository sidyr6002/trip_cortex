import type { FlightListing } from '../../data/schema';
import { Briefcase, Utensils, MonitorPlay, Wifi, BatteryCharging, Info } from 'lucide-react';

interface Props {
    flight: FlightListing;
}

export default function FlightDetailsTab({ flight }: Props) {
    const hasFacility = (icon: string) => flight.facilities.some(f => f.iconName === icon);

    // Helper to format date "20 Aug" from "2023-08-20T08:35:00"
    const formatDate = (dateStr: string) => {
        const d = new Date(dateStr);
        return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
    };

    const formatTime = (dateStr: string) => {
        return dateStr.split('T')[1].substring(0, 5);
    };

    return (
        <div className="pt-6 border-t border-divider-light mt-6 flex flex-col lg:flex-row gap-8">
            {/* Left Column: Timeline & Details */}
            <div className="flex-1 flex gap-6">
                {/* Timeline */}
                <div className="flex flex-col items-center w-16 shrink-0 pt-1">
                    <div className="text-sm font-bold text-content">{formatTime(flight.departureTime)}</div>
                    <div className="text-xs text-content-muted mb-2">{formatDate(flight.departureTime)}</div>

                    {/* Circle */}
                    <div className="w-3 h-3 rounded-full border-2 border-primary bg-white z-10"></div>

                    {/* Line */}
                    <div className="w-px flex-1 bg-divider my-1 relative">
                        <div className="absolute top-1/2 -translate-y-1/2 -right-8 text-xs text-content-muted whitespace-nowrap bg-white py-1">
                            <span className="flex items-center gap-1">
                                <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
                                {flight.durationString}
                            </span>
                        </div>
                    </div>

                    {/* Circle */}
                    <div className="w-3 h-3 rounded-full bg-primary z-10 border-2 border-primary"></div>

                    <div className="text-sm font-bold text-content mt-2">{formatTime(flight.arrivalTime)}</div>
                    <div className="text-xs text-content-muted">{formatDate(flight.arrivalTime)}</div>
                </div>

                {/* Details */}
                <div className="flex-1 flex flex-col pb-6">
                    {/* Departure */}
                    <div className="mb-6">
                        <div className="font-semibold text-content">{flight.departureCity.name} ({flight.departureCity.code})</div>
                        <div className="text-sm text-content-muted mb-4">Terminal 3 International (Mocked)</div>

                        {/* Boxed detail */}
                        <div className="bg-surface-muted/50 rounded-xl p-4 text-sm text-content flex flex-col gap-3 border border-divider-light">
                            <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
                                {hasFacility('baggage') && <div className="flex items-center gap-2"><Briefcase className="w-4 h-4 text-content-muted" /> Cabin: 1pc, baggage: 40kg</div>}
                                {hasFacility('wifi') && <div className="flex items-center gap-2"><Wifi className="w-4 h-4 text-content-muted" /> Wifi</div>}
                                {hasFacility('meal') && <div className="flex items-center gap-2"><Utensils className="w-4 h-4 text-content-muted" /> Free In-flight meal</div>}
                                {hasFacility('power') && <div className="flex items-center gap-2"><BatteryCharging className="w-4 h-4 text-content-muted" /> Power/USB port</div>}
                                {hasFacility('entertainment') && <div className="flex items-center gap-2"><MonitorPlay className="w-4 h-4 text-content-muted" /> In-flight entertainment</div>}
                            </div>

                            <hr className="border-divider-light my-1" />

                            <div className="flex items-start justify-between gap-4">
                                <div className="flex items-start gap-2">
                                    <svg className="w-4 h-4 text-content-muted mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.2-1.1.6L3 8l6 4-4 4-2.8-.9c-.4-.1-.8.1-1 .5L1 17l4 2 2 4 .7-.1c.4-.2.6-.6.5-1L7.3 19l4-4 4 6h1.2c.4 0 .7-.4.6-.9z" /></svg>
                                    <div>
                                        <div className="text-xs text-content-muted">Model</div>
                                        <div className="font-medium">Airbus A330-300</div>
                                    </div>
                                </div>
                                <div>
                                    <div className="text-xs text-content-muted">Layout</div>
                                    <div className="font-medium">2-2-2</div>
                                </div>
                                <div className="mr-8">
                                    <div className="text-xs text-content-muted">Seat</div>
                                    <div className="font-medium">{flight.flightClass.name}</div>
                                </div>
                            </div>
                        </div>

                        <div className="mt-4 flex items-center gap-2 text-sm text-content-muted bg-surface-muted/30 px-3 py-1.5 rounded-full w-fit border border-divider-light">
                            <Info className="w-4 h-4" />
                            Flight upgrade available
                        </div>
                    </div>

                    {/* Arrival */}
                    <div className="mt-auto">
                        <div className="font-semibold text-content">{flight.arrivalCity.name} ({flight.arrivalCity.code})</div>
                        <div className="text-sm text-content-muted">Terminal 3 International (Mocked)</div>
                    </div>
                </div>
            </div>

            {/* Right Column: Fake Map */}
            <div className="w-full lg:w-72 xl:w-80 h-64 lg:h-auto rounded-2xl bg-[#e5e7eb] relative overflow-hidden border border-divider-light shrink-0">
                <div className="absolute inset-0 opacity-40 mix-blend-multiply" style={{
                    backgroundImage: `url("data:image/svg+xml,%3Csvg width='100%25' height='100%25' viewBox='0 0 800 600' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' stroke='%23ffffff' stroke-width='2' stroke-linecap='square' stroke-linejoin='bevel'%3E%3Cpath d='M100 100l200 50l50 150l-100 100Z'/%3E%3Cpath d='M400 300l100-50l150 100l-50 150Z'/%3E%3C/g%3E%3C/svg%3E")`,
                    backgroundSize: 'cover'
                }}></div>

                {/* Cities on map */}
                <div className="absolute top-1/4 left-1/3 flex flex-col items-center gap-1 z-10">
                    <div className="w-2.5 h-2.5 bg-primary rounded-full border-2 border-white shadow-sm ring-2 ring-primary/20"></div>
                    <span className="text-xs font-semibold text-content-muted drop-shadow-md">{flight.departureCity.name}</span>
                </div>

                {/* Arc path */}
                <svg className="absolute inset-0 w-full h-full z-0" style={{ pointerEvents: 'none' }}>
                    <path d="M96 64 C 150 150, 180 200, 190 220" stroke="#3957d7" strokeWidth="2" strokeDasharray="4 4" fill="none" className="opacity-60" />
                </svg>

                <div className="absolute bottom-1/4 right-1/3 flex flex-col items-center gap-1 z-10">
                    <div className="w-2.5 h-2.5 bg-white border-2 border-primary rounded-full shadow-sm ring-2 ring-primary/20"></div>
                    <span className="text-xs font-semibold text-content-muted drop-shadow-md mt-6">{flight.arrivalCity.name}</span>
                </div>

                {/* Map Controls */}
                <div className="absolute bottom-4 left-4 flex flex-col bg-white rounded-lg shadow-sm border border-divider overflow-hidden z-20">
                    <button className="w-8 h-8 flex items-center justify-center border-b border-divider text-content-muted hover:text-content hover:bg-surface-muted transition-colors">+</button>
                    <button className="w-8 h-8 flex items-center justify-center text-content-muted hover:text-content hover:bg-surface-muted transition-colors">-</button>
                </div>
            </div>
        </div>
    )
}
