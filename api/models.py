# api/models.py
from django.db import models


# ── USER ──────────────────────────────────────
class User(models.Model):
    user_id     = models.AutoField(primary_key=True)
    email       = models.EmailField(unique=True)
    password    = models.CharField(max_length=255)
    nickname    = models.CharField(max_length=50)
    profile_img = models.CharField(max_length=500, blank=True, null=True)
    level       = models.IntegerField(default=1)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nickname


# ── QUEST ─────────────────────────────────────
class Quest(models.Model):
    quest_id    = models.AutoField(primary_key=True)
    quest_name  = models.CharField(max_length=100)
    level       = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    distance    = models.FloatField(blank=True, null=True)
    road_type   = models.CharField(max_length=50, blank=True, null=True)
    difficulty  = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.quest_name


# ── QUEST_RECORD ──────────────────────────────
class QuestRecord(models.Model):
    record_id      = models.AutoField(primary_key=True)
    user           = models.ForeignKey(
                         User, on_delete=models.CASCADE,
                         db_column='user_id')
    quest          = models.ForeignKey(
                         Quest, on_delete=models.CASCADE,
                         db_column='quest_id')
    completed_at   = models.DateTimeField(auto_now_add=True)
    drive_distance = models.FloatField(blank=True, null=True)
    duration       = models.IntegerField(blank=True, null=True)
    memo           = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.nickname} - {self.quest.quest_name}"


# ── BADGE ─────────────────────────────────────
class Badge(models.Model):
    badge_id   = models.AutoField(primary_key=True)
    user       = models.ForeignKey(
                     User, on_delete=models.CASCADE,
                     db_column='user_id')
    badge_type = models.CharField(max_length=50)
    earned_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.nickname} - {self.badge_type}"


# ── ROUTE ─────────────────────────────────────
class Route(models.Model):
    route_id   = models.AutoField(primary_key=True)
    user       = models.ForeignKey(
                     User, on_delete=models.CASCADE,
                     db_column='user_id')
    quest      = models.ForeignKey(
                     Quest, on_delete=models.SET_NULL,
                     null=True, blank=True,
                     db_column='quest_id')
    start_lat  = models.FloatField()
    start_lng  = models.FloatField()
    end_lat    = models.FloatField()
    end_lng    = models.FloatField()
    distance   = models.FloatField(blank=True, null=True)
    duration   = models.IntegerField(blank=True, null=True)
    difficulty = models.CharField(max_length=20, blank=True, null=True)
    saved_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Route {self.route_id} - {self.user.nickname}"


# ── DANGER_ZONE ───────────────────────────────
class DangerZone(models.Model):
    zone_id     = models.AutoField(primary_key=True)
    zone_type   = models.CharField(max_length=50)
    latitude    = models.FloatField()
    longitude   = models.FloatField()
    radius      = models.FloatField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.zone_type} ({self.latitude}, {self.longitude})"


# ── FAVORITE_ROUTE ────────────────────────────
class FavoriteRoute(models.Model):
    fav_id   = models.AutoField(primary_key=True)
    user     = models.ForeignKey(
                   User, on_delete=models.CASCADE,
                   db_column='user_id')
    route    = models.ForeignKey(
                   Route, on_delete=models.CASCADE,
                   db_column='route_id')
    saved_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.nickname} - Route {self.route.route_id}"


# ── COMMUNITY_POST ────────────────────────────
class CommunityPost(models.Model):
    post_id    = models.AutoField(primary_key=True)
    user       = models.ForeignKey(
                     User, on_delete=models.CASCADE,
                     db_column='user_id')
    title      = models.CharField(max_length=200)
    content    = models.TextField()
    category   = models.CharField(max_length=30, default='tip')
    route      = models.ForeignKey(
                     Route, on_delete=models.SET_NULL,
                     null=True, blank=True,
                     db_column='route_id')
    likes      = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


# ── COMMENT ───────────────────────────────────
class Comment(models.Model):
    comment_id = models.AutoField(primary_key=True)
    post       = models.ForeignKey(
                     CommunityPost, on_delete=models.CASCADE,
                     db_column='post_id')
    user       = models.ForeignKey(
                     User, on_delete=models.CASCADE,
                     db_column='user_id')
    content    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment {self.comment_id}"


