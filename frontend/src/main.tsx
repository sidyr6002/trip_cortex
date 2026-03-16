import './styles.css'
import ReactDOM from 'react-dom/client'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import { ClerkProvider, useAuth } from '@clerk/react'
import { routeTree } from './routeTree.gen'

const router = createRouter({
  routeTree,
  defaultPreload: 'intent',
  context: { isSignedIn: false },
})

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

function App() {
  const { isSignedIn } = useAuth()
  return (
    <RouterProvider
      router={router}
      context={{ isSignedIn: isSignedIn ?? false }}
    />
  )
}

ReactDOM.createRoot(document.getElementById('app')!).render(
  <ClerkProvider publishableKey={import.meta.env.VITE_CLERK_PUBLISHABLE_KEY}>
    <App />
  </ClerkProvider>,
)
