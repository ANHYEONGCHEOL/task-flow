import { useState } from 'react'
import {
  PRIORITIES,
  PRIORITY_LABEL,
  isTitleEmpty,
  type Priority,
  type TaskInput,
} from '../types'

interface Props {
  onCreate: (input: TaskInput) => Promise<void>
}

// 새 Task 입력은 보드 안 입력 영역에서 한다. (D-010)
export default function NewTaskForm({ onCreate }: Props) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState<Priority>('NORMAL')
  const [dueDate, setDueDate] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (isTitleEmpty(title)) {
      setError('제목을 입력해 주세요.')
      return
    }
    setError('')
    setBusy(true)
    try {
      // 마감일은 비워도 되고 지난 날짜도 된다. (BR-02)
      await onCreate({
        title,
        description,
        priority,
        due_date: dueDate || null,
      })
      setTitle('')
      setDescription('')
      setPriority('NORMAL')
      setDueDate('')
    } catch {
      // 실패하면 입력한 내용을 지우지 않는다.
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="new-task" onSubmit={submit}>
      <input
        aria-label="제목"
        placeholder="제목 (필수)"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />
      <textarea
        aria-label="설명"
        placeholder="설명 (선택)"
        rows={2}
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
      </div>
      <button type="submit" disabled={busy}>
        등록
      </button>
      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}
    </form>
  )
}
