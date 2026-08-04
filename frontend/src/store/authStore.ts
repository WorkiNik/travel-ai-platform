import { create } from 'zustand'
import { authApi } from '../services/api'

interface AuthState {
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string) => Promise<void>
  logout: () => void
  clearError: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null })
    try {
      const response = await authApi.login(email, password)
      localStorage.setItem('access_token', response.data.access_token)
      set({ isAuthenticated: true, isLoading: false })
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Не удалось войти. Проверьте данные.'
      set({ error: message, isLoading: false })
      throw err
    }
  },

  register: async (email, username, password) => {
    set({ isLoading: true, error: null })
    try {
      await authApi.register(email, username, password)
      set({ isLoading: false })
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Не удалось зарегистрироваться.'
      set({ error: message, isLoading: false })
      throw err
    }
  },

  logout: () => {
    localStorage.removeItem('access_token')
    set({ isAuthenticated: false })
  },

  clearError: () => set({ error: null }),
}))