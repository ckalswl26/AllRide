# 오라이 (ORAI) — 초보운전 레벨업 코치

초보운전자에게 **검증된 왕복 연습 루트**를 추천하고, 사용자가 미션처럼 하나씩 완주하며 레벨업하는 React 기반 앱·웹 프로토타입입니다. Django REST API와 React SPA를 연결했으며, 별도의 로그인 세션 없이 바로 체험할 수 있는 데모 사용자를 사용합니다.

## 구현된 핵심 기능

| 요구사항 | 구현 내용 |
|---|---|
| 컬러 시스템 | Green `#CDBC50`, Pink `#F34B5C`, Yellow `#F9B826`를 웹·앱 전반에 적용 |
| 오라이 캐릭터 | `api/static/api/orai_character.png`를 로딩, 사이드 프로필, 추천 빈 화면, 미션 완료 모달에 사용 |
| 루트 미리보기 | 카카오맵 SDK 동적 로드 + TMAP 자동차 경로 API + 저장된 경유지 fallback Polyline |
| 후기 노출 시점 | `주행 시작 → 주행 종료 → 후기 모달` 순서로만 접근 가능. 백엔드에서도 완료된 `drive_record_id`가 없으면 저장 거부 |
| 커뮤니티 | 운전 꿀팁, 주행 후기, 질문 글 등록 및 공감 버튼 구현 |
| 메인 지도 | 첫 화면 상단에 지도 배치. 앱 하단에는 `추천 / 미션 / 히스토리 / 커뮤니티` 4개 버블 내비게이션 배치 |
| 미션 레벨업 | 완주 기록, XP 획득, 누적 거리, 레벨 진행률, 완료 미션 표시 |
| 반응형 UI | 데스크톱 웹은 좌측 내비게이션, 모바일 앱은 하단 버블 내비게이션으로 자동 전환 |

## 실행 방법

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\\Scripts\\activate
python3 -m pip install -r requirements.txt
cp .env.example .env             # API 키를 입력하세요.
python3 manage.py migrate
python3 manage.py runserver
```

브라우저에서 아래 주소를 열면 됩니다.

- 웹 UI: `http://127.0.0.1:8000/`
- 모바일 앱 UI 미리보기: `http://127.0.0.1:8000/api/courses/recommend/app/`
- 지도 키 설정 확인: `http://127.0.0.1:8000/api/map-config/status/`

API 키가 없어도 앱은 실행됩니다. 카카오맵 키가 없으면 스타일링된 fallback 지도가 나타나고, TMAP 키가 없으면 저장된 경유지 연결선을 사용합니다.

## 프론트엔드 수정 후 빌드

React 소스는 `frontend/src/`에 있습니다. 수정 후 아래 명령으로 Django 정적 파일을 다시 빌드합니다.

```bash
cd frontend
npm install
npm run build -- --outDir ../api/static/api/orai-react --emptyOutDir
cd ..
```

빌드 결과물은 `api/static/api/orai-react/`에 포함되어 있으므로, UI를 수정하지 않는다면 `npm install` 없이도 Django 서버만 실행할 수 있습니다.

## 앱 사용 흐름

1. 첫 화면 지도에서 오라이존을 확인합니다.
2. 난이도, 집중 연습 목표, 연습 시간을 선택합니다.
3. 추천받은 코스의 `루트 미리보기`를 확인합니다.
4. `이 코스로 시작`을 누르면 주행 상태가 생성됩니다.
5. 안전한 곳에 정차한 뒤 `주행 종료`를 누르면 XP를 획득합니다.
6. 종료 직후 표시되는 후기 모달에서 좋아요 또는 어려웠어요를 남깁니다.
7. 미션, 히스토리, 커뮤니티 탭에서 성장 기록과 팁을 확인합니다.

## 주요 API

| Method | URL | 설명 |
|---|---|---|
| GET | `/api/app/bootstrap/` | React 앱 초기 데이터: 프로필, 오라이존, 미션, 히스토리, 커뮤니티 |
| POST | `/api/courses/recommend/` | 시간, 목표, 단계에 맞는 왕복 코스 추천 |
| GET | `/api/courses/<course_id>/preview/` | TMAP 또는 fallback 루트 미리보기 |
| POST | `/api/drives/start/` | 주행 상태 생성 |
| POST | `/api/drives/<drive_id>/finish/` | 주행 완료 및 XP 획득 |
| POST | `/api/drives/<drive_id>/cancel/` | 진행 중 주행 취소 |
| POST | `/api/courses/<course_id>/feedback/` | 종료된 주행 기록에만 후기 저장 |
| GET, POST | `/api/community/feed/` | 커뮤니티 목록 및 글 등록 |
| POST | `/api/community/posts/<post_id>/like/` | 게시글 공감 |

