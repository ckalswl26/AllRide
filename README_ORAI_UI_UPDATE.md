# 오라이 UI/카카오맵 업데이트 안내

## 추가된 점
- 카카오맵 SDK를 동적으로 로드하도록 수정
- 웹 버전 페이지: `/api/courses/recommend/page/`
- 앱 버전 페이지: `/api/courses/recommend/app/`
- 루트(`/`) 접속 시 웹 버전으로 자동 이동
- 후기(좋아요/싫어요)는 `주행 시작 -> 주행 종료` 이후에만 표시
- 오라이 캐릭터 이미지 적용
- 컬러 시스템 변경
  - Green: `#CDBC50`
  - Pink: `#F34B5C`
  - Yellow: `#F9B826`

## 반드시 확인할 것
1. `.env` 파일에 `KAKAO_JS_KEY`가 있어야 합니다.
2. 카카오 개발자 콘솔 > 플랫폼 > Web 에 아래 도메인이 등록되어 있어야 합니다.
   - `http://127.0.0.1:8000`
   - `http://localhost:8000`
3. 처음 실행 시 아래 명령을 꼭 수행하세요.

```bash
python3 manage.py migrate
python3 manage.py runserver
```

## 오라이존 데이터가 비어 있으면
```bash
curl -X POST http://127.0.0.1:8000/api/orai-zones/seed/
```
