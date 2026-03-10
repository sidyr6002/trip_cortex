import jsPDF from 'jspdf'
import type { FlightListing, PassengerData } from '../data/schema'
import { formatDuration } from '../data/mockData'
import { TAX_RATE } from '../data/helpers'

interface TicketData {
  bookingId: string
  flight: FlightListing
  passengers: PassengerData[]
  adults: number
  children: number
  total: number
  paymentIntentId?: string
}

// Premium Color Palette
const BRAND_PRIMARY = [15, 23, 42] as const   // Slate 900
const BRAND_ACCENT = [37, 99, 235] as const   // Blue 600
const TEXT_MAIN = [15, 23, 42] as const       // Slate 900 (darker)
const TEXT_MUTED = [71, 85, 105] as const     // Slate 600 (darker, more visible)
const BG_LIGHT = [248, 250, 252] as const     // Slate 50
const BORDER = [226, 232, 240] as const       // Slate 200
const WHITE = [255, 255, 255] as const
const SUCCESS = [16, 185, 129] as const       // Emerald 500

// Utility formatting functions
const formatDateShort = (iso: string) => new Date(iso).toLocaleString('en-US', {
  day: 'numeric', month: 'short', year: 'numeric'
})

const formatTime = (iso: string) => new Date(iso).toLocaleString('en-US', {
  hour: '2-digit', minute: '2-digit', hour12: true
})

// Helper to draw a dashed line
function drawDashedLine(doc: jsPDF, x1: number, y1: number, x2: number, y2: number, dashArray: number[] = [2, 2]) {
  doc.setDrawColor(...BORDER)
  doc.setLineWidth(0.5)
  doc.setLineDashPattern(dashArray, 0)
  doc.line(x1, y1, x2, y2)
  doc.setLineDashPattern([], 0) // reset
}