## 테스트

```bash
python3 manage.py test api
```

테스트는 초기 데이터 로드, 추천 및 미리보기, 주행 종료 전 후기 차단, 종료 후 XP 및 후기 저장, 커뮤니티 글 등록과 공감을 검증합니다.

## 보안 메모

`.env`는 `.gitignore`에 포함되어 있습니다. 실제 TMAP, 카카오, 공공데이터 API 키를 Git 저장소나 발표용 ZIP에 커밋하지 마세요. 배포 환경에서는 키를 환경 변수 또는 비밀 관리 서비스로 주입해야 합니다.

## 바로 열어보는 HTML 미리보기

서버 설치 전 UI를 먼저 확인하려면 `ORAI_STANDALONE_PREVIEW.html`을 더블클릭하세요. 이 파일은 캐릭터 이미지와 스타일을 내부에 포함한 단일 HTML 오프라인 데모이며, 추천·루트 미리보기·주행 시작·주행 종료·XP·미션·히스토리·커뮤니티 공감 흐름을 체험할 수 있습니다.

실제 카카오맵과 TMAP 경로는 보안을 위해 HTML 안에 API 키를 넣지 않았습니다. 실제 지도 연동은 `.env`에 API 키를 넣고 `./start_orai.sh` 또는 macOS의 `start_orai.command`를 실행한 뒤 `http://127.0.0.1:8000/`에서 확인하세요.

---

## 2026-06 UI V2 업데이트

- `루트 미리보기` 모달을 화면 최상단 fixed overlay로 교체해 모바일과 데스크톱에서 항상 표시되도록 수정했습니다.
- 실제 React 화면에서도 `/api/courses/<course_id>/preview/`를 호출하고, TMAP 응답 실패 시 검증 경유지 기반 fallback 경로를 모달에 표시합니다.
- 모바일 앱 스타일을 기준으로 지도, 검색 카드, 레벨 카드, 필터 시트, 추천 카드, 버블 하단 내비게이션을 전면 개편했습니다.
- 단일 HTML 체험 파일은 `ORAI_STANDALONE_PREVIEW.html`입니다. 다운로드 후 더블클릭하면 설치 없이 열립니다.
- 대규모 서비스 전환 기준은 `docs/PRODUCTION_ARCHITECTURE_10M.md`를 참고하세요.
- 로컬 인프라 샘플은 `infra/docker-compose.dev.yml`, 프록시 샘플은 `infra/nginx.conf`에 있습니다.

### 운영 점검 API

```text
GET /api/health/live/
GET /api/health/ready/
GET /api/system/capabilities/
```

## 2026-06 UI V3 — 주행 내비게이션 화면

`이 코스로 시작` 또는 미리보기 모달의 `이 코스로 연습 시작하기` 버튼을 누르면 일반 추천 화면에 머무르지 않고 전체 화면 내비게이션으로 전환됩니다.

- 카카오맵 SDK 위에 TMAP 자동차 길찾기 결과 Polyline을 표시합니다.
- TMAP 응답의 Point 안내 데이터를 해석해 다음 회전 및 직진 안내 카드를 표시합니다.
- GPS 권한이 허용된 브라우저에서는 현재 좌표와 가장 가까운 경로 인덱스를 기준으로 진행률을 계산합니다.
- GPS를 받을 수 없는 발표 환경에서는 데모 진행 모드로 자동 전환됩니다.
- 남은 거리, 예상 도착 시간, 진행률, 현재 속도, 제한 속도, 안전 안내, 주행 종료 버튼을 제공합니다.
- TMAP 호출 실패 시에도 저장된 검증 경유지와 기본 안전 안내로 화면이 유지됩니다.

### API 키 입력

프로젝트 루트에서 `.env.example`을 복사해 `.env`를 만든 뒤 실제 값을 입력합니다.

```bash
cp .env.example .env
```

```env
TMAP_API_KEY=발급받은_TMAP_앱키
KAKAO_JS_KEY=발급받은_카카오_JavaScript키
KAKAO_REST_API_KEY=발급받은_카카오_REST_API키
```

카카오 지도 JavaScript SDK를 로컬에서 확인하려면 카카오 개발자 콘솔의 JavaScript SDK 도메인에 아래 주소를 등록합니다.

```text
http://127.0.0.1:8000
http://localhost:8000
```

키 자체는 브라우저에 별도로 표시하지 않으며, 설정 여부만 `/api/map-config/status/`에서 확인할 수 있습니다.
