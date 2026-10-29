import { useBriefing } from '../useBriefing'
import {
  BRIEFING_EMPTY_TEXT,
  BRIEFING_FAILED_TEXT,
  BRIEFING_LOADING_TEXT,
} from '../messages'
import type { Briefing, Task } from '../types'

interface CardProps {
  briefing: Briefing
  tasks: Task[]
  onClose: () => void
}

// 오늘 브리핑 카드. 제목은 id로 지금 목록에서 찾고, 목록에 없는 id는 그 줄만 뺀다.
// 먼저 할 일이 하나도 남지 않으면 null이다. 부르는 쪽이 실패 문구를 보여 준다.
export function BriefingCard({ briefing, tasks, onClose }: CardProps) {
  const titles = new Map(tasks.map((t) => [t.id, t.title]))
  const top = briefing.top3.filter((p) => titles.has(p.id))
  const later = briefing.later.filter((id) => titles.has(id))
  if (top.length === 0) return null
  return (
    <section className="briefing-card" aria-label="오늘 브리핑">
      <h2>먼저 할 일</h2>
      <ol>
        {top.map((p) => (
          <li key={p.id}>
            <span className="briefing-title">{titles.get(p.id)}</span>
            <span className="briefing-reason"> — {p.reason}</span>
          </li>
        ))}
      </ol>
      {later.length > 0 && (
        <>
          <h2>미뤄도 되는 일</h2>
          <ul>
            {later.map((id) => (
              <li key={id}>{titles.get(id)}</li>
            ))}
          </ul>
        </>
      )}
      <p className="briefing-cheer">{briefing.cheer}</p>
      <div className="form-actions">
        <button type="button" onClick={onClose}>
          닫기
        </button>
      </div>
    </section>
  )
}

interface Props {
  tasks: Task[]
  onUnauthorized: () => void
}

// 등록 폼 아래, 보드 위에 놓는 [오늘 브리핑] 버튼과 결과.
export default function BriefingSection({ tasks, onUnauthorized }: Props) {
  const { busy, error, result, run, close } = useBriefing(onUnauthorized)

  let note = ''
  let card = null
  if (result) {
    if (result.top3.length === 0) {
      note = BRIEFING_EMPTY_TEXT
    } else {
      card = <BriefingCard briefing={result} tasks={tasks} onClose={close} />
      // 먼저 할 일을 목록에서 하나도 못 찾으면 받지 못한 것으로 본다.
      if (!result.top3.some((p) => tasks.some((t) => t.id === p.id))) {
        card = null
        note = BRIEFING_FAILED_TEXT
      }
    }
  }

  return (
    <div className="briefing">
      <button type="button" disabled={busy} onClick={run}>
        {busy ? BRIEFING_LOADING_TEXT : '오늘 브리핑'}
      </button>
      {error && (
        <p className="suggest-note error" role="alert">
          {error}
        </p>
      )}
      {note && (
        <p
          className={`suggest-note${note === BRIEFING_FAILED_TEXT ? ' error' : ''}`}
          role={note === BRIEFING_FAILED_TEXT ? 'alert' : 'status'}
        >
          {note}
        </p>
      )}
      {card}
    </div>
  )
}
