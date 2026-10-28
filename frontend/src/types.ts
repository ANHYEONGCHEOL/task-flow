export type Status = 'TODO' | 'IN_PROGRESS' | 'DONE'

// 응답에는 id와 email만 있다. 비밀번호와 해시는 오지 않는다.
export interface User {
  id: number
  email: string
}

export type Priority = 'LOW' | 'NORMAL' | 'HIGH'

export interface Task {
  id: number
  title: string
  description: string
  status: Status
  priority: Priority
  due_date: string | null // YYYY-MM-DD. 없으면 null
  is_overdue: boolean // 서버가 계산한다. 화면은 다시 계산하지 않는다. (BR-03)
}

// 생성과 수정에 보내는 값. 마감일을 비우면 null이다.
export interface TaskInput {
  title: string
  description: string
  priority: Priority
  due_date: string | null
}

// AI가 제안한 값. 저장되지 않고, 사용자가 저장 버튼을 눌러야 Task에 들어간다.
export interface Suggestion {
  priority: Priority
  due_date: string | null
  reason: string
}

// AI가 만든 할일 하나. 미리보기에만 있고, [모두 등록]을 눌러야 Task로 저장된다.
export interface PlanItem {
  title: string
  priority: Priority
  due_date: string
}

export const STATUSES: Status[] = ['TODO', 'IN_PROGRESS', 'DONE']

export const PRIORITIES: Priority[] = ['HIGH', 'NORMAL', 'LOW']

export const PRIORITY_LABEL: Record<Priority, string> = {
  HIGH: '높음',
  NORMAL: '보통',
  LOW: '낮음',
}

// 저장값 → 화면 표시 (DATA-MODEL.md)
export const STATUS_LABEL: Record<Status, string> = {
  TODO: '할 일',
  IN_PROGRESS: '진행 중',
  DONE: '완료',
}

// 제목 규칙은 API와 같다. 공백만 있는 제목은 빈 제목이다. (D-012)
export function isTitleEmpty(title: string): boolean {
  return title.trim() === ''
}
