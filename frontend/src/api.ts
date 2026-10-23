import type { Status, Task } from './types'

// 화면은 /api 로만 API를 부른다. (vite.config.ts 프록시)
const BASE = '/api'

// 실패한 응답의 상태 코드를 화면이 알 수 있게 담는다. (404 = 카드가 이미 없음)
export class ApiError extends Error {
  status: number

  constructor(status: number) {
    super(`요청 실패 (${status})`)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json' },
  })
  if (!res.ok) {
    throw new ApiError(res.status)
  }
  if (res.status === 204) {
    return undefined as T
  }
  return (await res.json()) as T
}

export function listTasks(): Promise<Task[]> {
  return request<Task[]>('/tasks')
}

export function createTask(input: {
  title: string
  description: string
}): Promise<Task> {
  return request<Task>('/tasks', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export function changeStatus(id: number, status: Status): Promise<Task> {
  return request<Task>(`/tasks/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  })
}

export function updateTask(
  id: number,
  input: { title: string; description: string },
): Promise<Task> {
  return request<Task>(`/tasks/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  })
}

export function deleteTask(id: number): Promise<void> {
  return request<void>(`/tasks/${id}`, { method: 'DELETE' })
}
