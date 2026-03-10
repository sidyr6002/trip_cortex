import { pdf } from '@react-pdf/renderer'
import TicketDocument from './TicketDocument'
import type { TicketData } from './TicketDocument'

export type { TicketData }

export async function generateTicketPdf(data: TicketData) {
  const blob = await pdf(<TicketDocument {...data} />).toBlob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `FlySmart-Ticket-${data.bookingId}.pdf`
  a.click()
  URL.revokeObjectURL(url)
}
