# api/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # 테스트
    path('', views.index, name='index'),
    path('health/live/',                     views.health_live,          name='health_live'),
    path('health/ready/',                    views.health_ready,         name='health_ready'),
    path('system/capabilities/',             views.system_capabilities, name='system_capabilities'),

    # 유저
    path('users/register/',                views.register,            name='register'),
    path('users/login/',                   views.login,               name='login'),
    path('users/level-diagnose/',          views.level_diagnose,      name='level_diagnose'),

    # 퀘스트
    path('quests/',                        views.quest_list,          name='quest_list'),
    path('quests/save/',                   views.save_quests,         name='save_quests'),
    path('quests/complete/',               views.complete_quest,      name='complete_quest'),

    # 기존 루트
    path('routes/recommend/',              views.route_recommend,     name='route_recommend'),
    path('routes/favorite/',               views.favorite_route_save, name='favorite_save'),
    path('routes/favorite/<int:user_id>/', views.favorite_route_list, name='favorite_list'),

    # ✅ 오라이존 기반 왕복 코스 추천
    path('orai-zones/',                     views.orai_zone_list,        name='orai_zone_list'),
    path('orai-zones/seed/',                views.seed_orai_courses,     name='seed_orai_courses'),
    path('courses/recommend/',              views.course_recommend,      name='course_recommend'),
    path('courses/recommend/page/',         views.course_recommend_page, name='course_recommend_page'),
    path('courses/recommend/app/',          views.course_recommend_app_page, name='course_recommend_app_page'),
    path('courses/<int:course_id>/feedback/', views.course_feedback,    name='course_feedback'),
    path('courses/<int:course_id>/preview/',  views.course_route_preview, name='course_route_preview'),
    path('map-config/status/',                 views.map_config_status, name='map_config_status'),


    # React SPA 데이터 (세션 미사용 데모 모드)
    path('app/bootstrap/',                   views.app_bootstrap,       name='app_bootstrap'),
    path('drives/start/',                    views.drive_start,         name='drive_start'),
    path('drives/<int:drive_id>/finish/',    views.drive_finish,        name='drive_finish'),
    path('drives/<int:drive_id>/cancel/',    views.drive_cancel,        name='drive_cancel'),
    path('drives/history/',                  views.drive_history,       name='drive_history'),
    path('community/feed/',                  views.community_feed,      name='community_feed'),
    path('community/posts/<int:post_id>/like/', views.community_like,   name='community_like'),

    # 위험구간
    path('danger-zones/',                  views.danger_zone_list,    name='danger_zone_list'),
    path('danger-zones/save/',             views.save_danger_zones,   name='save_danger_zones'),

    # 성장 기록
    path('records/<int:user_id>/',         views.growth_record,       name='growth_record'),

    # 커뮤니티
    path('posts/',                         views.post_list,           name='post_list'),
    path('posts/<int:post_id>/',           views.post_detail,         name='post_detail'),
    path('posts/<int:post_id>/comments/',  views.comment_create,      name='comment_create'),
]
