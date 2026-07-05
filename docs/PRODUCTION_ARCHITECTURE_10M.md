# 오라이 — 1,000만 사용자 대응 운영 아키텍처 제안

이 저장소는 로컬 실행과 기능 검증이 가능한 React + Django MVP입니다. 단일 서버를 그대로 1,000만 명에게 제공하는 것은 불가능합니다. 아래 구조는 실제 서비스 전환을 위한 배포 기준입니다.

## 1. 목표와 전제

- 누적 가입자 1,000만 명, 일간 활성 사용자 100만 명, 출퇴근 시간대 집중 트래픽을 가정합니다.
- 지도 키는 브라우저에 허용된 JavaScript 키만 전달하고, TMAP REST 키와 공공데이터 키는 서버 비밀 저장소에서만 관리합니다.
- 서버 세션에 의존하지 않습니다. 사용자 인증 도입 시 짧은 수명의 Access Token과 회전 가능한 Refresh Token을 사용합니다.
- 추천 결과와 경로 미리보기는 서로 다른 수명으로 캐시합니다. 실시간 교통이 필요한 호출과 정적 검증 코스 조회를 분리합니다.

## 2. 권장 구성

```text
Mobile Web / React App
        |
CDN + WAF + Bot Control
        |
API Gateway / Rate Limit / JWT Verification
        |
+---------------------+----------------------+------------------+
| Profile API         | Course API           | Community API    |
| Drive Record API    | Route Preview API    | Notification API |
+---------------------+----------------------+------------------+
        |                    |                         |
 PostgreSQL + replicas   Redis Cluster          Kafka / Queue
 PostGIS, partitioning   hot cache, locks       async events
        |                    |                         |
 Object Storage + CDN   TMAP/Kakao adapter     Data warehouse
```

## 3. 우선 적용 기술

### 엣지와 프론트엔드

- 정적 React 빌드는 CDN에 배포하고 버전 해시 파일명으로 캐시합니다.
- WAF, IP·사용자·디바이스 단위 rate limit, 비정상 봇 차단을 적용합니다.
- 지도 SDK 실패 시 검증 경유지 기반 fallback을 유지해 핵심 UI가 깨지지 않도록 합니다.
- Sentry 또는 OpenTelemetry로 프론트 오류와 Web Vitals를 수집합니다.

### 백엔드

- Django 애플리케이션을 컨테이너로 배포하고 Gunicorn/Uvicorn worker를 수평 확장합니다.
- `/api/health/live/`, `/api/health/ready/`를 Kubernetes probe와 로드밸런서 점검에 사용합니다.
- 외부 지도 API 호출은 timeout, circuit breaker, retry budget, bulkhead를 적용합니다.
- 경로 조회 adapter를 분리해 TMAP 장애 시 저장 경유지 또는 다른 공급자로 우회합니다.
- 추천 API는 검증 코스와 부담도 계산 결과를 Redis에 캐시하고, 교통 시간대 플래그만 짧게 갱신합니다.

### 데이터

- PostgreSQL을 기본 DB로 사용하고 읽기 replica를 분리합니다.
- 위치 데이터는 PostGIS로 관리하고 오라이존 인접 검색에 공간 인덱스를 적용합니다.
- 주행 기록은 월 단위 partitioning을 적용하고, 오래된 원본 위치 로그는 object storage로 이동합니다.
- 커뮤니티 피드는 fan-out 전략과 Redis sorted set을 사용하며 인기글 계산은 비동기 처리합니다.

### 비동기 처리

- Kafka 또는 관리형 큐를 사용해 `drive.finished`, `mission.completed`, `feedback.created` 이벤트를 발행합니다.
- XP 계산, 통계 적재, 추천 피처 갱신, 알림 발송은 요청 응답과 분리합니다.
- 중복 이벤트를 허용하되 consumer는 idempotency key로 멱등 처리합니다.

## 4. 단계별 확장

| 단계 | 사용자 규모 | 필수 작업 |
|---|---:|---|
| MVP | 1만 이하 | 단일 Django, PostgreSQL, CDN, 외부 API timeout, 기본 모니터링 |
| 성장기 | 10만~100만 | Redis, Celery/Queue, API Gateway, autoscaling, read replica, 로그 중앙화 |
| 대규모 | 1,000만 | 서비스 분리, Kafka, PostGIS, 파티셔닝, multi-AZ, 재해 복구, 공급자 이중화 |

## 5. 운영 체크리스트

- API 키를 `.env` 파일로 배포 이미지에 넣지 않고 Secret Manager에서 주입합니다.
- TMAP 및 카카오 쿼터와 허용 도메인을 운영·스테이징·로컬 환경별로 분리합니다.
- 경로 추천 응답에 생성 시각, 데이터 출처, fallback 여부를 기록합니다.
- 사고 다발 구간과 추천 결과의 변경 이력을 저장합니다.
- 운전 중 조작 제한 안내, 위치 데이터 최소 수집, 보관 기간, 삭제 정책을 명시합니다.
- 부하 테스트는 k6 또는 Locust로 추천 API, 경로 미리보기 API, 주행 완료 이벤트를 분리해 수행합니다.
