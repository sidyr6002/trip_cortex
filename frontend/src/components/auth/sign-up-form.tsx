import { useSignUp } from '@clerk/react'
import { useNavigate, Link } from '@tanstack/react-router'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useState } from 'react'
import { Eye, EyeOff, Loader2, Mail } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'

const credentialsSchema = z
  .object({
    firstName: z.string().min(1, 'First name is required'),
    lastName: z.string().min(1, 'Last name is required'),
    email: z.string().email('Enter a valid email address'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string(),
  })
  .refine((d) => d.password === d.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })

const otpSchema = z.object({
  code: z.string().length(6, 'Enter the 6-digit code'),
})

type CredentialsValues = z.infer<typeof credentialsSchema>
type OtpValues = z.infer<typeof otpSchema>

const CLERK_ERROR_MAP: Record<string, string> = {
  form_identifier_exists: 'An account with this email already exists.',
  form_password_pwned: 'This password has appeared in a data breach. Please choose a different one.',
  too_many_requests: 'Too many attempts. Please wait a moment and try again.',
  form_code_incorrect: 'Incorrect code. Please try again.',
  verification_expired: 'The code has expired. Please request a new one.',
  session_exists: 'You are already signed in. Please sign out first.',
}

function mapError(code: string) {
  return CLERK_ERROR_MAP[code] ?? 'Something went wrong. Please try again.'
}

