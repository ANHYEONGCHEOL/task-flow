import { useEffect, useState } from 'react'
import {
  ApiError,
  changeStatus,
  createTask,
  createTasksBulk,
  deleteTask,
  listTasks,
  updateTask,
} from './api'
import Board from './components/Board'
import NewTaskForm from './components/NewTaskForm'
import { EMPTY_TEXT, FAILURE_TEXT, LOADING_TEXT } from './messages'
import type { Status, Task, TaskInput, User } from './types'

type Load = 'loading' | 'ready' | 'failed'

interface Props {
  user: User
  onLogout: () => void
  onUnauthorized: () => void
}

export default function TaskBoard({ user, onLogout, onUnauthorized }: Props) {
  const [tasks, setTasks] = useState<Task[]>([])
  const [load, setLoad] = useState<Load>('loading')
  const [message, setMessage] = useState('')

  useEffect(() => {
    listTasks()
      .then((list) => {
        setTasks(list)
        setLoad('ready')
      })
      .catch((e) => {
        if (e instanceof ApiError && e.status === 401) {
          onUnauthorized()
          return
        }
        setLoad('failed')
      })
  }, [onUnauthorized])

  // 성공한 뒤 목록을 다시 받아 서버의 정렬과 기한 초과 계산에 맞춘다. (R-011, R-012)
  // 다시 받지 못하면 성공한 응답만 지금 목록에 반영한다.
  async function refresh(fallback: (prev: Task[]) => Task[]) {
    try {
      setTasks(await listTasks())
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        onUnauthorized()
        return
      }
      setTasks(fallback)
    }
  }

  async function handleCreate(input: TaskInput) {
    let created: Task
    try {
      created = await createTask(input)
    } catch (e) {
      setMessage(FAILURE_TEXT)
      await resyncIfGone(e)
      throw e
    }
    setMessage('')
    await refresh((prev) => [...prev, created])
  }

  // 미리본 할일을 한꺼번에 저장한다. 서버가 전부 저장하거나 하나도 저장하지 않는다.
  async function handleCreateMany(inputs: TaskInput[]) {
    let created: Task[]
    try {
      created = await createTasksBulk(inputs)
    } catch (e) {
      setMessage(FAILURE_TEXT)
      await resyncIfGone(e)
      throw e
    }
    setMessage('')
    await refresh((prev) => [...prev, ...created])
  }

  // 로그인이 끝났으면(401) 로그인 화면으로 보내고, 카드가 이미 없으면(404)
  // 목록을 다시 불러와 저장된 내용에 맞춘다. (API-SPEC 4)
  async function resyncIfGone(e: unknown) {
    if (e instanceof ApiError && e.status === 401) {
      onUnauthorized()
      return
    }
    if (e instanceof ApiError && e.status === 404) {
      try {
        setTasks(await listTasks())
      } catch {
        // 목록도 못 받으면 지금 화면을 그대로 둔다.
      }
    }
  }

  // 성공한 뒤에만 화면을 바꾼다. 실패하면 변경 전 상태 그대로 둔다.
  async function handleChangeStatus(id: number, status: Status) {
    let updated: Task
    try {
      updated = await changeStatus(id, status)
    } catch (e) {
      setMessage(FAILURE_TEXT)
      await resyncIfGone(e)
      return
    }
    setMessage('')
    await refresh((prev) => prev.map((t) => (t.id === id ? updated : t)))
  }

  async function handleUpdate(id: number, input: TaskInput) {
    let updated: Task
    try {
      updated = await updateTask(id, input)
    } catch (e) {
      setMessage(FAILURE_TEXT)
      await resyncIfGone(e)
      throw e
    }
    setMessage('')
    await refresh((prev) => prev.map((t) => (t.id === id ? updated : t)))
  }

  // 삭제는 서버가 성공한 뒤에만 목록에서 뺀다.
  async function handleDelete(id: number) {
    try {
      await deleteTask(id)
      setTasks((prev) => prev.filter((t) => t.id !== id))
      setMessage('')
    } catch (e) {
      setMessage(FAILURE_TEXT)
      await resyncIfGone(e)
    }
  }

  return (
    <main>
      <header className="app-header">
        <h1>task-flow</h1>
        <div className="user-box">
          <span className="user-email">{user.email}</span>
          <button type="button" onClick={onLogout}>
            로그아웃
          </button>
        </div>
      </header>
      <NewTaskForm
        onCreate={handleCreate}
        onCreateMany={handleCreateMany}
        onUnauthorized={onUnauthorized}
      />
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
        <p className="empty-note">{EMPTY_TEXT}</p>
      )}
      {/* 카드가 하나도 없어도 상태 열은 그대로 보인다. */}
      {load === 'ready' && (
        <Board
          tasks={tasks}
          onChangeStatus={handleChangeStatus}
          onUpdate={handleUpdate}
          onDelete={handleDelete}
          onUnauthorized={onUnauthorized}
        />
      )}
    </main>
  )
}

