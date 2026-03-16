import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CheckCircle2, Plane, CreditCard, Hash } from 'lucide-react'

interface Props {
  confirmation: {
    bookingReference: string
    paymentReference: string
    totalAmount: number
    flightNumber: string
  }
}

export function BookingConfirmation({ confirmation }: Props) {
  return (
    <Card className="w-full max-w-md border-green-200 bg-gradient-to-br from-green-50 to-emerald-50 dark:border-green-800 dark:from-green-950/40 dark:to-emerald-950/40">
      <CardContent className="pt-6">
        <div className="mb-4 flex items-center gap-2">
          <CheckCircle2 className="h-6 w-6 text-green-600 dark:text-green-400" />
          <h3 className="text-lg font-semibold text-green-800 dark:text-green-200">
            Booking Confirmed!
          </h3>
        </div>

        <div className="space-y-3">
          <Row icon={<Hash className="h-4 w-4" />} label="Reference">
            <Badge variant="secondary" className="font-mono text-sm">
              {confirmation.bookingReference}
            </Badge>
          </Row>
          <Row icon={<Plane className="h-4 w-4" />} label="Flight">
            {confirmation.flightNumber}
          </Row>
          <Row icon={<CreditCard className="h-4 w-4" />} label="Total Paid">
            <span className="font-semibold">${confirmation.totalAmount.toFixed(2)}</span>
          </Row>
        </div>

        <p className="mt-4 text-xs text-muted-foreground">
          Payment ref: {confirmation.paymentReference}
        </p>
      </CardContent>
    </Card>
  )
}

function Row({ icon, label, children }: { icon: React.ReactNode; label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between">
      <span className="flex items-center gap-2 text-sm text-muted-foreground">
        {icon} {label}
      </span>
      <span className="text-sm text-foreground">{children}</span>
    </div>
  )
}
