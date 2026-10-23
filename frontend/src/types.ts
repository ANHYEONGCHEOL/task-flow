export type Status = 'TODO' | 'IN_PROGRESS' | 'DONE'

// 응답에는 id와 email만 있다. 비밀번호와 해시는 오지 않는다.
export interface User {
  id: number
  email: string
}

export interface Task {
  id: number
  title: string
  description: string
  status: Status
}

export const STATUSES: Status[] = ['TODO', 'IN_PROGRESS', 'DONE']

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
