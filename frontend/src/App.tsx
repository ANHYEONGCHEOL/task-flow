import { useEffect, useState } from 'react'
import { createTask, listTasks } from './api'
import Board from './components/Board'
import NewTaskForm from './components/NewTaskForm'
import type { Task } from './types'

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

  return (
    <main>
      <header className="app-header">
        <h1>task-flow</h1>
      </header>
      <NewTaskForm onCreate={handleCreate} />
      {message && <p className="notice">{message}</p>}
      <Board tasks={tasks} />
    </main>
  )
}

export default App
