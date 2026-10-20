import { STATUSES, STATUS_LABEL, type Task } from '../types'
import TaskCard from './TaskCard'

interface Props {
  tasks: Task[]
}

// 카드를 상태별 열로 나누어 보여 준다. 각 카드는 자기 상태의 열에만 나온다. (R-004)
export default function Board({ tasks }: Props) {
  return (
    <div className="board">
      {STATUSES.map((status) => {
        const column = tasks.filter((t) => t.status === status)
        return (
          <section className="column" key={status} aria-label={STATUS_LABEL[status]}>
            <h2>
              {STATUS_LABEL[status]} <small>{column.length}</small>
            </h2>
            <ul>
              {column.map((t) => (
                <TaskCard key={t.id} task={t} />
              ))}
            </ul>
          </section>
        )
      })}
    </div>
  )
}
