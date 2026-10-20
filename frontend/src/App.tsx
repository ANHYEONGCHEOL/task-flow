import { useEffect, useState } from 'react'
import { changeStatus, createTask, listTasks } from './api'
import Board from './components/Board'
import NewTaskForm from './components/NewTaskForm'
import type { Status, Task } from './types'

function App() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [message, setMessage] = useState('')

  useEffect(() => {
    listTasks()
      .then(setTasks)
      .catch(() => setMessage('카드를 불러오지 못했습니다.'))
  }, [])

  async function handleCreate(input: { title: string; description: string }) {
    try {
      const created = await createTask(input)
      setTasks((prev) => [...prev, created])
      setMessage('')
    } catch (e) {
      setMessage('카드를 등록하지 못했습니다.')
      throw e
    }
  }

  // 성공한 뒤에만 화면을 바꾼다. 실패하면 변경 전 상태 그대로 둔다.
  async function handleChangeStatus(id: number, status: Status) {
    try {
      const updated = await changeStatus(id, status)
      setTasks((prev) => prev.map((t) => (t.id === id ? updated : t)))
      setMessage('')
    } catch {
      setMessage('상태를 바꾸지 못했습니다.')
    }
  }

  return (
    <main>
      <header className="app-header">
        <h1>task-flow</h1>
      </header>
      <NewTaskForm onCreate={handleCreate} />
      {message && <p className="notice">{message}</p>}
      <Board tasks={tasks} onChangeStatus={handleChangeStatus} />
    </main>
  )
}

export default App
