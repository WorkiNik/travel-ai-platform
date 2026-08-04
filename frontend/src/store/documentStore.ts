import { create } from 'zustand'
import { documentsApi } from '../services/api'
import type { DocumentItem } from '../types'

interface DocumentState {
  documents: DocumentItem[]
  isLoading: boolean
  isUploading: boolean
  error: string | null

  loadDocuments: () => Promise<void>
  uploadDocument: (title: string, content: string) => Promise<void>
  deleteDocument: (id: number) => Promise<void>
}

export const useDocumentStore = create<DocumentState>((set, get) => ({
  documents: [],
  isLoading: false,
  isUploading: false,
  error: null,

  loadDocuments: async () => {
    set({ isLoading: true })
    try {
      const response = await documentsApi.list()
      set({ documents: response.data, isLoading: false })
    } catch {
      set({ isLoading: false, error: 'Не удалось загрузить документы' })
    }
  },

  uploadDocument: async (title, content) => {
    set({ isUploading: true, error: null })
    try {
      await documentsApi.create(title, content)
      await get().loadDocuments()
      set({ isUploading: false })
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Не удалось загрузить документ'
      set({ isUploading: false, error: message })
      throw err
    }
  },

  deleteDocument: async (id) => {
    await documentsApi.delete(id)
    set((state) => ({ documents: state.documents.filter((d) => d.id !== id) }))
  },
}))