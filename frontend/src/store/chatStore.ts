import { create } from 'zustand'
import { conversationsApi, streamMessage } from '../services/api'
import type { Conversation, ConversationDetail } from '../types'

interface ChatState {
  conversations: Conversation[]
  currentConversation: ConversationDetail | null
  isLoadingList: boolean
  isSending: boolean
  error: string | null

  loadConversations: () => Promise<void>
  createConversation: (title: string) => Promise<number>
  openConversation: (id: number) => Promise<void>
  sendMessage: (content: string) => Promise<void>
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  currentConversation: null,
  isLoadingList: false,
  isSending: false,
  error: null,

  loadConversations: async () => {
    set({ isLoadingList: true })
    try {
      const response = await conversationsApi.list()
      set({ conversations: response.data, isLoadingList: false })
    } catch {
      set({ isLoadingList: false, error: 'Не удалось загрузить разговоры' })
    }
  },

  createConversation: async (title: string) => {
    const response = await conversationsApi.create(title)
    await get().loadConversations()
    return response.data.id
  },

  openConversation: async (id: number) => {
    const response = await conversationsApi.get(id)
    set({ currentConversation: response.data })
  },

  sendMessage: async (content: string) => {
    const conv = get().currentConversation
    if (!conv) return

    const optimisticUserMessage = {
      id: Date.now(),
      role: 'user' as const,
      content,
      created_at: new Date().toISOString(),
    }

    // Временное "пустое" сообщение ассистента — будет наполняться текстом по мере стрима
    const streamingId = Date.now() + 1
    const streamingPlaceholder = {
      id: streamingId,
      role: 'assistant' as const,
      content: '',
      created_at: new Date().toISOString(),
    }

    set({
      currentConversation: {
        ...conv,
        messages: [...conv.messages, optimisticUserMessage, streamingPlaceholder],
      },
      isSending: true,
      error: null,
    })

    await streamMessage(
      conv.id,
      content,
      // onDelta — очередной кусочек текста пришёл
      (delta) => {
        set((state) => {
          if (!state.currentConversation) return state
          return {
            currentConversation: {
              ...state.currentConversation,
              messages: state.currentConversation.messages.map((m) =>
                m.id === streamingId ? { ...m, content: m.content + delta } : m
              ),
            },
          }
        })
      },
      // onDone — стрим завершён, подставляем реальный id/timestamp из БД
      (final) => {
        set((state) => {
          if (!state.currentConversation) return state
          return {
            currentConversation: {
              ...state.currentConversation,
              messages: state.currentConversation.messages.map((m) =>
                m.id === streamingId ? { ...m, id: final.id, created_at: final.created_at } : m
              ),
            },
            isSending: false,
          }
        })
      },
      // onError — что-то пошло не так, убираем оба "черновых" сообщения
      (errMsg) => {
        set((state) => ({
          currentConversation: state.currentConversation
            ? {
                ...state.currentConversation,
                messages: state.currentConversation.messages.filter(
                  (m) => m.id !== optimisticUserMessage.id && m.id !== streamingId
                ),
              }
            : null,
          isSending: false,
          error: errMsg,
        }))
      }
    )
  },
}))