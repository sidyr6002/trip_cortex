import { useState } from 'react'
import { useUser, useClerk } from '@clerk/tanstack-react-start'
import { useNavigate } from '@tanstack/react-router'
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from '../ui/popover'

export default function UserMenu() {
  const { user } = useUser()
  const { signOut, openUserProfile } = useClerk()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  if (!user) return null

  const initials = [user.firstName, user.lastName]
    .filter(Boolean)
    .map((n) => n![0])
    .join('')
    .toUpperCase() || user.primaryEmailAddress?.emailAddress[0]?.toUpperCase() || '?'

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          className="w-10 h-10 rounded-full overflow-hidden border-2 border-primary/20 hover:border-primary/50 transition-colors cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary/40 focus:ring-offset-2"
          aria-label="User menu"
        >
          {user.imageUrl ? (
            <img
              src={user.imageUrl}
              alt={user.fullName || 'User avatar'}
              className="w-full h-full object-cover"
              referrerPolicy="no-referrer"
            />
          ) : (
            <div className="w-full h-full bg-primary text-white flex items-center justify-center text-sm font-semibold">
              {initials}
            </div>
          )}
        </button>
      </PopoverTrigger>

      <PopoverContent align="end" sideOffset={8} className="w-56 p-0">
        {/* User info header */}
        <div className="px-4 py-3 border-b border-slate-100">
          <p className="text-sm font-medium text-slate-900 truncate">
            {user.fullName || 'User'}
          </p>
          <p className="text-xs text-slate-500 truncate">
            {user.primaryEmailAddress?.emailAddress}
          </p>
        </div>

        {/* Menu items */}
        <div className="py-1">
          <button
            onClick={() => {
              setOpen(false)
              openUserProfile()
            }}
            className="w-full text-left px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer"
          >
            Edit Profile
          </button>
          <button
            onClick={() => {
              setOpen(false)
              navigate({ to: '/' })
            }}
            className="w-full text-left px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer"
          >
            My Bookings
          </button>
        </div>

        {/* Logout */}
        <div className="border-t border-slate-100 py-1">
          <button
            onClick={() => {
              setOpen(false)
              signOut({ redirectUrl: '/' })
            }}
            className="w-full text-left px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors cursor-pointer"
          >
            Log Out
          </button>
        </div>
      </PopoverContent>
    </Popover>
  )
}
