import type { FlightListing, FlightSegmentDetail, LayoverDetail } from './schema';
import {
  AIRPORT_TABLE,
  CLASS_TABLE,
  FLIGHT_TABLE,
  buildSegmentTable,
  PRICING_TABLE,
  AIRLINE_TABLE,
  FACILITY_TABLE,
  FLIGHT_FACILITY_MAPPING_TABLE,
} from './mockData';

export interface SearchParams {
  originAirportCode?: string;
  destinationAirportCode?: string;
  departureDate?: string; // YYYY-MM-DD format
  classId?: string;
  excludeSoldOut?: boolean; // default true
}

export function searchFlights(params: SearchParams = {}): FlightListing[] {
  const SEGMENT_TABLE = buildSegmentTable();
  const {
    originAirportCode,
    destinationAirportCode,
    departureDate,
    classId = 'class_1',
    excludeSoldOut = true
  } = params;

  // If airport code is provided but not found, return empty array
  if (originAirportCode && !AIRPORT_TABLE.find(a => a.code === originAirportCode)) {
    return [];
  }
  if (destinationAirportCode && !AIRPORT_TABLE.find(a => a.code === destinationAirportCode)) {
    return [];
  }

  const originAirportId = originAirportCode 
    ? AIRPORT_TABLE.find(a => a.code === originAirportCode)?.id 
    : undefined;
  const destinationAirportId = destinationAirportCode 
    ? AIRPORT_TABLE.find(a => a.code === destinationAirportCode)?.id 
    : undefined;

  const filteredFlights = FLIGHT_TABLE.filter(flight => {
    if (originAirportId && flight.departureAirportId !== originAirportId) return false;
    if (destinationAirportId && flight.arrivalAirportId !== destinationAirportId) return false;
    
    if (departureDate) {
      const firstSegment = SEGMENT_TABLE.find(s => s.id === flight.segmentIds[0]);
      if (firstSegment) {
        const flightDate = firstSegment.departureTime.split('T')[0];
        if (flightDate !== departureDate) return false;
      }
    }
    
    if (excludeSoldOut && flight.status === 'sold-out') return false;
    if (!PRICING_TABLE.some(p => p.flightId === flight.id && p.classId === classId)) return false;
    
    return true;
  });

  return filteredFlights.map(flight => {
    const departureAirport = AIRPORT_TABLE.find(a => a.id === flight.departureAirportId)!;
    const arrivalAirport = AIRPORT_TABLE.find(a => a.id === flight.arrivalAirportId)!;

    const segments: FlightSegmentDetail[] = flight.segmentIds.map(segId => {
      const seg = SEGMENT_TABLE.find(s => s.id === segId)!;
      const airline = AIRLINE_TABLE.find(a => a.id === seg.airlineId)!;
      const depAirport = AIRPORT_TABLE.find(a => a.id === seg.departureAirportId)!;
      const arrAirport = AIRPORT_TABLE.find(a => a.id === seg.arrivalAirportId)!;

      const facilityIds = FLIGHT_FACILITY_MAPPING_TABLE
        .filter(ffm => ffm.segmentId === segId)
        .map(ffm => ffm.facilityId);
      const facilities = FACILITY_TABLE.filter(f => facilityIds.includes(f.id));

      return {
        id: seg.id,
        airline,
        flightNumber: seg.flightNumber,
        departureAirport: depAirport,
        arrivalAirport: arrAirport,
        departureTime: seg.departureTime,
        arrivalTime: seg.arrivalTime,
        durationMinutes: seg.durationMinutes,
        facilities,
      };
    });

    const layovers: LayoverDetail[] = [];
    for (let i = 0; i < segments.length - 1; i++) {
      const arrTime = new Date(segments[i].arrivalTime).getTime();
      const depTime = new Date(segments[i + 1].departureTime).getTime();
      const layoverMinutes = Math.round((depTime - arrTime) / 60000);
      layovers.push({
        airport: segments[i].arrivalAirport,
        durationMinutes: layoverMinutes > 0 ? layoverMinutes : 0,
      });
    }

    const pricing = PRICING_TABLE.find(p => p.flightId === flight.id && p.classId === classId)!;
    const flightClass = CLASS_TABLE.find(c => c.id === classId)!;

    return {
      id: flight.id,
      departureAirport,
      arrivalAirport,
      segments,
      layovers,
      totalDurationMinutes: flight.totalDurationMinutes,
      transitType: flight.transitType,
      status: flight.status,
      pricing,
      flightClass,
    };
  });
}
