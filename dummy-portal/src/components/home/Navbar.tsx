import { Link, useRouterState } from '@tanstack/react-router'
import { SignedIn, SignedOut } from '@clerk/tanstack-react-start'
import UserMenu from './UserMenu'

export default function Navbar({ simplified = false }: { simplified?: boolean }) {
  const routerState = useRouterState()
  const currentUrl = routerState.location.href

  return (
    <nav className={`flex items-center justify-between px-8 py-6 ${simplified ? 'max-w-[1400px]' : 'max-w-7xl'} mx-auto relative z-20 mb-4 transition-[max-width,padding] duration-500 ease-in-out`}>
      <div className="flex items-center gap-8 text-sm font-medium w-1/3">
        {!simplified && (
          <>
            <a href="#" className="nav-link">Home</a>
            <Link to="/search" className="nav-link">Booking</Link>
          </>
        )}
      </div>

      {/* Logo with white background pill */}
      <div className="absolute left-1/2 -translate-x-1/2 top-0 z-10 w-[280px] md:w-[320px]">
        <svg
          viewBox="0 0 360 80"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-auto drop-shadow-[0_4px_12px_rgba(0,0,0,0.06)]"
        >
          <path
            d="M0 0H360C330 0 320 10 310 30L295 60C285 80 270 80 250 80H110C90 80 75 80 65 60L50 30C40 10 30 0 0 0Z"
            fill="white"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center pb-2">
          <Link to="/" className="text-2xl md:text-3xl font-bold tracking-tight">
            <span className="text-primary">Fly</span><span className="text-content">Smart</span>
          </Link>
        </div>
      </div>

      <div className="flex items-center justify-end gap-8 text-sm font-medium w-1/3">
        {!simplified && (
          <>
            <Link to="/deals" className="nav-link">Deals</Link>
          </>
        )}
        <SignedOut>
          <Link to="/login/$" search={{ redirect_url: currentUrl }} className="btn-outline">Login</Link>
        </SignedOut>
        <SignedIn>
          <UserMenu />
        </SignedIn>
      </div>
    </nav>
  );
}
