import { createFileRoute } from '@tanstack/react-router'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useChatSync } from '@/hooks/useChatSync'
import { useChatStore } from '@/stores/chat-store'
import { ChatLayout } from '@/components/booking/chat-layout'
import { ChatMessageBubble } from '@/components/booking/chat-message'
import { ChatInput } from '@/components/booking/chat-input'

export const Route = createFileRoute('/_authed/booking')({
  component: BookingPage,
})

function BookingPage() {
  useWebSocket()
  useChatSync()

  const messages = useChatStore((s) => s.messages)

  return (
    <ChatLayout input={<ChatInput />}>
      <div className="flex flex-col gap-3">
        {messages.length === 0 && (
          <p className="text-center text-sm text-muted-foreground">
            Describe your trip and I'll handle the booking.
          </p>
        )}
        {messages.map((msg, i) => (
          <ChatMessageBubble key={i} msg={msg} />
        ))}
      </div>
    </ChatLayout>
  )
}
