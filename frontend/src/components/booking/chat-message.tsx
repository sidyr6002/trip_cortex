import { cn } from '@/lib/utils'
import type { ChatMessage } from '@/stores/chat-store'
import { FlightSelection } from './flight-selection'

export function ChatMessageBubble({ msg }: { msg: ChatMessage }) {
  if (msg.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[70%] rounded-2xl rounded-br-sm bg-primary px-4 py-2 text-sm text-primary-foreground shadow-sm">
          {msg.text}
        </div>
      </div>
    )
  }

  const base =
    'max-w-[70%] rounded-2xl rounded-bl-sm bg-card px-4 py-2 text-sm shadow-sm'

  if (msg.type === 'progress') {
    return (
      <div className="flex">
        <div className={cn(base, 'text-muted-foreground')}>
          <span className="mr-2 inline-block animate-pulse">●</span>
          {msg.text}
        </div>
      </div>
    )
  }

  if (msg.type === 'confirmed') {
    return (
      <div className="flex">
        <div
          className={cn(
            base,
            'bg-green-50 text-green-800 dark:bg-green-900/40 dark:text-green-200',
          )}
        >
          {msg.text}
        </div>
      </div>
    )
  }

  if (msg.type === 'error') {
    return (
      <div className="flex">
        <div className={cn(base, 'bg-destructive/10 text-destructive')}>
          {msg.text}
        </div>
      </div>
    )
  }

  if (msg.type === 'flight_options') {
    return (
      <div className="flex">
        <div className="max-w-[85%]">
          <FlightSelection />
        </div>
      </div>
    )
  }

  // status
  return (
    <div className="flex">
      <div className={cn(base, 'text-foreground')}>{msg.text}</div>
    </div>
  )
}
