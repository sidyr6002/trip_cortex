import { Outlet, createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/_authed')({
  beforeLoad: ({ context }) => {
    if (!context.isSignedIn) {
      throw redirect({ to: '/sign-in' })
    }
  },
  component: () => <Outlet />,
})
