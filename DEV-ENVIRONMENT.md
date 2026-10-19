# 개발 환경

확인 날짜: 2026-10-19

## 운영체제 · 셸

| 항목 | 값 |
|---|---|
| 운영체제 | Microsoft Windows 11 Pro, 10.0.22631, 64비트 |
| 셸 | PowerShell 7.6.7 (보조: Git Bash) |

## 도구별 버전

`--version` 실행 결과를 그대로 적었다.

| 도구 | 명령 | 결과 |
|---|---|---|
| git | `git --version` | `git version 2.56.0.windows.2` |
| node | `node --version` | `v24.22.0` (2026-10-19 설치) |
| npm | `npm --version` | `11.19.1` |
| uv | `uv --version` | `uv 0.13.1 (62faed335 2026-10-13 x86_64-pc-windows-msvc)` |
| python | `python --version` | `Python` (종료 코드 9009). 실제 버전이 나오지 않는다. |
| python (uv 설치본) | `C:\Users\EZ\.local\bin\python3.12.exe --version` | `Python 3.12.15` |

### 참고

- `python`, `python3` 명령은 `C:\Users\EZ\AppData\Local\Microsoft\WindowsApps\` 의 Windows 앱 실행 별칭이다. 버전을 출력하지 않아 실제 Python이 아닌 것으로 보인다.
- 쓸 수 있는 Python은 uv가 설치한 3.12.15다. API는 uv로 실행한다.

## 새로 설치한 것

- Node.js LTS v24.22.0 (Krypton). `winget install`이 접근 위반(코드 -1073741819)으로 종료되어, nodejs.org의 `node-v24.22.0-win-x64.zip`을 받아 SHA256을 `SHASUMS256.txt`와 대조한 뒤 `%LOCALAPPDATA%\Programs\nodejs`에 풀었다. 사용자 PATH에 이 폴더를 추가했다. 관리자 권한은 쓰지 않았다.
- 새 터미널을 열어야 `node`, `npm`이 PATH에서 잡힌다.
