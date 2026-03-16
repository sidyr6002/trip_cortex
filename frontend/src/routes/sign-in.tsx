import { createFileRoute, redirect } from '@tanstack/react-router'
import { SignInForm } from '@/components/auth/sign-in-form'

export const Route = createFileRoute('/sign-in')({
  beforeLoad: ({ context }) => {
    if (context.isSignedIn) throw redirect({ to: '/booking' })
  },
  component: SignInPage,
})

function SignInPage() {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Left panel — branding */}
      <div className="hidden lg:flex flex-col justify-between bg-primary p-10 text-primary-foreground">
        <div className="flex items-center gap-2 text-lg font-semibold">
          <svg
            viewBox="0 0 24 24"
            className="size-6 fill-current"
            aria-hidden="true"
          >
            <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
          </svg>
          Trip Cortex
        </div>
        <blockquote className="space-y-2">
          <p className="text-lg leading-relaxed">
            "Book smarter. Travel compliant. Every trip, every time."
          </p>
          <footer className="text-sm text-primary-foreground/70">
            AI-powered corporate travel
          </footer>
        </blockquote>
      </div>

      {/* Right panel — form */}
      <div className="flex flex-col items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-sm space-y-6">
          {/* Mobile logo */}
          <div className="flex items-center gap-2 text-base font-semibold lg:hidden">
            <svg
              viewBox="0 0 24 24"
              className="size-5 fill-primary"
              aria-hidden="true"
            >
              <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
            </svg>
            Trip Cortex
          </div>
          <SignInForm />
        </div>
      </div>
    </div>
  )
}
