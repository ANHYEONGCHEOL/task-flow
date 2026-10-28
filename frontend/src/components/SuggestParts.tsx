import { SUGGEST_LOADING_TEXT } from '../messages'

interface ButtonProps {
  busy: boolean
  disabled: boolean
  onClick: () => void
}

// 요청 중에는 잠긴다. 제목이 비어 있으면 서버가 거절하므로 미리 잠근다.
export function SuggestButton({ busy, disabled, onClick }: ButtonProps) {
  return (
    <button type="button" disabled={busy || disabled} onClick={onClick}>
      AI 제안
    </button>
  )
}

interface NoteProps {
  busy: boolean
  error: string
  reason: string
}

// 받는 중 · 실패 · 제안 이유를 한 줄로 보여 준다.
export function SuggestNote({ busy, error, reason }: NoteProps) {
  if (busy) {
    return (
      <p className="suggest-note" role="status">
        {SUGGEST_LOADING_TEXT}
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
  if (reason) {
    return <p className="suggest-note">AI 제안: {reason}</p>
  }
  return null
}
