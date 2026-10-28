import { useState } from 'react'
import {
  PRIORITIES,
  PRIORITY_LABEL,
  isTitleEmpty,
  type Priority,
  type TaskInput,
} from '../types'
import { usePlan } from '../usePlan'
import { useSuggest } from '../useSuggest'
import { PlanButton, PlanNote, PlanPreview } from './PlanParts'
import { SuggestButton, SuggestNote } from './SuggestParts'

interface Props {
  onCreate: (input: TaskInput) => Promise<void>
  onCreateMany: (inputs: TaskInput[]) => Promise<void>
  onUnauthorized: () => void
}

// 새 Task 입력은 보드 안 입력 영역에서 한다. (D-010)
export default function NewTaskForm({
  onCreate,
  onCreateMany,
  onUnauthorized,
}: Props) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState<Priority>('NORMAL')
  const [dueDate, setDueDate] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  // 제안은 입력 칸만 채운다. 마감일 제안이 없으면 이미 적은 마감일은 그대로 둔다.
  const suggest = useSuggest((s) => {
    setPriority(s.priority)
    if (s.due_date) setDueDate(s.due_date)
  }, onUnauthorized)
  const plan = usePlan(onUnauthorized)
  const [saving, setSaving] = useState(false)

  function clearForm() {
    setTitle('')
    setDescription('')
    setPriority('NORMAL')
    setDueDate('')
    suggest.reset()
    plan.reset()
  }

  // 미리본 5개를 확인한 사용자가 눌렀을 때만 저장한다. 주제 자체는 저장하지 않는다.
  async function saveAll() {
    setSaving(true)
    try {
      await onCreateMany(
        plan.items.map((item) => ({
          title: item.title,
          description: '',
          priority: item.priority,
          due_date: item.due_date,
        })),
      )
      clearForm()
    } catch {
      // 실패하면 미리보기를 그대로 둔다. 서버는 하나도 저장하지 않았다.
    } finally {
      setSaving(false)
    }
  }

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
      clearForm()
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
      <SuggestNote
        busy={suggest.busy}
        error={suggest.error}
        reason={suggest.reason}
      />
      <div className="form-actions">
        <button type="submit" disabled={busy}>
          등록
        </button>
        <SuggestButton
          busy={suggest.busy}
          disabled={isTitleEmpty(title)}
          onClick={() => suggest.run({ title, description })}
        />
        <PlanButton
          busy={plan.busy}
          disabled={isTitleEmpty(title) || dueDate === ''}
          onClick={() => plan.run({ title, description, due_date: dueDate })}
        />
      </div>
      <PlanNote
        busy={plan.busy}
        error={plan.error}
        needDue={!isTitleEmpty(title) && dueDate === '' && plan.items.length === 0}
      />
      <PlanPreview
        items={plan.items}
        saving={saving}
        onSave={saveAll}
        onCancel={plan.reset}
      />
      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}
    </form>
  )
}
