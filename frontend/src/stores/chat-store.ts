import { create } from 'zustand'

export type ChatMessage =
  | { role: 'user'; type: 'request'; text: string }
  | { role: 'system'; type: 'status'; text: string }
  | { role: 'system'; type: 'progress'; text: string }
  | { role: 'system'; type: 'flight_options' }
  | { role: 'system'; type: 'confirmed'; text: string }
  | { role: 'system'; type: 'error'; text: string }

interface ChatState {
  messages: ChatMessage[]
  addMessage: (msg: ChatMessage) => void
  clear: () => void
}

export const useChatStore = create<ChatState>()((set) => ({
  messages: [],
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  clear: () => set({ messages: [] }),
}))
