import { useEffect, useRef, useState } from 'react'
import { ApiError, suggestTask } from './api'
import { SUGGEST_FAILED_TEXT, SUGGEST_OFF_TEXT } from './messages'
import type { Suggestion } from './types'

// AI 제안을 받아 onApply로 입력 칸에 채운다. 저장은 하지 않는다.
// 요청 중에는 제안 버튼만 잠그고, 등록 · 저장 버튼에는 영향을 주지 않는다.
export function useSuggest(
  onApply: (s: Suggestion) => void,
  onUnauthorized: () => void,
) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [reason, setReason] = useState('')
  // 가장 최근 요청만 인정한다. 등록 · 취소로 화면이 바뀐 뒤 늦게 온 답은 버린다.
  const latest = useRef(0)

  useEffect(() => {
    return () => {
      latest.current += 1
    }
  }, [])

  async function run(input: { title: string; description: string }) {
    const id = ++latest.current
    setBusy(true)
    setError('')
    setReason('')
    try {
      const suggestion = await suggestTask(input)
      if (id !== latest.current) return
      onApply(suggestion)
      setReason(suggestion.reason)
    } catch (e) {
      if (id !== latest.current) return
      if (e instanceof ApiError && e.status === 401) {
        onUnauthorized()
        return
      }
      setError(
        e instanceof ApiError && e.status === 503
          ? SUGGEST_OFF_TEXT
          : SUGGEST_FAILED_TEXT,
      )
    } finally {
      if (id === latest.current) setBusy(false)
    }
  }

  function reset() {
    latest.current += 1
    setBusy(false)
    setError('')
    setReason('')
  }

  return { busy, error, reason, run, reset }
}
