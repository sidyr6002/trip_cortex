import { useState } from 'react';
import { Briefcase, Utensils, MonitorPlay, Wifi, BatteryCharging } from 'lucide-react';
import type { FlightListing } from '../../data/schema';
import FlightPath from './FlightPath';
import { cn } from '../../lib/utils';

// Import newly created tab components
import FlightDetailsTab from './FlightDetailsTab';
import PriceDetailsTab from './PriceDetailsTab';
import PromosTab from './PromosTab';

interface FlightCardProps {
    flight: FlightListing;
}

type TabType = 'details' | 'price' | 'promos' | null;

export default function FlightCard({ flight }: FlightCardProps) {
    const [activeTab, setActiveTab] = useState<TabType>(null);

    const hasFacility = (icon: string) => flight.facilities.some(f => f.iconName === icon);

    const toggleTab = (tab: TabType) => {
        setActiveTab(current => current === tab ? null : tab);
    };

    return (
        <div className="bg-white rounded-2xl shadow-sm border border-divider-light p-6 pb-4 mb-4 hover:shadow-md transition-shadow">
            <div className="flex flex-col lg:flex-row items-center justify-between gap-6">

                {/* Airline Info */}
                <div className="flex items-center gap-4 w-full lg:w-1/4 shrink-0">
                    <div className="w-10 h-10 rounded-full bg-surface-muted flex items-center justify-center overflow-hidden shrink-0">
                        {/* Mock logo since I don't have the actual logo */}
                        <div className="text-[10px] font-bold text-center text-primary leading-tight px-1">
                            {flight.airline.name.split(' ').map(w => w[0]).join('')}
                        </div>
                    </div>
                    <div>
                        <h4 className="font-semibold text-content">{flight.airline.name}</h4>
                        <p className="text-xs text-content-muted">{flight.flightNumber} · <span className="text-content-light">{flight.flightClass.name}</span></p>
                    </div>
                </div>

                {/* Times & Duration */}
                <div className="flex items-center justify-between w-full lg:flex-1 px-4">
                    <div className="text-center">
                        <div className="font-bold text-lg">{flight.departureTime.split('T')[1].substring(0, 5)}</div>
                        <div className="text-xs text-content-muted">Sun, 20 Aug</div>
                        <div className="text-xs font-semibold mt-1 text-content-light">{flight.departureCity.code}</div>
                    </div>

                    <div className="flex-1 px-4 flex flex-col items-center">
                        <div className="text-xs text-content-muted mb-1">Duration: {flight.durationString}</div>
                        <FlightPath />
                        <div className="text-xs text-content-muted mt-1 font-medium">{flight.transitType}</div>
                    </div>

                    <div className="text-center">
                        <div className="font-bold text-lg">{flight.arrivalTime.split('T')[1].substring(0, 5)}</div>
                        <div className="text-xs text-content-muted">Sun, 20 Aug</div>
                        <div className="text-xs font-semibold mt-1 text-content-light">{flight.arrivalCity.code}</div>
                    </div>
                </div>

                {/* Facilities & Price */}
                <div className="flex items-center justify-between w-full lg:w-1/3 shrink-0 gap-4">
                    <div className="flex items-center gap-2.5 text-content-light">
                        {hasFacility('baggage') && <Briefcase className="w-4 h-4 shrink-0" />}
                        {hasFacility('meal') && <Utensils className="w-4 h-4 shrink-0" />}
                        {hasFacility('entertainment') && <MonitorPlay className="w-4 h-4 shrink-0" />}
                        {hasFacility('wifi') && <Wifi className="w-4 h-4 shrink-0" />}
                        {hasFacility('power') && <BatteryCharging className="w-4 h-4 shrink-0" />}
                    </div>
                    <div className="text-right">
                        <div className="flex items-baseline gap-1">
                            <span className="font-bold text-xl text-monza-500">{flight.pricing.currency} {flight.pricing.pricePerPassenger.toFixed(2)}</span>
                            <span className="text-xs text-content-muted font-medium">/pax</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Divider */}
            <hr className="my-5 border-divider-light" />

            {/* Bottom Actions */}
            <div className="flex flex-col">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-6 overflow-x-auto text-sm font-medium" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
                        <button
                            onClick={() => toggleTab('details')}
                            className={cn("whitespace-nowrap cursor-pointer transition-colors pb-2 border-b-2", activeTab === 'details' ? "text-monza-500 border-monza-600" : "text-primary-500 hover:text-monza-500 border-transparent")}
                        >
                            Flight Details
                        </button>
                        <button
                            onClick={() => toggleTab('price')}
                            className={cn("whitespace-nowrap cursor-pointer transition-colors pb-2 border-b-2", activeTab === 'price' ? "text-monza-500 border-monza-600" : "text-primary-500 hover:text-monza-600 border-transparent")}
                        >
                            Price Details
                        </button>
                        <button
                            onClick={() => toggleTab('promos')}
                            className={cn("whitespace-nowrap cursor-pointer transition-colors pb-2 border-b-2", activeTab === 'promos' ? "text-monza-500 border-monza-600" : "text-primary-500 hover:text-monza-600 border-transparent")}
                        >
                            Promos
                        </button>
                    </div>
                    <button className="bg-content hover:bg-black text-white px-6 py-2.5 rounded-xl text-sm font-semibold transition-colors shadow-sm cursor-pointer whitespace-nowrap hidden lg:block -mt-2">
                        Select Flight
                    </button>
                </div>

                {/* Mobile Select Flight Button */}
                <button className="w-full bg-content hover:bg-black text-white px-6 py-3 rounded-xl text-sm font-semibold transition-colors shadow-sm cursor-pointer lg:hidden mt-3">
                    Select Flight
                </button>

                {/* Expanded Content Area */}
                {activeTab === 'details' && <FlightDetailsTab flight={flight} />}
                {activeTab === 'price' && <PriceDetailsTab flight={flight} />}
                {activeTab === 'promos' && <PromosTab flight={flight} />}
            </div>
        </div >
    )
}
