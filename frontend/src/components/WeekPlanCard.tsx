import { useWeekPlan } from '../useWeekPlan'
import {
  WEEKPLAN_EMPTY_TEXT,
  WEEKPLAN_FAILED_TEXT,
  WEEKPLAN_LOADING_TEXT,
} from '../messages'
import type { Task, WeekPlan } from '../types'

const WEEKDAYS = ['일', '월', '화', '수', '목', '금', '토']

// 「10-29 (목)」. 날짜를 읽을 수 없으면 받은 글을 그대로 쓴다.
function dayLabel(date: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(date)
  if (!m) return date
  const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]))
  if (Number.isNaN(d.getTime())) return date
  return `${m[2]}-${m[3]} (${WEEKDAYS[d.getDay()]})`
}

interface TableProps {
  plan: WeekPlan
  tasks: Task[]
  onClose: () => void
}

// 이번 주 계획 표. 제목은 id로 지금 목록에서 찾고, 목록에 없는 id는 그 줄에서만 뺀다.
// 보여 줄 줄이 하나도 없으면 null이다. 부르는 쪽이 실패 문구를 보여 준다.
export function WeekPlanTable({ plan, tasks, onClose }: TableProps) {
  const titles = new Map(tasks.map((t) => [t.id, t.title]))
  const rows = plan.days
    .map((d) => ({ date: d.date, names: d.ids.flatMap((id) => titles.get(id) ?? []) }))
    .filter((r) => r.names.length > 0)
  if (rows.length === 0) return null
  return (
    <section className="weekplan-card" aria-label="이번 주 계획">
      <h2>이번 주 계획</h2>
      <table>
        <tbody>
          {rows.map((r) => (
            <tr key={r.date}>
              <th scope="row">{dayLabel(r.date)}</th>
              <td>{r.names.join(' · ')}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="weekplan-note">{plan.note}</p>
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

// [오늘 브리핑] 아래에 놓는 [이번 주 계획] 버튼과 결과.
export default function WeekPlanSection({ tasks, onUnauthorized }: Props) {
  const { busy, error, result, run, close } = useWeekPlan(onUnauthorized)

  let note = ''
  let isError = false
  let card = null
  if (result) {
    if (result.days.length === 0) {
      note = WEEKPLAN_EMPTY_TEXT
    } else {
      card = <WeekPlanTable plan={result} tasks={tasks} onClose={close} />
      // 보여 줄 줄을 하나도 못 만들면 받지 못한 것으로 본다.
      const known = new Set(tasks.map((t) => t.id))
      if (!result.days.some((d) => d.ids.some((id) => known.has(id)))) {
        card = null
        note = WEEKPLAN_FAILED_TEXT
        isError = true
      }
    }
  }

  return (
    <div className="weekplan">
      <button type="button" disabled={busy} onClick={run}>
        {busy ? WEEKPLAN_LOADING_TEXT : '이번 주 계획'}
      </button>
      {error && (
        <p className="suggest-note error" role="alert">
          {error}
        </p>
      )}
      {note && (
        <p
          className={`suggest-note${isError ? ' error' : ''}`}
          role={isError ? 'alert' : 'status'}
        >
          {note}
        </p>
      )}
      {card}
    </div>
  )
}
