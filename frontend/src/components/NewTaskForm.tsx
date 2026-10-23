import { useState } from 'react'
import { isTitleEmpty } from '../types'

interface Props {
  onCreate: (input: { title: string; description: string }) => Promise<void>
}

// 새 Task 입력은 보드 안 입력 영역에서 한다. (D-010)
export default function NewTaskForm({ onCreate }: Props) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
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
      await onCreate({ title, description })
      setTitle('')
      setDescription('')
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
