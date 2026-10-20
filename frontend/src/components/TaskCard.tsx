import { STATUS_LABEL, type Task } from '../types'

interface Props {
  task: Task
}

export default function TaskCard({ task }: Props) {
  return (
    <li className="card">
      <h3>{task.title}</h3>
      {task.description && <p className="card-desc">{task.description}</p>}
      <span className={`badge badge-${task.status}`}>
        {STATUS_LABEL[task.status]}
      </span>
    </li>
  )
}
