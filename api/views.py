# api/views.py
import os
import math
import requests
import environ
from urllib.parse import quote
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import (
    User, Quest, QuestRecord, Badge,
    Route, DangerZone, FavoriteRoute,
    CommunityPost, Comment, PracticeCourse,
    OraiZone, VerifiedPracticeCourse, PracticeDriveRecord, CourseFeedback
)
from .serializers import (
    UserSerializer, UserRegisterSerializer,
    QuestSerializer, QuestRecordSerializer,
    BadgeSerializer, RouteSerializer,
    DangerZoneSerializer, FavoriteRouteSerializer,
    CommunityPostSerializer, CommentSerializer,
    PracticeCourseSerializer, OraiZoneSerializer,
    VerifiedPracticeCourseSerializer, PracticeDriveRecordSerializer, CourseFeedbackSerializer
)

# 환경변수 로드
env = environ.Env()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

TMAP_API_KEY = env('TMAP_API_KEY', default='')
KAKAO_REST_API_KEY = env('KAKAO_REST_API_KEY', default=env('KAKAO_API_KEY', default=''))
KAKAO_JS_KEY = env('KAKAO_JS_KEY', default='')
PUBLIC_DATA_API_KEY = env('PUBLIC_DATA_API_KEY', default='')


@api_view(['GET'])
def health_live(request):
    """로드밸런서용 liveness probe. 외부 의존성을 호출하지 않는다."""
    return Response({'status': 'ok', 'service': 'orai-api', 'check': 'live'})


