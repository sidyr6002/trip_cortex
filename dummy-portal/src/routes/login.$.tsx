import { createFileRoute, Link } from '@tanstack/react-router'
import { useSignIn } from '@clerk/tanstack-react-start'
import { FcGoogle } from 'react-icons/fc'
import { FaArrowLeftLong } from 'react-icons/fa6'

export const Route = createFileRoute('/login/$')({ component: LoginPage })

function LoginPage() {
  const { signIn } = useSignIn()

  const handleGoogleSignIn = () => {
    signIn?.authenticateWithRedirect({
      strategy: 'oauth_google',
      redirectUrl: '/login/sso-callback',
      redirectUrlComplete: '/',
    })
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-linear-to-br from-royal-blue-200 to-zumthor-50 px-4 relative">
      {/* Back Button */}
      <Link
        to="/"
        className="absolute top-6 left-6 md:top-8 md:left-8 z-20 flex items-center gap-2 text-royal-blue-700 hover:text-royal-blue-800 font-medium transition-colors"
        aria-label="Go back to home"
      >
        <div className='flex items-center gap-2 px-4 py-2 bg-white rounded-full'>
          <FaArrowLeftLong className="w-4 h-4" />
          <span className='text-lg'>Home</span>
        </div>
      </Link>

      {/* Decorative background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-primary/5 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-primary/10 blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-primary/3 blur-3xl" />
      </div>

      <div className="relative z-10 flex flex-col items-center gap-8">
        {/* FlySmart Header */}
        <div className="text-center">
          <div className="text-4xl font-bold tracking-tight mb-2">
            <span className="text-primary">Fly</span>
            <span className="text-content">Smart</span>
          </div>
          <p className="text-content-light text-sm">Your journey starts here</p>
        </div>

        {/* Sign In Button */}
        <button
          onClick={handleGoogleSignIn}
          className="h-14 px-8 rounded-full bg-royal-blue-500 hover:bg-royal-blue-600 border-0 transition-all duration-300 shadow-lg shadow-royal-blue-500/25 hover:shadow-xl hover:shadow-royal-blue-500/30 hover:scale-[1.02] font-semibold text-white text-base flex items-center justify-center gap-3 cursor-pointer"
        >

          <div className='p-0.5 bg-white flex items-center justify-center rounded-full'>
            <FcGoogle className="w-6 h-6" />
          </div>
          Continue with Google
        </button>
      </div>
    </div>
  )
}
