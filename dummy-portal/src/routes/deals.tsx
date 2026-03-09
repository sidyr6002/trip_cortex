import { createFileRoute, Link } from '@tanstack/react-router'
import { useState } from 'react'
import { MapPin, Plane, ArrowRight } from 'lucide-react'
import Navbar from '../components/home/Navbar'
import { getCountryDeals } from '../data/dealsData'
import type { CountryDeal } from '../data/dealsData'

export const Route = createFileRoute('/deals')({ component: DealsPage })

function DealsPage() {
  const deals = getCountryDeals()
  const [selectedCountry, setSelectedCountry] = useState<CountryDeal | null>(null)

  return (
    <div className="min-h-screen bg-linear-to-b from-primary-100 via-primary-50 to-white font-sans text-content overflow-x-hidden">
      <Navbar />

      {/* Hero */}
      <section className="text-center pt-4 pb-12 px-4 max-w-4xl mx-auto">
        <h1 className="text-5xl md:text-6xl font-bold tracking-tight mb-4 text-content">
          Flight Deals
        </h1>
        <p className="text-content-light text-lg max-w-2xl mx-auto">
          Explore the cheapest flights to popular destinations. Pick a country to see city-level deals.
        </p>
      </section>

      {/* Country Cards Grid */}
      <section className="pb-8 px-4 max-w-6xl mx-auto">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {deals.map((deal) => (
            <CountryCard
              key={deal.countryCode}
              deal={deal}
              isSelected={selectedCountry?.countryCode === deal.countryCode}
              onSelect={() =>
                setSelectedCountry(
                  selectedCountry?.countryCode === deal.countryCode ? null : deal
                )
              }
            />
          ))}
        </div>
      </section>

      {/* Expanded City Deals */}
      {selectedCountry && (
        <section className="pb-20 px-4 max-w-6xl mx-auto animate-in fade-in slide-in-from-top-2 duration-300">
          <div className="bg-white/80 backdrop-blur-xl rounded-2xl p-6 sm:p-8 border border-white/60 shadow-sm">
            <div className="flex items-center gap-3 mb-6">
              <span className="text-3xl">{selectedCountry.flag}</span>
              <h2 className="text-2xl font-bold text-content">
                Flights to {selectedCountry.countryName}
              </h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {selectedCountry.cities.map((city) => (
                <Link
                  key={city.airportCode}
                  to="/search"
                  search={{
                    from: 'DEL',
                    to: city.airportCode,
                    date: getNextMonthDate(),
                    tripType: 'one-way',
                    class: 'economy',
                  }}
                  className="flex items-center justify-between p-4 rounded-xl border border-divider-light hover:border-primary-outline/50 hover:bg-primary-50/30 transition-all duration-200 group cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <div className="bg-primary-50 p-2 rounded-full">
                      <MapPin className="w-4 h-4 text-primary" />
                    </div>
                    <div>
                      <p className="font-semibold text-content">{city.cityName}</p>
                      <p className="text-xs text-content-light">{city.airportCode}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <p className="text-xs text-content-light">From</p>
                      <p className="font-bold text-primary text-lg">${city.priceFrom}</p>
                    </div>
                    <ArrowRight className="w-4 h-4 text-content-lighter group-hover:text-primary transition-colors" />
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Bottom padding when no country selected */}
      {!selectedCountry && <div className="pb-20" />}
    </div>
  )
}

function CountryCard({
  deal,
  isSelected,
  onSelect,
}: {
  deal: CountryDeal
  isSelected: boolean
  onSelect: () => void
}) {
  const cheapest = Math.min(...deal.cities.map((c) => c.priceFrom))

  return (
    <button
      onClick={onSelect}
      className={`relative h-[260px] rounded-2xl overflow-hidden cursor-pointer shadow-sm hover:shadow-xl transition-all duration-500 w-full text-left group ${
        isSelected ? 'ring-2 ring-primary ring-offset-2' : ''
      }`}
    >
      <img
        src={deal.image}
        alt={deal.countryName}
        className="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
      />
      <div className="absolute inset-0 bg-linear-to-t from-black/80 via-black/30 to-transparent" />
      <div className="absolute bottom-0 left-0 right-0 p-6 flex justify-between items-end">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">{deal.flag}</span>
            <h3 className="text-2xl font-bold text-white">{deal.countryName}</h3>
          </div>
          <p className="text-content-on-dark text-sm">
            {deal.cities.length} {deal.cities.length === 1 ? 'city' : 'cities'}
          </p>
        </div>
        <div className="text-right">
          <p className="text-content-on-dark text-xs mb-1">From</p>
          <p className="text-xl font-bold text-white">${cheapest}</p>
        </div>
      </div>
      {isSelected && (
        <div className="absolute top-3 right-3 bg-primary text-white text-xs font-semibold px-3 py-1 rounded-full flex items-center gap-1">
          <Plane className="w-3 h-3" /> Viewing
        </div>
      )}
    </button>
  )
}

function getNextMonthDate(): string {
  const d = new Date()
  d.setMonth(d.getMonth() + 1)
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`
}