@api_view(['GET'])
def health_ready(request):
    """오케스트레이터용 readiness probe. DB 연결 가능 여부를 확인한다."""
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        return Response({'status': 'ok', 'service': 'orai-api', 'check': 'ready'})
    except Exception:
        return Response({'status': 'unavailable', 'service': 'orai-api', 'check': 'ready'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
def system_capabilities(request):
    """운영 배포 시 프론트와 모니터링이 확인할 수 있는 비밀값 비노출 기능 플래그."""
    return Response({
        'service': 'orai-api',
        'version': '2.0.0',
        'features': {
            'kakao_map': bool(KAKAO_JS_KEY),
            'tmap_route_preview': bool(TMAP_API_KEY),
            'fallback_route_preview': True,
            'stateless_client_mode': True,
            'health_probe': True,
        },
    })


# ════════════════════════════════════════════════
#  기존 API
# ════════════════════════════════════════════════

@api_view(['GET'])
def index(request):
    return Response({
        "message" : "오라이D API 서버 정상 작동 중 🚗",
        "version" : "1.0.0",
        "endpoints": {
            "register"        : "/api/users/register/",
            "login"           : "/api/users/login/",
            "quests"          : "/api/quests/",
            "routes"          : "/api/routes/recommend/",
            "course_recommend": "/api/courses/recommend/",
            "danger_zones"    : "/api/danger-zones/",
            "posts"           : "/api/posts/",
        }
    })


@api_view(['POST'])
def register(request):
    serializer = UserRegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "회원가입 성공!", "data": serializer.data},
            status=status.HTTP_201_CREATED
        )
    return Response(
        {"message": "회원가입 실패", "errors": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
def login(request):
    import hashlib
    email    = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response(
            {"message": "이메일과 비밀번호를 입력해주세요."},
            status=status.HTTP_400_BAD_REQUEST
        )

    hashed_pw = hashlib.sha256(password.encode()).hexdigest()

    try:
        user       = User.objects.get(email=email, password=hashed_pw)
        serializer = UserSerializer(user)
        return Response(
            {"message": "로그인 성공!", "data": serializer.data},
            status=status.HTTP_200_OK
        )
    except User.DoesNotExist:
        return Response(
            {"message": "이메일 또는 비밀번호가 틀렸습니다."},
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['POST'])
def level_diagnose(request):
    user_id       = request.data.get('user_id')
    career_months = request.data.get('career_months', 0)
    score         = request.data.get('score', 0)

    if career_months == 0 and score <= 2:
        level = 1
    elif career_months <= 6 and score <= 4:
        level = 2
    elif career_months <= 12 and score <= 6:
        level = 3
    else:
        level = 4

    try:
        user       = User.objects.get(user_id=user_id)
        user.level = level
        user.save()
        return Response(
            {"message": "레벨 진단 완료!", "level": level},
            status=status.HTTP_200_OK
        )
    except User.DoesNotExist:
        return Response(
            {"message": "유저를 찾을 수 없습니다."},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def quest_list(request):
    level = request.GET.get('level')
    quests = Quest.objects.filter(level=level) if level else Quest.objects.all()
    serializer = QuestSerializer(quests, many=True)
    return Response(
        {"message": "퀘스트 목록 조회 성공", "data": serializer.data},
        status=status.HTTP_200_OK
    )


@api_view(['GET', 'POST'])
def save_quests(request):
    quest_data = [
        {"quest_name": "주차장 직진 연습",   "level": 1, "description": "넓은 주차장에서 직진 주행 연습", "distance": 0.5,  "road_type": "주차장",   "difficulty": "쉬움"},
        {"quest_name": "주차장 좌우 회전",   "level": 1, "description": "주차장에서 좌회전/우회전 연습",  "distance": 0.5,  "road_type": "주차장",   "difficulty": "쉬움"},
        {"quest_name": "주차 연습",          "level": 1, "description": "일반 주차 칸에 주차 연습",       "distance": 0.3,  "road_type": "주차장",   "difficulty": "쉬움"},
        {"quest_name": "이면도로 주행",      "level": 2, "description": "한적한 이면도로 주행 연습",      "distance": 2.0,  "road_type": "이면도로", "difficulty": "보통"},
        {"quest_name": "골목길 통과",        "level": 2, "description": "좁은 골목길 주행 연습",          "distance": 1.5,  "road_type": "이면도로", "difficulty": "보통"},
        {"quest_name": "일반도로 주행",      "level": 3, "description": "일반 도로 주행 연습",            "distance": 5.0,  "road_type": "일반도로", "difficulty": "어려움"},
        {"quest_name": "신호등 있는 교차로", "level": 3, "description": "신호등 교차로 통과 연습",        "distance": 3.0,  "road_type": "일반도로", "difficulty": "어려움"},
        {"quest_name": "야간 주행",          "level": 4, "description": "야간 일반도로 주행 연습",        "distance": 8.0,  "road_type": "일반도로", "difficulty": "매우어려움"},
        {"quest_name": "고속화도로 진입",    "level": 4, "description": "고속화도로 진입/진출 연습",      "distance": 10.0, "road_type": "고속도로", "difficulty": "매우어려움"},
    ]
    created_count = 0
    for data in quest_data:
        _, created = Quest.objects.get_or_create(
            quest_name=data['quest_name'], defaults=data
        )
        if created:
            created_count += 1

    return Response(
        {"message": f"퀘스트 {created_count}개 저장 완료!"},
        status=status.HTTP_201_CREATED
    )


@api_view(['POST'])
def route_recommend(request):
    user_id   = request.data.get('user_id')
    quest_id  = request.data.get('quest_id')
    start_lat = request.data.get('start_lat')
    start_lng = request.data.get('start_lng')
    end_lat   = request.data.get('end_lat')
    end_lng   = request.data.get('end_lng')

    if not all([start_lat, start_lng, end_lat, end_lng]):
        return Response(
            {"message": "출발지/도착지 좌표를 입력해주세요."},
            status=status.HTTP_400_BAD_REQUEST
        )

    tmap_url = "https://apis.openapi.sk.com/tmap/routes?version=1"
    headers  = {"appKey": TMAP_API_KEY, "Content-Type": "application/json"}
    body = {
        "startX": str(start_lng), "startY": str(start_lat),
        "endX"  : str(end_lng),   "endY"  : str(end_lat),
        "reqCoordType": "WGS84GEO", "resCoordType": "WGS84GEO",
        "startName": "출발지",      "endName": "도착지",
    }

    try:
        tmap_response = requests.post(tmap_url, json=body, headers=headers)
        tmap_data     = tmap_response.json()
        features      = tmap_data.get('features', [])
        distance = duration = 0
        if features:
            props    = features[0].get('properties', {})
            distance = props.get('totalDistance', 0) / 1000
            duration = props.get('totalTime', 0) // 60

        try:
            user  = User.objects.get(user_id=user_id)
            quest = Quest.objects.get(quest_id=quest_id) if quest_id else None
            route = Route.objects.create(
                user=user, quest=quest,
                start_lat=start_lat, start_lng=start_lng,
                end_lat=end_lat, end_lng=end_lng,
                distance=distance, duration=duration,
            )
            serializer = RouteSerializer(route)
            return Response(
                {"message": "루트 추천 성공!", "route": serializer.data, "tmap": tmap_data},
                status=status.HTTP_201_CREATED
            )
        except User.DoesNotExist:
            return Response({"message": "유저를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"message": f"T맵 API 호출 실패: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST', 'GET'])
def save_danger_zones(request):
    url = (
        f"https://apis.data.go.kr/B552061/frequentzoneLg/getRestFrequentzoneLg"
        f"?serviceKey={PUBLIC_DATA_API_KEY}"
        f"&searchYearCd=2022&siDo=11&guGun=680&type=json&numOfRows=100&pageNo=1"
    )
    try:
        response = requests.get(url)
        if not response.text.strip().startswith('{'):
            return Response(
                {"message": "공공데이터 API 응답 오류.", "detail": response.text},
                status=status.HTTP_502_BAD_GATEWAY
            )
        data  = response.json()
        items = data.get('items', {}).get('item', [])

        created_count = 0
        for item in items:
            if not item.get('la_crd') or not item.get('lo_crd'):
                continue
            _, created = DangerZone.objects.get_or_create(
                latitude=float(item.get('la_crd')),
                longitude=float(item.get('lo_crd')),
                defaults={
                    "zone_type"  : "교통사고다발",
                    "radius"     : 100,
                    "description": item.get('spot_nm', '교통사고 다발 구간'),
                }
            )
            if created:
                created_count += 1

        return Response(
            {"message": f"위험구간 {created_count}개 저장 완료!"},
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return Response({"message": f"서버 오류: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def danger_zone_list(request):
    zones      = DangerZone.objects.all()
    serializer = DangerZoneSerializer(zones, many=True)
    return Response({"message": "위험구간 조회 성공", "data": serializer.data}, status=status.HTTP_200_OK)


@api_view(['POST'])
def complete_quest(request):
    serializer = QuestRecordSerializer(data=request.data)
    if serializer.is_valid():
        record       = serializer.save()
        user         = User.objects.get(user_id=request.data.get('user_id'))
        quest        = Quest.objects.get(quest_id=request.data.get('quest_id'))
        record_count = QuestRecord.objects.filter(user=user).count()

        badge_type = None
        if record_count == 1:
            badge_type = "첫 퀘스트 완료"
        elif record_count == 5:
            badge_type = "5개 퀘스트 달성"
        elif record_count == 10:
            badge_type = "10개 퀘스트 달성"
        elif quest.level == 4:
            badge_type = "심화 퀘스트 완료"

        if badge_type:
            Badge.objects.create(user=user, badge_type=badge_type)

        return Response(
            {"message": "퀘스트 완료! 기록 저장됨", "badge": badge_type},
            status=status.HTTP_201_CREATED
        )
    return Response({"message": "저장 실패", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def growth_record(request, user_id):
    try:
        user    = User.objects.get(user_id=user_id)
        records = QuestRecord.objects.filter(user=user)
        badges  = Badge.objects.filter(user=user)
        return Response({
            "message"       : "성장 기록 조회 성공",
            "user"          : user.nickname,
            "level"         : user.level,
            "quest_records" : QuestRecordSerializer(records, many=True).data,
            "badges"        : BadgeSerializer(badges, many=True).data,
            "total_quests"  : records.count(),
            "total_distance": sum(r.drive_distance or 0 for r in records),
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"message": "유저를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET', 'POST'])
def post_list(request):
    if request.method == 'GET':
        posts      = CommunityPost.objects.all().order_by('-created_at')
        serializer = CommunityPostSerializer(posts, many=True)
        return Response({"message": "게시글 목록 조회 성공", "data": serializer.data}, status=status.HTTP_200_OK)
    serializer = CommunityPostSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "게시글 작성 성공!", "data": serializer.data}, status=status.HTTP_201_CREATED)
    return Response({"message": "게시글 작성 실패", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def post_detail(request, post_id):
    try:
        post     = CommunityPost.objects.get(post_id=post_id)
        comments = Comment.objects.filter(post=post)
        return Response({
            "message" : "게시글 조회 성공",
            "post"    : CommunityPostSerializer(post).data,
            "comments": CommentSerializer(comments, many=True).data,
        }, status=status.HTTP_200_OK)
    except CommunityPost.DoesNotExist:
        return Response({"message": "게시글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def comment_create(request, post_id):
    try:
        post       = CommunityPost.objects.get(post_id=post_id)
        data       = request.data.copy()
        data['post'] = post.post_id
        serializer = CommentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "댓글 작성 성공!", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"message": "댓글 작성 실패", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except CommunityPost.DoesNotExist:
        return Response({"message": "게시글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def favorite_route_save(request):
    serializer = FavoriteRouteSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "즐겨찾기 저장 성공!", "data": serializer.data}, status=status.HTTP_201_CREATED)
    return Response({"message": "즐겨찾기 저장 실패", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def favorite_route_list(request, user_id):
    favorites  = FavoriteRoute.objects.filter(user_id=user_id)
    serializer = FavoriteRouteSerializer(favorites, many=True)
    return Response({"message": "즐겨찾기 목록 조회 성공", "data": serializer.data}, status=status.HTTP_200_OK)



# ════════════════════════════════════════════════
#  오라이존 기반 검증형 왕복 코스 추천
# ════════════════════════════════════════════════

AVOID_FIELD_MAP = {
    'u_turn': 'u_turn_count',
    'lane_change': 'lane_change_count',
    'school_zone': 'school_zone_count',
    'accident_hotspot': 'accident_hotspot_count',
    'complex_intersection': 'complex_intersection_count',
    'speed_bump': 'speed_bump_count',
}


def is_congested_time(now=None):
    """MVP용 혼잡 시간 보정. 추후 카카오/티맵 실시간 ETA로 교체."""
    now = now or timezone.localtime()
    if now.weekday() >= 5:
        return False
    return 7 <= now.hour < 10 or 17 <= now.hour < 20


def adjusted_minutes(course, congested):
    return max(1, round(course.base_minutes * (1.20 if congested else 1.0)))


def burden_score(course):
    """사고 확률이 아니라 초보운전자의 체감 주행 부담도."""
    return (
        course.u_turn_count * 12
        + course.lane_change_count * 8
        + course.complex_intersection_count * 10
        + course.left_turn_count * 4
        + course.school_zone_count * 5
        + course.accident_hotspot_count * 15
        + course.speed_bump_count * 2
    )


def burden_label(score):
    if score <= 22:
        return '입문'
    if score <= 48:
        return '적응'
    return '도전'


def recommendation_score(course, requested_minutes, practice_type, level, avoid, eta):
    score = 100
    score -= min(abs(eta - requested_minutes) * 2, 36)
    score += 12 if course.practice_type == practice_type else -8
    score += 8 if course.level == level else -5
    for avoid_key in avoid:
        field_name = AVOID_FIELD_MAP.get(avoid_key)
        if field_name:
            score -= getattr(course, field_name, 0) * 9
    score -= course.accident_hotspot_count * 7
    score -= course.complex_intersection_count * 3
    score += max(-5, min(8, round((course.positive_ratio - 75) / 3)))
    return max(0, min(100, score))


def build_reason(course, eta):
    reasons = [
        f"예상 소요 시간은 약 {eta}분이에요.",
        f"{course.get_practice_type_display()} 연습에 맞춘 코스예요.",
    ]
    if course.u_turn_count == 0:
        reasons.append('유턴이 없어요.')
    if course.accident_hotspot_count == 0:
        reasons.append('등록된 사고 다발 구간을 포함하지 않아요.')
    if course.complex_intersection_count <= 1:
        reasons.append('복잡한 교차로가 적어요.')
    return ' '.join(reasons)


def route_coords(course):
    """카카오맵 Polyline용 좌표. 출발지 → 경유지 → 출발지."""
    points = [{'lat': course.zone.latitude, 'lng': course.zone.longitude, 'name': course.zone.zone_name}]
    for waypoint in course.waypoints:
        points.append({
            'lat': float(waypoint['lat']),
            'lng': float(waypoint['lng']),
            'name': waypoint.get('name', '경유지'),
        })
    points.append({'lat': course.zone.latitude, 'lng': course.zone.longitude, 'name': course.zone.zone_name})
    return points


@api_view(['GET'])
def orai_zone_list(request):
    zones = OraiZone.objects.filter(is_active=True).order_by('zone_id')
    return Response({'message': '오라이존 조회 성공', 'data': OraiZoneSerializer(zones, many=True).data})


@api_view(['POST', 'GET'])
def seed_orai_courses(request):
    """발표용 샘플 오라이존과 검증 코스를 저장한다."""
    multicampus, _ = OraiZone.objects.update_or_create(
        zone_name='삼성 멀티캠퍼스 역삼',
        defaults={
            'address': '서울 강남구 테헤란로 212 (역삼동 718-5)',
            'latitude': 37.501327,
            'longitude': 127.039623,
            'description': '멀티캠퍼스 역삼에서 출발하고 복귀하는 초보운전자 연습 존',
            'is_active': True,
        },
    )

    courses = [
        {
            'course_name': '역삼 차선 유지 입문 코스', 'practice_type': 'lane_keep', 'level': 'beginner',
            'waypoints': [
                {'name': '역삼역', 'lat': 37.500658, 'lng': 127.036430},
                {'name': '국기원 사거리', 'lat': 37.502688, 'lng': 127.030260},
            ],
            'base_minutes': 20, 'distance_km': 4.2, 'straight_ratio': 78,
            'right_turn_count': 2, 'left_turn_count': 1, 'u_turn_count': 0,
            'lane_change_count': 1, 'speed_bump_count': 1, 'school_zone_count': 0,
            'accident_hotspot_count': 0, 'complex_intersection_count': 1,
            'positive_ratio': 91, 'description': '직선 구간이 많아 차선 유지 연습에 적합합니다.'
        },
        {
            'course_name': '역삼 우회전 자신감 코스', 'practice_type': 'right_turn', 'level': 'beginner',
            'waypoints': [
                {'name': '역삼역', 'lat': 37.500658, 'lng': 127.036430},
                {'name': '강남역 1번 출구 인근', 'lat': 37.497912, 'lng': 127.027619},
                {'name': '테헤란로 이면도로', 'lat': 37.499954, 'lng': 127.034542},
            ],
            'base_minutes': 30, 'distance_km': 6.8, 'straight_ratio': 62,
            'right_turn_count': 5, 'left_turn_count': 1, 'u_turn_count': 0,
            'lane_change_count': 1, 'speed_bump_count': 1, 'school_zone_count': 0,
            'accident_hotspot_count': 0, 'complex_intersection_count': 1,
            'positive_ratio': 88, 'description': '유턴 없이 우회전을 반복해서 연습할 수 있습니다.'
        },
        {
            'course_name': '역삼 좌회전 적응 코스', 'practice_type': 'left_turn', 'level': 'adapt',
            'waypoints': [
                {'name': '선릉역 인근', 'lat': 37.504503, 'lng': 127.049008},
                {'name': '역삼역', 'lat': 37.500658, 'lng': 127.036430},
            ],
            'base_minutes': 35, 'distance_km': 7.3, 'straight_ratio': 58,
            'right_turn_count': 3, 'left_turn_count': 3, 'u_turn_count': 0,
            'lane_change_count': 2, 'speed_bump_count': 1, 'school_zone_count': 0,
            'accident_hotspot_count': 0, 'complex_intersection_count': 2,
            'positive_ratio': 82, 'description': '신호 좌회전과 일반도로 적응을 함께 연습합니다.'
        },
        {
            'course_name': '역삼 주차장 진입 코스', 'practice_type': 'parking', 'level': 'beginner',
            'waypoints': [
                {'name': '이마트 역삼점 인근', 'lat': 37.499476, 'lng': 127.048112},
            ],
            'base_minutes': 25, 'distance_km': 5.1, 'straight_ratio': 70,
            'right_turn_count': 2, 'left_turn_count': 1, 'u_turn_count': 0,
            'lane_change_count': 1, 'speed_bump_count': 2, 'school_zone_count': 0,
            'accident_hotspot_count': 0, 'complex_intersection_count': 1,
            'positive_ratio': 86, 'description': '주차장 진입과 저속 주행을 연습합니다.'
        },
        {
            'course_name': '테헤란로 차선 변경 도전 코스', 'practice_type': 'lane_change', 'level': 'challenge',
            'waypoints': [
                {'name': '선릉역', 'lat': 37.504503, 'lng': 127.049008},
                {'name': '삼성역 방향 반환점', 'lat': 37.508381, 'lng': 127.063691},
            ],
            'base_minutes': 45, 'distance_km': 10.2, 'straight_ratio': 66,
            'right_turn_count': 2, 'left_turn_count': 2, 'u_turn_count': 1,
            'lane_change_count': 4, 'speed_bump_count': 0, 'school_zone_count': 0,
            'accident_hotspot_count': 1, 'complex_intersection_count': 3,
            'positive_ratio': 71, 'description': '큰길과 차선 변경 구간을 포함한 도전 코스입니다.'
        },
    ]

    for item in courses:
        VerifiedPracticeCourse.objects.update_or_create(
            zone=multicampus,
            course_name=item['course_name'],
            defaults=item,
        )

    return Response({
        'message': '오라이존과 검증 코스 저장 완료',
        'zone': OraiZoneSerializer(multicampus).data,
        'course_count': VerifiedPracticeCourse.objects.filter(zone=multicampus).count(),
    }, status=status.HTTP_201_CREATED)


def _ui_context():
    return {
        'KAKAO_JS_KEY': KAKAO_JS_KEY,
        'ui_colors': {
            'green': '#CDBC50',
            'pink': '#F34B5C',
            'yellow': '#F9B826',
        },
    }


def course_recommend_page(request):
    context = _ui_context()
    context['display_mode'] = 'web'
    return render(request, 'api/orai_react.html', context)


def course_recommend_app_page(request):
    context = _ui_context()
    context['display_mode'] = 'app'
    return render(request, 'api/orai_react.html', context)


@api_view(['POST'])
def course_recommend(request):
    """
    POST /api/courses/recommend/
    {
      "zone_id": 1,
      "minutes": 30,
      "practice_type": "right_turn",
      "level": "beginner",
      "avoid": ["u_turn", "accident_hotspot"]
    }
    """
    zone_id = request.data.get('zone_id')
    minutes = request.data.get('minutes')
    practice_type = request.data.get('practice_type', 'beginner')
    level = request.data.get('level', 'beginner')
    avoid = request.data.get('avoid', [])

    if not zone_id or not minutes:
        return Response({'message': 'zone_id와 minutes 값이 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        zone = OraiZone.objects.get(zone_id=zone_id, is_active=True)
    except OraiZone.DoesNotExist:
        return Response({'message': '선택한 오라이존을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

    congested = is_congested_time()
    items = []
    courses = VerifiedPracticeCourse.objects.filter(zone=zone, is_active=True)
    for course in courses:
        eta = adjusted_minutes(course, congested)
        score = recommendation_score(course, int(minutes), practice_type, level, avoid, eta)
        burden = burden_score(course)
        items.append({
            'course_id': course.course_id,
            'course_name': course.course_name,
            'practice_type': course.practice_type,
            'practice_type_label': course.get_practice_type_display(),
            'level': course.level,
            'level_label': course.get_level_display(),
            'estimated_minutes': eta,
            'estimated_range': [max(1, eta - 4), eta + 6],
            'distance_km': course.distance_km,
            'recommend_score': score,
            'burden_score': burden,
            'burden_label': burden_label(burden),
            'reason': build_reason(course, eta),
            'metrics': {
                'straight_ratio': course.straight_ratio,
                'right_turn_count': course.right_turn_count,
                'left_turn_count': course.left_turn_count,
                'u_turn_count': course.u_turn_count,
                'lane_change_count': course.lane_change_count,
                'speed_bump_count': course.speed_bump_count,
                'school_zone_count': course.school_zone_count,
                'accident_hotspot_count': course.accident_hotspot_count,
                'complex_intersection_count': course.complex_intersection_count,
                'positive_ratio': course.positive_ratio,
            },
            'route_coords': route_coords(course),
            'reward_text': course.reward_text,
        })

    items.sort(key=lambda item: (-item['recommend_score'], abs(item['estimated_minutes'] - int(minutes))))

    # 사용자가 선택한 연습 목표를 우선한다. 같은 목표 코스가 없을 때만 다른 목표를 대체 제안한다.
    same_goal = [item for item in items if item['practice_type'] == practice_type]
    pool = same_goal or items
    exact = [item for item in pool if abs(item['estimated_minutes'] - int(minutes)) <= max(5, round(int(minutes) * 0.2))]

    policy_message = ''
    if exact:
        selected = exact[:3]
    else:
        selected = pool[:3]
        policy_message = (
            f'{minutes}분 조건에 정확히 맞는 코스는 없어요. '
            '현재 교통 상황과 요청 조건에서 가장 가까운 대체 코스를 안내할게요.'
        )
    if not same_goal and selected:
        policy_message += ' 선택한 연습 목표의 코스가 없어 비슷한 단계의 코스를 함께 제안합니다.'

    if not selected:
        return Response({
            'message': '현재 선택한 오라이존에는 추천 가능한 코스가 없습니다.',
            'policy_message': '다른 오라이존을 선택하거나 이용 시간을 늘려주세요.',
            'courses': [],
        }, status=status.HTTP_200_OK)

    return Response({
        'message': '오라이존 기반 코스 추천 성공',
        'zone': OraiZoneSerializer(zone).data,
        'congested': congested,
        'policy_message': policy_message,
        'legal_notice': (
            '추천 경로와 예상 시간은 참고 정보입니다. 실제 도로 상황, 사고, 공사, 날씨, '
            '운전자의 주행 속도에 따라 달라질 수 있습니다. 운전 중에는 현장 교통 상황과 '
            '안전 판단을 우선해 주세요.'
        ),
        'courses': selected,
    })


def _coords_from_tmap_features(features):
    """TMAP GeoJSON features에서 도로를 따라가는 좌표 배열을 추출한다."""
    coords = []
    for feature in features or []:
        geometry = feature.get('geometry') or {}
        if geometry.get('type') != 'LineString':
            continue
        for lng, lat in geometry.get('coordinates') or []:
            point = {'lat': float(lat), 'lng': float(lng)}
            if not coords or coords[-1] != point:
                coords.append(point)
    return coords


def _fallback_navigation_instructions(course):
    """외부 길찾기 응답이 없을 때도 내비게이션 화면을 구성할 수 있는 안전 안내."""
    points = route_coords(course)
    return [
        {'index': 0, 'distance_m': 120, 'name': course.zone.zone_name, 'description': '출발지에서 천천히 직진하세요.', 'turn_type': 0},
        {'index': max(1, len(points) // 3), 'distance_m': 320, 'name': '연습 구간', 'description': '차선을 유지하며 제한 속도를 확인하세요.', 'turn_type': 0},
        {'index': max(2, (len(points) * 2) // 3), 'distance_m': 180, 'name': '복귀 구간', 'description': '교차로 진입 전 보행자와 신호를 확인하세요.', 'turn_type': 12},
        {'index': max(3, len(points) - 1), 'distance_m': 0, 'name': course.zone.zone_name, 'description': '목적지에 도착했습니다. 안전한 곳에 정차하세요.', 'turn_type': 201},
    ]


def _navigation_instructions_from_tmap_features(features, coord_count):
    """TMAP Point feature의 안내 문구를 앱 내비게이션 카드용 데이터로 변환한다."""
    instructions = []
    for feature in features or []:
        geometry = feature.get('geometry') or {}
        properties = feature.get('properties') or {}
        if geometry.get('type') != 'Point':
            continue
        description = properties.get('description') or properties.get('name')
        if not description:
            continue
        point_index = properties.get('pointIndex', properties.get('index', 0))
        try:
            point_index = int(point_index)
        except (TypeError, ValueError):
            point_index = 0
        instructions.append({
            'index': max(0, min(point_index, max(0, coord_count - 1))),
            'distance_m': int(float(properties.get('distance', 0) or 0)),
            'name': properties.get('name') or '다음 안내',
            'description': str(description),
            'turn_type': int(properties.get('turnType', 0) or 0),
        })
    return instructions


def _stored_route_preview(course):
    """TMAP 호출이 불가능할 때 저장된 경유지 기반 미리보기 좌표를 반환한다."""
    coords = route_coords(course)
    return {
        'source': 'stored_waypoints',
        'route_coords': coords,
        'navigation_instructions': _fallback_navigation_instructions(course),
        'message': 'TMAP 실도로 경로를 불러오지 못해 저장된 경유지 연결선으로 표시합니다.',
    }


def _request_tmap_driving_preview(course):
    """
    TMAP 자동차 길찾기 API로 실제 도로를 따라가는 미리보기 경로를 조회한다.
    출발지와 도착지는 동일한 오라이존이며, 저장된 경유지를 passList로 전달한다.
    """
    if not TMAP_API_KEY:
        return _stored_route_preview(course)

    start_x = course.zone.longitude
    start_y = course.zone.latitude
    end_x = course.zone.longitude
    end_y = course.zone.latitude
    pass_list = '_'.join(
        f"{float(point['lng'])},{float(point['lat'])}"
        for point in course.waypoints
        if point.get('lng') is not None and point.get('lat') is not None
    )

    body = {
        'startX': str(start_x),
        'startY': str(start_y),
        'endX': str(end_x),
        'endY': str(end_y),
        'reqCoordType': 'WGS84GEO',
        'resCoordType': 'WGS84GEO',
        'startName': course.zone.zone_name,
        'endName': course.zone.zone_name,
        'searchOption': '0',
    }
    if pass_list:
        body['passList'] = pass_list

    try:
        response = requests.post(
            'https://apis.openapi.sk.com/tmap/routes?version=1&format=json',
            headers={
                'appKey': TMAP_API_KEY,
                'Content-Type': 'application/json',
            },
            json=body,
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()
        features = data.get('features', [])
        coords = _coords_from_tmap_features(features)
        properties = (features[0].get('properties') if features else {}) or {}

        if len(coords) < 2:
            return _stored_route_preview(course)

        instructions = _navigation_instructions_from_tmap_features(features, len(coords))
        if not instructions:
            instructions = _fallback_navigation_instructions(course)
        return {
            'source': 'tmap_driving_route',
            'route_coords': coords,
            'navigation_instructions': instructions,
            'distance_km': round(float(properties.get('totalDistance', 0)) / 1000, 1),
            'duration_minutes': max(1, round(float(properties.get('totalTime', 0)) / 60)),
            'message': 'TMAP 자동차 경로를 기준으로 실제 도로 미리보기를 표시합니다.',
        }
    except Exception:
        return _stored_route_preview(course)


@api_view(['GET'])
def map_config_status(request):
    """키 값 자체는 노출하지 않고, 지도 연동에 필요한 설정 여부만 확인한다."""
    return Response({
        'kakao_js_key_configured': bool(KAKAO_JS_KEY),
        'kakao_rest_key_configured': bool(KAKAO_REST_API_KEY),
        'tmap_key_configured': bool(TMAP_API_KEY),
        'allowed_web_domains': [
            'http://127.0.0.1:8000',
            'http://localhost:8000',
        ],
    })


@api_view(['GET'])
def course_route_preview(request, course_id):
    """
    추천 코스의 미리보기 경로를 반환한다.
    TMAP 키가 있으면 실제 자동차 도로 경로를 반환하고,
    실패하면 저장된 경유지 좌표를 연결한 fallback을 반환한다.
    """
    try:
        course = VerifiedPracticeCourse.objects.select_related('zone').get(
            course_id=course_id,
            is_active=True,
        )
    except VerifiedPracticeCourse.DoesNotExist:
        return Response(
            {'message': '코스를 찾을 수 없습니다.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    result = _request_tmap_driving_preview(course)
    result.update({
        'course_id': course.course_id,
        'course_name': course.course_name,
        'zone': OraiZoneSerializer(course.zone).data,
    })
    return Response(result)


@api_view(['POST'])
def course_feedback(request, course_id):
    """주행 종료가 확인된 기록에 대해서만 좋아요/싫어요 후기를 저장한다."""
    try:
        course = VerifiedPracticeCourse.objects.get(course_id=course_id)
    except VerifiedPracticeCourse.DoesNotExist:
        return Response({'message': '코스를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

    drive_record_id = request.data.get('drive_record_id')
    if not drive_record_id:
        return Response({'message': '주행 종료 기록이 있어야 후기를 남길 수 있습니다.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        drive = PracticeDriveRecord.objects.get(drive_id=drive_record_id, course=course)
    except PracticeDriveRecord.DoesNotExist:
        return Response({'message': '해당 코스의 주행 기록을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    if drive.status != 'completed':
        return Response({'message': '주행을 종료한 뒤 후기를 남겨주세요.'}, status=status.HTTP_400_BAD_REQUEST)
    if hasattr(drive, 'feedback'):
        return Response({'message': '이미 후기를 남긴 주행입니다.'}, status=status.HTTP_400_BAD_REQUEST)

    payload = request.data.copy()
    payload.pop('drive_record_id', None)
    payload['course'] = course.course_id
    payload['drive_record'] = drive.drive_id
    serializer = CourseFeedbackSerializer(data=payload)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': '후기가 저장되었습니다.', 'data': serializer.data}, status=status.HTTP_201_CREATED)
    return Response({'message': '후기 저장 실패', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ════════════════════════════════════════════════
#  React SPA용 데모/주행/커뮤니티 API (세션 미사용)
# ════════════════════════════════════════════════

def _demo_user():
    """로그인 세션 없이 바로 체험 가능한 데모 사용자를 반환한다."""
    import hashlib
    password = hashlib.sha256('orai-demo'.encode()).hexdigest()
    user, _ = User.objects.get_or_create(
        email='driver@orai.local',
        defaults={
            'password': password,
            'nickname': '초보운전자 민지',
            'level': 1,
        },
    )
    return user


def _profile_payload(user):
    completed = PracticeDriveRecord.objects.filter(user=user, status='completed')
    total_xp = sum(item.xp_earned for item in completed)
    level = max(1, total_xp // 500 + 1)
    level_xp = total_xp % 500
    if user.level != level:
        user.level = level
        user.save(update_fields=['level'])
    return {
        'user_id': user.user_id,
        'nickname': user.nickname,
        'level': level,
        'level_title': ['새싹 드라이버', '골목길 탐험가', '도로 적응 중', '자신감 드라이버', '베테랑 도전자'][min(level - 1, 4)],
        'xp': level_xp,
        'next_level_xp': 500,
        'total_xp': total_xp,
        'completed_drives': completed.count(),
        'total_distance': round(sum(item.course.distance_km for item in completed.select_related('course')), 1),
    }


def _community_payload(post):
    return {
        'post_id': post.post_id,
        'nickname': post.user.nickname,
        'title': post.title,
        'content': post.content,
        'category': post.category,
        'likes': post.likes,
        'comment_count': Comment.objects.filter(post=post).count(),
        'created_at': timezone.localtime(post.created_at).strftime('%m.%d %H:%M'),
    }


def _ensure_demo_posts(user):
    if CommunityPost.objects.exists():
        return
    CommunityPost.objects.create(
        user=user, category='tip', title='우회전할 때 보행자 신호 꼭 한 번 더 확인하세요',
        content='역삼 우회전 코스를 연습했는데, 횡단보도 앞에서 속도를 충분히 줄이니 훨씬 마음이 편했어요. 뒤차보다 안전이 먼저입니다!', likes=18,
    )
    CommunityPost.objects.create(
        user=user, category='review', title='차선 유지 입문 코스 첫 완주 후기 🚗',
        content='직선 구간이 많아서 초보가 연습하기 좋았어요. 두 번째 주행부터는 핸들을 덜 흔들게 됐습니다.', likes=12,
    )
    CommunityPost.objects.create(
        user=user, category='question', title='차선 변경 타이밍은 어떻게 익히셨나요?',
        content='사이드미러를 보는 순서와 깜빡이 켜는 타이밍이 아직 어렵네요. 연습 팁이 있다면 알려주세요!', likes=7,
    )


@api_view(['GET'])
def app_bootstrap(request):
    """React 앱 첫 화면에 필요한 데이터를 한 번에 반환한다."""
    user = _demo_user()
    _ensure_demo_posts(user)
    zones = OraiZone.objects.filter(is_active=True).order_by('zone_id')
    courses = VerifiedPracticeCourse.objects.filter(is_active=True).select_related('zone').order_by('course_id')
    completed_ids = set(PracticeDriveRecord.objects.filter(user=user, status='completed').values_list('course_id', flat=True))
    missions = []
    for course in courses:
        missions.append({
            'course_id': course.course_id,
            'course_name': course.course_name,
            'practice_type': course.practice_type,
            'practice_type_label': course.get_practice_type_display(),
            'level': course.level,
            'level_label': course.get_level_display(),
            'distance_km': course.distance_km,
            'estimated_minutes': course.base_minutes,
            'reward_xp': 120 + min(80, burden_score(course)),
            'description': course.description,
            'completed': course.course_id in completed_ids,
        })
    history = PracticeDriveRecord.objects.filter(user=user, status='completed').select_related('course', 'course__zone').order_by('-ended_at')[:20]
    posts = CommunityPost.objects.select_related('user').order_by('-created_at')[:20]
    return Response({
        'message': '오라이 React 앱 데이터 조회 성공',
        'profile': _profile_payload(user),
        'zones': OraiZoneSerializer(zones, many=True).data,
        'missions': missions,
        'history': PracticeDriveRecordSerializer(history, many=True).data,
        'posts': [_community_payload(post) for post in posts],
    })


@api_view(['POST'])
def drive_start(request):
    user = _demo_user()
    course_id = request.data.get('course_id')
    try:
        course = VerifiedPracticeCourse.objects.select_related('zone').get(course_id=course_id, is_active=True)
    except VerifiedPracticeCourse.DoesNotExist:
        return Response({'message': '연습 코스를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    PracticeDriveRecord.objects.filter(user=user, status='in_progress').update(status='cancelled', ended_at=timezone.now())
    drive = PracticeDriveRecord.objects.create(user=user, course=course)
    return Response({
        'message': '주행을 시작합니다. 안전운전하세요!',
        'drive': PracticeDriveRecordSerializer(drive).data,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def drive_finish(request, drive_id):
    user = _demo_user()
    try:
        drive = PracticeDriveRecord.objects.select_related('course').get(drive_id=drive_id, user=user)
    except PracticeDriveRecord.DoesNotExist:
        return Response({'message': '주행 기록을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    if drive.status != 'in_progress':
        return Response({'message': '이미 종료된 주행입니다.'}, status=status.HTTP_400_BAD_REQUEST)
    actual_minutes = request.data.get('actual_minutes') or drive.course.base_minutes
    try:
        actual_minutes = max(1, int(actual_minutes))
    except (TypeError, ValueError):
        actual_minutes = drive.course.base_minutes
    drive.status = 'completed'
    drive.ended_at = timezone.now()
    drive.actual_minutes = actual_minutes
    drive.xp_earned = 120 + min(80, burden_score(drive.course))
    drive.save(update_fields=['status', 'ended_at', 'actual_minutes', 'xp_earned'])
    return Response({
        'message': '미션 클리어! 경험치를 획득했습니다.',
        'drive': PracticeDriveRecordSerializer(drive).data,
        'profile': _profile_payload(user),
    })


@api_view(['POST'])
def drive_cancel(request, drive_id):
    user = _demo_user()
    try:
        drive = PracticeDriveRecord.objects.get(drive_id=drive_id, user=user, status='in_progress')
    except PracticeDriveRecord.DoesNotExist:
        return Response({'message': '취소할 주행 기록을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    drive.status = 'cancelled'
    drive.ended_at = timezone.now()
    drive.save(update_fields=['status', 'ended_at'])
    return Response({'message': '주행을 취소했습니다.'})


@api_view(['GET'])
def drive_history(request):
    user = _demo_user()
    history = PracticeDriveRecord.objects.filter(user=user, status='completed').select_related('course', 'course__zone').order_by('-ended_at')
    return Response({'data': PracticeDriveRecordSerializer(history, many=True).data, 'profile': _profile_payload(user)})


@api_view(['GET', 'POST'])
def community_feed(request):
    user = _demo_user()
    _ensure_demo_posts(user)
    if request.method == 'POST':
        title = (request.data.get('title') or '').strip()
        content = (request.data.get('content') or '').strip()
        category = request.data.get('category') or 'tip'
        if not title or not content:
            return Response({'message': '제목과 내용을 모두 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)
        if category not in {'tip', 'review', 'question'}:
            category = 'tip'
        post = CommunityPost.objects.create(user=user, title=title, content=content, category=category)
        return Response({'message': '게시글이 등록되었습니다.', 'data': _community_payload(post)}, status=status.HTTP_201_CREATED)
    posts = CommunityPost.objects.select_related('user').order_by('-created_at')[:50]
    return Response({'data': [_community_payload(post) for post in posts]})


@api_view(['POST'])
def community_like(request, post_id):
    try:
        post = CommunityPost.objects.get(post_id=post_id)
    except CommunityPost.DoesNotExist:
        return Response({'message': '게시글을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    post.likes += 1
    post.save(update_fields=['likes'])
    return Response({'message': '공감했습니다.', 'likes': post.likes})