export function generateTicketPdf(data: TicketData) {
  const { bookingId, flight, passengers, adults, children, total, paymentIntentId } = data
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
  const pageWidth = doc.internal.pageSize.getWidth()
  const pageHeight = doc.internal.pageSize.getHeight()
  const margin = 20
  const contentWidth = pageWidth - margin * 2

  let y = 0

  // helper to prevent overlapping by injecting new pages dynamically
  const checkPageBreak = (neededHeight: number) => {
    // 65mm reserved for footer at the bottom to ensure no overlap
    if (y + neededHeight > pageHeight - 65) {
      doc.addPage()
      y = 20
    }
  }

  // --- HEADER SECTION ---
  doc.setFillColor(...BRAND_PRIMARY)
  doc.rect(0, 0, pageWidth, 45, 'F')

  // Logo text
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(26)
  doc.setTextColor(...WHITE)
  doc.text('FlySmart', margin, 20)

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(10)
  doc.text('OFFICIAL E-TICKET & ITINERARY', margin, 27)

  // Right side header info
  doc.setFontSize(10)
  doc.text('BOOKING REFERENCE', pageWidth - margin, 18, { align: 'right' })
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(18)
  doc.setTextColor(...BRAND_ACCENT)
  doc.text(bookingId.toUpperCase(), pageWidth - margin, 26, { align: 'right' })

  // Status Badge
  doc.setFillColor(...SUCCESS)
  doc.roundedRect(pageWidth - margin - 35, 32, 35, 7, 1.5, 1.5, 'F')
  doc.setFontSize(8)
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(...WHITE)
  doc.text('CONFIRMED', pageWidth - margin - 17.5, 37, { align: 'center' })

  y = 55

  // --- PASSENGER & FLIGHT SUMMARY ROW ---
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(10)
  doc.setTextColor(...TEXT_MAIN)
  doc.text('PASSENGER(S)', margin, y)

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(10)
  doc.setTextColor(...TEXT_MUTED)
  const passengerNames = passengers.map(p => `${p.firstName} ${p.lastName}`).join(', ')
  doc.text(passengerNames, margin, y + 6, { maxWidth: contentWidth * 0.6 })

  // Issue Date
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(10)
  doc.setTextColor(...TEXT_MAIN)
  doc.text('DATE OF ISSUE', pageWidth - margin, y, { align: 'right' })

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(10)
  doc.setTextColor(...TEXT_MUTED)
  doc.text(formatDateShort(new Date().toISOString()), pageWidth - margin, y + 6, { align: 'right' })

  y += 20

  // --- MAIN ITINERARY CARD ---
  checkPageBreak(50)
  const cardY = y
  doc.setFillColor(...WHITE)
  doc.setDrawColor(...BORDER)
  doc.setLineWidth(0.3)
  doc.roundedRect(margin, cardY, contentWidth, 50, 3, 3, 'FD')

  // Main Route (Departure to Arrival)
  const routeY = cardY + 16
  const leftX = margin + 15
  const rightX = pageWidth - margin - 15
  const centerX = pageWidth / 2

  doc.setFont('helvetica', 'bold')
  doc.setFontSize(26)
  doc.setTextColor(...BRAND_PRIMARY)
  doc.text(flight.departureAirport.code, leftX, routeY)

  doc.text(flight.arrivalAirport.code, rightX, routeY, { align: 'right' })

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9)
  doc.setTextColor(...TEXT_MUTED)
  doc.text(flight.departureAirport.cityName, leftX, routeY + 6)
  doc.text(flight.arrivalAirport.cityName, rightX, routeY + 6, { align: 'right' })

  const departureTime = flight.segments[0].departureTime
  const arrivalTime = flight.segments[flight.segments.length - 1].arrivalTime

  // Departure Time & Date
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(11)
  doc.setTextColor(...TEXT_MAIN)
  doc.text(formatTime(departureTime), leftX, routeY + 14)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9)
  doc.setTextColor(...TEXT_MUTED)
  doc.text(formatDateShort(departureTime), leftX, routeY + 19)

  // Arrival Time & Date
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(11)
  doc.setTextColor(...TEXT_MAIN)
  doc.text(formatTime(arrivalTime), rightX, routeY + 14, { align: 'right' })
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9)
  doc.setTextColor(...TEXT_MUTED)
  doc.text(formatDateShort(arrivalTime), rightX, routeY + 19, { align: 'right' })

  // Center Duration/Direct line
  doc.setFontSize(9)
  doc.setTextColor(...TEXT_MUTED)
  doc.text(formatDuration(flight.totalDurationMinutes), centerX, routeY - 7.5, { align: 'center' })

  // Arrow Line
  doc.setDrawColor(...BORDER)
  doc.setLineWidth(1)
  const lineStart = leftX + 25
  const lineEnd = rightX - 25
  doc.line(lineStart, routeY - 3, lineEnd, routeY - 3)

  // Airplane SVG Icon Replacement (using custom shapes to look like a plane)
  doc.setFillColor(...BRAND_ACCENT)
  doc.roundedRect(centerX - 3.5, routeY - 4, 7, 2, 0.8, 0.8, 'F') // Fuselage
  doc.triangle(centerX - 1, routeY - 4, centerX + 1.5, routeY - 4, centerX - 2, routeY - 6.5, 'F') // Top Wing
  doc.triangle(centerX - 1, routeY - 2, centerX + 1.5, routeY - 2, centerX - 2, routeY + 0.5, 'F') // Bottom Wing
  doc.triangle(centerX - 3.5, routeY - 4, centerX - 2, routeY - 4, centerX - 3.5, routeY - 5.5, 'F') // Tail

  doc.setFont('helvetica', 'bold')
  doc.setFontSize(8)
  doc.setTextColor(...BRAND_ACCENT)
  doc.text(flight.transitType.toUpperCase(), centerX, routeY + 6, { align: 'center' })

  y = cardY + 62

  // --- SECTION TITLE HELPER ---
  const renderSectionTitle = (title: string) => {
    checkPageBreak(15) // make sure at least the title + 10mm fit
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(12)
    doc.setTextColor(...BRAND_PRIMARY)
    doc.text(title.toUpperCase(), margin, y)
    y += 4
    y += 6
  }

  // --- ITINERARY DETAILS ---
  renderSectionTitle('Flight Segments')

  flight.segments.forEach((seg, i) => {
    checkPageBreak(30) // check overflow for each segment card
    doc.setFillColor(...BG_LIGHT)
    doc.setDrawColor(...BORDER)
    doc.setLineWidth(0.3)
    doc.roundedRect(margin, y, contentWidth, 24, 2, 2, 'FD')

    const sY = y + 8

    // Airline & Class
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(10)
    doc.setTextColor(...TEXT_MAIN)
    doc.text(`${seg.airline.name} ${seg.flightNumber}`, margin + 6, sY)

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(9)
    doc.setTextColor(...TEXT_MUTED)
    doc.text(`Cabin: ${flight.flightClass.name}`, margin + 6, sY + 6)
    doc.text(`Duration: ${formatDuration(seg.durationMinutes)}`, margin + 6, sY + 11)

    // Dep / Arr Cols
    const col2 = margin + 70
    const col3 = margin + 120

    // Departure
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(10)
    doc.setTextColor(...TEXT_MAIN)
    doc.text(`${formatTime(seg.departureTime)} - ${seg.departureAirport.code}`, col2, sY)
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(9)
    doc.setTextColor(...TEXT_MUTED)
    doc.text(formatDateShort(seg.departureTime), col2, sY + 5)
    doc.text(seg.departureAirport.name, col2, sY + 10, { maxWidth: 45 })

    // Arrival
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(10)
    doc.setTextColor(...TEXT_MAIN)
    doc.text(`${formatTime(seg.arrivalTime)} - ${seg.arrivalAirport.code}`, col3, sY)
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(9)
    doc.setTextColor(...TEXT_MUTED)
    doc.text(formatDateShort(seg.arrivalTime), col3, sY + 5)
    doc.text(seg.arrivalAirport.name, col3, sY + 10, { maxWidth: 45 })

    y += 28

    if (i < flight.layovers.length) {
      checkPageBreak(12) // check overflow for layover
      const layover = flight.layovers[i]
      doc.setFillColor(254, 243, 199) // amber-100
      doc.setTextColor(180, 83, 9)   // amber-700
      doc.roundedRect(margin + 20, y - 2, contentWidth - 40, 7, 1, 1, 'F')
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(8)
      doc.text(
        `LAYOVER: ${formatDuration(layover.durationMinutes)} in ${layover.airport.cityName} (${layover.airport.code})`,
        centerX, y + 2.5, { align: 'center' }
      )
      y += 9
    }
  })

  y += 4

  // --- PASSENGERS TABLE ---
  renderSectionTitle('Passenger Details')

  checkPageBreak(12) // Ensure header fits
  // Table header
  doc.setFillColor(...BRAND_PRIMARY)
  doc.rect(margin, y, contentWidth, 8, 'F')
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(8)
  doc.setTextColor(...WHITE)
  doc.text('PASSENGER NAME', margin + 6, y + 5)
  doc.text('TICKET TYPE', margin + 80, y + 5)
  doc.text('SEAT', margin + 120, y + 5)
  doc.text('EXTRAS', margin + 150, y + 5)
  y += 8

  passengers.forEach((p, i) => {
    checkPageBreak(10) // Ensure row fits
    // Zebra striping
    if (i % 2 === 0) {
      doc.setFillColor(...BG_LIGHT)
      doc.rect(margin, y, contentWidth, 8, 'F')
    }

    doc.setFont('helvetica', 'bold')
    doc.setFontSize(9)
    doc.setTextColor(...TEXT_MAIN)
    doc.text(`${p.firstName} ${p.lastName}`, margin + 6, y + 5.5)

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(9)
    doc.setTextColor(...TEXT_MUTED)
    doc.text(i < adults ? 'Adult' : 'Child', margin + 80, y + 5.5)
    doc.text('Unassigned', margin + 120, y + 5.5)
    doc.text('Standard Baggage', margin + 150, y + 5.5)

    // Underline
    doc.setDrawColor(...BORDER)
    doc.setLineWidth(0.1)
    doc.line(margin, y + 8, margin + contentWidth, y + 8)

    y += 8
  })

  y += 10

  // --- PAYMENT SUMMARY ---
  renderSectionTitle('Payment Summary')

  const totalPassengers = adults + children
  const subtotal = flight.pricing.pricePerPassenger * totalPassengers
  const taxes = subtotal * TAX_RATE

  doc.setFillColor(...BG_LIGHT)
  doc.setDrawColor(...BORDER)
  doc.setLineWidth(0.3)
  doc.roundedRect(margin, y, contentWidth, 35, 2, 2, 'FD')

  const leftPrice = margin + 6
  const rightPrice = pageWidth - margin - 6

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9)
  doc.setTextColor(...TEXT_MUTED)
  doc.text(`Base Fare (${totalPassengers} traveller${totalPassengers > 1 ? 's' : ''})`, leftPrice, y + 8)
  doc.setTextColor(...TEXT_MAIN)
  doc.text(`$${subtotal.toFixed(2)}`, rightPrice, y + 8, { align: 'right' })

  doc.setTextColor(...TEXT_MUTED)
  doc.text('Taxes & Carrier-Imposed Fees', leftPrice, y + 15)
  doc.setTextColor(...TEXT_MAIN)
  doc.text(`$${taxes.toFixed(2)}`, rightPrice, y + 15, { align: 'right' })

  drawDashedLine(doc, leftPrice, y + 21, rightPrice, y + 21)

  doc.setFont('helvetica', 'bold')
  doc.setFontSize(12)
  doc.setTextColor(...BRAND_PRIMARY)
  doc.text('TOTAL AMOUNT', leftPrice, y + 28)
  doc.text(`$${total.toFixed(2)}`, rightPrice, y + 28, { align: 'right' })

  if (paymentIntentId) {
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(8)
    doc.setTextColor(...TEXT_MUTED)
    doc.text(`Reference: ${paymentIntentId}`, leftPrice, y + 33)
  }

  doc.save(`FlySmart-Ticket-${bookingId}.pdf`)
}
