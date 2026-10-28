import { useState } from 'react'
import {
  PRIORITIES,
  PRIORITY_LABEL,
  STATUSES,
  STATUS_LABEL,
  isTitleEmpty,
  type Priority,
  type Status,
  type Task,
  type TaskInput,
} from '../types'
import { useSuggest } from '../useSuggest'
import { SuggestButton, SuggestNote } from './SuggestParts'

interface Props {
  task: Task
  onChangeStatus: (id: number, status: Status) => void
  onUpdate: (id: number, input: TaskInput) => Promise<void>
  onDelete: (id: number) => void
  onUnauthorized: () => void
}

export default function TaskCard({
  task,
  onChangeStatus,
  onUpdate,
  onDelete,
  onUnauthorized,
}: Props) {
  const [editing, setEditing] = useState(false)
  const [title, setTitle] = useState(task.title)
  const [description, setDescription] = useState(task.description)
  const [priority, setPriority] = useState<Priority>(task.priority)
  const [dueDate, setDueDate] = useState(task.due_date ?? '')
  const [error, setError] = useState('')
  // 제안은 입력 칸만 채운다. 마감일 제안이 없으면 이미 적은 마감일은 그대로 둔다.
  const suggest = useSuggest((s) => {
    setPriority(s.priority)
    if (s.due_date) setDueDate(s.due_date)
  }, onUnauthorized)

  function startEdit() {
    setTitle(task.title)
    setDescription(task.description)
    setPriority(task.priority)
    setDueDate(task.due_date ?? '')
    setError('')
    suggest.reset()
    setEditing(true)
  }

  function cancelEdit() {
    suggest.reset()
    setEditing(false)
  }

  async function save(e: React.FormEvent) {
    e.preventDefault()
    if (isTitleEmpty(title)) {
      setError('제목을 입력해 주세요.')
      return
    }
    try {
      // 마감일을 비우면 null을 보내 지운다. (API-SPEC-CHANGE.md 7.3)
      await onUpdate(task.id, {
        title,
        description,
        priority,
        due_date: dueDate || null,
      })
      suggest.reset()
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
          <div className="field-row">
            <label>
              우선순위
              <select
                aria-label="우선순위"
                value={priority}
                onChange={(e) => setPriority(e.target.value as Priority)}
              >
                {PRIORITIES.map((p) => (
                  <option key={p} value={p}>
                    {PRIORITY_LABEL[p]}
                  </option>
                ))}
              </select>
            </label>
            <label>
              마감일
              <input
                type="date"
                aria-label="마감일"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
              />
            </label>
            {dueDate && (
              <button type="button" onClick={() => setDueDate('')}>
                마감일 지우기
              </button>
            )}
          </div>
          <SuggestNote
            busy={suggest.busy}
            error={suggest.error}
            reason={suggest.reason}
          />
          {error && (
            <p className="field-error" role="alert">
              {error}
            </p>
          )}
          <div className="card-actions">
            <button type="submit">저장</button>
            <SuggestButton
              busy={suggest.busy}
              disabled={isTitleEmpty(title)}
              onClick={() => suggest.run({ title, description })}
            />
            <button type="button" onClick={cancelEdit}>
              취소
            </button>
          </div>
        </form>
      </li>
    )
  }

  return (
    <li className={task.is_overdue ? 'card overdue' : 'card'}>
      <h3>{task.title}</h3>
      {task.description && <p className="card-desc">{task.description}</p>}
      <p className="card-meta">
        <span className={`priority priority-${task.priority.toLowerCase()}`}>
          우선순위 {PRIORITY_LABEL[task.priority]}
        </span>
        {task.due_date && <span>마감 {task.due_date}</span>}
        {/* 색만으로 구분하지 않도록 글자도 함께 보인다. (N-08) 상태는 바꾸지 않는다. (BR-05) */}
        {task.is_overdue && <span className="overdue-badge">기한 초과</span>}
      </p>
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
