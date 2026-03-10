import type { FlightListing } from '../../data/schema';
import { formatDuration, formatDateShort, formatTime } from '../../lib/dateUtils';
import { hasFacility } from '../../lib/flightUtils';
import { Briefcase, Utensils, MonitorPlay, Wifi, BatteryCharging, Info, Clock } from 'lucide-react';
import { FlightRouteMap } from './FlightRouteMap';

interface Props {
    flight: FlightListing;
}

export default function FlightDetailsTab({ flight }: Props) {

    // Build ordered airports array for the route map
    const routeAirports = [];
    for (const seg of flight.segments) {
        if (routeAirports.length === 0 ||
            routeAirports[routeAirports.length - 1].code !== seg.departureAirport.code) {
            routeAirports.push(seg.departureAirport);
        }
    }
    const lastSeg = flight.segments[flight.segments.length - 1];
    routeAirports.push(lastSeg.arrivalAirport);

    return (
        <div className="pt-6 border-t border-divider-light mt-6 flex flex-col lg:flex-row gap-8">
            {/* Left Column: Timeline with segments & layovers */}
            <div className="flex-1 flex gap-6">
                <div className="flex flex-col items-center w-16 shrink-0 pt-1">
                    {flight.segments.map((seg, idx) => (
                        <div key={seg.id} className="flex flex-col items-center w-full">
                            {/* Departure time */}
                            <div className="text-sm font-bold text-content">{formatTime(seg.departureTime)}</div>
                            <div className="text-xs text-content-muted mb-2">{formatDateShort(seg.departureTime)}</div>
                            <div className="w-3 h-3 rounded-full border-2 border-primary bg-white z-10"></div>

                            {/* Line with duration */}
                            <div className="w-px flex-1 bg-divider my-1 relative min-h-[80px]">
                                <div className="absolute top-1/2 -translate-y-1/2 -right-8 text-xs text-content-muted whitespace-nowrap bg-white py-1">
                                    <span className="flex items-center gap-1">
                                        <Clock className="w-3 h-3" />
                                        {formatDuration(seg.durationMinutes)}
                                    </span>
                                </div>
                            </div>

                            {/* Arrival circle */}
                            <div className="w-3 h-3 rounded-full bg-primary z-10 border-2 border-primary"></div>
                            <div className="text-sm font-bold text-content mt-2">{formatTime(seg.arrivalTime)}</div>
                            <div className="text-xs text-content-muted">{formatDateShort(seg.arrivalTime)}</div>

                            {/* Layover indicator between segments */}
                            {idx < flight.layovers.length && (
                                <div className="my-3 flex flex-col items-center">
                                    <div className="w-px h-4 bg-amber-400 border-dashed"></div>
                                    <div className="text-[10px] text-amber-600 font-medium whitespace-nowrap">
                                        {formatDuration(flight.layovers[idx].durationMinutes)}
                                    </div>
                                    <div className="w-px h-4 bg-amber-400 border-dashed"></div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>

                {/* Details column */}
                <div className="flex-1 flex flex-col pb-6 gap-6">
                    {flight.segments.map((seg, idx) => (
                        <div key={seg.id}>
                            {/* Departure */}
                            <div className="mb-4">
                                <div className="font-semibold text-content">{seg.departureAirport.name} ({seg.departureAirport.code})</div>
                                <div className="text-sm text-content-muted mb-3">Terminal (Mocked)</div>

                                <div className="bg-surface-muted/50 rounded-xl p-4 text-sm text-content flex flex-col gap-3 border border-divider-light">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="font-semibold">{seg.airline.name}</span>
                                        <span className="text-content-muted">·</span>
                                        <span className="text-content-muted">{seg.flightNumber}</span>
                                    </div>
                                    <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
                                        {hasFacility(seg, 'baggage') && <div className="flex items-center gap-2"><Briefcase className="w-4 h-4 text-content-muted" /> Cabin: 1pc, baggage: 40kg</div>}
                                        {hasFacility(seg, 'wifi') && <div className="flex items-center gap-2"><Wifi className="w-4 h-4 text-content-muted" /> Wifi</div>}
                                        {hasFacility(seg, 'meal') && <div className="flex items-center gap-2"><Utensils className="w-4 h-4 text-content-muted" /> Free In-flight meal</div>}
                                        {hasFacility(seg, 'power') && <div className="flex items-center gap-2"><BatteryCharging className="w-4 h-4 text-content-muted" /> Power/USB port</div>}
                                        {hasFacility(seg, 'entertainment') && <div className="flex items-center gap-2"><MonitorPlay className="w-4 h-4 text-content-muted" /> In-flight entertainment</div>}
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
                                            <div className="text-xs text-content-muted">Seat</div>
                                            <div className="font-medium">{flight.flightClass.name}</div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Arrival */}
                            <div>
                                <div className="font-semibold text-content">{seg.arrivalAirport.name} ({seg.arrivalAirport.code})</div>
                                <div className="text-sm text-content-muted">Terminal (Mocked)</div>
                            </div>

                            {/* Layover banner */}
                            {idx < flight.layovers.length && (
                                <div className="mt-4 flex items-center gap-2 text-sm text-amber-700 bg-amber-50 px-4 py-2.5 rounded-xl border border-amber-200">
                                    <Clock className="w-4 h-4" />
                                    Layover in {flight.layovers[idx].airport.cityName}: {formatDuration(flight.layovers[idx].durationMinutes)}
                                </div>
                            )}
                        </div>
                    ))}

                    {flight.segments.length === 1 && (
                        <div className="flex items-center gap-2 text-sm text-content-muted bg-surface-muted/30 px-3 py-1.5 rounded-full w-fit border border-divider-light">
                            <Info className="w-4 h-4" />
                            Flight upgrade available
                        </div>
                    )}
                </div>
            </div>

            {/* Right Column: Interactive Route Map */}
            <div className="w-full lg:w-72 xl:w-80 h-64 lg:h-auto shrink-0">
                <FlightRouteMap airports={routeAirports} />
            </div>
        </div>
    );
}