# ── PRACTICE_COURSE ───────────────────────────
class PracticeCourse(models.Model):
    """시간 기반 왕복 연습 코스"""

    DIFFICULTY_CHOICES = [
        ('low',    '하'),
        ('medium', '중'),
        ('high',   '상'),
    ]

    course_id         = models.AutoField(primary_key=True)
    user              = models.ForeignKey(
                            User, on_delete=models.CASCADE,
                            db_column='user_id',
                            null=True, blank=True)
    course_name       = models.CharField(max_length=100)
    origin_lat        = models.FloatField()
    origin_lng        = models.FloatField()
    dest_lat          = models.FloatField()
    dest_lng          = models.FloatField()
    dest_name         = models.CharField(max_length=100, blank=True)
    difficulty        = models.CharField(
                            max_length=10,
                            choices=DIFFICULTY_CHOICES,
                            default='low')
    target_minutes    = models.IntegerField()
    estimated_minutes = models.IntegerField()
    distance_km       = models.FloatField()
    risk_count        = models.IntegerField(default=0)
    reason            = models.TextField(blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course_name} ({self.estimated_minutes}분)"


# ── ORAI_ZONE ──────────────────────────────────
class OraiZone(models.Model):
    """검증된 초보운전 연습 출발 지점"""
    zone_id     = models.AutoField(primary_key=True)
    zone_name   = models.CharField(max_length=100, unique=True)
    address     = models.CharField(max_length=255, blank=True)
    latitude    = models.FloatField()
    longitude   = models.FloatField()
    description = models.TextField(blank=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.zone_name


# ── VERIFIED_PRACTICE_COURSE ───────────────────
class VerifiedPracticeCourse(models.Model):
    """오라이존에서 출발하고 복귀하는 검증형 왕복 연습 코스"""
    PRACTICE_TYPE_CHOICES = [
        ('beginner', '처음 운전'),
        ('lane_keep', '차선 유지'),
        ('right_turn', '우회전'),
        ('left_turn', '좌회전'),
        ('u_turn', '유턴'),
        ('lane_change', '차선 변경'),
        ('parking', '주차장 진입'),
    ]
    LEVEL_CHOICES = [
        ('beginner', '입문'),
        ('adapt', '적응'),
        ('challenge', '도전'),
    ]

    course_id                  = models.AutoField(primary_key=True)
    zone                       = models.ForeignKey(OraiZone, on_delete=models.CASCADE, related_name='courses')
    course_name                = models.CharField(max_length=120)
    practice_type              = models.CharField(max_length=30, choices=PRACTICE_TYPE_CHOICES)
    level                      = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    waypoints                  = models.JSONField(default=list, blank=True)
    base_minutes               = models.IntegerField()
    distance_km                = models.FloatField(default=0)
    straight_ratio             = models.IntegerField(default=0)
    right_turn_count           = models.IntegerField(default=0)
    left_turn_count            = models.IntegerField(default=0)
    u_turn_count               = models.IntegerField(default=0)
    lane_change_count          = models.IntegerField(default=0)
    speed_bump_count           = models.IntegerField(default=0)
    school_zone_count          = models.IntegerField(default=0)
    accident_hotspot_count     = models.IntegerField(default=0)
    complex_intersection_count = models.IntegerField(default=0)
    positive_ratio             = models.IntegerField(default=80)
    reward_text                = models.CharField(max_length=200, blank=True)
    description                = models.TextField(blank=True)
    is_active                  = models.BooleanField(default=True)
    created_at                 = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.zone.zone_name} - {self.course_name}"


# ── PRACTICE_DRIVE_RECORD ─────────────────────
class PracticeDriveRecord(models.Model):
    """세션 없이도 주행 시작/종료 상태와 레벨업 기록을 저장하는 연습 기록."""

    STATUS_CHOICES = [
        ('in_progress', '주행 중'),
        ('completed', '완료'),
        ('cancelled', '취소'),
    ]

    drive_id       = models.AutoField(primary_key=True)
    user           = models.ForeignKey(User, on_delete=models.CASCADE, related_name='practice_drives')
    course         = models.ForeignKey(VerifiedPracticeCourse, on_delete=models.CASCADE, related_name='drive_records')
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    started_at     = models.DateTimeField(auto_now_add=True)
    ended_at       = models.DateTimeField(null=True, blank=True)
    actual_minutes = models.IntegerField(null=True, blank=True)
    xp_earned      = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.nickname} - {self.course.course_name} - {self.status}"


# ── COURSE_FEEDBACK ────────────────────────────
class CourseFeedback(models.Model):
    VERDICT_CHOICES = [('good', '괜찮았어요'), ('bad', '어려웠어요')]

    feedback_id       = models.AutoField(primary_key=True)
    course            = models.ForeignKey(VerifiedPracticeCourse, on_delete=models.CASCADE, related_name='feedbacks')
    drive_record      = models.OneToOneField(PracticeDriveRecord, on_delete=models.CASCADE, related_name='feedback', null=True, blank=True)
    verdict           = models.CharField(max_length=10, choices=VERDICT_CHOICES)
    difficult_reasons = models.JSONField(default=list, blank=True)
    actual_minutes    = models.IntegerField(null=True, blank=True)
    memo              = models.TextField(blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course.course_name} - {self.verdict}"
