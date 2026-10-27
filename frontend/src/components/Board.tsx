import {
  STATUSES,
  STATUS_LABEL,
  type Status,
  type Task,
  type TaskInput,
} from '../types'
import TaskCard from './TaskCard'

interface Props {
  tasks: Task[]
  onChangeStatus: (id: number, status: Status) => void
  onUpdate: (id: number, input: TaskInput) => Promise<void>
  onDelete: (id: number) => void
}

// 카드를 상태별 열로 나누어 보여 준다. 각 카드는 자기 상태의 열에만 나온다. (R-004)
// 순서는 서버가 정렬해서 준 그대로 두고 화면에서 다시 정렬하지 않는다. (R-012, BR-04)
export default function Board({
  tasks,
  onChangeStatus,
  onUpdate,
  onDelete,
}: Props) {
  return (
    <div className="board">
      {STATUSES.map((status) => {
        const column = tasks.filter((t) => t.status === status)
        return (
          <section className="column" key={status} aria-label={STATUS_LABEL[status]}>
            <h2>{STATUS_LABEL[status]}</h2>
            <ul>
              {column.map((t) => (
                <TaskCard
                  key={t.id}
                  task={t}
                  onChangeStatus={onChangeStatus}
                  onUpdate={onUpdate}
                  onDelete={onDelete}
                />
              ))}
            </ul>
          </section>
        )
      })}
    </div>
  )
}
