import { useState } from 'react';
import { Calendar as CalendarIcon, User, Search, ChevronDown, ArrowRightLeft, PlaneTakeoff, PlaneLanding, Minus, Plus } from 'lucide-react';
import { useNavigate } from '@tanstack/react-router';
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

import { CITY_TABLE, CLASS_TABLE } from "../../data/mockData";

const CITIES = CITY_TABLE.map(c => c.name);

const CLASSES = CLASS_TABLE.map(c => c.name);

export default function SearchWidget() {
    const navigate = useNavigate();

    // State
    const [tripType, setTripType] = useState<string>("one-way");

    const [departureCity, setDepartureCity] = useState("New Delhi");
    const [arrivalCity, setArrivalCity] = useState("Mumbai");

    const [date, setDate] = useState<Date>(new Date());
    const [dateRange, setDateRange] = useState<DateRange | undefined>({
        from: new Date(),
        to: new Date(new Date().setDate(new Date().getDate() + 7)),
    });

    const [adults, setAdults] = useState(2);
    const [children, setChildren] = useState(1);

    const [flightClass, setFlightClass] = useState("Economy");

    const [citySelectorOpen, setCitySelectorOpen] = useState<"departure" | "arrival" | null>(null);

    const handleSearch = () => {
        // Trigger navigation to the search page, view transition will happen automatically
        navigate({ to: '/search' });
    };

    const swapCities = () => {
        setDepartureCity(arrivalCity);
        setArrivalCity(departureCity);
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
            <div className="flex flex-col lg:flex-row items-center gap-4 w-full">

                {/* Cities Group */}
                <div className="flex flex-col lg:flex-row w-full lg:flex-[2_1_0%] relative bg-white/70 rounded-3xl lg:rounded-4xl shadow-sm border border-divider hover:border-primary-outline/50 hover:bg-white hover:shadow-md transition-all duration-300">

                    {/* Common Boundary Divider */}
                    <div className="hidden lg:block absolute left-1/2 top-4 bottom-4 w-px bg-divider-light -translate-x-1/2 z-10 pointer-events-none transition-colors"></div>
                    <div className="lg:hidden absolute top-1/2 left-6 right-6 h-px bg-divider-light -translate-y-1/2 z-10 pointer-events-none transition-colors"></div>

                    {/* Swap Button */}
                    <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-30 flex items-center justify-center pointer-events-none">
                        <button className="w-8 h-8 lg:w-10 lg:h-10 rounded-full bg-white flex items-center justify-center border border-divider-light text-primary hover:bg-primary-50 hover:text-primary-hover shadow-sm lg:shadow-md hover:shadow-lg transition-transform active:scale-95 rotate-90 lg:rotate-0 pointer-events-auto cursor-pointer" onClick={(e) => { e.preventDefault(); swapCities(); }}>
                            <ArrowRightLeft className="w-3.5 h-3.5 lg:w-4 lg:h-4" />
                        </button>
                    </div>

                    {/* Departure City */}
                    <div className="flex-1 w-full relative z-20">
                        <Popover open={citySelectorOpen === "departure"} onOpenChange={(open) => setCitySelectorOpen(open ? "departure" : null)}>
                            <PopoverTrigger asChild>
                                <div className="flex items-center gap-4 p-4 lg:p-5 w-full cursor-pointer h-[72px] rounded-t-3xl lg:rounded-none lg:rounded-l-4xl hover:bg-primary-50/40 transition-colors">
                                    <div className="bg-primary-50 w-10 h-10 rounded-full shrink-0 flex items-center justify-center">
                                        <PlaneTakeoff className="w-5 h-5 text-primary-light" />
                                    </div>
                                    <div className="flex flex-col items-start min-w-0 text-left">
                                        <span className="text-xs text-content-light mb-0.5 whitespace-nowrap">Departure City</span>
                                        <span className="font-semibold text-content text-sm truncate w-full">{departureCity}</span>
                                    </div>
                                </div>
                            </PopoverTrigger>
                            <PopoverContent className="w-64 p-2 rounded-2xl" align="start" onOpenAutoFocus={(e) => e.preventDefault()}>
                                <div className="max-h-60 overflow-y-auto flex flex-col gap-1">
                                    {CITIES.map((city) => (
                                        <button
                                            key={city}
                                            className={cn("w-full outline-none px-4 py-2.5 text-sm text-left rounded-xl transition-all duration-200 hover:bg-primary-50 hover:text-primary focus:bg-primary-50 focus:text-primary cursor-pointer", departureCity === city ? "bg-primary-50 font-medium text-primary" : "text-content")}
                                            onClick={() => {
                                                setDepartureCity(city);
                                                setCitySelectorOpen(null);
                                            }}
                                        >
                                            {city}
                                        </button>
                                    ))}
                                </div>
                            </PopoverContent>
                        </Popover>
                    </div>

                    {/* Arrival City */}
                    <div className="flex-1 w-full relative z-20">
                        <Popover open={citySelectorOpen === "arrival"} onOpenChange={(open) => setCitySelectorOpen(open ? "arrival" : null)}>
                            <PopoverTrigger asChild>
                                <div className="flex items-center gap-4 p-4 lg:p-5 lg:pl-8 w-full cursor-pointer h-[72px] rounded-b-3xl lg:rounded-none lg:rounded-r-4xl hover:bg-primary-50/40 transition-colors">
                                    <div className="bg-primary-50 w-10 h-10 rounded-full shrink-0 flex items-center justify-center">
                                        <PlaneLanding className="w-5 h-5 text-primary-light" />
                                    </div>
                                    <div className="flex flex-col items-start min-w-0 text-left">
                                        <span className="text-xs text-content-light mb-0.5 whitespace-nowrap">Arrival City</span>
                                        <span className="font-semibold text-content text-sm truncate w-full">{arrivalCity}</span>
                                    </div>
                                </div>
                            </PopoverTrigger>
                            <PopoverContent className="w-64 p-2 rounded-2xl" align="start" onOpenAutoFocus={(e) => e.preventDefault()}>
                                <div className="max-h-60 overflow-y-auto flex flex-col gap-1">
                                    {CITIES.map((city) => (
                                        <button
                                            key={city}
                                            className={cn("w-full outline-none px-4 py-2.5 text-sm text-left rounded-xl transition-all duration-200 hover:bg-primary-50 hover:text-primary focus:bg-primary-50 focus:text-primary cursor-pointer", arrivalCity === city ? "bg-primary-50 font-medium text-primary" : "text-content")}
                                            onClick={() => {
                                                setArrivalCity(city);
                                                setCitySelectorOpen(null);
                                            }}
                                        >
                                            {city}
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
                            <div className="flex items-center gap-4 p-4 lg:p-5 bg-white/70 border border-divider hover:border-primary-outline/50 hover:bg-white transition-all duration-300 w-full cursor-pointer rounded-3xl lg:rounded-4xl shadow-sm h-[72px]">
                                <div className="bg-primary-50 w-10 h-10 rounded-full shrink-0 flex items-center justify-center">
                                    <CalendarIcon className="w-5 h-5 text-primary-light" />
                                </div>
                                <div className="flex flex-col items-start min-w-0 text-left overflow-hidden">
                                    <span className="text-xs text-content-light mb-0.5 whitespace-nowrap">
                                        {tripType === "one-way" ? "Departure" : "Departure - Return"}
                                    </span>
                                    <span className="font-semibold text-content text-sm truncate w-full">
                                        {tripType === "one-way" ? (
                                            date ? format(date, "dd MMM yyyy") : "Pick a date"
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
                            <div className="flex items-center gap-4 p-4 lg:p-5 bg-white/70 border border-divider hover:border-primary-outline/50 hover:bg-white transition-all duration-300 w-full cursor-pointer rounded-3xl lg:rounded-4xl shadow-sm h-[72px]">
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
                <button className="btn-primary-large cursor-pointer shrink-0" onClick={handleSearch}>
                    <Search className="w-5 h-5" />
                    Search
                </button>
            </div>
        </div>
    );
}
