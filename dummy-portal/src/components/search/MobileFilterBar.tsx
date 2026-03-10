import { useState } from 'react'
import { X, ArrowUpDown, Plane, DollarSign, Wifi } from 'lucide-react'
import { Slider } from '../ui/slider'
import { FACILITY_TABLE } from '../../data/mockData'
import { SORT_LABELS } from './FlightFilterSidebar'
import type { FilterState, SortOption, TransitFilter } from './FlightFilterSidebar'
import type { FlightListing } from '../../data/schema'

type SheetType = 'sort' | 'stops' | 'price' | 'facilities' | null

interface Props {
  filters: FilterState
  onFiltersChange: (filters: FilterState) => void
  flights: FlightListing[]
  sortBy: SortOption
  onSortChange: (sort: SortOption) => void
}

export default function MobileFilterBar({ filters, onFiltersChange, flights, sortBy, onSortChange }: Props) {
  const [activeSheet, setActiveSheet] = useState<SheetType>(null)

  const prices = flights.map(f => f.pricing.pricePerPassenger)
  const minPrice = prices.length > 0 ? Math.min(...prices) : 0
  const maxPrice = prices.length > 0 ? Math.max(...prices) : 0

  const activeFilterCount =
    filters.transitTypes.length +
    filters.facilities.length +
    (filters.priceRange[0] > minPrice || filters.priceRange[1] < maxPrice ? 1 : 0)

  const close = () => setActiveSheet(null)

  return (
    <>
      {/* Pill buttons row */}
      <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-none lg:hidden">
        <PillButton
          icon={<ArrowUpDown className="w-3.5 h-3.5" />}
          label="Sort"
          active={sortBy !== 'direct-first'}
          onClick={() => setActiveSheet('sort')}
        />
        <PillButton
          icon={<Plane className="w-3.5 h-3.5" />}
          label="Stops"
          count={filters.transitTypes.length}
          onClick={() => setActiveSheet('stops')}
        />
        <PillButton
          icon={<DollarSign className="w-3.5 h-3.5" />}
          label="Price"
          active={filters.priceRange[0] > minPrice || filters.priceRange[1] < maxPrice}
          onClick={() => setActiveSheet('price')}
        />
        <PillButton
          icon={<Wifi className="w-3.5 h-3.5" />}
          label="Facilities"
          count={filters.facilities.length}
          onClick={() => setActiveSheet('facilities')}
        />
        {activeFilterCount > 0 && (
          <button
            onClick={() => onFiltersChange({ transitTypes: [], priceRange: [minPrice, maxPrice], facilities: [] })}
            className="shrink-0 px-3 py-2 text-xs font-medium text-red-600 bg-red-50 rounded-full hover:bg-red-100 transition-colors"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Bottom sheet overlay */}
      {activeSheet && (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true">
          <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={close} aria-hidden="true" />
          <div className="absolute bottom-0 left-0 right-0 bg-white rounded-t-2xl shadow-xl max-h-[70vh] flex flex-col animate-in slide-in-from-bottom duration-300">
            {/* Sheet header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 shrink-0">
              <h3 className="font-semibold text-lg text-content">
                {activeSheet === 'sort' && 'Sort by'}
                {activeSheet === 'stops' && 'Number of Stops'}
                {activeSheet === 'price' && 'Price Range'}
                {activeSheet === 'facilities' && 'Facilities'}
              </h3>
              <button onClick={close} className="p-1.5 text-content-muted hover:text-content transition-colors" aria-label="Close">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Sheet content */}
            <div className="overflow-y-auto px-5 py-4 flex-1">
              {activeSheet === 'sort' && (
                <SortSheet sortBy={sortBy} onSortChange={(s) => { onSortChange(s); close() }} />
              )}
              {activeSheet === 'stops' && (
                <StopsSheet filters={filters} onFiltersChange={onFiltersChange} flights={flights} />
              )}
              {activeSheet === 'price' && (
                <PriceSheet filters={filters} onFiltersChange={onFiltersChange} minPrice={minPrice} maxPrice={maxPrice} />
              )}
              {activeSheet === 'facilities' && (
                <FacilitiesSheet filters={filters} onFiltersChange={onFiltersChange} flights={flights} />
              )}
            </div>

            {/* Apply button (for non-sort sheets) */}
            {activeSheet !== 'sort' && (
              <div className="px-5 py-4 border-t border-slate-100 shrink-0">
                <button
                  onClick={close}
                  className="w-full py-3 bg-primary text-white font-semibold rounded-xl hover:bg-primary/90 transition-colors"
                >
                  Apply
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}

/* ── Pill Button ── */
function PillButton({ icon, label, count, active, onClick }: {
  icon: React.ReactNode
  label: string
  count?: number
  active?: boolean
  onClick: () => void
}) {
  const hasIndicator = (count && count > 0) || active
  return (
    <button
      onClick={onClick}
      className={`shrink-0 flex items-center gap-1.5 px-3.5 py-2 rounded-full text-sm font-medium border transition-colors ${
        hasIndicator
          ? 'bg-primary-50 border-primary/30 text-primary'
          : 'bg-white border-divider-light text-content hover:border-primary/30'
      }`}
    >
      {icon}
      {label}
      {count && count > 0 ? (
        <span className="ml-0.5 w-5 h-5 rounded-full bg-primary text-white text-xs flex items-center justify-center font-semibold">
          {count}
        </span>
      ) : null}
    </button>
  )
}

/* ── Sort Sheet ── */
function SortSheet({ sortBy, onSortChange }: { sortBy: SortOption; onSortChange: (s: SortOption) => void }) {
  return (
    <div className="flex flex-col gap-1">
      {(Object.keys(SORT_LABELS) as SortOption[]).map(option => (
        <button
          key={option}
          onClick={() => onSortChange(option)}
          className={`w-full text-left px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
            sortBy === option ? 'bg-primary-50 text-primary' : 'text-content hover:bg-slate-50'
          }`}
        >
          {SORT_LABELS[option]}
        </button>
      ))}
    </div>
  )
}

/* ── Stops Sheet ── */
function StopsSheet({ filters, onFiltersChange, flights }: {
  filters: FilterState; onFiltersChange: (f: FilterState) => void; flights: FlightListing[]
}) {
  const availableTransitTypes = new Set(flights.map(f => f.transitType))
  const transitOptions: { value: TransitFilter; label: string }[] = [
    { value: 'Direct', label: 'Direct' },
    { value: '1 transit', label: '1 Stop' },
    { value: '2+ transit', label: '2+ Stops' },
  ]

  const toggle = (type: TransitFilter) => {
    const next = filters.transitTypes.includes(type)
      ? filters.transitTypes.filter(t => t !== type)
      : [...filters.transitTypes, type]
    onFiltersChange({ ...filters, transitTypes: next })
  }

  return (
    <div className="flex flex-col gap-2">
      {transitOptions.map(opt => {
        const available = availableTransitTypes.has(opt.value)
        const checked = filters.transitTypes.includes(opt.value)
        return (
          <label
            key={opt.value}
            className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${
              !available ? 'opacity-40 cursor-not-allowed' : checked ? 'bg-primary-50' : 'hover:bg-slate-50 cursor-pointer'
            }`}
          >
            <input
              type="checkbox"
              checked={checked}
              disabled={!available}
              onChange={() => toggle(opt.value)}
              className="w-5 h-5 rounded text-primary focus:ring-primary border-divider"
            />
            <span className="text-sm font-medium">{opt.label}</span>
          </label>
        )
      })}
    </div>
  )
}

/* ── Price Sheet ── */
function PriceSheet({ filters, onFiltersChange, minPrice, maxPrice }: {
  filters: FilterState; onFiltersChange: (f: FilterState) => void; minPrice: number; maxPrice: number
}) {
  const fmt = (p: number) => `$${p.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
  return (
    <div className="space-y-6 py-2">
      <div className="text-center">
        <span className="text-lg font-semibold text-content">
          {fmt(filters.priceRange[0])} — {fmt(filters.priceRange[1])}
        </span>
      </div>
      <div className="px-2">
        <Slider
          min={minPrice}
          max={maxPrice}
          step={1}
          value={[filters.priceRange[0], filters.priceRange[1]]}
          onValueChange={([low, high]) => onFiltersChange({ ...filters, priceRange: [low, high] })}
        />
      </div>
      <div className="flex justify-between text-xs text-content-muted px-2">
        <span>{fmt(minPrice)}</span>
        <span>{fmt(maxPrice)}</span>
      </div>
    </div>
  )
}

/* ── Facilities Sheet ── */
function FacilitiesSheet({ filters, onFiltersChange, flights }: {
  filters: FilterState; onFiltersChange: (f: FilterState) => void; flights: FlightListing[]
}) {
  const availableIds = new Set(flights.flatMap(f => f.segments.flatMap(s => s.facilities.map(fac => fac.id))))

  const toggle = (id: string) => {
    const next = filters.facilities.includes(id)
      ? filters.facilities.filter(fid => fid !== id)
      : [...filters.facilities, id]
    onFiltersChange({ ...filters, facilities: next })
  }

  return (
    <div className="flex flex-col gap-2">
      {FACILITY_TABLE.map(fac => {
        const available = availableIds.has(fac.id)
        const checked = filters.facilities.includes(fac.id)
        return (
          <label
            key={fac.id}
            className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${
              !available ? 'opacity-40 cursor-not-allowed' : checked ? 'bg-primary-50' : 'hover:bg-slate-50 cursor-pointer'
            }`}
          >
            <input
              type="checkbox"
              checked={checked}
              disabled={!available}
              onChange={() => toggle(fac.id)}
              className="w-5 h-5 rounded text-primary focus:ring-primary border-divider"
            />
            <span className="text-sm font-medium">{fac.name}</span>
          </label>
        )
      })}
    </div>
  )
}
