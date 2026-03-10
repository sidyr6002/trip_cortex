import { useState, useEffect } from 'react';
import { Calendar as CalendarIcon, Search, ChevronDown } from 'lucide-react';
import { useNavigate, useSearch } from '@tanstack/react-router';
import { format } from 'date-fns';
import type { DateRange } from 'react-day-picker';

import { cn } from '../../../lib/utils';
import { Calendar } from '../../ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '../../ui/popover';
import { Tabs, TabsList, TabsTrigger } from '../../ui/tabs';

import { AIRPORT_TABLE, CLASS_TABLE } from '../../../data/mockData';
import { getAirportByCode, getClassNameById } from '../../../data/helpers';
import type { Airport } from '../../../data/schema';
import { DATE_RANGE_OFFSET_DAYS, DEFAULT_ADULTS, DEFAULT_CHILDREN } from '../../../constants';
import CitySelector from './CitySelector';
import TravelerSelector from './TravelerSelector';

const CLASSES = CLASS_TABLE.map(c => c.name);

export default function SearchWidget() {
    const navigate = useNavigate();
    const searchParams: { from?: string; to?: string; date?: string; returnDate?: string; tripType?: string; class?: string; adults?: number; children?: number } = useSearch({ strict: false });

    const [tripType, setTripType] = useState<string>('one-way');
    const [departureAirport, setDepartureAirport] = useState<Airport>(AIRPORT_TABLE[0]);
    const [arrivalAirport, setArrivalAirport] = useState<Airport>(AIRPORT_TABLE[1]);
    const [date, setDate] = useState<Date>(new Date());
    const [dateRange, setDateRange] = useState<DateRange | undefined>({
        from: new Date(),
        to: new Date(new Date().setDate(new Date().getDate() + DATE_RANGE_OFFSET_DAYS)),
    });
    const [adults, setAdults] = useState(DEFAULT_ADULTS);
    const [children, setChildren] = useState(DEFAULT_CHILDREN);
    const [flightClass, setFlightClass] = useState('Economy');
    const [citySelectorOpen, setCitySelectorOpen] = useState<'departure' | 'arrival' | null>(null);

    useEffect(() => {
        if (searchParams.from) {
            const airport = getAirportByCode(searchParams.from);
            if (airport) setDepartureAirport(airport);
        }
        if (searchParams.to) {
            const airport = getAirportByCode(searchParams.to);
            if (airport) setArrivalAirport(airport);
        }
        if (searchParams.tripType) setTripType(searchParams.tripType);
        if (searchParams.date) {
            const parsedDate = new Date(searchParams.date);
            if (!isNaN(parsedDate.getTime())) {
                setDate(parsedDate);
                if (searchParams.tripType === 'round-trip') {
                    const returnDate = searchParams.returnDate ? new Date(searchParams.returnDate) : new Date(parsedDate.getTime() + DATE_RANGE_OFFSET_DAYS * 86400000);
                    setDateRange({ from: parsedDate, to: returnDate });
                }
            }
        }
        if (searchParams.class) {
            const className = getClassNameById(searchParams.class) || CLASS_TABLE.find(c => c.name.toLowerCase() === searchParams.class?.toLowerCase())?.name;
            if (className) setFlightClass(className);
        }
        if (searchParams.adults !== undefined) setAdults(Number(searchParams.adults));
        if (searchParams.children !== undefined) setChildren(Number(searchParams.children));
    }, [searchParams]);

    const handleSearch = () => {
        const search: Record<string, string> = {
            from: departureAirport.code,
            to: arrivalAirport.code,
            date: format(tripType === 'round-trip' && dateRange?.from ? dateRange.from : date, 'yyyy-MM-dd'),
            class: flightClass.toLowerCase(),
            tripType,
            adults: adults.toString(),
            children: children.toString(),
        };
        if (tripType === 'round-trip' && dateRange?.to) {
            search.returnDate = format(dateRange.to, 'yyyy-MM-dd');
        }
        navigate({ to: '/search', search });
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
                                    className={cn('w-full outline-none px-4 py-2.5 text-sm text-left rounded-xl transition-all duration-200 hover:text-primary focus:bg-primary-500 focus:text-white cursor-pointer', flightClass === c ? 'bg-primary hover:text-white text-white font-medium shadow-md shadow-primary/20' : 'text-content')}
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
                <CitySelector
                    departure={departureAirport}
                    arrival={arrivalAirport}
                    onDepartureChange={setDepartureAirport}
                    onArrivalChange={setArrivalAirport}
                    open={citySelectorOpen}
                    onOpenChange={setCitySelectorOpen}
                    onSwap={swapCities}
                />

                {/* Date Picker */}
                <div className="w-full lg:flex-[1_1_0%] relative">
                    <Popover>
                        <PopoverTrigger asChild>
                            <div className="flex items-center gap-4 p-4 lg:p-5 bg-white/70 border border-divider hover:border-primary-outline/50 hover:bg-white transition-all duration-300 w-full cursor-pointer rounded-2xl shadow-sm h-full">
                                <div className="bg-primary-50 w-10 h-10 rounded-full shrink-0 flex items-center justify-center">
                                    <CalendarIcon className="w-5 h-5 text-primary-light" />
                                </div>
                                <div className="flex flex-col items-start min-w-0 text-left overflow-hidden">
                                    <span className="text-xs text-content-light mb-0.5 whitespace-nowrap">
                                        {tripType === 'one-way' ? 'Departure' : 'Departure - Return'}
                                    </span>
                                    <span className="font-semibold text-content text-sm truncate w-full">
                                        {tripType === 'one-way' ? format(date, 'dd MMM yyyy') : (
                                            dateRange?.from ? (dateRange.to ? `${format(dateRange.from, 'dd MMM')} - ${format(dateRange.to, 'MMM dd')}` : format(dateRange.from, 'dd MMM yyyy')) : 'Pick Dates'
                                        )}
                                    </span>
                                </div>
                            </div>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-0 rounded-2xl" align="center" onOpenAutoFocus={(e) => e.preventDefault()}>
                            {tripType === 'one-way' ? (
                                <Calendar mode="single" selected={date} onSelect={(d) => d && setDate(d)} initialFocus />
                            ) : (
                                <Calendar initialFocus mode="range" defaultMonth={dateRange?.from} selected={dateRange} onSelect={setDateRange} numberOfMonths={2} />
                            )}
                        </PopoverContent>
                    </Popover>
                </div>

                {/* Traveler Selector */}
                <div className="w-full lg:flex-[1_1_0%] relative">
                    <TravelerSelector
                        adults={adults}
                        children={children}
                        onAdultsChange={setAdults}
                        onChildrenChange={setChildren}
                    />
                </div>

                <button className="btn-primary-large cursor-pointer shrink-0 self-stretch" onClick={handleSearch}>
                    <Search className="w-5 h-5" />
                    Search
                </button>
            </div>
        </div>
    );
}
