import type { City, Airline, Facility, FlightClass, Flight, FlightPricing, FlightFacilityMapping, FlightListing } from './schema';

// Tables

export const CITY_TABLE: City[] = [
    { id: 'city_1', name: 'New Delhi', code: 'DEL' },
    { id: 'city_2', name: 'Mumbai', code: 'BOM' },
    { id: 'city_3', name: 'Bangalore', code: 'BLR' },
    { id: 'city_4', name: 'Hyderabad', code: 'HYD' },
    { id: 'city_5', name: 'Chennai', code: 'MAA' },
    { id: 'city_6', name: 'Kolkata', code: 'CCU' },
    { id: 'city_7', name: 'Pune', code: 'PNQ' },
    { id: 'city_8', name: 'Ahmedabad', code: 'AMD' },
    { id: 'city_9', name: 'Jaipur', code: 'JAI' },
    { id: 'city_10', name: 'Surat', code: 'STV' },
    { id: 'city_11', name: 'Jakarta', code: 'CGK' },
    { id: 'city_12', name: 'Singapore', code: 'SIN' },
];

export const CLASS_TABLE: FlightClass[] = [
    { id: 'class_1', name: 'Economy' },
    { id: 'class_2', name: 'Premium Economy' },
    { id: 'class_3', name: 'Business' },
    { id: 'class_4', name: 'First Class' },
];

export const AIRLINE_TABLE: Airline[] = [
    { id: 'air_1', name: 'Garuda Indonesia', logoUrl: '/api/placeholder/40/40' },
    { id: 'air_2', name: 'Singapore Airlines', logoUrl: '/api/placeholder/40/40' },
    { id: 'air_3', name: 'Lion Air', logoUrl: '/api/placeholder/40/40' },
    { id: 'air_4', name: 'Batik Air', logoUrl: '/api/placeholder/40/40' },
];

export const FACILITY_TABLE: Facility[] = [
    { id: 'fac_1', name: 'Baggage', iconName: 'baggage' },
    { id: 'fac_2', name: 'In-flight meal', iconName: 'meal' },
    { id: 'fac_3', name: 'In-flight entertainment', iconName: 'entertainment' },
    { id: 'fac_4', name: 'Wifi', iconName: 'wifi' },
    { id: 'fac_5', name: 'Power/USB Port', iconName: 'power' },
];

// Flights (For UI demo, let's assume they are from Jakarta(CGK) to Singapore(SIN) on a specific date)
// Today's Date
const today = new Date();
const baseDateStr = `${today.getFullYear()}-${(today.getMonth() + 1).toString().padStart(2, '0')}-${today.getDate().toString().padStart(2, '0')}`;

export const FLIGHT_TABLE: Flight[] = [
    {
        id: 'flight_1',
        airlineId: 'air_1', // Garuda Indonesia
        flightNumber: 'GA-828',
        departureCityId: 'city_11', // CGK
        arrivalCityId: 'city_12', // SIN
        departureTime: `${baseDateStr}T08:35:00`,
        arrivalTime: `${baseDateStr}T11:20:00`,
        durationString: '1h 45m',
        transitType: 'Direct'
    },
    {
        id: 'flight_2',
        airlineId: 'air_2', // Singapore Airlines
        flightNumber: 'SQ-951',
        departureCityId: 'city_11',
        arrivalCityId: 'city_12',
        departureTime: `${baseDateStr}T05:25:00`,
        arrivalTime: `${baseDateStr}T08:10:00`,
        durationString: '1h 45m',
        transitType: 'Direct'
    },
    {
        id: 'flight_3',
        airlineId: 'air_3', // Lion Air
        flightNumber: 'JT-690',
        departureCityId: 'city_11',
        arrivalCityId: 'city_12',
        departureTime: `${baseDateStr}T12:10:00`,
        arrivalTime: `${baseDateStr}T14:55:00`,
        durationString: '1h 45m',
        transitType: 'Direct'
    },
    {
        id: 'flight_4',
        airlineId: 'air_4', // Batik Air
        flightNumber: 'ID-7157',
        departureCityId: 'city_11',
        arrivalCityId: 'city_12',
        departureTime: `${baseDateStr}T12:10:00`,
        arrivalTime: `${baseDateStr}T14:55:00`,
        durationString: '1h 45m',
        transitType: 'Direct'
    }
];

