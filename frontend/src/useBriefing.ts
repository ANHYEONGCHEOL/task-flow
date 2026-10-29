import { useEffect, useRef, useState } from 'react'
import { ApiError, getBriefing } from './api'
import { BRIEFING_FAILED_TEXT, BRIEFING_OFF_TEXT } from './messages'
import type { Briefing } from './types'

// 오늘 브리핑을 받는다. 저장은 하지 않는다.
// 요청 중에는 이 버튼만 잠그고, 등록 · 다른 AI 버튼에는 영향을 주지 않는다.
export function useBriefing(onUnauthorized: () => void) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<Briefing | null>(null)
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
      const briefing = await getBriefing()
      if (id !== latest.current) return
      setResult(briefing)
    } catch (e) {
      if (id !== latest.current) return
      if (e instanceof ApiError && e.status === 401) {
        onUnauthorized()
        return
      }
      if (e instanceof ApiError && e.status === 503) {
        setError(BRIEFING_OFF_TEXT)
      } else {
        setError(BRIEFING_FAILED_TEXT)
      }
    } finally {
      if (id === latest.current) setBusy(false)
    }
  }

  // 카드를 닫는다. 받는 중이면 그 답도 버린다.
  function close() {
    latest.current += 1
    setBusy(false)
    setError('')
    setResult(null)
  }

  return { busy, error, result, run, close }
}
