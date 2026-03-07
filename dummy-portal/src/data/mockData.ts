import type {
  City, Airline, Facility, FlightClass, FlightSegment, Flight,
  FlightPricing, FlightFacilityMapping, FlightListing,
  FlightSegmentDetail, LayoverDetail
} from './schema';

// ── Reference Tables ───────────────────────────────────────────────

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
  { id: 'city_13', name: 'Dubai', code: 'DXB' },
  { id: 'city_14', name: 'London', code: 'LHR' },
  { id: 'city_15', name: 'New York', code: 'JFK' },
];

export const CLASS_TABLE: FlightClass[] = [
  { id: 'class_1', name: 'Economy' },
  { id: 'class_2', name: 'Premium Economy' },
  { id: 'class_3', name: 'Business' },
  { id: 'class_4', name: 'First Class' },
];

export const AIRLINE_TABLE: Airline[] = [
  { id: 'air_1', name: 'IndiGo', logoUrl: '/api/placeholder/40/40' },
  { id: 'air_2', name: 'Air India', logoUrl: '/api/placeholder/40/40' },
  { id: 'air_3', name: 'SpiceJet', logoUrl: '/api/placeholder/40/40' },
  { id: 'air_4', name: 'Vistara', logoUrl: '/api/placeholder/40/40' },
  { id: 'air_5', name: 'Emirates', logoUrl: '/api/placeholder/40/40' },
  { id: 'air_6', name: 'Singapore Airlines', logoUrl: '/api/placeholder/40/40' },
  { id: 'air_7', name: 'British Airways', logoUrl: '/api/placeholder/40/40' },
  { id: 'air_8', name: 'Etihad Airways', logoUrl: '/api/placeholder/40/40' },
];

export const FACILITY_TABLE: Facility[] = [
  { id: 'fac_1', name: 'Baggage', iconName: 'baggage' },
  { id: 'fac_2', name: 'In-flight meal', iconName: 'meal' },
  { id: 'fac_3', name: 'In-flight entertainment', iconName: 'entertainment' },
  { id: 'fac_4', name: 'Wifi', iconName: 'wifi' },
  { id: 'fac_5', name: 'Power/USB Port', iconName: 'power' },
];

// ── Date helpers ───────────────────────────────────────────────────

