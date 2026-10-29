import { useEffect, useRef, useState } from 'react'
import { ApiError, getWeekPlan } from './api'
import { WEEKPLAN_FAILED_TEXT, WEEKPLAN_OFF_TEXT } from './messages'
import type { WeekPlan } from './types'

// 이번 주 계획을 받는다. 저장은 하지 않는다.
// 요청 중에는 이 버튼만 잠그고, 다른 버튼에는 영향을 주지 않는다.
export function useWeekPlan(onUnauthorized: () => void) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<WeekPlan | null>(null)
  // 가장 최근 요청만 인정한다. 닫은 뒤 늦게 온 답은 버린다.
  const latest = useRef(0)

  useEffect(() => {
    return () => {
      latest.current += 1
    }
  }, [])

  async function run() {
    const id = ++latest.current
    setBusy(true)
    setError('')
    setResult(null)
    try {
      const plan = await getWeekPlan()
      if (id !== latest.current) return
      setResult(plan)
    } catch (e) {
      if (id !== latest.current) return
      if (e instanceof ApiError && e.status === 401) {
        onUnauthorized()
        return
      }
      if (e instanceof ApiError && e.status === 503) {
        setError(WEEKPLAN_OFF_TEXT)
      } else {
        setError(WEEKPLAN_FAILED_TEXT)
      }
    } finally {
      if (id === latest.current) setBusy(false)
    }
  }

  // 표를 닫는다. 받는 중이면 그 답도 버린다.
  function close() {
    latest.current += 1
    setBusy(false)
    setError('')
    setResult(null)
  }

  return { busy, error, result, run, close }
}
