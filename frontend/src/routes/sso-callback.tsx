import { createFileRoute } from '@tanstack/react-router'
import { AuthenticateWithRedirectCallback } from '@clerk/react'

export const Route = createFileRoute('/sso-callback')({
  component: () => <AuthenticateWithRedirectCallback />,
})
