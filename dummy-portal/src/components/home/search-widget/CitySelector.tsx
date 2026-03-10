import { PlaneTakeoff, PlaneLanding, ArrowRightLeft } from 'lucide-react';
import { cn } from '../../../lib/utils';
import { Popover, PopoverContent, PopoverTrigger } from '../../ui/popover';
import { AIRPORT_TABLE } from '../../../data/mockData';
import type { Airport } from '../../../data/schema';

interface CitySelectorProps {
    departure: Airport;
    arrival: Airport;
    onDepartureChange: (a: Airport) => void;
    onArrivalChange: (a: Airport) => void;
    open: 'departure' | 'arrival' | null;
    onOpenChange: (v: 'departure' | 'arrival' | null) => void;
    onSwap: () => void;
}

export default function CitySelector({ departure, arrival, onDepartureChange, onArrivalChange, open, onOpenChange, onSwap }: CitySelectorProps) {
    return (
        <div className="flex flex-col lg:flex-row items-stretch w-full lg:flex-[1_1_0%] lg:max-w-[600px] bg-white/70 rounded-2xl shadow-sm border border-divider hover:border-primary-outline/50 hover:bg-white hover:shadow-md transition-all duration-300">
            <div className="flex-1 min-w-0">
                <Popover open={open === 'departure'} onOpenChange={(o) => onOpenChange(o ? 'departure' : null)}>
                    <PopoverTrigger asChild>
                        <div className="flex items-center gap-4 p-4 lg:p-5 w-full cursor-pointer h-[72px] rounded-t-2xl lg:rounded-none lg:rounded-l-2xl hover:bg-primary-50/40 transition-colors">
                            <div className="bg-primary-50 w-10 h-10 rounded-full shrink-0 flex items-center justify-center">
                                <PlaneTakeoff className="w-5 h-5 text-primary-light" />
                            </div>
                            <div className="flex flex-col items-start min-w-0 text-left">
                                <span className="text-xs text-content-light mb-0.5 whitespace-nowrap">From</span>
                                <span className="font-semibold text-content text-sm truncate w-full">{departure.cityName}</span>
                                <span className="text-xs text-content-muted truncate w-full">{departure.code} · {departure.name}</span>
                            </div>
                        </div>
                    </PopoverTrigger>
                    <PopoverContent className="w-80 p-2 rounded-2xl" align="start" onOpenAutoFocus={(e) => e.preventDefault()}>
                        <div className="max-h-80 overflow-y-auto flex flex-col gap-1">
                            {AIRPORT_TABLE.map((airport) => (
                                <button
                                    key={airport.id}
                                    className={cn('w-full outline-none px-4 py-3 text-left rounded-xl transition-all duration-200 hover:bg-primary-50 focus:bg-primary-50 cursor-pointer', departure.id === airport.id ? 'bg-primary-50' : '')}
                                    onClick={() => { onDepartureChange(airport); onOpenChange(null); }}
                                >
                                    <div className="flex items-center justify-between gap-3">
                                        <div className="flex-1 min-w-0">
                                            <div className="font-semibold text-content text-sm">{airport.cityName}</div>
                                            <div className="text-xs text-content-muted truncate">{airport.name}</div>
                                        </div>
                                        <div className="text-sm font-mono font-semibold text-content-light shrink-0">{airport.code}</div>
                                    </div>
                                </button>
                            ))}
                        </div>
                    </PopoverContent>
                </Popover>
            </div>

            <div className="shrink-0 flex items-center justify-center lg:py-4">
                <div className="lg:hidden flex items-center w-full px-4">
                    <div className="flex-1 h-px bg-divider-light" />
                    <button className="mx-2 w-8 h-8 rounded-full bg-white flex items-center justify-center border border-divider-light text-primary hover:bg-primary-50 hover:text-primary-hover transition-transform active:scale-95 rotate-90 cursor-pointer shrink-0" onClick={(e) => { e.preventDefault(); onSwap(); }}>
                        <ArrowRightLeft className="w-3.5 h-3.5" />
                    </button>
                    <div className="flex-1 h-px bg-divider-light" />
                </div>
                <div className="hidden lg:flex flex-col items-center h-full">
                    <div className="flex-1 w-px bg-divider-light" />
                    <button className="my-1 w-10 h-10 rounded-full bg-white flex items-center justify-center border border-divider-light text-primary hover:bg-primary-100 hover:text-primary-hover transition-transform active:scale-95 cursor-pointer shrink-0 lg:shadow" onClick={(e) => { e.preventDefault(); onSwap(); }}>
                        <ArrowRightLeft className="w-4 h-4" />
                    </button>
                    <div className="flex-1 w-px bg-divider-light" />
                </div>
            </div>

            <div className="flex-1 min-w-0">
                <Popover open={open === 'arrival'} onOpenChange={(o) => onOpenChange(o ? 'arrival' : null)}>
                    <PopoverTrigger asChild>
                        <div className="flex items-center gap-4 p-4 lg:p-5 w-full cursor-pointer h-[72px] rounded-b-2xl lg:rounded-none lg:rounded-r-2xl hover:bg-primary-50/40 transition-colors">
                            <div className="bg-primary-50 w-10 h-10 rounded-full shrink-0 flex items-center justify-center">
                                <PlaneLanding className="w-5 h-5 text-primary-light" />
                            </div>
                            <div className="flex flex-col items-start min-w-0 text-left">
                                <span className="text-xs text-content-light mb-0.5 whitespace-nowrap">To</span>
                                <span className="font-semibold text-content text-sm truncate w-full">{arrival.cityName}</span>
                                <span className="text-xs text-content-muted truncate w-full">{arrival.code} · {arrival.name}</span>
                            </div>
                        </div>
                    </PopoverTrigger>
                    <PopoverContent className="w-80 p-2 rounded-2xl" align="start" onOpenAutoFocus={(e) => e.preventDefault()}>
                        <div className="max-h-80 overflow-y-auto flex flex-col gap-1">
                            {AIRPORT_TABLE.map((airport) => (
                                <button
                                    key={airport.id}
                                    className={cn('w-full outline-none px-4 py-3 text-left rounded-xl transition-all duration-200 hover:bg-primary-50 focus:bg-primary-50 cursor-pointer', arrival.id === airport.id ? 'bg-primary-50' : '')}
                                    onClick={() => { onArrivalChange(airport); onOpenChange(null); }}
                                >
                                    <div className="flex items-center justify-between gap-3">
                                        <div className="flex-1 min-w-0">
                                            <div className="font-semibold text-content text-sm">{airport.cityName}</div>
                                            <div className="text-xs text-content-muted truncate">{airport.name}</div>
                                        </div>
                                        <div className="text-sm font-mono font-semibold text-content-light shrink-0">{airport.code}</div>
                                    </div>
                                </button>
                            ))}
                        </div>
                    </PopoverContent>
                </Popover>
            </div>
        </div>
    );
}
