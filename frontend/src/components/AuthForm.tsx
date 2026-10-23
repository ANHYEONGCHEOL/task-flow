import { useState } from 'react'
import { ApiError, loginUser, registerUser } from '../api'
import {
  EMAIL_TAKEN_TEXT,
  EMPTY_INPUT_TEXT,
  FAILURE_TEXT,
  INVALID_INPUT_TEXT,
  LOGIN_FAILED_TEXT,
} from '../messages'
import type { User } from '../types'

interface Props {
  onLoggedIn: (user: User) => void
  notice?: string
}

type Mode = 'login' | 'register'

function errorText(mode: Mode, e: unknown): string {
  if (e instanceof ApiError) {
    if (mode === 'login' && e.status === 401) return LOGIN_FAILED_TEXT
    if (mode === 'register' && e.status === 409) return EMAIL_TAKEN_TEXT
    if (mode === 'register' && e.status === 422) return INVALID_INPUT_TEXT
  }
  return FAILURE_TEXT
}

// 로그인과 가입을 한 화면에서 고른다. 가입에 성공하면 이어서 로그인한다.
export default function AuthForm({ onLoggedIn, notice }: Props) {
  const [mode, setMode] = useState<Mode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (email.trim() === '' || password === '') {
      setError(EMPTY_INPUT_TEXT)
      return
    }
    setError('')
    setBusy(true)
    try {
      if (mode === 'register') {
        await registerUser(email, password)
      }
      const user = await loginUser(email, password)
      onLoggedIn(user)
    } catch (err) {
      setError(errorText(mode, err))
    } finally {
      setBusy(false)
    }
  }

  function switchMode() {
    setMode(mode === 'login' ? 'register' : 'login')
    setError('')
  }

  return (
    <form className="auth-form" onSubmit={submit}>
      <h2>{mode === 'login' ? '로그인' : '가입'}</h2>
      {notice && <p className="notice">{notice}</p>}
      <input
        aria-label="이메일"
        type="email"
        placeholder="이메일"
        autoComplete="username"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <input
        aria-label="비밀번호"
        type="password"
        placeholder={mode === 'register' ? '비밀번호 (8자 이상)' : '비밀번호'}
        autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}
      <div className="auth-actions">
        <button type="submit" disabled={busy}>
          {mode === 'login' ? '로그인' : '가입'}
        </button>
        <button type="button" onClick={switchMode}>
          {mode === 'login' ? '가입하러 가기' : '로그인하러 가기'}
        </button>
      </div>
    </form>
  )
}
