import { STATUSES, STATUS_LABEL, type Status, type Task } from '../types'

interface Props {
  task: Task
  onChangeStatus: (id: number, status: Status) => void
}

export default function TaskCard({ task, onChangeStatus }: Props) {
  return (
    <li className="card">
      <h3>{task.title}</h3>
      {task.description && <p className="card-desc">{task.description}</p>}
      <span className={`badge badge-${task.status}`}>
        {STATUS_LABEL[task.status]}
      </span>
      {/* 사용자가 고른 뒤에만 요청한다. (R-003) */}
      <select
        aria-label={`${task.title} 상태 변경`}
        value={task.status}
        onChange={(e) => onChangeStatus(task.id, e.target.value as Status)}
      >
        {STATUSES.map((s) => (
          <option key={s} value={s}>
            {STATUS_LABEL[s]}
          </option>
        ))}
      </select>
    </li>
  )
}
