import { useState, useEffect } from 'react';
import { Calendar as CalendarIcon, User, Search, ChevronDown, ArrowRightLeft, PlaneTakeoff, PlaneLanding, Minus, Plus } from 'lucide-react';
import { useNavigate, useSearch } from '@tanstack/react-router';
import { format } from "date-fns";
import type { DateRange } from "react-day-picker";

import { cn } from "../../lib/utils";
import { Calendar } from "../ui/calendar";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "../ui/popover";
import { Tabs, TabsList, TabsTrigger } from "../ui/tabs";

import { AIRPORT_TABLE, CLASS_TABLE } from "../../data/mockData";
import { getAirportByCode, getClassNameById } from "../../data/helpers";
import type { Airport } from "../../data/schema";

const CLASSES = CLASS_TABLE.map(c => c.name);

export default function SearchWidget() {
    const navigate = useNavigate();
    const searchParams: { from?: string; to?: string; date?: string; class?: string } = useSearch({ strict: false });

    // State
    const [tripType, setTripType] = useState<string>("one-way");

    const [departureAirport, setDepartureAirport] = useState<Airport>(AIRPORT_TABLE[0]); // DEL
    const [arrivalAirport, setArrivalAirport] = useState<Airport>(AIRPORT_TABLE[1]); // BOM

    const [date, setDate] = useState<Date>(new Date());
    const [dateRange, setDateRange] = useState<DateRange | undefined>({
        from: new Date(),
        to: new Date(new Date().setDate(new Date().getDate() + 7)),
    });

    const [adults, setAdults] = useState(2);
    const [children, setChildren] = useState(1);

    const [flightClass, setFlightClass] = useState("Economy");

    const [citySelectorOpen, setCitySelectorOpen] = useState<"departure" | "arrival" | null>(null);

    // Pre-populate from URL params
    useEffect(() => {
        if (searchParams.from) {
            const airport = getAirportByCode(searchParams.from);
            if (airport) setDepartureAirport(airport);
        }
        if (searchParams.to) {
            const airport = getAirportByCode(searchParams.to);
            if (airport) setArrivalAirport(airport);
        }
        if (searchParams.date) {
            const parsedDate = new Date(searchParams.date);
            if (!isNaN(parsedDate.getTime())) setDate(parsedDate);
        }
        if (searchParams.class) {
            const className = getClassNameById(searchParams.class) || 
                             CLASS_TABLE.find(c => c.name.toLowerCase() === searchParams.class?.toLowerCase())?.name;
            if (className) setFlightClass(className);
        }
    }, [searchParams]);

    const handleSearch = () => {
        navigate({ 
            to: '/search',
            search: {
                from: departureAirport.code,
                to: arrivalAirport.code,
                date: format(date, 'yyyy-MM-dd'),
                class: flightClass.toLowerCase(),
            }
        });
    };

    const swapCities = () => {
        const temp = departureAirport;
        setDepartureAirport(arrivalAirport);
        setArrivalAirport(temp);
    };

    return (
        <div className="search-widget">
            {/* Top Row */}
            <div className="flex flex-row flex-wrap items-center justify-between gap-4 mb-6 px-2">
                <Tabs value={tripType} onValueChange={setTripType} className="w-auto">
                    <TabsList className="bg-surface-muted text-content-muted h-12 rounded-xl p-1 w-full justify-start space-x-1 border border-divider-light">
                        <TabsTrigger value="one-way" className="rounded-lg data-[state=active]:bg-primary-600! data-[state=active]:text-white! data-[state=active]:shadow-sm data-[state=active]:border data-[state=active]:border-primary! px-6 py-2 transition-all font-medium cursor-pointer">One Way</TabsTrigger>
                        <TabsTrigger value="round-trip" className="rounded-lg data-[state=active]:bg-primary-600! data-[state=active]:text-white! data-[state=active]:shadow-sm data-[state=active]:border data-[state=active]:border-primary! px-6 py-2 transition-all font-medium cursor-pointer">Round Trip</TabsTrigger>
                    </TabsList>
                </Tabs>

                <Popover>
                    <PopoverTrigger asChild>
                        <button className="flex items-center gap-2 text-sm font-medium text-content hover:text-primary transition-colors cursor-pointer">
                            {flightClass} <ChevronDown className="w-4 h-4" />
                        </button>
                    </PopoverTrigger>
                    <PopoverContent className="w-48 p-2 rounded-2xl" align="end" onOpenAutoFocus={(e) => e.preventDefault()}>
                        <div className="flex flex-col gap-1">
                            {CLASSES.map((c) => (
                                <button
                                    key={c}
                                    className={cn("w-full outline-none px-4 py-2.5 text-sm text-left rounded-xl transition-all duration-200 hover:text-primary focus:bg-primary-500 focus:text-white cursor-pointer", flightClass === c ? "bg-primary hover:text-white text-white font-medium shadow-md shadow-primary/20" : "text-content")}
                                    onClick={() => setFlightClass(c)}
                                >
                                    {c}
                                </button>
                            ))}
                        </div>
                    </PopoverContent>
                </Popover>
            </div>

            {/* Bottom Row */}
            <div className="flex flex-col lg:flex-row items-stretch gap-4 w-full">

                {/* Cities Group */}
                <div className="flex flex-col lg:flex-row items-stretch w-full lg:flex-[1_1_0%] lg:max-w-[600px] bg-white/70 rounded-3xl lg:rounded-4xl shadow-sm border border-divider hover:border-primary-outline/50 hover:bg-white hover:shadow-md transition-all duration-300">

                    {/* Departure City */}
                    <div className="flex-1 min-w-0">
                        <Popover open={citySelectorOpen === "departure"} onOpenChange={(open) => setCitySelectorOpen(open ? "departure" : null)}>
                            <PopoverTrigger asChild>
                                <div className="flex items-center gap-4 p-4 lg:p-5 w-full cursor-pointer h-[72px] rounded-t-3xl lg:rounded-none lg:rounded-l-4xl hover:bg-primary-50/40 transition-colors">
                                    <div className="bg-primary-50 w-10 h-10 rounded-full shrink-0 flex items-center justify-center">
                                        <PlaneTakeoff className="w-5 h-5 text-primary-light" />
                                    </div>
                                    <div className="flex flex-col items-start min-w-0 text-left">
                                        <span className="text-xs text-content-light mb-0.5 whitespace-nowrap">From</span>
                                        <span className="font-semibold text-content text-sm truncate w-full">{departureAirport.cityName}</span>
                                        <span className="text-xs text-content-muted truncate w-full">{departureAirport.code} · {departureAirport.name}</span>
                                    </div>
                                </div>
                            </PopoverTrigger>
                            <PopoverContent className="w-80 p-2 rounded-2xl" align="start" onOpenAutoFocus={(e) => e.preventDefault()}>
                                <div className="max-h-80 overflow-y-auto flex flex-col gap-1">
                                    {AIRPORT_TABLE.map((airport) => (
                                        <button
                                            key={airport.id}
                                            className={cn("w-full outline-none px-4 py-3 text-left rounded-xl transition-all duration-200 hover:bg-primary-50 focus:bg-primary-50 cursor-pointer", departureAirport.id === airport.id ? "bg-primary-50" : "")}
                                            onClick={() => {
                                                setDepartureAirport(airport);
                                                setCitySelectorOpen(null);
                                            }}
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

                    {/* Swap Button — in-flow flex item */}
                    <div className="shrink-0 flex items-center justify-center lg:py-4">
                        {/* Horizontal divider on mobile */}
                        <div className="lg:hidden flex items-center w-full px-4">
                            <div className="flex-1 h-px bg-divider-light" />
                            <button className="mx-2 w-8 h-8 rounded-full bg-white flex items-center justify-center border border-divider-light text-primary hover:bg-primary-50 hover:text-primary-hover transition-transform active:scale-95 rotate-90 cursor-pointer shrink-0" onClick={(e) => { e.preventDefault(); swapCities(); }}>
                                <ArrowRightLeft className="w-3.5 h-3.5" />
                            </button>
                            <div className="flex-1 h-px bg-divider-light" />
                        </div>
                        {/* Vertical divider on desktop */}
                        <div className="hidden lg:flex flex-col items-center h-full">
                            <div className="flex-1 w-px bg-divider-light" />
                            <button className="my-1 w-10 h-10 rounded-full bg-white flex items-center justify-center border border-divider-light text-primary hover:bg-primary-100 hover:text-primary-hover transition-transform active:scale-95 cursor-pointer shrink-0 lg:shadow" onClick={(e) => { e.preventDefault(); swapCities(); }}>
                                <ArrowRightLeft className="w-4 h-4" />
                            </button>
                            <div className="flex-1 w-px bg-divider-light" />
                        </div>
                    </div>

                    {/* Arrival City */}
                    <div className="flex-1 min-w-0">
                        <Popover open={citySelectorOpen === "arrival"} onOpenChange={(open) => setCitySelectorOpen(open ? "arrival" : null)}>
                            <PopoverTrigger asChild>
                                <div className="flex items-center gap-4 p-4 lg:p-5 w-full cursor-pointer h-[72px] rounded-b-3xl lg:rounded-none lg:rounded-r-4xl hover:bg-primary-50/40 transition-colors">
                                    <div className="bg-primary-50 w-10 h-10 rounded-full shrink-0 flex items-center justify-center">
                                        <PlaneLanding className="w-5 h-5 text-primary-light" />
                                    </div>
                                    <div className="flex flex-col items-start min-w-0 text-left">
                                        <span className="text-xs text-content-light mb-0.5 whitespace-nowrap">To</span>
                                        <span className="font-semibold text-content text-sm truncate w-full">{arrivalAirport.cityName}</span>
                                        <span className="text-xs text-content-muted truncate w-full">{arrivalAirport.code} · {arrivalAirport.name}</span>
                                    </div>
                                </div>
                            </PopoverTrigger>
                            <PopoverContent className="w-80 p-2 rounded-2xl" align="start" onOpenAutoFocus={(e) => e.preventDefault()}>
                                <div className="max-h-80 overflow-y-auto flex flex-col gap-1">
                                    {AIRPORT_TABLE.map((airport) => (
                                        <button
                                            key={airport.id}
                                            className={cn("w-full outline-none px-4 py-3 text-left rounded-xl transition-all duration-200 hover:bg-primary-50 focus:bg-primary-50 cursor-pointer", arrivalAirport.id === airport.id ? "bg-primary-50" : "")}
                                            onClick={() => {
                                                setArrivalAirport(airport);
                                                setCitySelectorOpen(null);
                                            }}
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

                {/* Date Picker */}
                <div className="w-full lg:flex-[1_1_0%] relative">
                    <Popover>
                        <PopoverTrigger asChild>
                            <div className="flex items-center gap-4 p-4 lg:p-5 bg-white/70 border border-divider hover:border-primary-outline/50 hover:bg-white transition-all duration-300 w-full cursor-pointer rounded-3xl lg:rounded-4xl shadow-sm h-full">
                                <div className="bg-primary-50 w-10 h-10 rounded-full shrink-0 flex items-center justify-center">
                                    <CalendarIcon className="w-5 h-5 text-primary-light" />
                                </div>
                                <div className="flex flex-col items-start min-w-0 text-left overflow-hidden">
                                    <span className="text-xs text-content-light mb-0.5 whitespace-nowrap">
                                        {tripType === "one-way" ? "Departure" : "Departure - Return"}
                                    </span>
                                    <span className="font-semibold text-content text-sm truncate w-full">
                                        {tripType === "one-way" ? (
                                            format(date, "dd MMM yyyy")
                                        ) : (
                                            dateRange?.from ? (
                                                dateRange.to ? (
                                                    `${format(dateRange.from, "dd MMM")} - ${format(dateRange.to, "MMM dd")}`
                                                ) : (
                                                    format(dateRange.from, "dd MMM yyyy")
                                                )
                                            ) : (
                                                "Pick Dates"
                                            )
                                        )}
                                    </span>
                                </div>
                            </div>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-0 rounded-2xl" align="center" onOpenAutoFocus={(e) => e.preventDefault()}>
                            {tripType === "one-way" ? (
                                <Calendar
                                    mode="single"
                                    selected={date}
                                    onSelect={(d) => d && setDate(d)}
                                    initialFocus
                                />
                            ) : (
                                <Calendar
                                    initialFocus
                                    mode="range"
                                    defaultMonth={dateRange?.from}
                                    selected={dateRange}
                                    onSelect={setDateRange}
                                    numberOfMonths={2}
                                />
                            )}
                        </PopoverContent>
                    </Popover>
                </div>

                {/* Traveler */}
                <div className="w-full lg:flex-[1_1_0%] relative">
                    <Popover>
                        <PopoverTrigger asChild>
                            <div className="flex items-center gap-4 p-4 lg:p-5 bg-white/70 border border-divider hover:border-primary-outline/50 hover:bg-white transition-all duration-300 w-full cursor-pointer rounded-3xl lg:rounded-4xl shadow-sm h-full">
                                <div className="bg-primary-50 w-10 h-10 rounded-full shrink-0 flex items-center justify-center">
                                    <User className="w-5 h-5 text-primary-light" />
                                </div>
                                <div className="flex flex-col items-start min-w-0 text-left">
                                    <span className="text-xs text-content-light mb-0.5 whitespace-nowrap">Travelers</span>
                                    <span className="font-semibold text-content text-sm truncate w-full">
                                        {adults} Adult{adults > 1 ? 's' : ''}{children > 0 ? `, ${children} Child${children > 1 ? 'ren' : ''}` : ''}
                                    </span>
                                </div>
                            </div>
                        </PopoverTrigger>
                        <PopoverContent className="w-64 p-4 rounded-2xl" align="center" onOpenAutoFocus={(e) => e.preventDefault()}>
                            <div className="flex flex-col gap-4">
                                <div className="flex items-center justify-between">
                                    <div className="flex flex-col">
                                        <span className="font-medium text-sm">Adults</span>
                                        <span className="text-xs text-content-muted">Age 12+</span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <button
                                            className="w-8 h-8 rounded-full border border-divider flex items-center justify-center hover:bg-surface-muted transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                                            onClick={() => setAdults(Math.max(1, adults - 1))}
                                            disabled={adults <= 1}
                                        >
                                            <Minus className="w-4 h-4" />
                                        </button>
                                        <span className="w-4 text-center font-medium">{adults}</span>
                                        <button
                                            className="w-8 h-8 rounded-full border border-divider flex items-center justify-center hover:bg-surface-muted transition-colors cursor-pointer"
                                            onClick={() => setAdults(adults + 1)}
                                        >
                                            <Plus className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                                <div className="flex items-center justify-between">
                                    <div className="flex flex-col">
                                        <span className="font-medium text-sm">Children</span>
                                        <span className="text-xs text-content-muted">Age 2-11</span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <button
                                            className="w-8 h-8 rounded-full border border-divider flex items-center justify-center hover:bg-surface-muted transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                                            onClick={() => setChildren(Math.max(0, children - 1))}
                                            disabled={children <= 0}
                                        >
                                            <Minus className="w-4 h-4" />
                                        </button>
                                        <span className="w-4 text-center font-medium">{children}</span>
                                        <button
                                            className="w-8 h-8 rounded-full border border-divider flex items-center justify-center hover:bg-surface-muted transition-colors cursor-pointer"
                                            onClick={() => setChildren(children + 1)}
                                        >
                                            <Plus className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </PopoverContent>
                    </Popover>
                </div>

                {/* Search Button */}
                <button className="btn-primary-large cursor-pointer shrink-0 self-stretch" onClick={handleSearch}>
                    <Search className="w-5 h-5" />
                    Search
                </button>
            </div>
        </div>
    );
}