export function SignUpForm() {
  const { signUp, fetchStatus } = useSignUp()
  const navigate = useNavigate()
  const [step, setStep] = useState<'credentials' | 'verify'>('credentials')
  const [serverError, setServerError] = useState<string | null>(null)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  const credentialsForm = useForm<CredentialsValues>({
    resolver: zodResolver(credentialsSchema),
  })

  const otpForm = useForm<OtpValues>({
    resolver: zodResolver(otpSchema),
  })

  const loading = credentialsForm.formState.isSubmitting ||
    otpForm.formState.isSubmitting ||
    fetchStatus === 'fetching'

  async function onCredentialsSubmit({ firstName, lastName, email, password }: CredentialsValues) {
    setServerError(null)
    const { error } = await signUp.password({
      emailAddress: email,
      password,
      firstName,
      lastName,
    })
    if (error) {
      console.error('[SignUp] password error:', error)
      setServerError(mapError(error.code))
      return
    }
    console.log('[SignUp] status after password:', signUp.status)

    if (signUp.status === 'complete') {
      // Email verification disabled — finalize immediately
      await signUp.finalize({
        navigate: ({ decorateUrl }) => {
          navigate({ to: decorateUrl('/booking') as '/booking' })
        },
      })
      return
    }

    // Email verification enabled — send OTP
    const { error: sendError } = await signUp.verifications.sendEmailCode()
    if (sendError) {
      console.error('[SignUp] sendEmailCode error:', sendError)
      setServerError(mapError(sendError.code))
      return
    }
    setStep('verify')
  }

  async function onOtpSubmit({ code }: OtpValues) {
    setServerError(null)
    const { error } = await signUp.verifications.verifyEmailCode({ code })
    if (error) {
      console.error('[SignUp] verifyEmailCode error:', error)
      setServerError(mapError(error.code))
      return
    }
    console.log('[SignUp] status after verify:', signUp.status)
    if (signUp.status === 'complete') {
      await signUp.finalize({
        navigate: ({ decorateUrl }) => {
          navigate({ to: decorateUrl('/booking') as '/booking' })
        },
      })
    }
  }

  async function signUpWithGoogle() {
    console.log('[SignUp] initiating Google SSO')
    await signUp.sso({
      strategy: 'oauth_google',
      redirectUrl: '/sso-callback',
      redirectCallbackUrl: '/booking',
    })
  }

  async function resendCode() {
    setServerError(null)
    const { error } = await signUp.verifications.sendEmailCode()
    if (error) setServerError(mapError(error.code))
  }

  // — Verification step —
  if (step === 'verify') {
    return (
      <div className="space-y-6">
        <div className="space-y-1">
          <div className="flex size-10 items-center justify-center rounded-full bg-primary/10 text-primary mb-3">
            <Mail className="size-5" />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">Check your email</h1>
          <p className="text-sm text-muted-foreground">
            We sent a 6-digit code to{' '}
            <span className="font-medium text-foreground">
              {signUp.emailAddress}
            </span>
          </p>
        </div>

        <form onSubmit={otpForm.handleSubmit(onOtpSubmit)} className="space-y-4" noValidate>
          <div className="space-y-1.5">
            <Label htmlFor="code">Verification code</Label>
            <Input
              id="code"
              type="text"
              inputMode="numeric"
              maxLength={6}
              placeholder="000000"
              autoComplete="one-time-code"
              autoFocus
              className="tracking-widest text-center text-lg"
              aria-invalid={!!otpForm.formState.errors.code}
              aria-describedby={otpForm.formState.errors.code ? 'code-error' : undefined}
              {...otpForm.register('code')}
            />
            {otpForm.formState.errors.code && (
              <p id="code-error" role="alert" className="text-xs text-destructive">
                {otpForm.formState.errors.code.message}
              </p>
            )}
          </div>

          {serverError && (
            <div role="alert" className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {serverError}
            </div>
          )}

          <Button type="submit" className="w-full" disabled={loading} size="lg">
            {loading ? <><Loader2 className="size-4 animate-spin" /> Verifying…</> : 'Verify email'}
          </Button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          Didn't receive it?{' '}
          <button
            type="button"
            onClick={resendCode}
            disabled={loading}
            className="font-medium text-primary hover:underline underline-offset-4 cursor-pointer disabled:opacity-50"
          >
            Resend code
          </button>
        </p>

        <p className="text-center text-sm text-muted-foreground">
          <button
            type="button"
            onClick={() => { setStep('credentials'); setServerError(null) }}
            className="font-medium text-primary hover:underline underline-offset-4 cursor-pointer"
          >
            ← Back
          </button>
        </p>
      </div>
    )
  }

  // — Credentials step —
  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Create an account</h1>
        <p className="text-sm text-muted-foreground">
          Start booking smarter today
        </p>
      </div>

      <Button
        variant="outline"
        className="w-full"
        onClick={signUpWithGoogle}
        type="button"
        disabled={loading}
      >
        <svg className="size-4 shrink-0" viewBox="0 0 24 24" aria-hidden="true">
          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" />
          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
        </svg>
        Continue with Google
      </Button>

      <div className="flex items-center gap-3">
        <Separator className="flex-1" />
        <span className="text-xs text-muted-foreground">or</span>
        <Separator className="flex-1" />
      </div>

      <form onSubmit={credentialsForm.handleSubmit(onCredentialsSubmit)} className="space-y-4" noValidate>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label htmlFor="firstName">First name</Label>
            <Input
              id="firstName"
              type="text"
              autoComplete="given-name"
              autoFocus
              aria-invalid={!!credentialsForm.formState.errors.firstName}
              {...credentialsForm.register('firstName')}
            />
            {credentialsForm.formState.errors.firstName && (
              <p role="alert" className="text-xs text-destructive">
                {credentialsForm.formState.errors.firstName.message}
              </p>
            )}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="lastName">Last name</Label>
            <Input
              id="lastName"
              type="text"
              autoComplete="family-name"
              aria-invalid={!!credentialsForm.formState.errors.lastName}
              {...credentialsForm.register('lastName')}
            />
            {credentialsForm.formState.errors.lastName && (
              <p role="alert" className="text-xs text-destructive">
                {credentialsForm.formState.errors.lastName.message}
              </p>
            )}
          </div>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="email">Work email</Label>
          <Input
            id="email"
            type="email"
            placeholder="you@company.com"
            autoComplete="email"
            aria-invalid={!!credentialsForm.formState.errors.email}
            {...credentialsForm.register('email')}
          />
          {credentialsForm.formState.errors.email && (
            <p role="alert" className="text-xs text-destructive">
              {credentialsForm.formState.errors.email.message}
            </p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="password">Password</Label>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="new-password"
              aria-invalid={!!credentialsForm.formState.errors.password}
              className="pr-9"
              {...credentialsForm.register('password')}
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 cursor-pointer text-muted-foreground hover:text-foreground transition-colors"
            >
              {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
            </button>
          </div>
          {credentialsForm.formState.errors.password && (
            <p role="alert" className="text-xs text-destructive">
              {credentialsForm.formState.errors.password.message}
            </p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="confirmPassword">Confirm password</Label>
          <div className="relative">
            <Input
              id="confirmPassword"
              type={showConfirm ? 'text' : 'password'}
              autoComplete="new-password"
              aria-invalid={!!credentialsForm.formState.errors.confirmPassword}
              className="pr-9"
              {...credentialsForm.register('confirmPassword')}
            />
            <button
              type="button"
              onClick={() => setShowConfirm((v) => !v)}
              aria-label={showConfirm ? 'Hide password' : 'Show password'}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 cursor-pointer text-muted-foreground hover:text-foreground transition-colors"
            >
              {showConfirm ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
            </button>
          </div>
          {credentialsForm.formState.errors.confirmPassword && (
            <p role="alert" className="text-xs text-destructive">
              {credentialsForm.formState.errors.confirmPassword.message}
            </p>
          )}
        </div>

        {serverError && (
          <div role="alert" className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {serverError}
          </div>
        )}

        {/* Required for Clerk bot protection */}
        <div id="clerk-captcha" />

        <Button type="submit" className="w-full" disabled={loading} size="lg">
          {loading ? <><Loader2 className="size-4 animate-spin" /> Creating account…</> : 'Create account'}
        </Button>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        Already have an account?{' '}
        <Link to="/sign-in" className="font-medium text-primary hover:underline underline-offset-4">
          Sign in
        </Link>
      </p>
    </div>
  )
}
