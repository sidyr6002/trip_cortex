import { createFileRoute } from '@tanstack/react-router'
import { searchFlights } from '../../data/searchFlights'

const classMap: Record<string, string> = {
  economy: 'class_1',
  premium_economy: 'class_2',
  business: 'class_3',
  first: 'class_4',
}

export const Route = createFileRoute('/api/flights')({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const url = new URL(request.url)
        const from = url.searchParams.get('from') ?? undefined
        const to = url.searchParams.get('to') ?? undefined
        const date = url.searchParams.get('date') ?? undefined
        const cabin = url.searchParams.get('class') ?? 'economy'

        const flights = searchFlights({
          originAirportCode: from,
          destinationAirportCode: to,
          departureDate: date,
          classId: classMap[cabin] ?? cabin,
          excludeSoldOut: true,
        })

        return Response.json({ flights, total: flights.length })
      },
    },
  },
})
