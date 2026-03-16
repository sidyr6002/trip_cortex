import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/sso-callback')({
  component: () => <div>Authenticating...</div>, // replaced with Clerk callback in Task 5
})
