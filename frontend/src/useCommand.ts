import { useEffect, useRef, useState } from 'react'
import {
  ApiError,
  changeDueDate,
  changeStatus,
  CommandError,
  createTask,
  postCommand,
} from './api'
import type { Command, CommandAction } from './types'

// 한 문장으로 시키기 문구
export const COMMAND_LOADING_TEXT = '알아듣는 중…'
export const COMMAND_OFF_TEXT = '지금은 시킬 수 없습니다'
export const COMMAND_FAILED_TEXT = '알아듣지 못했습니다'
export const COMMAND_CHECK_TEXT = '입력을 확인해 주세요.'

// 확인한 제안 하나를 기존 API로 한 번 적용한다.
async function applyOne(a: CommandAction) {
  if (a.kind === 'add') {
    await createTask({
      title: a.title ?? '',
      description: '',
      priority: a.priority ?? 'NORMAL',
      due_date: a.due_date,
    })
  } else if (a.kind === 'due' && a.id !== null && a.due_date) {
    await changeDueDate(a.id, a.due_date)
  } else if (a.kind === 'done' && a.id !== null) {
    await changeStatus(a.id, 'DONE')
  }
}

// 한 문장을 제안으로 바꿔 받고, 사용자가 확인하면 기존 API로 적용한다.
// 요청 중에는 이 단추만 잠그고, 다른 버튼에는 영향을 주지 않는다.
export function useCommand(
  onUnauthorized: () => void,
  onApplied: () => Promise<void>,
) {
  const [busy, setBusy] = useState(false)
  const [applying, setApplying] = useState(false)
  const [error, setError] = useState('')
  const [note, setNote] = useState('')
  const [result, setResult] = useState<Command | null>(null)
  // 가장 최근 요청만 인정한다. 취소한 뒤 늦게 온 답은 버린다.
  const latest = useRef(0)

  useEffect(() => {
    return () => {
      latest.current += 1
    }
  }, [])

  async function run(text: string) {
    const id = ++latest.current
    setBusy(true)
    setError('')
    setNote('')
    setResult(null)
    try {
      const command = await postCommand(text)
      if (id !== latest.current) return
      setResult(command)
    } catch (e) {
      if (id !== latest.current) return
      if (e instanceof ApiError && e.status === 401) {
        onUnauthorized()
        return
      }
      if (e instanceof CommandError && e.status === 422) {
        setError(e.detail || COMMAND_CHECK_TEXT)
      } else if (e instanceof ApiError && e.status === 503) {
        setError(COMMAND_OFF_TEXT)
      } else {
        setError(COMMAND_FAILED_TEXT)
      }
    } finally {
      if (id === latest.current) setBusy(false)
    }
  }

  // 줄마다 기존 API를 차례로 한 번씩 부르고, 끝나면 목록을 한 번 다시 받는다.
  // 일부가 실패해도 나머지는 계속하고, 못 한 것만 카드에 남긴다.
  async function apply(actions: CommandAction[]) {
    if (applying) return
    const id = ++latest.current
    setApplying(true)
    setError('')
    const failed: CommandAction[] = []
    try {
      for (const action of actions) {
        try {
          await applyOne(action)
        } catch (e) {
          if (e instanceof ApiError && e.status === 401) {
            onUnauthorized()
            return
          }
          failed.push(action)
        }
      }
      await onApplied()
    } finally {
      if (id === latest.current) setApplying(false)
    }
    if (id !== latest.current) return
    if (failed.length === 0) {
      setResult(null)
      setNote(`${actions.length}개를 바꿨습니다.`)
    } else {
      setResult({ actions: failed, ask: null })
      setNote(`${actions.length}개 중 ${actions.length - failed.length}개만 바꿨습니다.`)
    }
  }

  // 카드를 닫는다. 받는 중이면 그 답도 버린다.
  function cancel() {
    latest.current += 1
    setBusy(false)
    setApplying(false)
    setError('')
    setNote('')
    setResult(null)
  }

  return { busy, applying, error, note, result, run, apply, cancel }
}
