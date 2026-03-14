import { useState } from 'react'
import { createFileRoute, Link } from '@tanstack/react-router'
import {
  useSignIn,
  AuthenticateWithRedirectCallback,
} from '@clerk/tanstack-react-start'
import { FcGoogle } from 'react-icons/fc'
import { FaArrowLeftLong } from 'react-icons/fa6'

export const Route = createFileRoute('/login/$')({
  validateSearch: (search: Record<string, unknown>) => ({
    redirect_url: (search.redirect_url as string) || '/',
  }),
  component: LoginPage,
})

function LoginPage() {
  const { signIn, setActive, isLoaded } = useSignIn()
  const { _splat } = Route.useParams()
  const { redirect_url } = Route.useSearch()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (_splat === 'sso-callback') {
    return <AuthenticateWithRedirectCallback />
  }

  const handleGoogleSignIn = () => {
    signIn?.authenticateWithRedirect({
      strategy: 'oauth_google',
      redirectUrl: '/login/sso-callback',
      redirectUrlComplete: redirect_url,
    })
  }

  const handleEmailPasswordSignIn = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isLoaded || !signIn) return

    setError('')
    setLoading(true)

    try {
      const result = await signIn.create({
        identifier: email,
        password,
      })

      if (result.status === 'complete' && result.createdSessionId) {
        await setActive!({ session: result.createdSessionId })
        window.location.href = redirect_url
      } else {
        setError('Sign in could not be completed. Please try again.')
      }
    } catch (err: any) {
      const msg =
        err?.errors?.[0]?.longMessage ||
        err?.errors?.[0]?.message ||
        'Invalid email or password.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-linear-to-br from-royal-blue-200 to-zumthor-50 px-4 relative">
      {/* Back Button */}
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

      {/* Decorative background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-primary/5 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-primary/10 blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-primary/3 blur-3xl" />
      </div>

      <div className="relative z-10 flex flex-col items-center gap-6 w-full max-w-sm">
        {/* Header */}
        <div className="text-center">
          <div className="text-4xl font-bold tracking-tight mb-2">
            <span className="text-primary">Fly</span>
            <span className="text-content">Smart</span>
          </div>
          <p className="text-content-light text-sm">Your journey starts here</p>
        </div>

        {/* Email/Password Form */}
        <form
          onSubmit={handleEmailPasswordSignIn}
          className="w-full flex flex-col gap-4 bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg"
        >
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
            <label
              htmlFor="password"
              className="text-sm font-medium text-content"
            >
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
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>

        {/* Divider */}
        <div className="flex items-center gap-3 w-full px-2">
          <div className="flex-1 h-px bg-slate-300" />
          <span className="text-xs text-content-light uppercase tracking-wide">
            or
          </span>
          <div className="flex-1 h-px bg-slate-300" />
        </div>

        {/* Google OAuth */}
        <button
          onClick={handleGoogleSignIn}
          className="h-14 w-full px-8 rounded-full bg-primary-500 hover:bg-primary-600 border-0 transition-all duration-300 shadow-lg shadow-primary-500/25 hover:shadow-xl hover:shadow-primary-500/30 hover:scale-[1.02] font-semibold text-white text-base flex items-center justify-center gap-3 cursor-pointer"
        >
          <div className="p-0.5 bg-white flex items-center justify-center rounded-full">
            <FcGoogle className="w-6 h-6" />
          </div>
          Continue with Google
        </button>

        {/* Link to register */}
        <p className="text-sm text-content-light">
          Don&apos;t have an account?{' '}
          <Link
            to="/register"
            search={{ redirect_url }}
            className="text-primary font-medium hover:underline"
          >
            Create account
          </Link>
        </p>
      </div>
    </div>
  )
}
