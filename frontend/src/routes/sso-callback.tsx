import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useClerk } from '@clerk/react'
import { useEffect } from 'react'

function SSOCallback() {
  const { session, loaded } = useClerk()
  const navigate = useNavigate()

  useEffect(() => {
    if (!loaded) return
    navigate({ to: session ? '/booking' : '/sign-in', replace: true })
  }, [loaded, session])

  return null
}

export const Route = createFileRoute('/sso-callback')({
  component: SSOCallback,
})
