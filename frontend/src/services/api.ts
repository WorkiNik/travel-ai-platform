import axios from 'axios'

export const api = axios.create({
  baseURL: '',  // относительный путь — работает через Caddy на любом домене/порту
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  register: (email: string, username: string, password: string) =>
    api.post('/auth/register', { email, username, password }),

  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
}

export const conversationsApi = {
  list: () => api.get('/conversations/'),
  create: (title: string) => api.post('/conversations/', { title }),
  get: (id: number) => api.get(`/conversations/${id}`),
  sendMessage: (id: number, content: string) =>
    api.post(`/conversations/${id}/messages`, { content }),
}

export const documentsApi = {
  list: () => api.get('/documents/'),
  create: (title: string, content: string) => api.post('/documents/', { title, content }),
  delete: (id: number) => api.delete(`/documents/${id}`),
}

interface StreamDoneData {
  id: number
  created_at: string
}

/**
 * Отправляет сообщение и читает ответ AI по кусочкам через SSE.
 * Использует нативный fetch, так как axios плохо работает со streaming-body в браузере.
 */
export async function streamMessage(
  convId: number,
  content: string,
  onDelta: (text: string) => void,
  onDone: (data: StreamDoneData) => void,
  onError: (message: string) => void
) {
  const token = localStorage.getItem('access_token')

  let response: Response
  try {
    response = await fetch(`/conversations/${convId}/messages/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ content }),
    })
  } catch {
    onError('Не удалось связаться с сервером')
    return
  }

  if (!response.ok || !response.body) {
    onError('AI не ответил. Попробуйте ещё раз.')
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const events = buffer.split('\n\n')
    buffer = events.pop() || ''

    for (const event of events) {
      if (!event.startsWith('data: ')) continue
      const jsonStr = event.slice(6)
      try {
        const data = JSON.parse(jsonStr)
        if (data.delta) onDelta(data.delta)
        else if (data.done) onDone({ id: data.id, created_at: data.created_at })
        else if (data.error) onError(data.error)
      } catch {
        // игнорируем неполные/битые JSON-куски на границах чанков
      }
    }
  }


  

}
/**
 * FastAPI возвращает detail как строку в обычных ошибках (HTTPException),
 * но как массив объектов {type, loc, msg, ...} при 422-ошибках валидации Pydantic.
 * Эта функция приводит оба случая к безопасной для рендера строке.
 */
export function extractErrorMessage(err: any, fallback: string): string {
  const detail = err?.response?.data?.detail

  if (typeof detail === 'string') {
    return detail
  }

  if (Array.isArray(detail)) {
    return detail.map((d: any) => d.msg || 'Ошибка валидации').join('; ')
  }

  return fallback
}