export interface User {
  id: number
  email: string
  username: string
  is_active: boolean
  created_at: string
}

export interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface Conversation {
  id: number
  title: string
  created_at: string
  updated_at: string
}

export interface ConversationDetail extends Conversation {
  messages: Message[]
}

export interface DocumentItem {
  id: number
  title: string
  created_at: string
  chunk_count: number
}