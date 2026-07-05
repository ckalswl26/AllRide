# 오라이 지도 API 키 설정

## 1. `.env` 생성

프로젝트 루트에서 실행합니다.

```bash
cp .env.example .env
```

`.env` 파일에 값을 입력합니다.

```env
TMAP_API_KEY=발급받은_TMAP_앱키
KAKAO_JS_KEY=발급받은_카카오_JavaScript키
KAKAO_REST_API_KEY=발급받은_카카오_REST_API키
```

## 2. 카카오맵 JavaScript SDK 도메인 등록

로컬 실행을 위해 카카오 개발자 콘솔의 JavaScript SDK 도메인에 아래 주소를 등록합니다.

```text
http://127.0.0.1:8000
http://localhost:8000
```

배포 시에는 실제 HTTPS 서비스 도메인도 추가합니다.

## 3. 실행

```bash
./start_orai.sh
```

브라우저에서 아래 주소를 엽니다.

```text
http://127.0.0.1:8000/
```

## 4. 설정 상태 확인

```text
http://127.0.0.1:8000/api/map-config/status/
```

응답에는 키 원문이 아니라 설정 여부만 표시됩니다.

## 5. 키 역할

- `KAKAO_JS_KEY`: 브라우저에서 카카오 지도 타일과 Polyline을 표시합니다.
- `TMAP_API_KEY`: Django 서버가 TMAP 자동차 경로 안내 API를 호출할 때 사용합니다.
- `KAKAO_REST_API_KEY`: 향후 장소 검색과 서버 측 지오코딩 확장에 사용할 수 있습니다.
