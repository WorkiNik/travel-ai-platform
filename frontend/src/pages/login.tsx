import { useState, type SyntheticEvent, type CSSProperties } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export const Login = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const { login, isLoading, error, clearError } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e: SyntheticEvent) => {
    e.preventDefault()
    clearError()
    try {
      await login(email, password)
      navigate('/')
    } catch {
      // ошибка уже показана через store
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.eyebrow}>TRAVEL AI · BOARDING</div>
        <h1 style={styles.title}>С возвращением</h1>
        <p style={styles.subtitle}>Войдите, чтобы продолжить планирование поездки</p>

        <form onSubmit={handleSubmit} style={styles.form}>
          <label style={styles.label}>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={styles.input}
              placeholder="you@example.com"
            />
          </label>

          <label style={styles.label}>
            Пароль
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={styles.input}
              placeholder="••••••••"
            />
          </label>

          {error && <div style={styles.errorBox}>{error}</div>}

          <button type="submit" disabled={isLoading} style={styles.submitBtn}>
            {isLoading ? 'Вход…' : 'Войти'}
          </button>
        </form>

        <p style={styles.footer}>
          Нет аккаунта? <Link to="/register" style={styles.link}>Зарегистрироваться</Link>
        </p>
      </div>
    </div>
  )
}

const styles: Record<string, CSSProperties> = {
  page: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background:
      'radial-gradient(circle at 50% 0%, #1a2635 0%, #0f1720 60%)',
    padding: 20,
  },
  card: {
    width: '100%',
    maxWidth: 380,
    background: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    borderRadius: 14,
    padding: '36px 32px',
  },
  eyebrow: {
    fontFamily: 'var(--font-mono)',
    fontSize: 11,
    letterSpacing: 2,
    color: 'var(--color-accent)',
    marginBottom: 12,
  },
  title: {
    fontFamily: 'var(--font-display)',
    fontSize: 28,
    fontWeight: 600,
    margin: '0 0 6px',
  },
  subtitle: {
    color: 'var(--color-text-muted)',
    fontSize: 14,
    margin: '0 0 28px',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
  },
  label: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
    fontSize: 13,
    color: 'var(--color-text-muted)',
  },
  input: {
    background: 'var(--color-surface-raised)',
    border: '1px solid var(--color-border)',
    borderRadius: 8,
    padding: '11px 12px',
    color: 'var(--color-text)',
    fontSize: 14,
  },
  errorBox: {
    background: 'rgba(224, 104, 90, 0.12)',
    border: '1px solid var(--color-danger)',
    color: '#f0a99e',
    borderRadius: 8,
    padding: '10px 12px',
    fontSize: 13,
  },
  submitBtn: {
    background: 'var(--color-accent)',
    color: '#1a1204',
    border: 'none',
    borderRadius: 8,
    padding: '12px 0',
    fontWeight: 600,
    fontSize: 14,
    marginTop: 6,
  },
  footer: {
    marginTop: 24,
    fontSize: 13,
    color: 'var(--color-text-muted)',
    textAlign: 'center',
  },
  link: {
    color: 'var(--color-accent)',
    textDecoration: 'none',
  },
}