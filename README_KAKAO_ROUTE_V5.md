# 오라이 카카오맵 + 실도로 경로 미리보기 V5

## 핵심 변경점
- 카카오 지도 Web SDK를 동적으로 로드합니다.
- `.env`의 `KAKAO_JS_KEY`를 웹 지도 appkey로 사용합니다.
- 카카오 REST 키 변수명은 `KAKAO_API_KEY`와 `KAKAO_REST_API_KEY`를 모두 지원합니다.
- 추천 코스 미리보기 시 `/api/courses/<course_id>/preview/`를 호출합니다.
- TMAP 키가 있으면 자동차 경로 API를 호출해 실제 도로 좌표를 받아 카카오맵 Polyline으로 표시합니다.
- TMAP 호출이 실패하면 저장된 경유지 연결선을 fallback으로 표시합니다.

## .env 예시
실제 키는 저장소에 커밋하지 마세요.

```env
DEBUG=True
TMAP_API_KEY=YOUR_TMAP_API_KEY
PUBLIC_DATA_API_KEY=YOUR_PUBLIC_DATA_API_KEY
KAKAO_API_KEY=YOUR_KAKAO_REST_API_KEY
KAKAO_JS_KEY=YOUR_KAKAO_JAVASCRIPT_KEY
```

## 카카오 개발자 콘솔 설정
JavaScript 키의 JavaScript SDK 도메인에 아래 주소를 등록하세요.

```text
http://127.0.0.1:8000
http://localhost:8000
```

## 실행
```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py runserver
```

## 접속 주소
- 웹: `http://127.0.0.1:8000/`
- 앱 UI: `http://127.0.0.1:8000/api/courses/recommend/app/`
- 지도 설정 확인: `http://127.0.0.1:8000/api/map-config/status/`

## 지도 설정 확인 API
키 값 자체는 노출하지 않고 설정 여부만 반환합니다.

```json
{
  "kakao_js_key_configured": true,
  "kakao_rest_key_configured": true,
  "tmap_key_configured": true
}
```
