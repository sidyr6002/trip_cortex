import type {
  Airport, Airline, Facility, FlightClass, FlightSegment, Flight,
  FlightPricing, FlightFacilityMapping, FlightListing,
  FlightSegmentDetail, LayoverDetail
} from './schema';

// ── Reference Tables ───────────────────────────────────────────────

export const AIRPORT_TABLE: Airport[] = [
  { id: 'apt_1', name: 'Indira Gandhi International Airport', code: 'DEL', cityName: 'New Delhi', countryCode: 'IN', lat: 28.5562, lng: 77.1000 },
  { id: 'apt_2', name: 'Chhatrapati Shivaji Maharaj International Airport', code: 'BOM', cityName: 'Mumbai', countryCode: 'IN', lat: 19.0896, lng: 72.8656 },
  { id: 'apt_3', name: 'Kempegowda International Airport', code: 'BLR', cityName: 'Bangalore', countryCode: 'IN', lat: 13.1986, lng: 77.7066 },
  { id: 'apt_4', name: 'Rajiv Gandhi International Airport', code: 'HYD', cityName: 'Hyderabad', countryCode: 'IN', lat: 17.2403, lng: 78.4294 },
  { id: 'apt_5', name: 'Chennai International Airport', code: 'MAA', cityName: 'Chennai', countryCode: 'IN', lat: 12.9941, lng: 80.1709 },
  { id: 'apt_6', name: 'Netaji Subhas Chandra Bose International Airport', code: 'CCU', cityName: 'Kolkata', countryCode: 'IN', lat: 22.6547, lng: 88.4467 },
  { id: 'apt_7', name: 'Pune Airport', code: 'PNQ', cityName: 'Pune', countryCode: 'IN', lat: 18.5822, lng: 73.9197 },
  { id: 'apt_8', name: 'Sardar Vallabhbhai Patel International Airport', code: 'AMD', cityName: 'Ahmedabad', countryCode: 'IN', lat: 23.0772, lng: 72.6347 },
  { id: 'apt_9', name: 'Jaipur International Airport', code: 'JAI', cityName: 'Jaipur', countryCode: 'IN', lat: 26.8242, lng: 75.8122 },
  { id: 'apt_10', name: 'Surat Airport', code: 'STV', cityName: 'Surat', countryCode: 'IN', lat: 21.1141, lng: 72.7417 },
  { id: 'apt_11', name: 'Soekarno-Hatta International Airport', code: 'CGK', cityName: 'Jakarta', countryCode: 'ID', lat: -6.1256, lng: 106.6558 },
  { id: 'apt_12', name: 'Singapore Changi Airport', code: 'SIN', cityName: 'Singapore', countryCode: 'SG', lat: 1.3644, lng: 103.9915 },
  { id: 'apt_13', name: 'Dubai International Airport', code: 'DXB', cityName: 'Dubai', countryCode: 'AE', lat: 25.2532, lng: 55.3657 },
  { id: 'apt_14', name: 'London Heathrow Airport', code: 'LHR', cityName: 'London', countryCode: 'GB', lat: 51.4700, lng: -0.4543 },
  { id: 'apt_15', name: 'John F. Kennedy International Airport', code: 'JFK', cityName: 'New York', countryCode: 'US', lat: 40.6413, lng: -73.7781 },
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

// ── Flight Segments (individual non-stop hops) ─────────────────────

// Base segment templates (time only, no date)
const BASE_SEGMENTS = [
  // Domestic
  { id: 1, airlineId: 'air_1', flightNumber: '6E-2134', from: 'apt_1', to: 'apt_2', depTime: '06:00:00', duration: 135 },
  { id: 2, airlineId: 'air_2', flightNumber: 'AI-860', from: 'apt_1', to: 'apt_2', depTime: '11:30:00', duration: 135 },
  { id: 3, airlineId: 'air_3', flightNumber: 'SG-8194', from: 'apt_1', to: 'apt_2', depTime: '17:00:00', duration: 135 },
  { id: 4, airlineId: 'air_4', flightNumber: 'UK-995', from: 'apt_2', to: 'apt_1', depTime: '21:30:00', duration: 135 },
  { id: 5, airlineId: 'air_1', flightNumber: '6E-6112', from: 'apt_1', to: 'apt_3', depTime: '07:15:00', duration: 165 },
  { id: 6, airlineId: 'air_2', flightNumber: 'AI-804', from: 'apt_1', to: 'apt_3', depTime: '13:00:00', duration: 165 },
  { id: 7, airlineId: 'air_4', flightNumber: 'UK-829', from: 'apt_3', to: 'apt_1', depTime: '18:30:00', duration: 165 },
  { id: 8, airlineId: 'air_1', flightNumber: '6E-5327', from: 'apt_2', to: 'apt_3', depTime: '08:00:00', duration: 105 },
  { id: 9, airlineId: 'air_3', flightNumber: 'SG-1136', from: 'apt_2', to: 'apt_3', depTime: '14:30:00', duration: 105 },
  { id: 10, airlineId: 'air_4', flightNumber: 'UK-864', from: 'apt_3', to: 'apt_2', depTime: '20:00:00', duration: 105 },
  { id: 11, airlineId: 'air_1', flightNumber: '6E-2063', from: 'apt_1', to: 'apt_4', depTime: '09:30:00', duration: 135 },
  { id: 12, airlineId: 'air_2', flightNumber: 'AI-544', from: 'apt_1', to: 'apt_4', depTime: '16:00:00', duration: 135 },
  { id: 13, airlineId: 'air_1', flightNumber: '6E-5054', from: 'apt_2', to: 'apt_5', depTime: '10:00:00', duration: 105 },
  { id: 14, airlineId: 'air_3', flightNumber: 'SG-1024', from: 'apt_2', to: 'apt_5', depTime: '15:30:00', duration: 105 },
  // International
  { id: 15, airlineId: 'air_5', flightNumber: 'EK-512', from: 'apt_1', to: 'apt_13', depTime: '08:30:00', duration: 210 },
  { id: 16, airlineId: 'air_2', flightNumber: 'AI-995', from: 'apt_1', to: 'apt_13', depTime: '22:00:00', duration: 210 },
  { id: 17, airlineId: 'air_5', flightNumber: 'EK-500', from: 'apt_2', to: 'apt_13', depTime: '09:00:00', duration: 195 },
  { id: 18, airlineId: 'air_6', flightNumber: 'SQ-402', from: 'apt_1', to: 'apt_12', depTime: '07:00:00', duration: 330 },
  { id: 19, airlineId: 'air_2', flightNumber: 'AI-345', from: 'apt_1', to: 'apt_12', depTime: '23:00:00', duration: 330 },
  { id: 20, airlineId: 'air_6', flightNumber: 'SQ-424', from: 'apt_2', to: 'apt_12', depTime: '10:30:00', duration: 330 },
  { id: 21, airlineId: 'air_7', flightNumber: 'BA-142', from: 'apt_1', to: 'apt_14', depTime: '14:00:00', duration: 570 },
  { id: 22, airlineId: 'air_2', flightNumber: 'AI-161', from: 'apt_1', to: 'apt_14', depTime: '13:30:00', duration: 570 },
  // Transit legs
  { id: 23, airlineId: 'air_5', flightNumber: 'EK-514', from: 'apt_1', to: 'apt_13', depTime: '09:00:00', duration: 210 },
  { id: 24, airlineId: 'air_5', flightNumber: 'EK-029', from: 'apt_13', to: 'apt_14', depTime: '14:30:00', duration: 420 },
  { id: 25, airlineId: 'air_5', flightNumber: 'EK-502', from: 'apt_2', to: 'apt_13', depTime: '10:00:00', duration: 195 },
  { id: 26, airlineId: 'air_5', flightNumber: 'EK-031', from: 'apt_13', to: 'apt_14', depTime: '15:00:00', duration: 420 },
  { id: 27, airlineId: 'air_2', flightNumber: 'AI-191', from: 'apt_1', to: 'apt_14', depTime: '12:00:00', duration: 570 },
  { id: 28, airlineId: 'air_7', flightNumber: 'BA-117', from: 'apt_14', to: 'apt_15', depTime: '19:00:00', duration: 480 },
  { id: 29, airlineId: 'air_5', flightNumber: 'EK-516', from: 'apt_1', to: 'apt_13', depTime: '08:00:00', duration: 210 },
  { id: 30, airlineId: 'air_5', flightNumber: 'EK-003', from: 'apt_13', to: 'apt_14', depTime: '13:30:00', duration: 420 },
  { id: 31, airlineId: 'air_7', flightNumber: 'BA-115', from: 'apt_14', to: 'apt_15', depTime: '21:00:00', duration: 480 },
  { id: 32, airlineId: 'air_2', flightNumber: 'AI-866', from: 'apt_2', to: 'apt_1', depTime: '06:00:00', duration: 135 },
  { id: 33, airlineId: 'air_2', flightNumber: 'AI-111', from: 'apt_1', to: 'apt_14', depTime: '11:00:00', duration: 570 },
  { id: 34, airlineId: 'air_7', flightNumber: 'BA-119', from: 'apt_14', to: 'apt_15', depTime: '18:00:00', duration: 480 },

  // ── Additional domestic segments ─────────────────────────────────
  // DEL ↔ BOM (more timings)
  { id: 35, airlineId: 'air_4', flightNumber: 'UK-933', from: 'apt_1', to: 'apt_2', depTime: '09:00:00', duration: 130 },
  { id: 36, airlineId: 'air_1', flightNumber: '6E-2210', from: 'apt_1', to: 'apt_2', depTime: '20:30:00', duration: 140 },
  { id: 133, airlineId: 'air_4', flightNumber: 'UK-955', from: 'apt_1', to: 'apt_2', depTime: '14:00:00', duration: 125 },
  { id: 37, airlineId: 'air_3', flightNumber: 'SG-8170', from: 'apt_2', to: 'apt_1', depTime: '07:00:00', duration: 140 },
  { id: 38, airlineId: 'air_1', flightNumber: '6E-2290', from: 'apt_2', to: 'apt_1', depTime: '14:00:00', duration: 135 },

  // DEL ↔ BLR (more timings)
  { id: 39, airlineId: 'air_3', flightNumber: 'SG-8710', from: 'apt_1', to: 'apt_3', depTime: '19:00:00', duration: 170 },
  { id: 40, airlineId: 'air_1', flightNumber: '6E-6180', from: 'apt_3', to: 'apt_1', depTime: '06:00:00', duration: 160 },
  { id: 41, airlineId: 'air_2', flightNumber: 'AI-808', from: 'apt_3', to: 'apt_1', depTime: '12:00:00', duration: 165 },

  // BOM ↔ BLR (more timings)
  { id: 42, airlineId: 'air_4', flightNumber: 'UK-852', from: 'apt_2', to: 'apt_3', depTime: '19:00:00', duration: 100 },
  { id: 43, airlineId: 'air_2', flightNumber: 'AI-650', from: 'apt_3', to: 'apt_2', depTime: '07:30:00', duration: 100 },
  { id: 44, airlineId: 'air_1', flightNumber: '6E-5390', from: 'apt_3', to: 'apt_2', depTime: '15:00:00', duration: 110 },

  // DEL ↔ HYD (reverse + more)
  { id: 45, airlineId: 'air_4', flightNumber: 'UK-891', from: 'apt_1', to: 'apt_4', depTime: '06:30:00', duration: 130 },
  { id: 46, airlineId: 'air_1', flightNumber: '6E-2075', from: 'apt_4', to: 'apt_1', depTime: '08:00:00', duration: 135 },
  { id: 47, airlineId: 'air_2', flightNumber: 'AI-548', from: 'apt_4', to: 'apt_1', depTime: '17:30:00', duration: 140 },
  { id: 48, airlineId: 'air_3', flightNumber: 'SG-1250', from: 'apt_4', to: 'apt_1', depTime: '22:00:00', duration: 135 },

  // DEL ↔ MAA
  { id: 49, airlineId: 'air_1', flightNumber: '6E-2045', from: 'apt_1', to: 'apt_5', depTime: '07:00:00', duration: 175 },
  { id: 50, airlineId: 'air_2', flightNumber: 'AI-430', from: 'apt_1', to: 'apt_5', depTime: '14:30:00', duration: 170 },
  { id: 51, airlineId: 'air_4', flightNumber: 'UK-827', from: 'apt_1', to: 'apt_5', depTime: '21:00:00', duration: 175 },
  { id: 52, airlineId: 'air_1', flightNumber: '6E-2046', from: 'apt_5', to: 'apt_1', depTime: '06:00:00', duration: 180 },
  { id: 53, airlineId: 'air_2', flightNumber: 'AI-431', from: 'apt_5', to: 'apt_1', depTime: '13:00:00', duration: 175 },

  // DEL ↔ CCU
  { id: 54, airlineId: 'air_1', flightNumber: '6E-2310', from: 'apt_1', to: 'apt_6', depTime: '06:30:00', duration: 140 },
  { id: 55, airlineId: 'air_2', flightNumber: 'AI-020', from: 'apt_1', to: 'apt_6', depTime: '12:00:00', duration: 135 },
  { id: 56, airlineId: 'air_3', flightNumber: 'SG-8340', from: 'apt_1', to: 'apt_6', depTime: '18:30:00', duration: 145 },
  { id: 57, airlineId: 'air_1', flightNumber: '6E-2311', from: 'apt_6', to: 'apt_1', depTime: '07:00:00', duration: 140 },
  { id: 58, airlineId: 'air_2', flightNumber: 'AI-021', from: 'apt_6', to: 'apt_1', depTime: '15:00:00', duration: 135 },

  // BOM ↔ HYD
  { id: 59, airlineId: 'air_1', flightNumber: '6E-5410', from: 'apt_2', to: 'apt_4', depTime: '07:30:00', duration: 90 },
  { id: 60, airlineId: 'air_4', flightNumber: 'UK-876', from: 'apt_2', to: 'apt_4', depTime: '13:00:00', duration: 85 },
  { id: 61, airlineId: 'air_3', flightNumber: 'SG-1180', from: 'apt_2', to: 'apt_4', depTime: '19:30:00', duration: 90 },
  { id: 62, airlineId: 'air_1', flightNumber: '6E-5411', from: 'apt_4', to: 'apt_2', depTime: '06:00:00', duration: 90 },
  { id: 63, airlineId: 'air_2', flightNumber: 'AI-619', from: 'apt_4', to: 'apt_2', depTime: '16:00:00', duration: 85 },

  // BOM ↔ MAA (reverse + more)
  { id: 64, airlineId: 'air_4', flightNumber: 'UK-840', from: 'apt_2', to: 'apt_5', depTime: '20:00:00', duration: 110 },
  { id: 65, airlineId: 'air_1', flightNumber: '6E-5055', from: 'apt_5', to: 'apt_2', depTime: '06:30:00', duration: 105 },
  { id: 66, airlineId: 'air_2', flightNumber: 'AI-671', from: 'apt_5', to: 'apt_2', depTime: '14:00:00', duration: 110 },

  // BOM ↔ CCU
  { id: 67, airlineId: 'air_1', flightNumber: '6E-5520', from: 'apt_2', to: 'apt_6', depTime: '08:00:00', duration: 155 },
  { id: 68, airlineId: 'air_2', flightNumber: 'AI-676', from: 'apt_2', to: 'apt_6', depTime: '16:00:00', duration: 160 },
  { id: 69, airlineId: 'air_1', flightNumber: '6E-5521', from: 'apt_6', to: 'apt_2', depTime: '09:00:00', duration: 160 },
  { id: 70, airlineId: 'air_3', flightNumber: 'SG-1310', from: 'apt_6', to: 'apt_2', depTime: '18:00:00', duration: 155 },

  // BLR ↔ HYD
  { id: 71, airlineId: 'air_1', flightNumber: '6E-6310', from: 'apt_3', to: 'apt_4', depTime: '07:00:00', duration: 75 },
  { id: 72, airlineId: 'air_4', flightNumber: 'UK-880', from: 'apt_3', to: 'apt_4', depTime: '14:00:00', duration: 70 },
  { id: 73, airlineId: 'air_3', flightNumber: 'SG-1410', from: 'apt_3', to: 'apt_4', depTime: '20:00:00', duration: 75 },
  { id: 74, airlineId: 'air_1', flightNumber: '6E-6311', from: 'apt_4', to: 'apt_3', depTime: '08:30:00', duration: 75 },
  { id: 75, airlineId: 'air_2', flightNumber: 'AI-552', from: 'apt_4', to: 'apt_3', depTime: '17:00:00', duration: 70 },

  // BLR ↔ MAA
  { id: 76, airlineId: 'air_1', flightNumber: '6E-6410', from: 'apt_3', to: 'apt_5', depTime: '06:30:00', duration: 60 },
  { id: 77, airlineId: 'air_2', flightNumber: 'AI-570', from: 'apt_3', to: 'apt_5', depTime: '12:00:00', duration: 55 },
  { id: 78, airlineId: 'air_4', flightNumber: 'UK-845', from: 'apt_3', to: 'apt_5', depTime: '18:30:00', duration: 60 },
  { id: 79, airlineId: 'air_1', flightNumber: '6E-6411', from: 'apt_5', to: 'apt_3', depTime: '07:30:00', duration: 60 },
  { id: 80, airlineId: 'air_3', flightNumber: 'SG-1510', from: 'apt_5', to: 'apt_3', depTime: '16:00:00', duration: 55 },

  // BLR ↔ CCU
  { id: 81, airlineId: 'air_1', flightNumber: '6E-6510', from: 'apt_3', to: 'apt_6', depTime: '09:00:00', duration: 165 },
  { id: 82, airlineId: 'air_2', flightNumber: 'AI-575', from: 'apt_3', to: 'apt_6', depTime: '17:00:00', duration: 170 },
  { id: 83, airlineId: 'air_1', flightNumber: '6E-6511', from: 'apt_6', to: 'apt_3', depTime: '10:00:00', duration: 165 },

  // HYD ↔ MAA
  { id: 84, airlineId: 'air_1', flightNumber: '6E-7010', from: 'apt_4', to: 'apt_5', depTime: '07:00:00', duration: 75 },
  { id: 85, airlineId: 'air_3', flightNumber: 'SG-1610', from: 'apt_4', to: 'apt_5', depTime: '15:00:00', duration: 80 },
  { id: 86, airlineId: 'air_1', flightNumber: '6E-7011', from: 'apt_5', to: 'apt_4', depTime: '08:00:00', duration: 75 },
  { id: 87, airlineId: 'air_2', flightNumber: 'AI-560', from: 'apt_5', to: 'apt_4', depTime: '18:00:00', duration: 80 },

  // HYD ↔ CCU
  { id: 88, airlineId: 'air_1', flightNumber: '6E-7110', from: 'apt_4', to: 'apt_6', depTime: '10:00:00', duration: 140 },
  { id: 89, airlineId: 'air_2', flightNumber: 'AI-743', from: 'apt_4', to: 'apt_6', depTime: '19:00:00', duration: 145 },
  { id: 90, airlineId: 'air_1', flightNumber: '6E-7111', from: 'apt_6', to: 'apt_4', depTime: '11:00:00', duration: 140 },

  // MAA ↔ CCU
  { id: 91, airlineId: 'air_1', flightNumber: '6E-7210', from: 'apt_5', to: 'apt_6', depTime: '08:00:00', duration: 155 },
  { id: 92, airlineId: 'air_2', flightNumber: 'AI-880', from: 'apt_5', to: 'apt_6', depTime: '17:00:00', duration: 150 },
  { id: 93, airlineId: 'air_1', flightNumber: '6E-7211', from: 'apt_6', to: 'apt_5', depTime: '09:00:00', duration: 155 },
  { id: 94, airlineId: 'air_3', flightNumber: 'SG-1710', from: 'apt_6', to: 'apt_5', depTime: '19:00:00', duration: 150 },

  // DEL ↔ PNQ
  { id: 95, airlineId: 'air_1', flightNumber: '6E-2410', from: 'apt_1', to: 'apt_7', depTime: '08:00:00', duration: 130 },
  { id: 96, airlineId: 'air_2', flightNumber: 'AI-852', from: 'apt_1', to: 'apt_7', depTime: '16:00:00', duration: 125 },
  { id: 97, airlineId: 'air_1', flightNumber: '6E-2411', from: 'apt_7', to: 'apt_1', depTime: '10:00:00', duration: 130 },
  { id: 98, airlineId: 'air_3', flightNumber: 'SG-8410', from: 'apt_7', to: 'apt_1', depTime: '19:00:00', duration: 125 },

  // DEL ↔ AMD
  { id: 99, airlineId: 'air_1', flightNumber: '6E-2510', from: 'apt_1', to: 'apt_8', depTime: '07:30:00', duration: 110 },
  { id: 100, airlineId: 'air_4', flightNumber: 'UK-971', from: 'apt_1', to: 'apt_8', depTime: '15:00:00', duration: 105 },
  { id: 101, airlineId: 'air_1', flightNumber: '6E-2511', from: 'apt_8', to: 'apt_1', depTime: '09:00:00', duration: 110 },
  { id: 102, airlineId: 'air_2', flightNumber: 'AI-310', from: 'apt_8', to: 'apt_1', depTime: '18:00:00', duration: 105 },

  // DEL ↔ JAI
  { id: 103, airlineId: 'air_1', flightNumber: '6E-2610', from: 'apt_1', to: 'apt_9', depTime: '08:00:00', duration: 65 },
  { id: 104, airlineId: 'air_2', flightNumber: 'AI-470', from: 'apt_1', to: 'apt_9', depTime: '14:00:00', duration: 60 },
  { id: 105, airlineId: 'air_3', flightNumber: 'SG-8510', from: 'apt_1', to: 'apt_9', depTime: '20:00:00', duration: 65 },
  { id: 106, airlineId: 'air_1', flightNumber: '6E-2611', from: 'apt_9', to: 'apt_1', depTime: '07:00:00', duration: 65 },
  { id: 107, airlineId: 'air_4', flightNumber: 'UK-715', from: 'apt_9', to: 'apt_1', depTime: '17:00:00', duration: 60 },

  // BOM ↔ PNQ
  { id: 108, airlineId: 'air_1', flightNumber: '6E-5610', from: 'apt_2', to: 'apt_7', depTime: '07:00:00', duration: 55 },
  { id: 109, airlineId: 'air_4', flightNumber: 'UK-690', from: 'apt_2', to: 'apt_7', depTime: '15:00:00', duration: 50 },
  { id: 110, airlineId: 'air_1', flightNumber: '6E-5611', from: 'apt_7', to: 'apt_2', depTime: '08:00:00', duration: 55 },
  { id: 111, airlineId: 'air_3', flightNumber: 'SG-1810', from: 'apt_7', to: 'apt_2', depTime: '18:00:00', duration: 50 },

  // BOM ↔ AMD
  { id: 112, airlineId: 'air_1', flightNumber: '6E-5710', from: 'apt_2', to: 'apt_8', depTime: '06:30:00', duration: 75 },
  { id: 113, airlineId: 'air_2', flightNumber: 'AI-655', from: 'apt_2', to: 'apt_8', depTime: '14:00:00', duration: 70 },
  { id: 114, airlineId: 'air_1', flightNumber: '6E-5711', from: 'apt_8', to: 'apt_2', depTime: '09:00:00', duration: 75 },
  { id: 115, airlineId: 'air_4', flightNumber: 'UK-680', from: 'apt_8', to: 'apt_2', depTime: '17:00:00', duration: 70 },

  // BOM ↔ JAI
  { id: 116, airlineId: 'air_1', flightNumber: '6E-5810', from: 'apt_2', to: 'apt_9', depTime: '08:00:00', duration: 120 },
  { id: 117, airlineId: 'air_2', flightNumber: 'AI-680', from: 'apt_2', to: 'apt_9', depTime: '17:00:00', duration: 115 },
  { id: 118, airlineId: 'air_1', flightNumber: '6E-5811', from: 'apt_9', to: 'apt_2', depTime: '10:00:00', duration: 120 },

  // CCU ↔ HYD (already have 88-90, add CCU→BOM transit)
  // BLR ↔ PNQ
  { id: 119, airlineId: 'air_1', flightNumber: '6E-6610', from: 'apt_3', to: 'apt_7', depTime: '09:00:00', duration: 100 },
  { id: 120, airlineId: 'air_1', flightNumber: '6E-6611', from: 'apt_7', to: 'apt_3', depTime: '12:00:00', duration: 100 },

  // HYD ↔ BOM (already have 59-63)
  // Additional international
  // BLR → DXB
  { id: 121, airlineId: 'air_5', flightNumber: 'EK-569', from: 'apt_3', to: 'apt_13', depTime: '10:00:00', duration: 240 },
  { id: 122, airlineId: 'air_2', flightNumber: 'AI-971', from: 'apt_3', to: 'apt_13', depTime: '22:00:00', duration: 245 },
  // HYD → DXB
  { id: 123, airlineId: 'air_5', flightNumber: 'EK-527', from: 'apt_4', to: 'apt_13', depTime: '09:30:00', duration: 240 },
  // MAA → DXB
  { id: 124, airlineId: 'air_5', flightNumber: 'EK-545', from: 'apt_5', to: 'apt_13', depTime: '11:00:00', duration: 255 },
  { id: 125, airlineId: 'air_8', flightNumber: 'EY-237', from: 'apt_5', to: 'apt_13', depTime: '20:00:00', duration: 250 },
  // CCU → DXB
  { id: 126, airlineId: 'air_5', flightNumber: 'EK-571', from: 'apt_6', to: 'apt_13', depTime: '08:00:00', duration: 300 },
  // BLR → SIN
  { id: 127, airlineId: 'air_6', flightNumber: 'SQ-505', from: 'apt_3', to: 'apt_12', depTime: '08:00:00', duration: 270 },
  // MAA → SIN
  { id: 128, airlineId: 'air_6', flightNumber: 'SQ-529', from: 'apt_5', to: 'apt_12', depTime: '09:30:00', duration: 255 },
  // BOM → LHR
  { id: 129, airlineId: 'air_7', flightNumber: 'BA-138', from: 'apt_2', to: 'apt_14', depTime: '15:00:00', duration: 585 },
  { id: 130, airlineId: 'air_2', flightNumber: 'AI-131', from: 'apt_2', to: 'apt_14', depTime: '01:30:00', duration: 575 },
  // BLR → LHR (1 transit via DXB)
  { id: 131, airlineId: 'air_5', flightNumber: 'EK-568', from: 'apt_3', to: 'apt_13', depTime: '07:00:00', duration: 240 },
  { id: 132, airlineId: 'air_5', flightNumber: 'EK-005', from: 'apt_13', to: 'apt_14', depTime: '14:00:00', duration: 420 },
];

// Generate segments for 7 days
// NOTE: exported as a function so callers can invoke at request-time (not module-init time)
// Cloudflare Workers freeze Date during module evaluation, so new Date() at module level returns epoch.
export function buildSegmentTable(): FlightSegment[] {
  const table: FlightSegment[] = [];
  for (let day = 0; day < 7; day++) {
    const dateStr = getDateString(day);
    BASE_SEGMENTS.forEach(seg => {
      const depTime = `${dateStr}T${seg.depTime}`;
      const arrTime = addMinutesToTime(depTime, seg.duration);
      table.push({
        id: `seg_${seg.id}_d${day}`,
        airlineId: seg.airlineId,
        flightNumber: seg.flightNumber,
        departureAirportId: seg.from,
        arrivalAirportId: seg.to,
        departureTime: depTime,
        arrivalTime: arrTime,
        durationMinutes: seg.duration,
      });
    });
  }
  return table;
}
export const SEGMENT_TABLE: FlightSegment[] = buildSegmentTable();

// ── Flights (journeys composed of segments) ────────────────────────

// Base flight templates
const BASE_FLIGHTS = [
  // Direct domestic
  { id: 1, from: 'apt_1', to: 'apt_2', segs: [1], duration: 135, type: 'Direct', status: 'available' },
  { id: 2, from: 'apt_1', to: 'apt_2', segs: [2], duration: 135, type: 'Direct', status: 'available' },
  { id: 3, from: 'apt_1', to: 'apt_2', segs: [3], duration: 135, type: 'Direct', status: 'available' },
  { id: 4, from: 'apt_2', to: 'apt_1', segs: [4], duration: 135, type: 'Direct', status: 'available' },
  { id: 5, from: 'apt_1', to: 'apt_3', segs: [5], duration: 165, type: 'Direct', status: 'available' },
  { id: 6, from: 'apt_1', to: 'apt_3', segs: [6], duration: 165, type: 'Direct', status: 'available' },
  { id: 7, from: 'apt_3', to: 'apt_1', segs: [7], duration: 165, type: 'Direct', status: 'available' },
  { id: 8, from: 'apt_2', to: 'apt_3', segs: [8], duration: 105, type: 'Direct', status: 'available' },
  { id: 9, from: 'apt_2', to: 'apt_3', segs: [9], duration: 105, type: 'Direct', status: 'available' },
  { id: 10, from: 'apt_3', to: 'apt_2', segs: [10], duration: 105, type: 'Direct', status: 'available' },
  { id: 11, from: 'apt_1', to: 'apt_4', segs: [11], duration: 135, type: 'Direct', status: 'available' },
  { id: 12, from: 'apt_1', to: 'apt_4', segs: [12], duration: 135, type: 'Direct', status: 'sold-out' },
  { id: 13, from: 'apt_2', to: 'apt_5', segs: [13], duration: 105, type: 'Direct', status: 'available' },
  { id: 14, from: 'apt_2', to: 'apt_5', segs: [14], duration: 105, type: 'Direct', status: 'available' },
  // Direct international
  { id: 15, from: 'apt_1', to: 'apt_13', segs: [15], duration: 210, type: 'Direct', status: 'available' },
  { id: 16, from: 'apt_1', to: 'apt_13', segs: [16], duration: 210, type: 'Direct', status: 'available' },
  { id: 17, from: 'apt_2', to: 'apt_13', segs: [17], duration: 195, type: 'Direct', status: 'available' },
  { id: 18, from: 'apt_1', to: 'apt_12', segs: [18], duration: 330, type: 'Direct', status: 'available' },
  { id: 19, from: 'apt_1', to: 'apt_12', segs: [19], duration: 330, type: 'Direct', status: 'available' },
  { id: 20, from: 'apt_2', to: 'apt_12', segs: [20], duration: 330, type: 'Direct', status: 'sold-out' },
  { id: 21, from: 'apt_1', to: 'apt_14', segs: [21], duration: 570, type: 'Direct', status: 'available' },
  { id: 22, from: 'apt_1', to: 'apt_14', segs: [22], duration: 570, type: 'Direct', status: 'available' },
  // 1 transit
  { id: 23, from: 'apt_1', to: 'apt_14', segs: [23, 24], duration: 690, type: '1 transit', status: 'available' },
  { id: 24, from: 'apt_2', to: 'apt_14', segs: [25, 26], duration: 660, type: '1 transit', status: 'available' },
  { id: 25, from: 'apt_1', to: 'apt_15', segs: [27, 28], duration: 1080, type: '1 transit', status: 'available' },
  // 2+ transit
  { id: 26, from: 'apt_1', to: 'apt_15', segs: [29, 30, 31], duration: 1440, type: '2+ transit', status: 'available' },
  { id: 27, from: 'apt_2', to: 'apt_15', segs: [32, 33, 34], duration: 1320, type: '2+ transit', status: 'available' },

  // ── Additional domestic direct flights ───────────────────────────
  // DEL ↔ BOM
  { id: 28, from: 'apt_1', to: 'apt_2', segs: [35], duration: 130, type: 'Direct', status: 'available' },
  { id: 29, from: 'apt_1', to: 'apt_2', segs: [36], duration: 140, type: 'Direct', status: 'available' },
  { id: 134, from: 'apt_1', to: 'apt_2', segs: [133], duration: 125, type: 'Direct', status: 'available' },
  { id: 30, from: 'apt_2', to: 'apt_1', segs: [37], duration: 140, type: 'Direct', status: 'available' },
  { id: 31, from: 'apt_2', to: 'apt_1', segs: [38], duration: 135, type: 'Direct', status: 'available' },
  // DEL ↔ BLR
  { id: 32, from: 'apt_1', to: 'apt_3', segs: [39], duration: 170, type: 'Direct', status: 'available' },
  { id: 33, from: 'apt_3', to: 'apt_1', segs: [40], duration: 160, type: 'Direct', status: 'available' },
  { id: 34, from: 'apt_3', to: 'apt_1', segs: [41], duration: 165, type: 'Direct', status: 'available' },
  // BOM ↔ BLR
  { id: 35, from: 'apt_2', to: 'apt_3', segs: [42], duration: 100, type: 'Direct', status: 'available' },
  { id: 36, from: 'apt_3', to: 'apt_2', segs: [43], duration: 100, type: 'Direct', status: 'available' },
  { id: 37, from: 'apt_3', to: 'apt_2', segs: [44], duration: 110, type: 'Direct', status: 'sold-out' },
  // DEL ↔ HYD
  { id: 38, from: 'apt_1', to: 'apt_4', segs: [45], duration: 130, type: 'Direct', status: 'available' },
  { id: 39, from: 'apt_4', to: 'apt_1', segs: [46], duration: 135, type: 'Direct', status: 'available' },
  { id: 40, from: 'apt_4', to: 'apt_1', segs: [47], duration: 140, type: 'Direct', status: 'available' },
  { id: 41, from: 'apt_4', to: 'apt_1', segs: [48], duration: 135, type: 'Direct', status: 'sold-out' },
  // DEL ↔ MAA
  { id: 42, from: 'apt_1', to: 'apt_5', segs: [49], duration: 175, type: 'Direct', status: 'available' },
  { id: 43, from: 'apt_1', to: 'apt_5', segs: [50], duration: 170, type: 'Direct', status: 'available' },
  { id: 44, from: 'apt_1', to: 'apt_5', segs: [51], duration: 175, type: 'Direct', status: 'available' },
  { id: 45, from: 'apt_5', to: 'apt_1', segs: [52], duration: 180, type: 'Direct', status: 'available' },
  { id: 46, from: 'apt_5', to: 'apt_1', segs: [53], duration: 175, type: 'Direct', status: 'available' },
  // DEL ↔ CCU
  { id: 47, from: 'apt_1', to: 'apt_6', segs: [54], duration: 140, type: 'Direct', status: 'available' },
  { id: 48, from: 'apt_1', to: 'apt_6', segs: [55], duration: 135, type: 'Direct', status: 'available' },
  { id: 49, from: 'apt_1', to: 'apt_6', segs: [56], duration: 145, type: 'Direct', status: 'sold-out' },
  { id: 50, from: 'apt_6', to: 'apt_1', segs: [57], duration: 140, type: 'Direct', status: 'available' },
  { id: 51, from: 'apt_6', to: 'apt_1', segs: [58], duration: 135, type: 'Direct', status: 'available' },
  // BOM ↔ HYD
  { id: 52, from: 'apt_2', to: 'apt_4', segs: [59], duration: 90, type: 'Direct', status: 'available' },
  { id: 53, from: 'apt_2', to: 'apt_4', segs: [60], duration: 85, type: 'Direct', status: 'available' },
  { id: 54, from: 'apt_2', to: 'apt_4', segs: [61], duration: 90, type: 'Direct', status: 'available' },
  { id: 55, from: 'apt_4', to: 'apt_2', segs: [62], duration: 90, type: 'Direct', status: 'available' },
  { id: 56, from: 'apt_4', to: 'apt_2', segs: [63], duration: 85, type: 'Direct', status: 'available' },
  // BOM ↔ MAA
  { id: 57, from: 'apt_2', to: 'apt_5', segs: [64], duration: 110, type: 'Direct', status: 'available' },
  { id: 58, from: 'apt_5', to: 'apt_2', segs: [65], duration: 105, type: 'Direct', status: 'available' },
  { id: 59, from: 'apt_5', to: 'apt_2', segs: [66], duration: 110, type: 'Direct', status: 'available' },
  // BOM ↔ CCU
  { id: 60, from: 'apt_2', to: 'apt_6', segs: [67], duration: 155, type: 'Direct', status: 'available' },
  { id: 61, from: 'apt_2', to: 'apt_6', segs: [68], duration: 160, type: 'Direct', status: 'available' },
  { id: 62, from: 'apt_6', to: 'apt_2', segs: [69], duration: 160, type: 'Direct', status: 'available' },
  { id: 63, from: 'apt_6', to: 'apt_2', segs: [70], duration: 155, type: 'Direct', status: 'available' },
  // BLR ↔ HYD
  { id: 64, from: 'apt_3', to: 'apt_4', segs: [71], duration: 75, type: 'Direct', status: 'available' },
  { id: 65, from: 'apt_3', to: 'apt_4', segs: [72], duration: 70, type: 'Direct', status: 'available' },
  { id: 66, from: 'apt_3', to: 'apt_4', segs: [73], duration: 75, type: 'Direct', status: 'available' },
  { id: 67, from: 'apt_4', to: 'apt_3', segs: [74], duration: 75, type: 'Direct', status: 'available' },
  { id: 68, from: 'apt_4', to: 'apt_3', segs: [75], duration: 70, type: 'Direct', status: 'available' },
  // BLR ↔ MAA
  { id: 69, from: 'apt_3', to: 'apt_5', segs: [76], duration: 60, type: 'Direct', status: 'available' },
  { id: 70, from: 'apt_3', to: 'apt_5', segs: [77], duration: 55, type: 'Direct', status: 'available' },
  { id: 71, from: 'apt_3', to: 'apt_5', segs: [78], duration: 60, type: 'Direct', status: 'available' },
  { id: 72, from: 'apt_5', to: 'apt_3', segs: [79], duration: 60, type: 'Direct', status: 'available' },
  { id: 73, from: 'apt_5', to: 'apt_3', segs: [80], duration: 55, type: 'Direct', status: 'sold-out' },
  // BLR ↔ CCU
  { id: 74, from: 'apt_3', to: 'apt_6', segs: [81], duration: 165, type: 'Direct', status: 'available' },
  { id: 75, from: 'apt_3', to: 'apt_6', segs: [82], duration: 170, type: 'Direct', status: 'available' },
  { id: 76, from: 'apt_6', to: 'apt_3', segs: [83], duration: 165, type: 'Direct', status: 'available' },
  // HYD ↔ MAA
  { id: 77, from: 'apt_4', to: 'apt_5', segs: [84], duration: 75, type: 'Direct', status: 'available' },
  { id: 78, from: 'apt_4', to: 'apt_5', segs: [85], duration: 80, type: 'Direct', status: 'available' },
  { id: 79, from: 'apt_5', to: 'apt_4', segs: [86], duration: 75, type: 'Direct', status: 'available' },
  { id: 80, from: 'apt_5', to: 'apt_4', segs: [87], duration: 80, type: 'Direct', status: 'available' },
  // HYD ↔ CCU
  { id: 81, from: 'apt_4', to: 'apt_6', segs: [88], duration: 140, type: 'Direct', status: 'available' },
  { id: 82, from: 'apt_4', to: 'apt_6', segs: [89], duration: 145, type: 'Direct', status: 'available' },
  { id: 83, from: 'apt_6', to: 'apt_4', segs: [90], duration: 140, type: 'Direct', status: 'available' },
  // MAA ↔ CCU
  { id: 84, from: 'apt_5', to: 'apt_6', segs: [91], duration: 155, type: 'Direct', status: 'available' },
  { id: 85, from: 'apt_5', to: 'apt_6', segs: [92], duration: 150, type: 'Direct', status: 'available' },
  { id: 86, from: 'apt_6', to: 'apt_5', segs: [93], duration: 155, type: 'Direct', status: 'available' },
  { id: 87, from: 'apt_6', to: 'apt_5', segs: [94], duration: 150, type: 'Direct', status: 'available' },
  // DEL ↔ PNQ
  { id: 88, from: 'apt_1', to: 'apt_7', segs: [95], duration: 130, type: 'Direct', status: 'available' },
  { id: 89, from: 'apt_1', to: 'apt_7', segs: [96], duration: 125, type: 'Direct', status: 'available' },
  { id: 90, from: 'apt_7', to: 'apt_1', segs: [97], duration: 130, type: 'Direct', status: 'available' },
  { id: 91, from: 'apt_7', to: 'apt_1', segs: [98], duration: 125, type: 'Direct', status: 'available' },
  // DEL ↔ AMD
  { id: 92, from: 'apt_1', to: 'apt_8', segs: [99], duration: 110, type: 'Direct', status: 'available' },
  { id: 93, from: 'apt_1', to: 'apt_8', segs: [100], duration: 105, type: 'Direct', status: 'available' },
  { id: 94, from: 'apt_8', to: 'apt_1', segs: [101], duration: 110, type: 'Direct', status: 'available' },
  { id: 95, from: 'apt_8', to: 'apt_1', segs: [102], duration: 105, type: 'Direct', status: 'available' },
  // DEL ↔ JAI
  { id: 96, from: 'apt_1', to: 'apt_9', segs: [103], duration: 65, type: 'Direct', status: 'available' },
  { id: 97, from: 'apt_1', to: 'apt_9', segs: [104], duration: 60, type: 'Direct', status: 'available' },
  { id: 98, from: 'apt_1', to: 'apt_9', segs: [105], duration: 65, type: 'Direct', status: 'available' },
  { id: 99, from: 'apt_9', to: 'apt_1', segs: [106], duration: 65, type: 'Direct', status: 'available' },
  { id: 100, from: 'apt_9', to: 'apt_1', segs: [107], duration: 60, type: 'Direct', status: 'available' },
  // BOM ↔ PNQ
  { id: 101, from: 'apt_2', to: 'apt_7', segs: [108], duration: 55, type: 'Direct', status: 'available' },
  { id: 102, from: 'apt_2', to: 'apt_7', segs: [109], duration: 50, type: 'Direct', status: 'available' },
  { id: 103, from: 'apt_7', to: 'apt_2', segs: [110], duration: 55, type: 'Direct', status: 'available' },
  { id: 104, from: 'apt_7', to: 'apt_2', segs: [111], duration: 50, type: 'Direct', status: 'available' },
  // BOM ↔ AMD
  { id: 105, from: 'apt_2', to: 'apt_8', segs: [112], duration: 75, type: 'Direct', status: 'available' },
  { id: 106, from: 'apt_2', to: 'apt_8', segs: [113], duration: 70, type: 'Direct', status: 'available' },
  { id: 107, from: 'apt_8', to: 'apt_2', segs: [114], duration: 75, type: 'Direct', status: 'available' },
  { id: 108, from: 'apt_8', to: 'apt_2', segs: [115], duration: 70, type: 'Direct', status: 'available' },
  // BOM ↔ JAI
  { id: 109, from: 'apt_2', to: 'apt_9', segs: [116], duration: 120, type: 'Direct', status: 'available' },
  { id: 110, from: 'apt_2', to: 'apt_9', segs: [117], duration: 115, type: 'Direct', status: 'available' },
  { id: 111, from: 'apt_9', to: 'apt_2', segs: [118], duration: 120, type: 'Direct', status: 'available' },
  // BLR ↔ PNQ
  { id: 112, from: 'apt_3', to: 'apt_7', segs: [119], duration: 100, type: 'Direct', status: 'available' },
  { id: 113, from: 'apt_7', to: 'apt_3', segs: [120], duration: 100, type: 'Direct', status: 'available' },

  // ── Additional international direct flights ──────────────────────
  // BLR → DXB
  { id: 114, from: 'apt_3', to: 'apt_13', segs: [121], duration: 240, type: 'Direct', status: 'available' },
  { id: 115, from: 'apt_3', to: 'apt_13', segs: [122], duration: 245, type: 'Direct', status: 'available' },
  // HYD → DXB
  { id: 116, from: 'apt_4', to: 'apt_13', segs: [123], duration: 240, type: 'Direct', status: 'available' },
  // MAA → DXB
  { id: 117, from: 'apt_5', to: 'apt_13', segs: [124], duration: 255, type: 'Direct', status: 'available' },
  { id: 118, from: 'apt_5', to: 'apt_13', segs: [125], duration: 250, type: 'Direct', status: 'available' },
  // CCU → DXB
  { id: 119, from: 'apt_6', to: 'apt_13', segs: [126], duration: 300, type: 'Direct', status: 'available' },
  // BLR → SIN
  { id: 120, from: 'apt_3', to: 'apt_12', segs: [127], duration: 270, type: 'Direct', status: 'available' },
  // MAA → SIN
  { id: 121, from: 'apt_5', to: 'apt_12', segs: [128], duration: 255, type: 'Direct', status: 'available' },
  // BOM → LHR
  { id: 122, from: 'apt_2', to: 'apt_14', segs: [129], duration: 585, type: 'Direct', status: 'available' },
  { id: 123, from: 'apt_2', to: 'apt_14', segs: [130], duration: 575, type: 'Direct', status: 'available' },
  // BLR → LHR (1 transit via DXB)
  { id: 124, from: 'apt_3', to: 'apt_14', segs: [131, 132], duration: 720, type: '1 transit', status: 'available' },
  // Additional sold-out flights across popular routes
  { id: 125, from: 'apt_1', to: 'apt_2', segs: [1], duration: 135, type: 'Direct', status: 'sold-out' },   // DEL → BOM
  { id: 126, from: 'apt_2', to: 'apt_1', segs: [4], duration: 135, type: 'Direct', status: 'sold-out' },   // BOM → DEL
  { id: 127, from: 'apt_1', to: 'apt_3', segs: [5], duration: 165, type: 'Direct', status: 'sold-out' },   // DEL → BLR
  { id: 128, from: 'apt_2', to: 'apt_4', segs: [59], duration: 90, type: 'Direct', status: 'sold-out' },   // BOM → HYD
  { id: 129, from: 'apt_3', to: 'apt_4', segs: [71], duration: 75, type: 'Direct', status: 'sold-out' },   // BLR → HYD
  { id: 130, from: 'apt_4', to: 'apt_2', segs: [62], duration: 90, type: 'Direct', status: 'sold-out' },   // HYD → BOM
  { id: 131, from: 'apt_6', to: 'apt_2', segs: [69], duration: 160, type: 'Direct', status: 'sold-out' },  // CCU → BOM
  { id: 132, from: 'apt_1', to: 'apt_13', segs: [15], duration: 210, type: 'Direct', status: 'sold-out' }, // DEL → DXB
  { id: 133, from: 'apt_3', to: 'apt_12', segs: [127], duration: 270, type: 'Direct', status: 'sold-out' }, // BLR → SIN
];

// Generate flights for 7 days
export const FLIGHT_TABLE: Flight[] = [];
for (let day = 0; day < 7; day++) {
  BASE_FLIGHTS.forEach(flight => {
    FLIGHT_TABLE.push({
      id: `flight_${flight.id}_d${day}`,
      departureAirportId: flight.from,
      arrivalAirportId: flight.to,
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

  // ── Additional domestic pricing ──────────────────────────────────
  // DEL ↔ BOM
  { flightId: 28, prices: [{ class: 'class_1', price: 98 }, { class: 'class_2', price: 155 }, { class: 'class_3', price: 330 }, { class: 'class_4', price: 580 }] },
  { flightId: 29, prices: [{ class: 'class_1', price: 78 }, { class: 'class_2', price: 130 }] },
  { flightId: 30, prices: [{ class: 'class_1', price: 75 }, { class: 'class_3', price: 285 }] },
  { flightId: 31, prices: [{ class: 'class_1', price: 82 }, { class: 'class_2', price: 138 }] },
  // DEL ↔ BLR
  { flightId: 32, prices: [{ class: 'class_1', price: 88 }] },
  { flightId: 33, prices: [{ class: 'class_1', price: 92 }, { class: 'class_3', price: 340 }] },
  { flightId: 34, prices: [{ class: 'class_1', price: 102 }, { class: 'class_2', price: 160 }] },
  // BOM ↔ BLR
  { flightId: 35, prices: [{ class: 'class_1', price: 72 }, { class: 'class_2', price: 118 }, { class: 'class_3', price: 290 }] },
  { flightId: 36, prices: [{ class: 'class_1', price: 70 }, { class: 'class_2', price: 115 }] },
  { flightId: 37, prices: [{ class: 'class_1', price: 65 }] },
  // DEL ↔ HYD
  { flightId: 38, prices: [{ class: 'class_1', price: 82 }, { class: 'class_2', price: 135 }, { class: 'class_3', price: 310 }] },
  { flightId: 39, prices: [{ class: 'class_1', price: 80 }, { class: 'class_3', price: 300 }] },
  { flightId: 40, prices: [{ class: 'class_1', price: 88 }, { class: 'class_2', price: 142 }] },
  { flightId: 41, prices: [{ class: 'class_1', price: 76 }] },
  // DEL ↔ MAA
  { flightId: 42, prices: [{ class: 'class_1', price: 105 }, { class: 'class_2', price: 168 }] },
  { flightId: 43, prices: [{ class: 'class_1', price: 112 }, { class: 'class_3', price: 380 }] },
  { flightId: 44, prices: [{ class: 'class_1', price: 98 }, { class: 'class_2', price: 155 }, { class: 'class_3', price: 360 }] },
  { flightId: 45, prices: [{ class: 'class_1', price: 110 }] },
  { flightId: 46, prices: [{ class: 'class_1', price: 108 }, { class: 'class_2', price: 170 }] },
  // DEL ↔ CCU
  { flightId: 47, prices: [{ class: 'class_1', price: 88 }, { class: 'class_2', price: 142 }] },
  { flightId: 48, prices: [{ class: 'class_1', price: 95 }, { class: 'class_3', price: 320 }] },
  { flightId: 49, prices: [{ class: 'class_1', price: 82 }] },
  { flightId: 50, prices: [{ class: 'class_1', price: 90 }, { class: 'class_2', price: 145 }] },
  { flightId: 51, prices: [{ class: 'class_1', price: 92 }] },
  // BOM ↔ HYD
  { flightId: 52, prices: [{ class: 'class_1', price: 58 }, { class: 'class_2', price: 95 }] },
  { flightId: 53, prices: [{ class: 'class_1', price: 62 }, { class: 'class_2', price: 100 }, { class: 'class_3', price: 240 }] },
  { flightId: 54, prices: [{ class: 'class_1', price: 55 }] },
  { flightId: 55, prices: [{ class: 'class_1', price: 60 }, { class: 'class_3', price: 235 }] },
  { flightId: 56, prices: [{ class: 'class_1', price: 65 }, { class: 'class_2', price: 105 }] },
  // BOM ↔ MAA
  { flightId: 57, prices: [{ class: 'class_1', price: 68 }, { class: 'class_2', price: 112 }, { class: 'class_3', price: 270 }] },
  { flightId: 58, prices: [{ class: 'class_1', price: 62 }] },
  { flightId: 59, prices: [{ class: 'class_1', price: 70 }, { class: 'class_2', price: 115 }] },
  // BOM ↔ CCU
  { flightId: 60, prices: [{ class: 'class_1', price: 95 }, { class: 'class_2', price: 152 }] },
  { flightId: 61, prices: [{ class: 'class_1', price: 102 }, { class: 'class_3', price: 340 }] },
  { flightId: 62, prices: [{ class: 'class_1', price: 98 }] },
  { flightId: 63, prices: [{ class: 'class_1', price: 90 }, { class: 'class_2', price: 148 }] },
  // BLR ↔ HYD
  { flightId: 64, prices: [{ class: 'class_1', price: 48 }, { class: 'class_2', price: 78 }] },
  { flightId: 65, prices: [{ class: 'class_1', price: 55 }, { class: 'class_2', price: 88 }, { class: 'class_3', price: 210 }] },
  { flightId: 66, prices: [{ class: 'class_1', price: 45 }] },
  { flightId: 67, prices: [{ class: 'class_1', price: 50 }, { class: 'class_3', price: 200 }] },
  { flightId: 68, prices: [{ class: 'class_1', price: 52 }, { class: 'class_2', price: 85 }] },
  // BLR ↔ MAA
  { flightId: 69, prices: [{ class: 'class_1', price: 38 }, { class: 'class_2', price: 62 }] },
  { flightId: 70, prices: [{ class: 'class_1', price: 42 }, { class: 'class_2', price: 68 }, { class: 'class_3', price: 165 }] },
  { flightId: 71, prices: [{ class: 'class_1', price: 40 }, { class: 'class_3', price: 160 }] },
  { flightId: 72, prices: [{ class: 'class_1', price: 39 }] },
  { flightId: 73, prices: [{ class: 'class_1', price: 35 }] },
  // BLR ↔ CCU
  { flightId: 74, prices: [{ class: 'class_1', price: 105 }, { class: 'class_2', price: 168 }] },
  { flightId: 75, prices: [{ class: 'class_1', price: 112 }] },
  { flightId: 76, prices: [{ class: 'class_1', price: 108 }, { class: 'class_3', price: 365 }] },
  // HYD ↔ MAA
  { flightId: 77, prices: [{ class: 'class_1', price: 45 }, { class: 'class_2', price: 72 }] },
  { flightId: 78, prices: [{ class: 'class_1', price: 48 }] },
  { flightId: 79, prices: [{ class: 'class_1', price: 42 }, { class: 'class_3', price: 175 }] },
  { flightId: 80, prices: [{ class: 'class_1', price: 50 }, { class: 'class_2', price: 80 }] },
  // HYD ↔ CCU
  { flightId: 81, prices: [{ class: 'class_1', price: 92 }, { class: 'class_2', price: 148 }] },
  { flightId: 82, prices: [{ class: 'class_1', price: 98 }] },
  { flightId: 83, prices: [{ class: 'class_1', price: 95 }, { class: 'class_3', price: 320 }] },
  // MAA ↔ CCU
  { flightId: 84, prices: [{ class: 'class_1', price: 98 }, { class: 'class_2', price: 155 }] },
  { flightId: 85, prices: [{ class: 'class_1', price: 105 }, { class: 'class_3', price: 350 }] },
  { flightId: 86, prices: [{ class: 'class_1', price: 100 }] },
  { flightId: 87, prices: [{ class: 'class_1', price: 95 }, { class: 'class_2', price: 152 }] },
  // DEL ↔ PNQ
  { flightId: 88, prices: [{ class: 'class_1', price: 82 }, { class: 'class_2', price: 132 }] },
  { flightId: 89, prices: [{ class: 'class_1', price: 90 }, { class: 'class_3', price: 310 }] },
  { flightId: 90, prices: [{ class: 'class_1', price: 85 }] },
  { flightId: 91, prices: [{ class: 'class_1', price: 78 }, { class: 'class_2', price: 128 }] },
  // DEL ↔ AMD
  { flightId: 92, prices: [{ class: 'class_1', price: 72 }, { class: 'class_2', price: 118 }] },
  { flightId: 93, prices: [{ class: 'class_1', price: 78 }, { class: 'class_2', price: 125 }, { class: 'class_3', price: 280 }] },
  { flightId: 94, prices: [{ class: 'class_1', price: 75 }] },
  { flightId: 95, prices: [{ class: 'class_1', price: 70 }, { class: 'class_2', price: 115 }] },
  // DEL ↔ JAI
  { flightId: 96, prices: [{ class: 'class_1', price: 42 }, { class: 'class_2', price: 68 }] },
  { flightId: 97, prices: [{ class: 'class_1', price: 45 }, { class: 'class_2', price: 72 }, { class: 'class_3', price: 165 }] },
  { flightId: 98, prices: [{ class: 'class_1', price: 40 }] },
  { flightId: 99, prices: [{ class: 'class_1', price: 44 }] },
  { flightId: 100, prices: [{ class: 'class_1', price: 48 }, { class: 'class_2', price: 75 }] },
  // BOM ↔ PNQ
  { flightId: 101, prices: [{ class: 'class_1', price: 35 }, { class: 'class_2', price: 58 }] },
  { flightId: 102, prices: [{ class: 'class_1', price: 40 }, { class: 'class_2', price: 65 }, { class: 'class_3', price: 155 }] },
  { flightId: 103, prices: [{ class: 'class_1', price: 38 }] },
  { flightId: 104, prices: [{ class: 'class_1', price: 32 }] },
  // BOM ↔ AMD
  { flightId: 105, prices: [{ class: 'class_1', price: 48 }, { class: 'class_2', price: 78 }] },
  { flightId: 106, prices: [{ class: 'class_1', price: 52 }, { class: 'class_3', price: 195 }] },
  { flightId: 107, prices: [{ class: 'class_1', price: 50 }] },
  { flightId: 108, prices: [{ class: 'class_1', price: 45 }, { class: 'class_2', price: 72 }] },
  // BOM ↔ JAI
  { flightId: 109, prices: [{ class: 'class_1', price: 75 }, { class: 'class_2', price: 120 }] },
  { flightId: 110, prices: [{ class: 'class_1', price: 80 }, { class: 'class_3', price: 275 }] },
  { flightId: 111, prices: [{ class: 'class_1', price: 78 }] },
  // BLR ↔ PNQ
  { flightId: 112, prices: [{ class: 'class_1', price: 62 }, { class: 'class_2', price: 100 }] },
  { flightId: 113, prices: [{ class: 'class_1', price: 65 }] },

  // ── Additional international pricing ─────────────────────────────
  // BLR → DXB
  { flightId: 114, prices: [{ class: 'class_1', price: 235 }, { class: 'class_3', price: 720 }, { class: 'class_4', price: 1350 }] },
  { flightId: 115, prices: [{ class: 'class_1', price: 205 }] },
  // HYD → DXB
  { flightId: 116, prices: [{ class: 'class_1', price: 228 }, { class: 'class_3', price: 700 }] },
  // MAA → DXB
  { flightId: 117, prices: [{ class: 'class_1', price: 240 }, { class: 'class_3', price: 740 }, { class: 'class_4', price: 1400 }] },
  { flightId: 118, prices: [{ class: 'class_1', price: 255 }, { class: 'class_3', price: 760 }] },
  // CCU → DXB
  { flightId: 119, prices: [{ class: 'class_1', price: 265 }, { class: 'class_3', price: 800 }] },
  // BLR → SIN
  { flightId: 120, prices: [{ class: 'class_1', price: 285 }, { class: 'class_3', price: 850 }] },
  // MAA → SIN
  { flightId: 121, prices: [{ class: 'class_1', price: 270 }, { class: 'class_3', price: 820 }] },
  // BOM → LHR
  { flightId: 122, prices: [{ class: 'class_1', price: 495 }, { class: 'class_3', price: 1480 }, { class: 'class_4', price: 2900 }] },
  { flightId: 123, prices: [{ class: 'class_1', price: 440 }, { class: 'class_3', price: 1280 }] },
  // BLR → LHR (1 transit)
  { flightId: 124, prices: [{ class: 'class_1', price: 410 }, { class: 'class_3', price: 1180 }] },
  { flightId: 125, prices: [{ class: 'class_1', price: 89 }] },   // DEL → BOM
  { flightId: 126, prices: [{ class: 'class_1', price: 91 }] },   // BOM → DEL
  { flightId: 127, prices: [{ class: 'class_1', price: 99 }] },   // DEL → BLR
  { flightId: 128, prices: [{ class: 'class_1', price: 73 }] },   // BOM → HYD
  { flightId: 129, prices: [{ class: 'class_1', price: 51 }] },   // BLR → HYD
  { flightId: 130, prices: [{ class: 'class_1', price: 76 }] },   // HYD → BOM
  { flightId: 131, prices: [{ class: 'class_1', price: 97 }] },   // CCU → BOM
  { flightId: 132, prices: [{ class: 'class_1', price: 215 }] },  // DEL → DXB
  { flightId: 133, prices: [{ class: 'class_1', price: 290 }] },  // BLR → SIN
  { flightId: 134, prices: [{ class: 'class_1', price: 145 }, { class: 'class_3', price: 420 }] },  // DEL → BOM (premium)
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

  // ── Additional segment facilities ────────────────────────────────
  // Vistara: baggage + meal + wifi + power
  { segId: 35, facilities: ['fac_1', 'fac_2', 'fac_4', 'fac_5'] },
  { segId: 42, facilities: ['fac_1', 'fac_2', 'fac_4', 'fac_5'] },
  { segId: 45, facilities: ['fac_1', 'fac_2', 'fac_4', 'fac_5'] },
  { segId: 60, facilities: ['fac_1', 'fac_2', 'fac_4', 'fac_5'] },
  { segId: 72, facilities: ['fac_1', 'fac_2', 'fac_4', 'fac_5'] },
  { segId: 78, facilities: ['fac_1', 'fac_2', 'fac_4'] },
  { segId: 100, facilities: ['fac_1', 'fac_2', 'fac_4', 'fac_5'] },
  { segId: 107, facilities: ['fac_1', 'fac_2', 'fac_4'] },
  { segId: 109, facilities: ['fac_1', 'fac_2', 'fac_4'] },
  { segId: 115, facilities: ['fac_1', 'fac_2', 'fac_4'] },
  // IndiGo: baggage + power
  { segId: 36, facilities: ['fac_1', 'fac_5'] },
  { segId: 38, facilities: ['fac_1', 'fac_5'] },
  { segId: 40, facilities: ['fac_1', 'fac_5'] },
  { segId: 44, facilities: ['fac_1'] },
  { segId: 46, facilities: ['fac_1', 'fac_5'] },
  { segId: 49, facilities: ['fac_1', 'fac_5'] },
  { segId: 52, facilities: ['fac_1'] },
  { segId: 54, facilities: ['fac_1', 'fac_5'] },
  { segId: 57, facilities: ['fac_1'] },
  { segId: 59, facilities: ['fac_1', 'fac_5'] },
  { segId: 62, facilities: ['fac_1'] },
  { segId: 65, facilities: ['fac_1'] },
  { segId: 67, facilities: ['fac_1', 'fac_5'] },
  { segId: 69, facilities: ['fac_1'] },
  { segId: 71, facilities: ['fac_1', 'fac_5'] },
  { segId: 74, facilities: ['fac_1'] },
  { segId: 76, facilities: ['fac_1', 'fac_5'] },
  { segId: 79, facilities: ['fac_1'] },
  { segId: 81, facilities: ['fac_1', 'fac_5'] },
  { segId: 83, facilities: ['fac_1'] },
  { segId: 84, facilities: ['fac_1', 'fac_5'] },
  { segId: 86, facilities: ['fac_1'] },
  { segId: 88, facilities: ['fac_1', 'fac_5'] },
  { segId: 90, facilities: ['fac_1'] },
  { segId: 91, facilities: ['fac_1', 'fac_5'] },
  { segId: 93, facilities: ['fac_1'] },
  { segId: 95, facilities: ['fac_1', 'fac_5'] },
  { segId: 97, facilities: ['fac_1'] },
  { segId: 99, facilities: ['fac_1', 'fac_5'] },
  { segId: 101, facilities: ['fac_1'] },
  { segId: 103, facilities: ['fac_1'] },
  { segId: 106, facilities: ['fac_1'] },
  { segId: 108, facilities: ['fac_1', 'fac_5'] },
  { segId: 110, facilities: ['fac_1'] },
  { segId: 112, facilities: ['fac_1', 'fac_5'] },
  { segId: 114, facilities: ['fac_1'] },
  { segId: 116, facilities: ['fac_1', 'fac_5'] },
  { segId: 118, facilities: ['fac_1'] },
  { segId: 119, facilities: ['fac_1', 'fac_5'] },
  { segId: 120, facilities: ['fac_1'] },
  // Air India: baggage + meal + entertainment
  { segId: 41, facilities: ['fac_1', 'fac_2', 'fac_3'] },
  { segId: 47, facilities: ['fac_1', 'fac_2'] },
  { segId: 50, facilities: ['fac_1', 'fac_2', 'fac_3'] },
  { segId: 53, facilities: ['fac_1', 'fac_2'] },
  { segId: 55, facilities: ['fac_1', 'fac_2', 'fac_3'] },
  { segId: 58, facilities: ['fac_1', 'fac_2'] },
  { segId: 63, facilities: ['fac_1', 'fac_2'] },
  { segId: 66, facilities: ['fac_1', 'fac_2', 'fac_3'] },
  { segId: 68, facilities: ['fac_1', 'fac_2'] },
  { segId: 75, facilities: ['fac_1', 'fac_2'] },
  { segId: 77, facilities: ['fac_1', 'fac_2', 'fac_3'] },
  { segId: 82, facilities: ['fac_1', 'fac_2'] },
  { segId: 87, facilities: ['fac_1', 'fac_2', 'fac_3'] },
  { segId: 89, facilities: ['fac_1', 'fac_2'] },
  { segId: 92, facilities: ['fac_1', 'fac_2', 'fac_3'] },
  { segId: 96, facilities: ['fac_1', 'fac_2'] },
  { segId: 102, facilities: ['fac_1', 'fac_2'] },
  { segId: 104, facilities: ['fac_1', 'fac_2'] },
  { segId: 113, facilities: ['fac_1', 'fac_2'] },
  { segId: 117, facilities: ['fac_1', 'fac_2'] },
  { segId: 122, facilities: ['fac_1', 'fac_2', 'fac_3'] },
  { segId: 130, facilities: ['fac_1', 'fac_2', 'fac_3', 'fac_4'] },
  // SpiceJet: baggage only
  { segId: 37, facilities: ['fac_1'] },
  { segId: 39, facilities: ['fac_1'] },
  { segId: 48, facilities: ['fac_1'] },
  { segId: 56, facilities: ['fac_1'] },
  { segId: 61, facilities: ['fac_1'] },
  { segId: 70, facilities: ['fac_1'] },
  { segId: 73, facilities: ['fac_1'] },
  { segId: 80, facilities: ['fac_1'] },
  { segId: 85, facilities: ['fac_1'] },
  { segId: 94, facilities: ['fac_1'] },
  { segId: 98, facilities: ['fac_1'] },
  { segId: 105, facilities: ['fac_1'] },
  { segId: 111, facilities: ['fac_1'] },
  // Emirates: all facilities
  { segId: 121, facilities: ['fac_1', 'fac_2', 'fac_3', 'fac_4', 'fac_5'] },
  { segId: 123, facilities: ['fac_1', 'fac_2', 'fac_3', 'fac_4', 'fac_5'] },
  { segId: 124, facilities: ['fac_1', 'fac_2', 'fac_3', 'fac_4', 'fac_5'] },
  { segId: 126, facilities: ['fac_1', 'fac_2', 'fac_3', 'fac_4', 'fac_5'] },
  { segId: 131, facilities: ['fac_1', 'fac_2', 'fac_3', 'fac_4', 'fac_5'] },
  { segId: 132, facilities: ['fac_1', 'fac_2', 'fac_3', 'fac_4', 'fac_5'] },
  // Etihad: baggage + meal + entertainment + wifi
  { segId: 125, facilities: ['fac_1', 'fac_2', 'fac_3', 'fac_4'] },
  // Singapore Airlines: baggage + meal + entertainment + wifi
  { segId: 127, facilities: ['fac_1', 'fac_2', 'fac_3', 'fac_4'] },
  { segId: 128, facilities: ['fac_1', 'fac_2', 'fac_3', 'fac_4'] },
  // British Airways: baggage + meal + entertainment + power
  { segId: 129, facilities: ['fac_1', 'fac_2', 'fac_3', 'fac_5'] },
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

// ── Join helper: build FlightListing from normalized tables ────────

export function getAvailableFlights(classId?: string): FlightListing[] {
  const targetClassId = classId ?? 'class_1'; // default to Economy

  return FLIGHT_TABLE
    .filter(flight => {
      // must have pricing for the requested class
      return PRICING_TABLE.some(p => p.flightId === flight.id && p.classId === targetClassId);
    })
    .map(flight => {
      const departureAirport = AIRPORT_TABLE.find(a => a.id === flight.departureAirportId)!;
      const arrivalAirport = AIRPORT_TABLE.find(a => a.id === flight.arrivalAirportId)!;

      // Build segment details in order
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

      // Build layovers between consecutive segments
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

      const pricing = PRICING_TABLE.find(p => p.flightId === flight.id && p.classId === targetClassId)!;
      const flightClass = CLASS_TABLE.find(c => c.id === targetClassId)!;

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
