import type { Facility, FlightSegmentDetail } from '../data/schema';

export function hasFacility(segmentOrFacilities: FlightSegmentDetail | Facility[], iconName: string): boolean {
  const facilities = Array.isArray(segmentOrFacilities)
    ? segmentOrFacilities
    : segmentOrFacilities.facilities;
  return facilities.some(f => f.iconName === iconName);
}
