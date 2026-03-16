import { useRef, useEffect, useCallback } from 'react'
import { useClerk, useUser } from '@clerk/react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { useBookingStore } from '@/stores/booking-store'
import { useChatStore } from '@/stores/chat-store'

type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'error'

const badgeVariant: Record<
  ConnectionStatus,
  'default' | 'secondary' | 'outline' | 'destructive'
> = {
  connected: 'default',
  connecting: 'secondary',
  disconnected: 'outline',
  error: 'destructive',
}

interface ChatLayoutProps {
  children: React.ReactNode
  input: React.ReactNode
}

export function ChatLayout({ children, input }: ChatLayoutProps) {
  const { signOut } = useClerk()
  const { user } = useUser()
  const connectionStatus = useBookingStore(
    (s) => s.connectionStatus,
  ) as ConnectionStatus
  const messages = useChatStore((s) => s.messages)

  const viewportRef = useRef<HTMLElement | null>(null)
  const userScrolled = useRef(false)

  const scrollAreaRef = useCallback((node: HTMLElement | null) => {
    if (!node) return
    viewportRef.current = node.querySelector(
      '[data-slot="scroll-area-viewport"]',
    )
  }, [])

  useEffect(() => {
    const el = viewportRef.current
    if (!el || userScrolled.current) return
    el.scrollTop = el.scrollHeight
  }, [messages])

  return (
    <div className="bg-background flex h-screen flex-col">
      {/* Header — card bg + shadow to lift it */}
      <header className="bg-card flex items-center justify-between px-5 py-3 shadow-sm">
        <span className="text-base font-semibold tracking-tight">
          Trip Cortex
        </span>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">
            {user?.primaryEmailAddress?.emailAddress}
          </span>
          <Badge variant={badgeVariant[connectionStatus]}>
            {connectionStatus}
          </Badge>
          <Button
            size="sm"
            variant="destructive"
            onClick={() => signOut({ redirectUrl: '/sign-in' })}
          >
            Sign out
          </Button>
        </div>
      </header>

      {/* Message area — muted wash to contrast with white bubbles */}
      <ScrollArea
        ref={scrollAreaRef}
        className="bg-muted/40 flex-1 px-4 py-6"
        onScrollCapture={() => {
          const el = viewportRef.current
          if (!el) return
          userScrolled.current =
            el.scrollHeight - el.scrollTop - el.clientHeight > 40
        }}
      >
        {children}
      </ScrollArea>

      {/* Footer — card bg + top border to separate from chat */}
      <div className="bg-card border-t">{input}</div>
    </div>
  )
}
