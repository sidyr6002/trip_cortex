import { useState } from 'react'
import { createFileRoute, Link } from '@tanstack/react-router'
import { useSignUp } from '@clerk/tanstack-react-start'
import { FaArrowLeftLong } from 'react-icons/fa6'

export const Route = createFileRoute('/register')({
  validateSearch: (search: Record<string, unknown>) => ({
    redirect_url: (search.redirect_url as string) || '/search',
  }),
  component: RegisterPage,
})

function RegisterPage() {
  const { signUp, setActive, isLoaded } = useSignUp()
  const { redirect_url } = Route.useSearch()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [code, setCode] = useState('')
  const [pendingVerification, setPendingVerification] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const activateAndRedirect = async (sessionId: string) => {
    if (!setActive) return
    await setActive({ session: sessionId })
    window.location.replace(redirect_url)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isLoaded) return

    setError('')
    setLoading(true)

    try {
      const result = await signUp.create({ emailAddress: email, password })

      if (result.status === 'complete' && result.createdSessionId) {
        // Sign-up completed immediately (no email verification required)
        await activateAndRedirect(result.createdSessionId)
        return
      }

      // Email verification required
      await signUp.prepareEmailAddressVerification({ strategy: 'email_code' })
      setPendingVerification(true)
    } catch (err: any) {
      setError(
        err?.errors?.[0]?.longMessage ||
          err?.errors?.[0]?.message ||
          'Something went wrong.',
      )
    } finally {
      setLoading(false)
    }
  }

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isLoaded) return

    setError('')
    setLoading(true)

    try {
      const result = await signUp.attemptEmailAddressVerification({ code })

      if (result.status === 'complete' && result.createdSessionId) {
        await activateAndRedirect(result.createdSessionId)
      } else {
        setError('Verification could not be completed. Please try again.')
      }
    } catch (err: any) {
      setError(
        err?.errors?.[0]?.longMessage ||
          err?.errors?.[0]?.message ||
          'Invalid verification code.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-linear-to-br from-royal-blue-200 to-zumthor-50 px-4 relative">
      <Link
        to="/"
        className="absolute top-6 left-6 md:top-8 md:left-8 z-20 flex items-center gap-2 text-royal-blue-700 hover:text-royal-blue-800 font-medium transition-colors"
        aria-label="Go back to home"
      >
        <div className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-full">
          <FaArrowLeftLong className="w-4 h-4" />
          <span className="text-lg">Home</span>
        </div>
      </Link>

      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-primary/5 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-primary/10 blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-primary/3 blur-3xl" />
      </div>

      <div className="relative z-10 flex flex-col items-center gap-6 w-full max-w-sm">
        <div className="text-center">
          <div className="text-4xl font-bold tracking-tight mb-2">
            <span className="text-primary">Fly</span>
            <span className="text-content">Smart</span>
          </div>
          <p className="text-content-light text-sm">Create your account</p>
        </div>

        <form
          onSubmit={pendingVerification ? handleVerify : handleSubmit}
          className="w-full flex flex-col gap-4 bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg"
        >
          {!pendingVerification ? (
            <>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="email" className="text-sm font-medium text-content">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="h-11 px-4 rounded-lg border border-slate-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary transition-colors"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="password" className="text-sm font-medium text-content">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="h-11 px-4 rounded-lg border border-slate-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary transition-colors"
                />
              </div>
            </>
          ) : (
            <div className="flex flex-col gap-1.5">
              <label htmlFor="code" className="text-sm font-medium text-content">
                Verification Code
              </label>
              <p className="text-xs text-content-light">We sent a code to {email}</p>
              <input
                id="code"
                type="text"
                inputMode="numeric"
                required
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="Enter code"
                className="h-11 px-4 rounded-lg border border-slate-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary transition-colors"
              />
            </div>
          )}

          {error && (
            <p className="text-sm text-red-600" role="alert">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading || !isLoaded}
            className="h-11 rounded-lg bg-primary-500 hover:bg-primary-600 text-white font-semibold text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {loading
              ? pendingVerification ? 'Verifying…' : 'Creating account…'
              : pendingVerification ? 'Verify Email' : 'Create Account'}
          </button>
        </form>

        <p className="text-sm text-content-light">
          Already have an account?{' '}
          <Link
            to="/login/$"
            params={{ _splat: '' }}
            search={{ redirect_url }}
            className="text-primary font-medium hover:underline"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
