import { useEffect, useState } from 'react'

type Connection = 'checking' | 'ok' | 'fail'

function App() {
  const [connection, setConnection] = useState<Connection>('checking')

  useEffect(() => {
    fetch('/api/health')
      .then((res) => setConnection(res.ok ? 'ok' : 'fail'))
      .catch(() => setConnection('fail'))
  }, [])

  const message = {
    checking: 'API 연결 확인 중...',
    ok: 'API 연결됨',
    fail: 'API에 연결할 수 없음',
  }[connection]

  return (
    <main>
      <h1>task-flow</h1>
      <p>{message}</p>
    </main>
  )
}

export default App
