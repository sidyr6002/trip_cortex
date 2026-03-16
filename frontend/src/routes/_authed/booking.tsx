import { createFileRoute } from '@tanstack/react-router'
import { useClerk, useUser } from '@clerk/react'
import { Button } from '@/components/ui/button'

export const Route = createFileRoute('/_authed/booking')({
  component: BookingPage,
})

function BookingPage() {
  const { signOut } = useClerk()
  const { user } = useUser()

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4">
      <p className="text-muted-foreground text-sm">
        Signed in as <span className="font-medium text-foreground">{user?.primaryEmailAddress?.emailAddress}</span>
      </p>
      <p className="text-muted-foreground">Booking chat — Story 8.4</p>
      <Button variant="outline" onClick={() => signOut({ redirectUrl: '/sign-in' })}>
        Sign out
      </Button>
    </div>
  )
}
