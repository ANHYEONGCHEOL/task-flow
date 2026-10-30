import { useState, type FormEvent } from 'react'
import { COMMAND_FAILED_TEXT, COMMAND_LOADING_TEXT, useCommand } from '../useCommand'
import { PRIORITY_LABEL, type CommandAction, type Task } from '../types'

const MAX_LENGTH = 200

interface Row {
  action: CommandAction
  text: string
}

// 한 줄로 보여 줄 글. 제목은 id로 지금 목록에서 찾고, 목록에 없는 id는 null이다(그 줄을 뺀다).
function describe(action: CommandAction, tasks: Map<number, Task>): string | null {
  if (action.kind === 'add') {
    const title = action.title ?? ''
    const priority = PRIORITY_LABEL[action.priority ?? 'NORMAL']
    return `${title} — 새로 등록 (우선순위 ${priority} · 마감 ${action.due_date ?? '없음'})`
  }
  const task = action.id === null ? undefined : tasks.get(action.id)
  if (!task) return null
  if (action.kind === 'done') return `${task.title} — 완료로`
  return `${task.title} (지금 마감 ${task.due_date ?? '없음'}) — 마감을 ${action.due_date}로`
}

interface CardProps {
  rows: Row[]
  applying: boolean
  onApply: () => void
  onCancel: () => void
}

// 확인 카드. [적용]을 눌러야 기존 API로 바뀐다.
export function CommandCard({ rows, applying, onApply, onCancel }: CardProps) {
  return (
    <section className="briefing-card" aria-label="한 문장으로 시키기 확인">
      <h2>이렇게 바꿀까요? {rows.length}개</h2>
      <ul>
        {rows.map((r, i) => (
          <li key={i}>{r.text}</li>
        ))}
      </ul>
      <div className="form-actions">
        <button type="button" disabled={applying} onClick={onApply}>
          적용
        </button>
        <button type="button" disabled={applying} onClick={onCancel}>
          취소
        </button>
      </div>
    </section>
  )
}

interface Props {
  tasks: Task[]
  onUnauthorized: () => void
  onApplied: () => Promise<void>
}

// [오늘 브리핑] 아래, 보드 위에 놓는 입력란과 [시키기] 단추.
export default function CommandSection({ tasks, onUnauthorized, onApplied }: Props) {
  const [text, setText] = useState('')
  const { busy, applying, error, note, result, run, apply, cancel } = useCommand(
    onUnauthorized,
    onApplied,
  )

  function submit(e: FormEvent) {
    e.preventDefault()
    if (busy || applying || text.trim() === '') return
    run(text)
  }

  let ask = ''
  let rows: Row[] = []
  let failed = false
  if (result) {
    if (result.actions.length === 0) {
      ask = result.ask ?? ''
      failed = ask === ''
    } else {
      const byId = new Map(tasks.map((t) => [t.id, t]))
      rows = result.actions.flatMap((action) => {
        const line = describe(action, byId)
        return line === null ? [] : [{ action, text: line }]
      })
      // 보여 줄 줄이 하나도 없으면 알아듣지 못한 것으로 본다.
      failed = rows.length === 0
    }
  }

  return (
    <div className="briefing">
      <form className="new-task" style={{ width: '100%', margin: 0 }} onSubmit={submit}>
        <input
          aria-label="한 문장으로 시키기"
          placeholder="한 문장으로 시키기 (예: 장보기 끝냈고 내일까지 보고서 추가)"
          maxLength={MAX_LENGTH}
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <div className="form-actions">
          <button type="submit" disabled={busy || applying || text.trim() === ''}>
            {busy ? COMMAND_LOADING_TEXT : '시키기'}
          </button>
        </div>
      </form>
      {error && (
        <p className="suggest-note error" role="alert">
          {error}
        </p>
      )}
      {note && (
        <p className="suggest-note" role="status">
          {note}
        </p>
      )}
      {ask && (
        <p className="suggest-note" role="status">
          {ask}
        </p>
      )}
      {failed && (
        <p className="suggest-note error" role="alert">
          {COMMAND_FAILED_TEXT}
        </p>
      )}
      {rows.length > 0 && (
        <CommandCard
          rows={rows}
          applying={applying}
          onApply={() => apply(rows.map((r) => r.action))}
          onCancel={cancel}
        />
      )}
    </div>
  )
}
