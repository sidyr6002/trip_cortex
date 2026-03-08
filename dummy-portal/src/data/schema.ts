export interface Airport {
  id: string;
  name: string;
  code: string; // IATA code e.g., 'BOM', 'DXB', 'LHR'
  cityName: string; // e.g., 'Mumbai', 'Dubai', 'London'
  countryCode: string; // ISO 3166-1 alpha-2 e.g., 'IN', 'AE', 'GB'
}

export interface Airline {
  id: string;
  name: string;
  logoUrl: string;
}

export interface Facility {
  id: string;
  name: string;
  iconName: string; // e.g., 'baggage', 'wifi', 'meal'
}

export interface FlightClass {
  id: string;
  name: string; // 'Economy' | 'Premium Economy' | 'Business' | 'First Class'
}

// A single non-stop hop (e.g., Mumbai BOM → Dubai DXB)
export interface FlightSegment {
  id: string;
  airlineId: string;
  flightNumber: string; // e.g., 'EK-507'
  departureAirportId: string;
  arrivalAirportId: string;
  departureTime: string; // ISO 8601
  arrivalTime: string; // ISO 8601
  durationMinutes: number; // e.g., 195
}

// The full journey (e.g., Mumbai BOM → London LHR via Dubai DXB)
// A direct flight has 1 segment; a 1-transit flight has 2 segments, etc.
export interface Flight {
  id: string;
  departureAirportId: string; // origin airport of the whole journey
  arrivalAirportId: string; // final destination airport
  segmentIds: string[]; // ordered list of FlightSegment IDs
  totalDurationMinutes: number; // gate-to-gate including layovers
  transitType: 'Direct' | '1 transit' | '2+ transit';
  status: 'available' | 'sold-out';
}

// Layover info derived from consecutive segments
export interface Layover {
  airportId: string;
  durationMinutes: number; // time between arrival of seg N and departure of seg N+1
}

export interface FlightPricing {
  id: string;
  flightId: string;
  classId: string;
  pricePerPassenger: number;
  currency: string; // e.g., 'USD'
}

export interface FlightFacilityMapping {
  id: string;
  segmentId: string; // facilities are per-segment (wifi on leg 1 doesn't mean wifi on leg 2)
  facilityId: string;
}


// ── Joined UI representations ──────────────────────────────────────

export interface FlightSegmentDetail {
  id: string;
  airline: Airline;
  flightNumber: string;
  departureAirport: Airport;
  arrivalAirport: Airport;
  departureTime: string;
  arrivalTime: string;
  durationMinutes: number;
  facilities: Facility[];
}

export interface LayoverDetail {
  airport: Airport;
  durationMinutes: number;
}

export interface FlightListing {
  id: string;
  departureAirport: Airport;
  arrivalAirport: Airport;
  segments: FlightSegmentDetail[];
  layovers: LayoverDetail[]; // length = segments.length - 1
  totalDurationMinutes: number;
  transitType: 'Direct' | '1 transit' | '2+ transit';
  status: 'available' | 'sold-out';
  pricing: FlightPricing;
  flightClass: FlightClass;
}
