# api/serializers.py
from rest_framework import serializers
from .models import (
    User, Quest, QuestRecord, Badge,
    Route, DangerZone, FavoriteRoute,
    CommunityPost, Comment, PracticeCourse,
    OraiZone, VerifiedPracticeCourse, PracticeDriveRecord, CourseFeedback
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['user_id', 'email', 'nickname',
                  'profile_img', 'level', 'created_at']


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['email', 'password', 'nickname']

    def create(self, validated_data):
        import hashlib
        validated_data['password'] = hashlib.sha256(
            validated_data['password'].encode()
        ).hexdigest()
        return super().create(validated_data)


class QuestSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Quest
        fields = '__all__'


class QuestRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model  = QuestRecord
        fields = '__all__'


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Badge
        fields = '__all__'


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Route
        fields = '__all__'


class DangerZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DangerZone
        fields = '__all__'


class FavoriteRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FavoriteRoute
        fields = '__all__'


class CommunityPostSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CommunityPost
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Comment
        fields = '__all__'


# ── 새로 추가 ──────────────────────────────────
class PracticeCourseSerializer(serializers.ModelSerializer):
    difficulty_label = serializers.SerializerMethodField()

    class Meta:
        model  = PracticeCourse
        fields = '__all__'

    def get_difficulty_label(self, obj):
        return {'low': '하', 'medium': '중', 'high': '상'}.get(obj.difficulty, '')


class OraiZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = OraiZone
        fields = '__all__'


class VerifiedPracticeCourseSerializer(serializers.ModelSerializer):
    practice_type_label = serializers.CharField(source='get_practice_type_display', read_only=True)
    level_label = serializers.CharField(source='get_level_display', read_only=True)

    class Meta:
        model = VerifiedPracticeCourse
        fields = '__all__'


class CourseFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseFeedback
        fields = '__all__'


class PracticeDriveRecordSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.course_name', read_only=True)
    practice_type_label = serializers.CharField(source='course.get_practice_type_display', read_only=True)
    level_label = serializers.CharField(source='course.get_level_display', read_only=True)
    distance_km = serializers.FloatField(source='course.distance_km', read_only=True)
    zone_name = serializers.CharField(source='course.zone.zone_name', read_only=True)
    has_feedback = serializers.SerializerMethodField()

    class Meta:
        model = PracticeDriveRecord
        fields = [
            'drive_id', 'user', 'course', 'course_name', 'practice_type_label',
            'level_label', 'distance_km', 'zone_name', 'status', 'started_at',
            'ended_at', 'actual_minutes', 'xp_earned', 'has_feedback',
        ]

    def get_has_feedback(self, obj):
        return hasattr(obj, 'feedback')
