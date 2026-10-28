import { useEffect, useRef, useState } from 'react'
import { ApiError, planTasks } from './api'
import {
  PLAN_FAILED_TEXT,
  PLAN_OFF_TEXT,
  PLAN_PAST_DUE_TEXT,
} from './messages'
import type { PlanItem } from './types'

// AI로 할일 5개의 미리보기를 받는다. 저장은 하지 않는다.
// 요청 중에는 이 버튼만 잠그고, 등록 · AI 제안 버튼에는 영향을 주지 않는다.
export function usePlan(onUnauthorized: () => void) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [items, setItems] = useState<PlanItem[]>([])
  // 가장 최근 요청만 인정한다. 취소 · 등록으로 화면이 바뀐 뒤 늦게 온 답은 버린다.
  const latest = useRef(0)

  useEffect(() => {
    return () => {
      latest.current += 1
    }
  }, [])

  async function run(input: {
    title: string
    description: string
    due_date: string
  }) {
    const id = ++latest.current
    setBusy(true)
    setError('')
    setItems([])
    try {
      const planned = await planTasks(input)
      if (id !== latest.current) return
      setItems(planned)
    } catch (e) {
      if (id !== latest.current) return
      if (e instanceof ApiError && e.status === 401) {
        onUnauthorized()
        return
      }
      if (e instanceof ApiError && e.status === 422) {
        setError(PLAN_PAST_DUE_TEXT)
      } else if (e instanceof ApiError && e.status === 503) {
        setError(PLAN_OFF_TEXT)
      } else {
        setError(PLAN_FAILED_TEXT)
      }
    } finally {
      if (id === latest.current) setBusy(false)
    }
  }

  function reset() {
    latest.current += 1
    setBusy(false)
    setError('')
    setItems([])
  }

  return { busy, error, items, run, reset }
}
