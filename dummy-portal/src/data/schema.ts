export interface City {
    id: string; // Primary Key
    name: string;
    code: string;
}

export interface Airline {
    id: string; // Primary Key
    name: string;
    logoUrl: string; // S3 or path in public folder
}

export interface Facility {
    id: string; // Primary Key
    name: string;
    iconName: string; // icon identifier (e.g., 'baggage', 'wifi')
}

export interface FlightClass {
    id: string; // Primary Key
    name: string;
}

export interface Flight {
    id: string; // Primary Key
    airlineId: string; // Foreign Key to Airline
    flightNumber: string; // e.g., GA-828
    departureCityId: string; // Foreign Key to City
    arrivalCityId: string; // Foreign Key to City
    departureTime: string; // ISO String (Date+Time)
    arrivalTime: string; // ISO String (Date+Time)
    durationString: string; // e.g., '1h 45m' (Derived or stored)
    transitType: 'Direct' | '1 transit' | '2+ transit';
}

export interface FlightPricing {
    id: string; // Primary Key
    flightId: string; // Foreign Key to Flight
    classId: string; // Foreign Key to FlightClass
    pricePerPassenger: number; // e.g., 567.00
    currency: string; // e.g., 'US$'
}

export interface FlightFacilityMapping {
    id: string; // Primary Key
    flightId: string; // Foreign Key to Flight
    facilityId: string; // Foreign Key to Facility
}

// Joined representation for the UI (this is what a GraphQL/REST response would look like)
export interface FlightListing {
    id: string;
    airline: Airline;
    flightNumber: string;
    departureCity: City;
    arrivalCity: City;
    departureTime: string;
    arrivalTime: string;
    durationString: string;
    transitType: 'Direct' | '1 transit' | '2+ transit';
    facilities: Facility[];
    pricing: FlightPricing;
    flightClass: FlightClass;
}
