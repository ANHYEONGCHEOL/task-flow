import type {
  PlanItem,
  Status,
  Suggestion,
  Task,
  TaskInput,
  User,
} from './types'

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

export function createTask(input: TaskInput): Promise<Task> {
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

export function updateTask(id: number, input: TaskInput): Promise<Task> {
  return request<Task>(`/tasks/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  })
}

// 제안만 받는다. 서버는 DB를 바꾸지 않는다.
export function suggestTask(input: {
  title: string
  description: string
}): Promise<Suggestion> {
  return request<Suggestion>('/tasks/suggest', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

// 주제 하나를 할일 5개로 나눈 미리보기만 받는다. 서버는 DB를 바꾸지 않는다.
export async function planTasks(input: {
  title: string
  description: string
  due_date: string
}): Promise<PlanItem[]> {
  const plan = await request<{ items: PlanItem[] }>('/tasks/plan', {
    method: 'POST',
    body: JSON.stringify(input),
  })
  return plan.items
}

// 미리본 할일을 한꺼번에 저장한다. 서버가 전부 저장하거나 하나도 저장하지 않는다.
export function createTasksBulk(items: TaskInput[]): Promise<Task[]> {
  return request<Task[]>('/tasks/bulk', {
    method: 'POST',
    body: JSON.stringify({ items }),
  })
}

export function deleteTask(id: number): Promise<void> {
  return request<void>(`/tasks/${id}`, { method: 'DELETE' })
}

export function getMe(): Promise<User> {
  return request<User>('/auth/me')
}

export function registerUser(email: string, password: string): Promise<User> {
  return request<User>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function loginUser(email: string, password: string): Promise<User> {
  return request<User>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function logoutUser(): Promise<void> {
  return request<void>('/auth/logout', { method: 'POST' })
}
