import { useState } from 'react'
import {
  STATUSES,
  STATUS_LABEL,
  isTitleEmpty,
  type Status,
  type Task,
} from '../types'

interface Props {
  task: Task
  onChangeStatus: (id: number, status: Status) => void
  onUpdate: (
    id: number,
    input: { title: string; description: string },
  ) => Promise<void>
  onDelete: (id: number) => void
}

export default function TaskCard({
  task,
  onChangeStatus,
  onUpdate,
  onDelete,
}: Props) {
  const [editing, setEditing] = useState(false)
  const [title, setTitle] = useState(task.title)
  const [description, setDescription] = useState(task.description)
  const [error, setError] = useState('')

  function startEdit() {
    setTitle(task.title)
    setDescription(task.description)
    setError('')
    setEditing(true)
  }

  async function save(e: React.FormEvent) {
    e.preventDefault()
    if (isTitleEmpty(title)) {
      setError('제목을 입력해 주세요.')
      return
    }
    try {
      await onUpdate(task.id, { title, description })
      setEditing(false)
    } catch {
      // 실패하면 편집 중인 내용을 그대로 둔다.
    }
  }

  function remove() {
    // 지우기 전에 한 번 묻고, 확인한 뒤에만 요청한다. (D-014)
    if (window.confirm(`"${task.title}" 카드를 삭제할까요?`)) {
      onDelete(task.id)
    }
  }

  if (editing) {
    return (
      <li className="card">
        <form className="edit-form" onSubmit={save}>
          <input
            aria-label="제목"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <textarea
            aria-label="설명"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          {error && (
            <p className="field-error" role="alert">
              {error}
            </p>
          )}
          <div className="card-actions">
            <button type="submit">저장</button>
            <button type="button" onClick={() => setEditing(false)}>
              취소
            </button>
          </div>
        </form>
      </li>
    )
  }

  return (
    <li className="card">
      <h3>{task.title}</h3>
      {task.description && <p className="card-desc">{task.description}</p>}
      <div className="card-actions">
        {/* 사용자가 고른 뒤에만 요청한다. (R-003) */}
        <div
          className="status-buttons"
          role="group"
          aria-label={`${task.title} 상태 변경`}
        >
          {STATUSES.map((s) => (
            <button
              key={s}
              type="button"
              className={s === task.status ? 'current' : undefined}
              aria-pressed={s === task.status}
              onClick={() => {
                if (s !== task.status) onChangeStatus(task.id, s)
              }}
            >
              {STATUS_LABEL[s]}
            </button>
          ))}
        </div>
        <button type="button" onClick={startEdit}>
          수정
        </button>
        <button type="button" onClick={remove}>
          삭제
        </button>
      </div>
    </li>
  )
}
