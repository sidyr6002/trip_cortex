import { Document, Page, View, Text, StyleSheet, Svg, Path, G } from '@react-pdf/renderer'
import type { FlightListing, PassengerData } from '../data/schema'
import { formatDuration } from '../data/mockData'
import { TAX_RATE } from '../data/helpers'
import { formatDateLong, formatTimePM } from '../lib/dateUtils'

export interface TicketData {
  bookingId: string
  flight: FlightListing
  returnFlight?: FlightListing | null
  passengers: PassengerData[]
  adults: number
  children: number
  total: number
  paymentIntentId?: string
}

const S = StyleSheet.create({
  page: { fontFamily: 'Helvetica', padding: 30, fontSize: 9, color: '#0f172a' },

  // Header
  header: { backgroundColor: '#0f172a', padding: '14 20', flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 },
  headerLeft: {},
  headerBrand: { fontSize: 22, color: '#ffffff', fontFamily: 'Helvetica-Bold' },
  headerSub: { fontSize: 8, color: '#94a3b8', marginTop: 2 },
  headerRight: { alignItems: 'flex-end' },
  headerRefLabel: { fontSize: 8, color: '#94a3b8' },
  headerRef: { fontSize: 15, color: '#2563eb', fontFamily: 'Helvetica-Bold', marginTop: 2 },
  badge: { backgroundColor: '#10b981', borderRadius: 3, paddingHorizontal: 8, paddingVertical: 3, marginTop: 4 },
  badgeText: { color: '#ffffff', fontSize: 7, fontFamily: 'Helvetica-Bold' },

  // Passenger row
  passengerRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 },
  passengerLabel: { fontSize: 8, color: '#64748b', marginBottom: 2, fontFamily: 'Helvetica-Bold' },
  passengerValue: { fontSize: 9, color: '#475569' },

  // Section title
  sectionTitle: { fontSize: 10, fontFamily: 'Helvetica-Bold', color: '#0f172a', marginBottom: 6, marginTop: 10 },

  // Flight card
  card: { border: '1 solid #e2e8f0', borderRadius: 4, padding: '12 14', marginBottom: 8 },
  cardRoute: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 6 },
  airportCode: { fontSize: 22, fontFamily: 'Helvetica-Bold', color: '#0f172a' },
  cityName: { fontSize: 8, color: '#64748b', marginTop: 2 },
  routeCenter: { alignItems: 'center', flex: 1, paddingHorizontal: 8 },
  duration: { fontSize: 8, color: '#64748b', marginBottom: 3 },
  routeLine: { borderBottom: '1 solid #e2e8f0', width: '100%', marginBottom: 3 },
  transitType: { fontSize: 7, color: '#2563eb', fontFamily: 'Helvetica-Bold' },
  timeBlock: {},
  time: { fontSize: 10, fontFamily: 'Helvetica-Bold', color: '#0f172a' },
  date: { fontSize: 8, color: '#64748b', marginTop: 1 },

  // Segment row
  segRow: { backgroundColor: '#f8fafc', border: '1 solid #e2e8f0', borderRadius: 3, padding: '7 10', marginBottom: 4, flexDirection: 'row' },
  segCol1: { width: '28%' },
  segCol2: { width: '36%' },
  segCol3: { width: '36%' },
  segAirline: { fontSize: 9, fontFamily: 'Helvetica-Bold', color: '#0f172a', marginBottom: 2 },
  segMuted: { fontSize: 8, color: '#64748b', marginBottom: 1 },
  segTime: { fontSize: 9, fontFamily: 'Helvetica-Bold', color: '#0f172a', marginBottom: 1 },
  segAirportName: { fontSize: 7, color: '#94a3b8' },

  // Layover badge
  layover: { backgroundColor: '#fef3c7', borderRadius: 3, padding: '3 10', marginBottom: 4, alignSelf: 'center' },
  layoverText: { fontSize: 7, color: '#b45309', fontFamily: 'Helvetica-Bold' },

  // Passenger table
  tableHeader: { backgroundColor: '#0f172a', flexDirection: 'row', padding: '5 8' },
  tableHeaderText: { color: '#ffffff', fontSize: 7, fontFamily: 'Helvetica-Bold' },
  tableRow: { flexDirection: 'row', padding: '5 8', borderBottom: '1 solid #e2e8f0' },
  tableRowAlt: { backgroundColor: '#f8fafc' },
  colName: { width: '40%' },
  colType: { width: '20%' },
  colSeat: { width: '20%' },
  colExtras: { width: '20%' },
  tableCell: { fontSize: 8, color: '#475569' },
  tableCellBold: { fontSize: 8, fontFamily: 'Helvetica-Bold', color: '#0f172a' },

  // Payment summary
  payBox: { backgroundColor: '#f8fafc', border: '1 solid #e2e8f0', borderRadius: 4, padding: '10 12', marginTop: 4 },
  payRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 5 },
  payLabel: { fontSize: 8, color: '#64748b' },
  payValue: { fontSize: 8, color: '#0f172a' },
  payDivider: { borderBottom: '1 dashed #cbd5e1', marginVertical: 6 },
  payTotal: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 2 },
  payTotalLabel: { fontSize: 11, fontFamily: 'Helvetica-Bold', color: '#0f172a' },
  payTotalValue: { fontSize: 11, fontFamily: 'Helvetica-Bold', color: '#0f172a' },
  payRef: { fontSize: 7, color: '#94a3b8', marginTop: 6 },
})

