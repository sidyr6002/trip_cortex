import { Outlet, createRootRouteWithContext } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/router-devtools'

export interface RouterContext {
  isSignedIn: boolean
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: () => (
    <>
      <div className="min-h-screen bg-background">
        <Outlet />
      </div>
      <TanStackRouterDevtools position="bottom-right" />
    </>
  ),
})
