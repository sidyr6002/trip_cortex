import { useState } from 'react'
import { Link, useRouterState } from '@tanstack/react-router'
import { SignedIn, SignedOut } from '@clerk/tanstack-react-start'
import { Menu, X } from 'lucide-react'
import UserMenu from './UserMenu'

export default function Navbar({ simplified = false }: { simplified?: boolean }) {
  const routerState = useRouterState()
  const currentUrl = routerState.location.href
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <>
      <nav className={`flex items-center justify-between px-4 sm:px-8 py-6 ${simplified ? 'max-w-[1400px]' : 'max-w-7xl'} mx-auto relative z-20 mb-4 transition-[max-width,padding] duration-500 ease-in-out`}>
        {/* Left links — desktop only */}
        <div className="hidden md:flex items-center gap-8 text-sm font-medium w-1/3">
          {!simplified && (
            <>
              <Link to="/" className="nav-link">Home</Link>
              <Link to="/search" className="nav-link">Booking</Link>
            </>
          )}
        </div>

        {/* Hamburger — mobile only */}
        <button
          className="md:hidden p-2 -ml-2 text-content hover:text-primary transition-colors"
          onClick={() => setMobileOpen(true)}
          aria-label="Open menu"
        >
          <Menu className="w-6 h-6" />
        </button>

        {/* Logo with white background pill */}
        <div className="absolute left-1/2 -translate-x-1/2 top-0 z-10 w-[240px] sm:w-[280px] md:w-[320px]">
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

        {/* Right links — desktop only */}
        <div className="hidden md:flex items-center justify-end gap-8 text-sm font-medium w-1/3">
          {!simplified && (
            <Link to="/deals" className="nav-link">Deals</Link>
          )}
          <SignedIn>
            <Link to="/bookings" className="nav-link">My Bookings</Link>
          </SignedIn>
          <SignedOut>
            <Link to="/login/$" search={{ redirect_url: currentUrl }} className="btn-outline">Login</Link>
          </SignedOut>
          <SignedIn>
            <UserMenu />
          </SignedIn>
        </div>

        {/* Right side — mobile: just auth controls */}
        <div className="flex md:hidden items-center gap-3">
          <SignedOut>
            <Link to="/login/$" search={{ redirect_url: currentUrl }} className="btn-outline text-xs px-4 py-1.5">Login</Link>
          </SignedOut>
          <SignedIn>
            <UserMenu />
          </SignedIn>
        </div>
      </nav>

      {/* Mobile drawer overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden" role="dialog" aria-modal="true">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/30 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
            aria-hidden="true"
          />

          {/* Drawer */}
          <div className="absolute top-0 left-0 h-full w-72 bg-white shadow-xl animate-in slide-in-from-left duration-300">
            <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100">
              <Link to="/" className="text-xl font-bold tracking-tight" onClick={() => setMobileOpen(false)}>
                <span className="text-primary">Fly</span><span className="text-content">Smart</span>
              </Link>
              <button
                onClick={() => setMobileOpen(false)}
                className="p-1.5 text-content-muted hover:text-content transition-colors"
                aria-label="Close menu"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex flex-col px-6 py-4 gap-1">
              {!simplified && (
                <>
                  <MobileNavLink to="/" onClick={() => setMobileOpen(false)}>Home</MobileNavLink>
                  <MobileNavLink to="/search" onClick={() => setMobileOpen(false)}>Booking</MobileNavLink>
                  <MobileNavLink to="/deals" onClick={() => setMobileOpen(false)}>Deals</MobileNavLink>
                </>
              )}
              <SignedIn>
                <MobileNavLink to="/bookings" onClick={() => setMobileOpen(false)}>My Bookings</MobileNavLink>
              </SignedIn>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

function MobileNavLink({ to, onClick, children }: { to: string; onClick: () => void; children: React.ReactNode }) {
  return (
    <Link
      to={to}
      onClick={onClick}
      className="block py-3 px-3 text-base font-medium text-content hover:text-primary hover:bg-primary-50 rounded-lg transition-colors"
    >
      {children}
    </Link>
  )
}