const fmt = formatDateLong
const fmtTime = formatTimePM

function FlightCard({ flight, label }: { flight: FlightListing; label?: string }) {
  const dep = flight.segments[0].departureTime
  const arr = flight.segments[flight.segments.length - 1].arrivalTime
  return (
    <>
      {label && <Text style={S.sectionTitle}>{label}</Text>}
      <View style={S.card}>
        <View style={S.cardRoute}>
          <View style={S.timeBlock}>
            <Text style={S.airportCode}>{flight.departureAirport.code}</Text>
            <Text style={S.cityName}>{flight.departureAirport.cityName}</Text>
            <Text style={[S.time, { marginTop: 4 }]}>{fmtTime(dep)}</Text>
            <Text style={S.date}>{fmt(dep)}</Text>
          </View>
          <View style={S.routeCenter}>
            <Text style={S.duration}>{formatDuration(flight.totalDurationMinutes)}</Text>
            <View style={S.routeLine} />
            <View style={{ alignItems: 'center', marginBottom: 2 }}>
              <Svg viewBox="0 0 576 512" width={14} height={14}>
                <G style={{ transformOrigin: '288px 256px', transform: 'rotate(-45deg)' }}>
                  <Path 
                    d="M480 192H365.71L260.61 8.06A16.014 16.014 0 0 0 246.71 0h-65.5c-10.63 0-18.3 10.17-15.38 20.39L214.86 192H112l-43.2-57.6c-3.02-4.03-7.77-6.4-12.8-6.4H16.01C5.6 128-2.04 137.78.49 147.88L32 256 .49 364.12C-2.04 374.22 5.6 384 16.01 384H56c5.04 0 9.78-2.37 12.8-6.4L112 320h102.86l-49.03 171.6c-2.92 10.22 4.75 20.4 15.38 20.4h65.5c5.74 0 11.04-3.08 13.89-8.06L365.71 320H480c35.35 0 96-28.65 96-64s-60.65-64-96-64z" 
                    fill="#2563eb" 
                  />
                </G>
              </Svg>
            </View>
            <Text style={S.transitType}>{flight.transitType.toUpperCase()}</Text>
          </View>
          <View style={[S.timeBlock, { alignItems: 'flex-end' }]}>
            <Text style={S.airportCode}>{flight.arrivalAirport.code}</Text>
            <Text style={S.cityName}>{flight.arrivalAirport.cityName}</Text>
            <Text style={[S.time, { marginTop: 4 }]}>{fmtTime(arr)}</Text>
            <Text style={S.date}>{fmt(arr)}</Text>
          </View>
        </View>
      </View>
    </>
  )
}

function SegmentsSection({ flight, label }: { flight: FlightListing; label?: string }) {
  return (
    <>
      <Text style={S.sectionTitle}>{label ?? 'FLIGHT SEGMENTS'}</Text>
      {flight.segments.map((seg, i) => (
        <View key={seg.id}>
          <View style={S.segRow}>
            <View style={S.segCol1}>
              <Text style={S.segAirline}>{seg.airline.name} {seg.flightNumber}</Text>
              <Text style={S.segMuted}>{flight.flightClass.name}</Text>
              <Text style={S.segMuted}>{formatDuration(seg.durationMinutes)}</Text>
            </View>
            <View style={S.segCol2}>
              <Text style={S.segTime}>{fmtTime(seg.departureTime)} · {seg.departureAirport.code}</Text>
              <Text style={S.segMuted}>{fmt(seg.departureTime)}</Text>
              <Text style={S.segAirportName}>{seg.departureAirport.name}</Text>
            </View>
            <View style={S.segCol3}>
              <Text style={S.segTime}>{fmtTime(seg.arrivalTime)} · {seg.arrivalAirport.code}</Text>
              <Text style={S.segMuted}>{fmt(seg.arrivalTime)}</Text>
              <Text style={S.segAirportName}>{seg.arrivalAirport.name}</Text>
            </View>
          </View>
          {i < flight.layovers.length && (
            <View style={S.layover}>
              <Text style={S.layoverText}>
                LAYOVER: {formatDuration(flight.layovers[i].durationMinutes)} in {flight.layovers[i].airport.cityName} ({flight.layovers[i].airport.code})
              </Text>
            </View>
          )}
        </View>
      ))}
    </>
  )
}

