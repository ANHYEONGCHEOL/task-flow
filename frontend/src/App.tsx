import { useCallback, useEffect, useState } from 'react'
import { getMe, logoutUser } from './api'
import AuthForm from './components/AuthForm'
import { LOADING_TEXT, SESSION_ENDED_TEXT } from './messages'
import TaskBoard from './TaskBoard'
import type { User } from './types'

// 로그인한 사용자가 있으면 보드를, 없으면 로그인 · 가입 화면을 보여 준다.
// user: undefined = 확인 중, null = 로그인하지 않음
function App() {
  const [user, setUser] = useState<User | null | undefined>(undefined)
  const [notice, setNotice] = useState('')

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => setUser(null))
  }, [])

  async function handleLogout() {
    try {
      await logoutUser()
    } catch {
      // 이미 로그인이 끝난 경우에도 로그인 화면으로 간다.
    }
    setNotice('')
    setUser(null)
  }

  // 보드가 불러오기를 다시 하지 않도록 함수가 바뀌지 않게 둔다.
  const handleUnauthorized = useCallback(() => {
    setNotice(SESSION_ENDED_TEXT)
    setUser(null)
  }, [])

  if (user === undefined) {
    return (
      <main>
        <p className="screen-state">{LOADING_TEXT}</p>
      </main>
    )
  }

  if (user === null) {
    return (
      <main>
        <header className="app-header">
          <h1>task-flow</h1>
        </header>
        <AuthForm
          notice={notice}
          onLoggedIn={(loggedIn) => {
            setNotice('')
            setUser(loggedIn)
          }}
        />
      </main>
    )
  }

  return (
    <TaskBoard
      key={user.id}
      user={user}
      onLogout={handleLogout}
      onUnauthorized={handleUnauthorized}
    />
  )
}

export default App