function getDateString(daysOffset: number): string {
  const date = new Date();
  date.setDate(date.getDate() + daysOffset);
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`;
}

function addMinutesToTime(timeStr: string, minutes: number): string {
  const date = new Date(timeStr);
  date.setMinutes(date.getMinutes() + minutes);
  return date.toISOString().slice(0, 19);
}

const today = new Date();
const D = `${today.getFullYear()}-${(today.getMonth() + 1).toString().padStart(2, '0')}-${today.getDate().toString().padStart(2, '0')}`;

// ── Flight Segments (individual non-stop hops) ─────────────────────

// Base segment templates (time only, no date)
const BASE_SEGMENTS = [
  // Domestic
  { id: 1, airlineId: 'air_1', flightNumber: '6E-2134', from: 'city_1', to: 'city_2', depTime: '06:00:00', duration: 135 },
  { id: 2, airlineId: 'air_2', flightNumber: 'AI-860', from: 'city_1', to: 'city_2', depTime: '11:30:00', duration: 135 },
  { id: 3, airlineId: 'air_3', flightNumber: 'SG-8194', from: 'city_1', to: 'city_2', depTime: '17:00:00', duration: 135 },
  { id: 4, airlineId: 'air_4', flightNumber: 'UK-995', from: 'city_2', to: 'city_1', depTime: '21:30:00', duration: 135 },
  { id: 5, airlineId: 'air_1', flightNumber: '6E-6112', from: 'city_1', to: 'city_3', depTime: '07:15:00', duration: 165 },
  { id: 6, airlineId: 'air_2', flightNumber: 'AI-804', from: 'city_1', to: 'city_3', depTime: '13:00:00', duration: 165 },
  { id: 7, airlineId: 'air_4', flightNumber: 'UK-829', from: 'city_3', to: 'city_1', depTime: '18:30:00', duration: 165 },
  { id: 8, airlineId: 'air_1', flightNumber: '6E-5327', from: 'city_2', to: 'city_3', depTime: '08:00:00', duration: 105 },
  { id: 9, airlineId: 'air_3', flightNumber: 'SG-1136', from: 'city_2', to: 'city_3', depTime: '14:30:00', duration: 105 },
  { id: 10, airlineId: 'air_4', flightNumber: 'UK-864', from: 'city_3', to: 'city_2', depTime: '20:00:00', duration: 105 },
  { id: 11, airlineId: 'air_1', flightNumber: '6E-2063', from: 'city_1', to: 'city_4', depTime: '09:30:00', duration: 135 },
  { id: 12, airlineId: 'air_2', flightNumber: 'AI-544', from: 'city_1', to: 'city_4', depTime: '16:00:00', duration: 135 },
  { id: 13, airlineId: 'air_1', flightNumber: '6E-5054', from: 'city_2', to: 'city_5', depTime: '10:00:00', duration: 105 },
  { id: 14, airlineId: 'air_3', flightNumber: 'SG-1024', from: 'city_2', to: 'city_5', depTime: '15:30:00', duration: 105 },
  // International
  { id: 15, airlineId: 'air_5', flightNumber: 'EK-512', from: 'city_1', to: 'city_13', depTime: '08:30:00', duration: 210 },
  { id: 16, airlineId: 'air_2', flightNumber: 'AI-995', from: 'city_1', to: 'city_13', depTime: '22:00:00', duration: 210 },
  { id: 17, airlineId: 'air_5', flightNumber: 'EK-500', from: 'city_2', to: 'city_13', depTime: '09:00:00', duration: 195 },
  { id: 18, airlineId: 'air_6', flightNumber: 'SQ-402', from: 'city_1', to: 'city_12', depTime: '07:00:00', duration: 330 },
  { id: 19, airlineId: 'air_2', flightNumber: 'AI-345', from: 'city_1', to: 'city_12', depTime: '23:00:00', duration: 330 },
  { id: 20, airlineId: 'air_6', flightNumber: 'SQ-424', from: 'city_2', to: 'city_12', depTime: '10:30:00', duration: 330 },
  { id: 21, airlineId: 'air_7', flightNumber: 'BA-142', from: 'city_1', to: 'city_14', depTime: '14:00:00', duration: 570 },
  { id: 22, airlineId: 'air_2', flightNumber: 'AI-161', from: 'city_1', to: 'city_14', depTime: '13:30:00', duration: 570 },
  // Transit legs
  { id: 23, airlineId: 'air_5', flightNumber: 'EK-514', from: 'city_1', to: 'city_13', depTime: '09:00:00', duration: 210 },
  { id: 24, airlineId: 'air_5', flightNumber: 'EK-029', from: 'city_13', to: 'city_14', depTime: '14:30:00', duration: 420 },
  { id: 25, airlineId: 'air_5', flightNumber: 'EK-502', from: 'city_2', to: 'city_13', depTime: '10:00:00', duration: 195 },
  { id: 26, airlineId: 'air_5', flightNumber: 'EK-031', from: 'city_13', to: 'city_14', depTime: '15:00:00', duration: 420 },
  { id: 27, airlineId: 'air_2', flightNumber: 'AI-191', from: 'city_1', to: 'city_14', depTime: '12:00:00', duration: 570 },
  { id: 28, airlineId: 'air_7', flightNumber: 'BA-117', from: 'city_14', to: 'city_15', depTime: '19:00:00', duration: 480 },
  { id: 29, airlineId: 'air_5', flightNumber: 'EK-516', from: 'city_1', to: 'city_13', depTime: '08:00:00', duration: 210 },
  { id: 30, airlineId: 'air_5', flightNumber: 'EK-003', from: 'city_13', to: 'city_14', depTime: '13:30:00', duration: 420 },
  { id: 31, airlineId: 'air_7', flightNumber: 'BA-115', from: 'city_14', to: 'city_15', depTime: '21:00:00', duration: 480 },
  { id: 32, airlineId: 'air_2', flightNumber: 'AI-866', from: 'city_2', to: 'city_1', depTime: '06:00:00', duration: 135 },
  { id: 33, airlineId: 'air_2', flightNumber: 'AI-111', from: 'city_1', to: 'city_14', depTime: '11:00:00', duration: 570 },
  { id: 34, airlineId: 'air_7', flightNumber: 'BA-119', from: 'city_14', to: 'city_15', depTime: '18:00:00', duration: 480 },
];

// Generate segments for 7 days
export const SEGMENT_TABLE: FlightSegment[] = [];
for (let day = 0; day < 7; day++) {
  const dateStr = getDateString(day);
  BASE_SEGMENTS.forEach(seg => {
    const depTime = `${dateStr}T${seg.depTime}`;
    const arrTime = addMinutesToTime(depTime, seg.duration);
    SEGMENT_TABLE.push({
      id: `seg_${seg.id}_d${day}`,
      airlineId: seg.airlineId,
      flightNumber: seg.flightNumber,
      departureCityId: seg.from,
      arrivalCityId: seg.to,
      departureTime: depTime,
      arrivalTime: arrTime,
      durationMinutes: seg.duration,
    });
  });
}

// ── Flights (journeys composed of segments) ────────────────────────

// Base flight templates
const BASE_FLIGHTS = [
  // Direct domestic
  { id: 1, from: 'city_1', to: 'city_2', segs: [1], duration: 135, type: 'Direct', status: 'available' },
  { id: 2, from: 'city_1', to: 'city_2', segs: [2], duration: 135, type: 'Direct', status: 'available' },
  { id: 3, from: 'city_1', to: 'city_2', segs: [3], duration: 135, type: 'Direct', status: 'available' },
  { id: 4, from: 'city_2', to: 'city_1', segs: [4], duration: 135, type: 'Direct', status: 'available' },
  { id: 5, from: 'city_1', to: 'city_3', segs: [5], duration: 165, type: 'Direct', status: 'available' },
  { id: 6, from: 'city_1', to: 'city_3', segs: [6], duration: 165, type: 'Direct', status: 'available' },
  { id: 7, from: 'city_3', to: 'city_1', segs: [7], duration: 165, type: 'Direct', status: 'available' },
  { id: 8, from: 'city_2', to: 'city_3', segs: [8], duration: 105, type: 'Direct', status: 'available' },
  { id: 9, from: 'city_2', to: 'city_3', segs: [9], duration: 105, type: 'Direct', status: 'available' },
  { id: 10, from: 'city_3', to: 'city_2', segs: [10], duration: 105, type: 'Direct', status: 'available' },
  { id: 11, from: 'city_1', to: 'city_4', segs: [11], duration: 135, type: 'Direct', status: 'available' },
  { id: 12, from: 'city_1', to: 'city_4', segs: [12], duration: 135, type: 'Direct', status: 'sold-out' },
  { id: 13, from: 'city_2', to: 'city_5', segs: [13], duration: 105, type: 'Direct', status: 'available' },
  { id: 14, from: 'city_2', to: 'city_5', segs: [14], duration: 105, type: 'Direct', status: 'available' },
  // Direct international
  { id: 15, from: 'city_1', to: 'city_13', segs: [15], duration: 210, type: 'Direct', status: 'available' },
  { id: 16, from: 'city_1', to: 'city_13', segs: [16], duration: 210, type: 'Direct', status: 'available' },
  { id: 17, from: 'city_2', to: 'city_13', segs: [17], duration: 195, type: 'Direct', status: 'available' },
  { id: 18, from: 'city_1', to: 'city_12', segs: [18], duration: 330, type: 'Direct', status: 'available' },
  { id: 19, from: 'city_1', to: 'city_12', segs: [19], duration: 330, type: 'Direct', status: 'available' },
  { id: 20, from: 'city_2', to: 'city_12', segs: [20], duration: 330, type: 'Direct', status: 'sold-out' },
  { id: 21, from: 'city_1', to: 'city_14', segs: [21], duration: 570, type: 'Direct', status: 'available' },
  { id: 22, from: 'city_1', to: 'city_14', segs: [22], duration: 570, type: 'Direct', status: 'available' },
  // 1 transit
  { id: 23, from: 'city_1', to: 'city_14', segs: [23, 24], duration: 690, type: '1 transit', status: 'available' },
  { id: 24, from: 'city_2', to: 'city_14', segs: [25, 26], duration: 660, type: '1 transit', status: 'available' },
  { id: 25, from: 'city_1', to: 'city_15', segs: [27, 28], duration: 1080, type: '1 transit', status: 'available' },
  // 2+ transit
  { id: 26, from: 'city_1', to: 'city_15', segs: [29, 30, 31], duration: 1440, type: '2+ transit', status: 'available' },
  { id: 27, from: 'city_2', to: 'city_15', segs: [32, 33, 34], duration: 1320, type: '2+ transit', status: 'available' },
];

// Generate flights for 7 days
export const FLIGHT_TABLE: Flight[] = [];
for (let day = 0; day < 7; day++) {
  BASE_FLIGHTS.forEach(flight => {
    FLIGHT_TABLE.push({
      id: `flight_${flight.id}_d${day}`,
      departureCityId: flight.from,
      arrivalCityId: flight.to,
      segmentIds: flight.segs.map(s => `seg_${s}_d${day}`),
      totalDurationMinutes: flight.duration,
      transitType: flight.type as 'Direct' | '1 transit' | '2+ transit',
      status: flight.status as 'available' | 'sold-out',
    });
  });
}

// ── Pricing (multiple classes per flight) ──────────────────────────

// Base pricing templates (per base flight)
const BASE_PRICING = [
  { flightId: 1, prices: [{ class: 'class_1', price: 85 }, { class: 'class_2', price: 140 }, { class: 'class_3', price: 310 }, { class: 'class_4', price: 567 }] },
  { flightId: 2, prices: [{ class: 'class_1', price: 92 }, { class: 'class_3', price: 340 }, { class: 'class_4', price: 530 }] },
  { flightId: 3, prices: [{ class: 'class_1', price: 72 }, { class: 'class_4', price: 418 }] },
  { flightId: 4, prices: [{ class: 'class_1', price: 88 }, { class: 'class_3', price: 295 }, { class: 'class_4', price: 430 }] },
  { flightId: 5, prices: [{ class: 'class_1', price: 95 }, { class: 'class_3', price: 350 }] },
  { flightId: 6, prices: [{ class: 'class_1', price: 105 }, { class: 'class_2', price: 165 }] },
  { flightId: 7, prices: [{ class: 'class_1', price: 98 }] },
  { flightId: 8, prices: [{ class: 'class_1', price: 68 }, { class: 'class_2', price: 110 }] },
  { flightId: 9, prices: [{ class: 'class_1', price: 62 }] },
  { flightId: 10, prices: [{ class: 'class_1', price: 75 }, { class: 'class_3', price: 280 }] },
  { flightId: 11, prices: [{ class: 'class_1', price: 78 }] },
  { flightId: 12, prices: [{ class: 'class_1', price: 82 }] },
  { flightId: 13, prices: [{ class: 'class_1', price: 65 }] },
  { flightId: 14, prices: [{ class: 'class_1', price: 58 }] },
  { flightId: 15, prices: [{ class: 'class_1', price: 220 }, { class: 'class_3', price: 680 }, { class: 'class_4', price: 1250 }] },
  { flightId: 16, prices: [{ class: 'class_1', price: 195 }] },
  { flightId: 17, prices: [{ class: 'class_1', price: 210 }, { class: 'class_3', price: 650 }] },
  { flightId: 18, prices: [{ class: 'class_1', price: 310 }, { class: 'class_3', price: 890 }] },
  { flightId: 19, prices: [{ class: 'class_1', price: 275 }] },
  { flightId: 20, prices: [{ class: 'class_1', price: 320 }] },
  { flightId: 21, prices: [{ class: 'class_1', price: 480 }, { class: 'class_3', price: 1450 }, { class: 'class_4', price: 2800 }] },
  { flightId: 22, prices: [{ class: 'class_1', price: 420 }, { class: 'class_3', price: 1200 }] },
  { flightId: 23, prices: [{ class: 'class_1', price: 385 }, { class: 'class_3', price: 1100 }] },
  { flightId: 24, prices: [{ class: 'class_1', price: 395 }] },
  { flightId: 25, prices: [{ class: 'class_1', price: 620 }, { class: 'class_3', price: 1850 }] },
  { flightId: 26, prices: [{ class: 'class_1', price: 540 }] },
  { flightId: 27, prices: [{ class: 'class_1', price: 580 }, { class: 'class_3', price: 1750 }] },
];

// Generate pricing for all flights across 7 days
export const PRICING_TABLE: FlightPricing[] = [];
for (let day = 0; day < 7; day++) {
  BASE_PRICING.forEach(fp => {
    fp.prices.forEach((p, idx) => {
      PRICING_TABLE.push({
        id: `pr_${fp.flightId}_${idx}_d${day}`,
        flightId: `flight_${fp.flightId}_d${day}`,
        classId: p.class,
        pricePerPassenger: p.price,
        currency: 'USD',
      });
    });
  });
}

// ── Facility mappings (per segment, not per flight) ────────────────

// ── Facility mappings (per segment, not per flight) ────────────────

// Base facility mappings (per base segment)
const BASE_FACILITY_MAPPINGS = [
  // IndiGo: baggage + power
  { segId: 1, facilities: ['fac_1', 'fac_5'] },
  { segId: 5, facilities: ['fac_1', 'fac_5'] },
  { segId: 8, facilities: ['fac_1'] },
  { segId: 11, facilities: ['fac_1'] },
  { segId: 13, facilities: ['fac_1'] },
  // Air India: baggage + meal + entertainment
  { segId: 2, facilities: ['fac_1', 'fac_2', 'fac_3'] },
  { segId: 6, facilities: ['fac_1', 'fac_2'] },
  { segId: 12, facilities: ['fac_1', 'fac_2'] },
  // SpiceJet: baggage only
  { segId: 3, facilities: ['fac_1'] },
  { segId: 9, facilities: ['fac_1'] },
  { segId: 14, facilities: ['fac_1'] },
  // Vistara: baggage + meal + wifi + power
  { segId: 4, facilities: ['fac_1', 'fac_2', 'fac_4', 'fac_5'] },
  { segId: 7, facilities: ['fac_1', 'fac_2', 'fac_4'] },
  { segId: 10, facilities: ['fac_1', 'fac_2'] },
  // Emirates: all facilities
  { segId: 15, facilities: ['fac_1', 'fac_2', 'fac_3', 'fac_4', 'fac_5'] },
  { segId: 17, facilities: ['fac_1', 'fac_2', 'fac_3', 'fac_4', 'fac_5'] },
  { segId: 23, facilities: ['fac_1', 'fac_2', 'fac_3', 'fac_4', 'fac_5'] },
  { segId: 24, facilities: ['fac_1', 'fac_2', 'fac_3', 'fac_4', 'fac_5'] },
  { segId: 25, facilities: ['fac_1', 'fac_2', 'fac_3', 'fac_4', 'fac_5'] },
  { segId: 26, facilities: ['fac_1', 'fac_2', 'fac_3', 'fac_4', 'fac_5'] },
  // Singapore Airlines: baggage + meal + entertainment + wifi
  { segId: 18, facilities: ['fac_1', 'fac_2', 'fac_3', 'fac_4'] },
  { segId: 20, facilities: ['fac_1', 'fac_2', 'fac_3', 'fac_4'] },
  // British Airways: baggage + meal + entertainment + power
  { segId: 21, facilities: ['fac_1', 'fac_2', 'fac_3', 'fac_5'] },
  { segId: 28, facilities: ['fac_1', 'fac_2', 'fac_3', 'fac_5'] },
];

// Generate facility mappings for all segments across 7 days
export const FLIGHT_FACILITY_MAPPING_TABLE: FlightFacilityMapping[] = [];
for (let day = 0; day < 7; day++) {
  BASE_FACILITY_MAPPINGS.forEach(fm => {
    fm.facilities.forEach((facId, idx) => {
      FLIGHT_FACILITY_MAPPING_TABLE.push({
        id: `ff_${fm.segId}_${idx}_d${day}`,
        segmentId: `seg_${fm.segId}_d${day}`,
        facilityId: facId,
      });
    });
  });
}

// ── Helper: format minutes as "Xh Ym" ─────────────────────────────

export function formatDuration(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

// ── Join helper: build FlightListing from normalized tables ────────

export function getAvailableFlights(classId?: string): FlightListing[] {
  const targetClassId = classId ?? 'class_1'; // default to Economy

  return FLIGHT_TABLE
    .filter(flight => {
      // must have pricing for the requested class
      return PRICING_TABLE.some(p => p.flightId === flight.id && p.classId === targetClassId);
    })
    .map(flight => {
      const departureCity = CITY_TABLE.find(c => c.id === flight.departureCityId)!;
      const arrivalCity = CITY_TABLE.find(c => c.id === flight.arrivalCityId)!;

      // Build segment details in order
      const segments: FlightSegmentDetail[] = flight.segmentIds.map(segId => {
        const seg = SEGMENT_TABLE.find(s => s.id === segId)!;
        const airline = AIRLINE_TABLE.find(a => a.id === seg.airlineId)!;
        const depCity = CITY_TABLE.find(c => c.id === seg.departureCityId)!;
        const arrCity = CITY_TABLE.find(c => c.id === seg.arrivalCityId)!;

        const facilityIds = FLIGHT_FACILITY_MAPPING_TABLE
          .filter(ffm => ffm.segmentId === segId)
          .map(ffm => ffm.facilityId);
        const facilities = FACILITY_TABLE.filter(f => facilityIds.includes(f.id));

        return {
          id: seg.id,
          airline,
          flightNumber: seg.flightNumber,
          departureCity: depCity,
          arrivalCity: arrCity,
          departureTime: seg.departureTime,
          arrivalTime: seg.arrivalTime,
          durationMinutes: seg.durationMinutes,
          facilities,
        };
      });

      // Build layovers between consecutive segments
      const layovers: LayoverDetail[] = [];
      for (let i = 0; i < segments.length - 1; i++) {
        const arrTime = new Date(segments[i].arrivalTime).getTime();
        const depTime = new Date(segments[i + 1].departureTime).getTime();
        const layoverMinutes = Math.round((depTime - arrTime) / 60000);
        layovers.push({
          city: segments[i].arrivalCity,
          durationMinutes: layoverMinutes > 0 ? layoverMinutes : 0,
        });
      }

      const pricing = PRICING_TABLE.find(p => p.flightId === flight.id && p.classId === targetClassId)!;
      const flightClass = CLASS_TABLE.find(c => c.id === targetClassId)!;

      return {
        id: flight.id,
        departureCity,
        arrivalCity,
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