function PassengerTable({ passengers, adults }: { passengers: PassengerData[]; adults: number }) {
  return (
    <>
      <Text style={S.sectionTitle}>PASSENGER DETAILS</Text>
      <View style={S.tableHeader}>
        <Text style={[S.tableHeaderText, S.colName]}>PASSENGER NAME</Text>
        <Text style={[S.tableHeaderText, S.colType]}>TICKET TYPE</Text>
        <Text style={[S.tableHeaderText, S.colSeat]}>SEAT</Text>
        <Text style={[S.tableHeaderText, S.colExtras]}>EXTRAS</Text>
      </View>
      {passengers.map((p, i) => (
        <View key={i} style={[S.tableRow, i % 2 !== 0 ? S.tableRowAlt : {}]}>
          <Text style={[S.tableCellBold, S.colName]}>{p.firstName} {p.lastName}</Text>
          <Text style={[S.tableCell, S.colType]}>{i < adults ? 'Adult' : 'Child'}</Text>
          <Text style={[S.tableCell, S.colSeat]}>Unassigned</Text>
          <Text style={[S.tableCell, S.colExtras]}>Standard Baggage</Text>
        </View>
      ))}
    </>
  )
}

function PaymentSummary({ flight, returnFlight, adults, children, total, paymentIntentId }: Omit<TicketData, 'bookingId' | 'passengers'>) {
  const totalPassengers = adults + children
  const outboundSubtotal = flight.pricing.pricePerPassenger * totalPassengers
  const returnSubtotal = returnFlight ? returnFlight.pricing.pricePerPassenger * totalPassengers : 0
  const subtotal = outboundSubtotal + returnSubtotal
  const taxes = subtotal * TAX_RATE
  const hasReturn = !!returnFlight

  return (
    <>
      <Text style={S.sectionTitle}>PAYMENT SUMMARY</Text>
      <View style={S.payBox}>
        <View style={S.payRow}>
          <Text style={S.payLabel}>{hasReturn ? 'Outbound' : 'Base Fare'} ({totalPassengers} traveller{totalPassengers > 1 ? 's' : ''})</Text>
          <Text style={S.payValue}>${outboundSubtotal.toFixed(2)}</Text>
        </View>
        {hasReturn && (
          <View style={S.payRow}>
            <Text style={S.payLabel}>Return ({totalPassengers} traveller{totalPassengers > 1 ? 's' : ''})</Text>
            <Text style={S.payValue}>${returnSubtotal.toFixed(2)}</Text>
          </View>
        )}
        <View style={S.payRow}>
          <Text style={S.payLabel}>Taxes & Carrier-Imposed Fees</Text>
          <Text style={S.payValue}>${taxes.toFixed(2)}</Text>
        </View>
        <View style={S.payDivider} />
        <View style={S.payTotal}>
          <Text style={S.payTotalLabel}>TOTAL AMOUNT{hasReturn ? ' (ROUND TRIP)' : ''}</Text>
          <Text style={S.payTotalValue}>${total.toFixed(2)}</Text>
        </View>
        {paymentIntentId && (
          <Text style={S.payRef}>Reference: {paymentIntentId}</Text>
        )}
      </View>
    </>
  )
}

export default function TicketDocument(props: TicketData) {
  const { bookingId, flight, returnFlight, passengers, adults, children, total, paymentIntentId } = props
  const hasReturn = !!returnFlight

  return (
    <Document>
      <Page size="A4" style={S.page}>
        {/* Header */}
        <View style={S.header}>
          <View style={S.headerLeft}>
            <Text style={S.headerBrand}>FlySmart</Text>
            <Text style={S.headerSub}>OFFICIAL E-TICKET & ITINERARY</Text>
          </View>
          <View style={S.headerRight}>
            <Text style={S.headerRefLabel}>BOOKING REFERENCE</Text>
            <Text style={S.headerRef}>{bookingId.toUpperCase()}</Text>
            <View style={S.badge}><Text style={S.badgeText}>CONFIRMED</Text></View>
          </View>
        </View>

        {/* Passenger row */}
        <View style={S.passengerRow}>
          <View>
            <Text style={S.passengerLabel}>PASSENGER(S)</Text>
            <Text style={S.passengerValue}>{passengers.map(p => `${p.firstName} ${p.lastName}`).join(', ')}</Text>
          </View>
          <View style={{ alignItems: 'flex-end' }}>
            <Text style={S.passengerLabel}>DATE OF ISSUE</Text>
            <Text style={S.passengerValue}>{fmt(new Date().toISOString())}</Text>
          </View>
        </View>

        {/* Outbound flight */}
        <FlightCard flight={flight} label={hasReturn ? 'OUTBOUND FLIGHT' : undefined} />
        <SegmentsSection flight={flight} label={hasReturn ? 'OUTBOUND SEGMENTS' : undefined} />

        {/* Return flight */}
        {returnFlight && (
          <>
            <FlightCard flight={returnFlight} label="RETURN FLIGHT" />
            <SegmentsSection flight={returnFlight} label="RETURN SEGMENTS" />
          </>
        )}

        <PassengerTable passengers={passengers} adults={adults} />
        <PaymentSummary
          flight={flight}
          returnFlight={returnFlight}
          adults={adults}
          children={children}
          total={total}
          paymentIntentId={paymentIntentId}
        />
      </Page>
    </Document>
  )
}
