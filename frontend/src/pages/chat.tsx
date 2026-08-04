import { useEffect, useState, type SyntheticEvent, type CSSProperties } from 'react'
import { useChatStore } from '../store/chatStore'
import { useAuthStore } from '../store/authStore'
import { useDocumentStore } from '../store/documentStore'

export const Chat = () => {
  const {
    conversations,
    currentConversation,
    isSending,
    error,
    loadConversations,
    createConversation,
    openConversation,
    sendMessage,
  } = useChatStore()
  const { logout } = useAuthStore()
  const {
    documents,
    isUploading,
    error: docError,
    loadDocuments,
    uploadDocument,
    deleteDocument,
  } = useDocumentStore()

  const [draft, setDraft] = useState('')
  const [showDocForm, setShowDocForm] = useState(false)
  const [docTitle, setDocTitle] = useState('')
  const [docContent, setDocContent] = useState('')

  useEffect(() => {
    loadConversations()
    loadDocuments()
  }, [])

  const handleNewConversation = async () => {
    const title = window.prompt('Название поездки (например, "Отпуск в Японии")')
    if (!title) return
    const id = await createConversation(title)
    await openConversation(id)
  }

  const handleSend = async (e: SyntheticEvent) => {
    e.preventDefault()
    if (!draft.trim()) return
    const text = draft
    setDraft('')
    await sendMessage(text)
  }

  const handleUploadDocument = async (e: SyntheticEvent) => {
    e.preventDefault()
    if (!docTitle.trim() || !docContent.trim()) return
    try {
      await uploadDocument(docTitle, docContent)
      setDocTitle('')
      setDocContent('')
      setShowDocForm(false)
    } catch {
      // ошибка уже показана через store
    }
  }

  const handleDeleteDocument = async (id: number, e: SyntheticEvent) => {
    e.stopPropagation()
    if (!window.confirm('Удалить документ? AI перестанет учитывать его в ответах.')) return
    await deleteDocument(id)
  }

  return (
    <div style={styles.app}>
      {/* Sidebar — список рейсов/разговоров + документы */}
      <aside style={styles.sidebar}>
        <div style={styles.sidebarHeader}>
          <div>
            <div style={styles.eyebrow}>TRAVEL AI</div>
            <div style={styles.brand}>Панель рейсов</div>
          </div>
          <button onClick={logout} style={styles.logoutBtn} title="Выйти">
            ⏻
          </button>
        </div>

        <button onClick={handleNewConversation} style={styles.newBtn}>
          + Новая поездка
        </button>

        <div style={styles.convList}>
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => openConversation(conv.id)}
              style={{
                ...styles.convItem,
                ...(currentConversation?.id === conv.id ? styles.convItemActive : {}),
              }}
            >
              <span style={styles.convId}>#{String(conv.id).padStart(3, '0')}</span>
              <span style={styles.convTitle}>{conv.title}</span>
            </button>
          ))}
          {conversations.length === 0 && (
            <p style={styles.emptyHint}>Пока нет поездок. Создайте первую выше.</p>
          )}
        </div>

        {/* --- Секция документов (RAG) --- */}
        <div style={styles.sectionDivider} />

        <div style={styles.sidebarSectionHeader}>
          <span style={styles.eyebrow}>ДОКУМЕНТЫ</span>
          <button
            onClick={() => setShowDocForm((v) => !v)}
            style={styles.smallAddBtn}
            title="Добавить документ"
          >
            {showDocForm ? '×' : '+'}
          </button>
        </div>

        {showDocForm && (
          <form onSubmit={handleUploadDocument} style={styles.docForm}>
            <input
              value={docTitle}
              onChange={(e) => setDocTitle(e.target.value)}
              placeholder="Название (например, «Гайд по Токио»)"
              style={styles.docFormInput}
            />
            <textarea
              value={docContent}
              onChange={(e) => setDocContent(e.target.value)}
              placeholder="Вставьте текст: заметки, гайд, визовые требования…"
              style={styles.docFormTextarea}
              rows={5}
            />
            {docError && <div style={styles.docFormError}>{docError}</div>}
            <button type="submit" disabled={isUploading} style={styles.docFormSubmit}>
              {isUploading ? 'Обрабатываем…' : 'Сохранить'}
            </button>
          </form>
        )}

        <div style={styles.docList}>
          {documents.map((doc) => (
            <div key={doc.id} style={styles.docItem}>
              <div style={styles.docItemInfo}>
                <span style={styles.docItemTitle}>{doc.title}</span>
                <span style={styles.docItemMeta}>{doc.chunk_count} фрагм.</span>
              </div>
              <button
                onClick={(e) => handleDeleteDocument(doc.id, e)}
                style={styles.docDeleteBtn}
                title="Удалить"
              >
                ×
              </button>
            </div>
          ))}
          {documents.length === 0 && !showDocForm && (
            <p style={styles.emptyHint}>
              Загрузите гайд или заметки — AI будет учитывать их в ответах
            </p>
          )}
        </div>
      </aside>

      {/* Линия отрыва — фирменный элемент */}
      <div style={styles.perforation} />

      {/* Основное окно чата */}
      <main style={styles.main}>
        {!currentConversation ? (
          <div style={styles.emptyState}>
            <div style={styles.emptyIcon}>✈</div>
            <p>Выберите поездку слева или создайте новую</p>
          </div>
        ) : (
          <>
            <header style={styles.chatHeader}>
              <span style={styles.convId}>#{String(currentConversation.id).padStart(3, '0')}</span>
              <h2 style={styles.chatTitle}>{currentConversation.title}</h2>
            </header>

            <div style={styles.messages}>
              {currentConversation.messages.map((msg) => (
                <div
                  key={msg.id}
                  style={{
                    ...styles.messageRow,
                    justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  }}
                >
                  <div
                    style={{
                      ...styles.bubble,
                      ...(msg.role === 'user' ? styles.bubbleUser : styles.bubbleAssistant),
                    }}
                  >
                    {msg.role === 'assistant' && (
                      <div style={styles.bubbleLabel}>TRAVEL AI</div>
                    )}
                    {msg.role === 'assistant' && msg.content === '' ? (
                      <div style={styles.typingDots} className="typing-dots">
                        <span /><span /><span />
                      </div>
                    ) : (
                      <div style={styles.bubbleContent}>{msg.content}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {error && <div style={styles.errorBanner}>{error}</div>}

            <form onSubmit={handleSend} style={styles.inputBar}>
              <input
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder="Спросите про маршрут, отель, билеты…"
                style={styles.textInput}
              />
              <button type="submit" disabled={isSending || !draft.trim()} style={styles.sendBtn}>
                Отправить
              </button>
            </form>
          </>
        )}
      </main>
    </div>
  )
}

const styles: Record<string, CSSProperties> = {
  app: {
    display: 'flex',
    height: '100vh',
    background: 'var(--color-bg)',
  },
  sidebar: {
    width: 280,
    display: 'flex',
    flexDirection: 'column',
    padding: '20px 16px',
    gap: 16,
    overflowY: 'auto',
  },
  sidebarHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  eyebrow: {
    fontFamily: 'var(--font-mono)',
    fontSize: 10,
    letterSpacing: 2,
    color: 'var(--color-accent)',
  },
  brand: {
    fontFamily: 'var(--font-display)',
    fontSize: 18,
    fontWeight: 600,
    marginTop: 4,
  },
  logoutBtn: {
    background: 'transparent',
    border: '1px solid var(--color-border)',
    color: 'var(--color-text-muted)',
    borderRadius: 8,
    width: 32,
    height: 32,
    fontSize: 14,
  },
  newBtn: {
    background: 'var(--color-surface-raised)',
    border: '1px dashed var(--color-accent-dim)',
    color: 'var(--color-accent)',
    borderRadius: 8,
    padding: '10px 0',
    fontSize: 13,
    fontWeight: 600,
  },
  convList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  convItem: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-start',
    gap: 2,
    background: 'transparent',
    border: '1px solid transparent',
    borderRadius: 8,
    padding: '10px 12px',
    textAlign: 'left',
  },
  convItemActive: {
    background: 'var(--color-surface-raised)',
    borderColor: 'var(--color-border)',
  },
  convId: {
    fontFamily: 'var(--font-mono)',
    fontSize: 10,
    color: 'var(--color-accent)',
    letterSpacing: 1,
  },
  convTitle: {
    fontSize: 14,
    color: 'var(--color-text)',
  },
  emptyHint: {
    color: 'var(--color-text-muted)',
    fontSize: 13,
    padding: '0 4px',
  },
  sectionDivider: {
    height: 1,
    background: 'var(--color-border)',
    margin: '4px 0',
  },
  sidebarSectionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  smallAddBtn: {
    background: 'var(--color-surface-raised)',
    border: '1px solid var(--color-border)',
    color: 'var(--color-accent)',
    borderRadius: 6,
    width: 22,
    height: 22,
    fontSize: 14,
    lineHeight: 1,
    padding: 0,
  },
  docForm: {
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
    background: 'var(--color-surface-raised)',
    border: '1px solid var(--color-border)',
    borderRadius: 8,
    padding: 10,
  },
  docFormInput: {
    background: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    borderRadius: 6,
    padding: '8px 10px',
    color: 'var(--color-text)',
    fontSize: 13,
  },
  docFormTextarea: {
    background: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    borderRadius: 6,
    padding: '8px 10px',
    color: 'var(--color-text)',
    fontSize: 13,
    resize: 'vertical',
    fontFamily: 'var(--font-body)',
  },
  docFormError: {
    fontSize: 12,
    color: '#f0a99e',
  },
  docFormSubmit: {
    background: 'var(--color-accent)',
    color: '#1a1204',
    border: 'none',
    borderRadius: 6,
    padding: '8px 0',
    fontWeight: 600,
    fontSize: 13,
  },
  docList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  docItem: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    background: 'var(--color-surface-raised)',
    border: '1px solid var(--color-border)',
    borderRadius: 8,
    padding: '8px 10px',
  },
  docItemInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: 2,
    minWidth: 0,
  },
  docItemTitle: {
    fontSize: 13,
    color: 'var(--color-text)',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  docItemMeta: {
    fontFamily: 'var(--font-mono)',
    fontSize: 10,
    color: 'var(--color-text-muted)',
  },
  docDeleteBtn: {
    background: 'transparent',
    border: 'none',
    color: 'var(--color-text-muted)',
    fontSize: 16,
    lineHeight: 1,
    padding: '0 4px',
    flexShrink: 0,
  },
  perforation: {
    width: 1,
    backgroundImage:
      'repeating-linear-gradient(to bottom, var(--color-border) 0, var(--color-border) 6px, transparent 6px, transparent 14px)',
  },
  main: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
  },
  emptyState: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    color: 'var(--color-text-muted)',
  },
  emptyIcon: {
    fontSize: 32,
    color: 'var(--color-accent)',
  },
  chatHeader: {
    padding: '20px 28px',
    borderBottom: '1px solid var(--color-border)',
    display: 'flex',
    alignItems: 'center',
    gap: 10,
  },
  chatTitle: {
    fontFamily: 'var(--font-display)',
    fontSize: 18,
    fontWeight: 600,
    margin: 0,
  },
  messages: {
    flex: 1,
    overflowY: 'auto',
    padding: '24px 28px',
    display: 'flex',
    flexDirection: 'column',
    gap: 14,
  },
  messageRow: {
    display: 'flex',
  },
  bubble: {
    maxWidth: '70%',
    borderRadius: 12,
    padding: '12px 16px',
    fontSize: 14,
    lineHeight: 1.5,
  },
  bubbleUser: {
    background: 'var(--color-user-bubble)',
    color: 'var(--color-text)',
  },
  bubbleAssistant: {
    background: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    borderLeft: '3px solid var(--color-accent)',
  },
  bubbleLabel: {
    fontFamily: 'var(--font-mono)',
    fontSize: 10,
    letterSpacing: 1.5,
    color: 'var(--color-accent)',
    marginBottom: 6,
  },
  bubbleContent: {
    whiteSpace: 'pre-wrap',
  },
  typingDots: {
    display: 'flex',
    gap: 4,
  },
  errorBanner: {
    margin: '0 28px 12px',
    background: 'rgba(224, 104, 90, 0.12)',
    border: '1px solid var(--color-danger)',
    color: '#f0a99e',
    borderRadius: 8,
    padding: '10px 14px',
    fontSize: 13,
  },
  inputBar: {
    display: 'flex',
    gap: 10,
    padding: '18px 28px',
    borderTop: '1px solid var(--color-border)',
  },
  textInput: {
    flex: 1,
    background: 'var(--color-surface-raised)',
    border: '1px solid var(--color-border)',
    borderRadius: 8,
    padding: '12px 14px',
    color: 'var(--color-text)',
    fontSize: 14,
  },
  sendBtn: {
    background: 'var(--color-accent)',
    color: '#1a1204',
    border: 'none',
    borderRadius: 8,
    padding: '0 22px',
    fontWeight: 600,
    fontSize: 14,
  },
}