export const PRICING_TABLE: FlightPricing[] = [
    { id: 'price_1', flightId: 'flight_1', classId: 'class_4', pricePerPassenger: 567.00, currency: 'US$' },
    { id: 'price_2', flightId: 'flight_2', classId: 'class_4', pricePerPassenger: 530.00, currency: 'US$' },
    { id: 'price_3', flightId: 'flight_3', classId: 'class_4', pricePerPassenger: 418.00, currency: 'US$' },
    { id: 'price_4', flightId: 'flight_4', classId: 'class_4', pricePerPassenger: 430.00, currency: 'US$' },
];

export const FLIGHT_FACILITY_MAPPING_TABLE: FlightFacilityMapping[] = [
    { id: 'ff_1_1', flightId: 'flight_1', facilityId: 'fac_1' },
    { id: 'ff_1_2', flightId: 'flight_1', facilityId: 'fac_2' },
    { id: 'ff_1_3', flightId: 'flight_1', facilityId: 'fac_3' },
    { id: 'ff_1_4', flightId: 'flight_1', facilityId: 'fac_4' },
    { id: 'ff_1_5', flightId: 'flight_1', facilityId: 'fac_5' },

    { id: 'ff_2_1', flightId: 'flight_2', facilityId: 'fac_1' },
    { id: 'ff_2_2', flightId: 'flight_2', facilityId: 'fac_2' },
    { id: 'ff_2_3', flightId: 'flight_2', facilityId: 'fac_3' },
    { id: 'ff_2_4', flightId: 'flight_2', facilityId: 'fac_4' },
    { id: 'ff_2_5', flightId: 'flight_2', facilityId: 'fac_5' },

    { id: 'ff_3_1', flightId: 'flight_3', facilityId: 'fac_1' },
    { id: 'ff_3_2', flightId: 'flight_3', facilityId: 'fac_2' },
    { id: 'ff_3_3', flightId: 'flight_3', facilityId: 'fac_3' },
    { id: 'ff_3_4', flightId: 'flight_3', facilityId: 'fac_4' },
    { id: 'ff_3_5', flightId: 'flight_3', facilityId: 'fac_5' },

    { id: 'ff_4_1', flightId: 'flight_4', facilityId: 'fac_1' },
    { id: 'ff_4_2', flightId: 'flight_4', facilityId: 'fac_2' },
    { id: 'ff_4_3', flightId: 'flight_4', facilityId: 'fac_3' },
    { id: 'ff_4_4', flightId: 'flight_4', facilityId: 'fac_4' },
    { id: 'ff_4_5', flightId: 'flight_4', facilityId: 'fac_5' },
];

// Helper to "join" all tables and return the `FlightListing` models for the UI
export function getAvailableFlights(): FlightListing[] {
    return FLIGHT_TABLE.map(flight => {
        const airline = AIRLINE_TABLE.find(a => a.id === flight.airlineId)!;
        const departureCity = CITY_TABLE.find(c => c.id === flight.departureCityId)!;
        const arrivalCity = CITY_TABLE.find(c => c.id === flight.arrivalCityId)!;

        const facilityIds = FLIGHT_FACILITY_MAPPING_TABLE.filter(ffm => ffm.flightId === flight.id).map(ffm => ffm.facilityId);
        const facilities = FACILITY_TABLE.filter(fac => facilityIds.includes(fac.id));

        const pricing = PRICING_TABLE.find(p => p.flightId === flight.id)!;
        const flightClass = CLASS_TABLE.find(c => c.id === pricing.classId)!;

        return {
            id: flight.id,
            airline,
            flightNumber: flight.flightNumber,
            departureCity,
            arrivalCity,
            departureTime: flight.departureTime,
            arrivalTime: flight.arrivalTime,
            durationString: flight.durationString,
            transitType: flight.transitType,
            facilities,
            pricing,
            flightClass
        };
    });
}
