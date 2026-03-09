import { AIRPORT_TABLE, CLASS_TABLE } from './mockData';

export const TAX_RATE = 0.12; // 12% tax rate
import { searchFlights } from './searchFlights';
import type { FlightListing } from './schema';

export function getAirportByCode(code: string) {
  return AIRPORT_TABLE.find(a => a.code === code);
}

export function getAirportCodeByCityName(cityName: string) {
  const normalized = cityName.toLowerCase().trim();
  return AIRPORT_TABLE.find(a => a.cityName.toLowerCase() === normalized)?.code;
}

export function getClassIdByName(className: string) {
  const normalized = className.toLowerCase().trim();
  return CLASS_TABLE.find(c => c.name.toLowerCase() === normalized)?.id;
}

export function getClassNameById(classId: string) {
  return CLASS_TABLE.find(c => c.id === classId)?.name;
}

export function getFlightById(flightId: string): FlightListing | undefined {
  // Search all flights without filters to find the specific flight
  const allFlights = searchFlights({ excludeSoldOut: false });
  return allFlights.find(f => f.id === flightId);
}
