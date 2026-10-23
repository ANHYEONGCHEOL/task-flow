import { useEffect, useState } from 'react'
import {
  changeStatus,
  createTask,
  deleteTask,
  listTasks,
  updateTask,
} from './api'
import Board from './components/Board'
import NewTaskForm from './components/NewTaskForm'
import type { Status, Task } from './types'

// 화면 상태 문구는 SCREEN-SPEC.md의 사용자 지정 문구 그대로다.
const LOADING_TEXT = '로딩중'
const EMPTY_TEXT = '결과값을 찾아오지 못하였습니다.'
const FAILURE_TEXT = '사용자의 권한이 없습니다'

type Load = 'loading' | 'ready' | 'failed'

function App() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [load, setLoad] = useState<Load>('loading')
  const [message, setMessage] = useState('')

  useEffect(() => {
    listTasks()
      .then((list) => {
        setTasks(list)
        setLoad('ready')
      })
      .catch(() => setLoad('failed'))
  }, [])

  async function handleCreate(input: { title: string; description: string }) {
    try {
      const created = await createTask(input)
      setTasks((prev) => [...prev, created])
      setMessage('')
    } catch (e) {
      setMessage(FAILURE_TEXT)
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
      setMessage(FAILURE_TEXT)
    }
  }

  async function handleUpdate(
    id: number,
    input: { title: string; description: string },
  ) {
    try {
      const updated = await updateTask(id, input)
      setTasks((prev) => prev.map((t) => (t.id === id ? updated : t)))
      setMessage('')
    } catch (e) {
      setMessage(FAILURE_TEXT)
      throw e
    }
  }

  // 삭제는 서버가 성공한 뒤에만 목록에서 뺀다.
  async function handleDelete(id: number) {
    try {
      await deleteTask(id)
      setTasks((prev) => prev.filter((t) => t.id !== id))
      setMessage('')
    } catch {
      setMessage(FAILURE_TEXT)
    }
  }

  return (
    <main>
      <header className="app-header">
        <h1>task-flow</h1>
      </header>
      <NewTaskForm onCreate={handleCreate} />
      {message && (
        <p className="notice" role="alert">
          {message}
        </p>
      )}
      {load === 'loading' && <p className="screen-state">{LOADING_TEXT}</p>}
      {load === 'failed' && (
        <p className="screen-state failure" role="alert">
          {FAILURE_TEXT}
        </p>
      )}
      {load === 'ready' && tasks.length === 0 && (
        <p className="screen-state">{EMPTY_TEXT}</p>
      )}
      {load === 'ready' && tasks.length > 0 && (
        <Board
          tasks={tasks}
          onChangeStatus={handleChangeStatus}
          onUpdate={handleUpdate}
          onDelete={handleDelete}
        />
      )}
    </main>
  )
}

export default App
