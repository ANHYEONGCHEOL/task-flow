// 화면 상태 문구는 SCREEN-SPEC.md의 사용자 지정 문구 그대로다.
export const LOADING_TEXT = '로딩중'
export const EMPTY_TEXT = '결과값을 찾아오지 못하였습니다.'
export const FAILURE_TEXT = '사용자의 권한이 없습니다'

// AI 제안 문구 (503 = AI를 쓸 수 없음, 그 밖의 실패 = 제안을 못 받음)
export const SUGGEST_LOADING_TEXT = '제안을 받는 중...'
export const SUGGEST_OFF_TEXT =
  '지금은 AI 제안을 쓸 수 없습니다. 직접 입력해 주세요.'
export const SUGGEST_FAILED_TEXT =
  '제안을 못 받았습니다. 다시 제안 버튼을 눌러 보세요.'

// AI로 할일 만들기 문구 (구현에서 정한 것이다)
export const PLAN_LOADING_TEXT = '할일을 만드는 중...'
export const PLAN_NEED_DUE_TEXT =
  '마감일을 입력하면 AI가 마감일까지의 일정을 짜 줍니다.'
export const PLAN_PAST_DUE_TEXT = '마감일은 오늘이거나 오늘 이후여야 합니다.'
export const PLAN_OFF_TEXT =
  '지금은 AI 할일 만들기를 쓸 수 없습니다. 직접 입력해 주세요.'
export const PLAN_FAILED_TEXT =
  '할일을 만들지 못했습니다. 버튼을 다시 눌러 보세요.'
export const PLAN_PREVIEW_TEXT =
  '미리보기입니다. [모두 등록]을 눌러야 저장됩니다.'

// 오늘 브리핑 문구 (503 = AI를 쓸 수 없음, 그 밖의 실패 = 받지 못함)
export const BRIEFING_LOADING_TEXT = '만드는 중…'
export const BRIEFING_OFF_TEXT = '지금은 브리핑을 쓸 수 없습니다'
export const BRIEFING_FAILED_TEXT = '브리핑을 받지 못했습니다'
export const BRIEFING_EMPTY_TEXT = '오늘은 비어 있어요'

// 로그인 · 가입 화면 문구 (문서에 정해진 문구가 없어 구현에서 정한 것이다)
export const LOGIN_FAILED_TEXT = '이메일이나 비밀번호가 맞지 않습니다.'
export const EMAIL_TAKEN_TEXT = '이미 쓰고 있는 이메일입니다.'
export const INVALID_INPUT_TEXT =
  '이메일 형식과 비밀번호(8자 이상 128자 이하)를 확인해 주세요.'
export const EMPTY_INPUT_TEXT = '이메일과 비밀번호를 입력해 주세요.'
export const SESSION_ENDED_TEXT = '로그인이 끝났습니다. 다시 로그인해 주세요.'
