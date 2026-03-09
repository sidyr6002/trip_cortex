import { AIRPORT_TABLE } from './mockData';

export interface CountryDeal {
  countryCode: string;
  countryName: string;
  flag: string;
  image: string;
  cities: { cityName: string; airportCode: string; priceFrom: number }[];
}

const COUNTRY_INFO: Record<string, { name: string; flag: string; image: string }> = {
  IN: {
    name: 'India',
    flag: '🇮🇳',
    image: 'https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&q=80&w=800',
  },
  AE: {
    name: 'United Arab Emirates',
    flag: '🇦🇪',
    image: 'https://images.unsplash.com/photo-1518684079-3c830dcef090?auto=format&fit=crop&q=80&w=800',
  },
  SG: {
    name: 'Singapore',
    flag: '🇸🇬',
    image: 'https://images.unsplash.com/photo-1525625293386-3f8f99389edd?auto=format&fit=crop&q=80&w=800',
  },
  GB: {
    name: 'United Kingdom',
    flag: '🇬🇧',
    image: 'https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?auto=format&fit=crop&q=80&w=800',
  },
  US: {
    name: 'United States',
    flag: '🇺🇸',
    image: 'https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?auto=format&fit=crop&q=80&w=800',
  },
  ID: {
    name: 'Indonesia',
    flag: '🇮🇩',
    image: 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&q=80&w=800',
  },
};

// Simulated "from" prices per city (USD)
const CITY_PRICES: Record<string, number> = {
  DEL: 45, BOM: 52, BLR: 48, HYD: 40, MAA: 38, CCU: 42, PNQ: 55, AMD: 47, JAI: 50, STV: 60,
  DXB: 310, SIN: 280, LHR: 520, JFK: 680, CGK: 245,
};

export function getCountryDeals(): CountryDeal[] {
  const grouped = new Map<string, CountryDeal>();

  for (const airport of AIRPORT_TABLE) {
    const cc = airport.countryCode;
    if (!(cc in COUNTRY_INFO)) continue;
    const info = COUNTRY_INFO[cc];

    if (!grouped.has(cc)) {
      grouped.set(cc, {
        countryCode: cc,
        countryName: info.name,
        flag: info.flag,
        image: info.image,
        cities: [],
      });
    }

    grouped.get(cc)!.cities.push({
      cityName: airport.cityName,
      airportCode: airport.code,
      priceFrom: CITY_PRICES[airport.code] ?? 199,
    });
  }

  // Sort: international first, then by cheapest city price
  const deals = Array.from(grouped.values());
  deals.sort((a, b) => {
    const aMin = Math.min(...a.cities.map(c => c.priceFrom));
    const bMin = Math.min(...b.cities.map(c => c.priceFrom));
    return aMin - bMin;
  });

  return deals;
}
