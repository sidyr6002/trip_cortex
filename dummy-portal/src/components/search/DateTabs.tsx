import { useState } from 'react';
import { ChevronLeft, ChevronRight, Calendar } from 'lucide-react';
import { useNavigate } from '@tanstack/react-router';
import { cn } from "../../lib/utils";
import { searchFlights } from '../../data/searchFlights';

interface DateTabsProps {
    departureDate?: string;
    from?: string;
    to?: string;
    flightClass?: string;
    isReturnLeg?: boolean;
}

function buildDateRange(center: Date, offset: number) {
    return Array.from({ length: 7 }, (_, i) => {
        const d = new Date(center);
        d.setUTCDate(d.getUTCDate() + (i - 3) + offset);
        return d;
    });
}

function formatDate(d: Date) {
    return d.toLocaleDateString('en-US', {
        weekday: 'short', day: 'numeric', month: 'short', timeZone: 'UTC',
    });
}

function toISODate(d: Date) {
    return d.toISOString().split('T')[0];
}

function getCheapestPrice(date: string, from?: string, to?: string, classId?: string): number | null {
    const flights = searchFlights({
        originAirportCode: from,
        destinationAirportCode: to,
        departureDate: date,
        classId,
    });
    if (flights.length === 0) return null;
    return Math.min(...flights.map(f => f.pricing.pricePerPassenger));
}

function formatPrice(price: number | null, currency = 'USD'): string {
    if (price === null) return '—';
    return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(price);
}

export default function DateTabs({ departureDate, from, to, flightClass, isReturnLeg = false }: DateTabsProps) {
    const [offset, setOffset] = useState(0);
    const navigate = useNavigate();
    const center = departureDate ? new Date(departureDate + 'T00:00:00Z') : new Date();
    const dates = buildDateRange(center, offset);

    const handleDateClick = (iso: string) => {
        // When viewing return leg, update returnDate; otherwise update date
        const paramKey = isReturnLeg ? 'returnDate' : 'date';
        navigate({
            to: '/search',
            search: (prev: Record<string, unknown>) => ({ ...prev, [paramKey]: iso }),
        });
    };

    return (
        <div className="flex items-center gap-2 bg-white rounded-2xl p-2 shadow-sm border border-divider-light w-full mb-6 overflow-x-auto overflow-y-hidden" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
            <style dangerouslySetInnerHTML={{
                __html: `.date-tabs-container::-webkit-scrollbar { display: none; }`
            }} />
            <button
                onClick={() => setOffset(o => o - 7)}
                className="w-10 h-10 shrink-0 rounded-full border border-divider-light flex flex-col items-center justify-center hover:bg-surface-muted transition-colors ml-2 cursor-pointer"
            >
                <ChevronLeft className="w-4 h-4 text-content-muted" />
            </button>
            <div className="flex-1 flex items-center justify-between min-w-max gap-2 px-2 date-tabs-container">
                {dates.map((d) => {
                    const iso = toISODate(d);
                    const active = iso === departureDate;
                    const price = getCheapestPrice(iso, from, to, flightClass);
                    return (
                        <button
                            key={iso}
                            onClick={() => handleDateClick(iso)}
                            className={cn(
                                "flex flex-col items-center justify-center py-2 px-4 rounded-xl transition-colors shrink-0 cursor-pointer",
                                active ? "bg-primary-50 border border-primary-100" : "hover:bg-surface-muted border border-transparent"
                            )}
                        >
                            <span className={cn("text-sm mb-1 font-medium", active ? "text-content" : "text-content-muted")}>{formatDate(d)}</span>
                            <span className={cn("text-xs font-semibold", active ? "text-primary" : "text-content-light")}>{formatPrice(price)}</span>
                        </button>
                    );
                })}
            </div>
            <button
                onClick={() => setOffset(o => o + 7)}
                className="w-10 h-10 shrink-0 rounded-full border border-divider-light flex items-center justify-center hover:bg-surface-muted transition-colors mr-2 cursor-pointer"
            >
                <ChevronRight className="w-4 h-4 text-content-muted" />
            </button>
            <button className="w-10 h-10 shrink-0 rounded-full border border-divider-light text-primary flex items-center justify-center hover:bg-primary-50 transition-colors mr-2 shadow-sm cursor-pointer">
                <Calendar className="w-4 h-4" />
            </button>
        </div>
    );
}
