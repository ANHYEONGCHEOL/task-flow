import {
  PLAN_LOADING_TEXT,
  PLAN_NEED_DUE_TEXT,
  PLAN_PREVIEW_TEXT,
} from '../messages'
import { PRIORITY_LABEL, type PlanItem } from '../types'

interface ButtonProps {
  busy: boolean
  disabled: boolean
  onClick: () => void
}

// 요청 중에는 잠긴다. 제목과 마감일이 없으면 서버가 거절하므로 미리 잠근다.
export function PlanButton({ busy, disabled, onClick }: ButtonProps) {
  return (
    <button type="button" disabled={busy || disabled} onClick={onClick}>
      AI로 할일 만들기
    </button>
  )
}

interface NoteProps {
  busy: boolean
  error: string
  needDue: boolean
}

// 만드는 중 · 실패 · 마감일 안내를 한 줄로 보여 준다.
export function PlanNote({ busy, error, needDue }: NoteProps) {
  if (busy) {
    return (
      <p className="suggest-note" role="status">
        {PLAN_LOADING_TEXT}
      </p>
    )
  }
  if (error) {
    return (
      <p className="suggest-note error" role="alert">
        {error}
      </p>
    )
  }
  if (needDue) {
    return <p className="suggest-note">{PLAN_NEED_DUE_TEXT}</p>
  }
  return null
}

interface PreviewProps {
  items: PlanItem[]
  saving: boolean
  onSave: () => void
  onCancel: () => void
}

// 저장 전 미리보기. [모두 등록]을 눌러야 5개가 한꺼번에 저장된다.
export function PlanPreview({ items, saving, onSave, onCancel }: PreviewProps) {
  if (items.length === 0) return null
  return (
    <section className="plan-preview" aria-label="AI 할일 미리보기">
      <p className="suggest-note">{PLAN_PREVIEW_TEXT}</p>
      <ol>
        {items.map((item, i) => (
          <li key={i}>
            <span className="plan-date">{item.due_date}</span>
            <span className={`priority priority-${item.priority.toLowerCase()}`}>
              {PRIORITY_LABEL[item.priority]}
            </span>
            <span className="plan-title">{item.title}</span>
          </li>
        ))}
      </ol>
      <div className="form-actions">
        <button type="button" disabled={saving} onClick={onSave}>
          모두 등록
        </button>
        <button type="button" disabled={saving} onClick={onCancel}>
          취소
        </button>
      </div>
    </section>
  )
}
