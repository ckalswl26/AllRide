from django.test import TestCase
from rest_framework.test import APIClient

from .models import CourseFeedback, PracticeDriveRecord
from . import views


class OraiReactFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        views.TMAP_API_KEY = ''  # 외부 API 없이 fallback 경로를 검증한다.
        response = self.client.post('/api/orai-zones/seed/')
        self.assertEqual(response.status_code, 201)

    def test_bootstrap_returns_react_app_data(self):
        response = self.client.get('/api/app/bootstrap/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['zones'])
        self.assertTrue(data['missions'])
        self.assertTrue(data['posts'])
        self.assertEqual(data['profile']['level'], 1)

    def test_route_recommend_and_preview(self):
        zone_id = self.client.get('/api/app/bootstrap/').json()['zones'][0]['zone_id']
        response = self.client.post('/api/courses/recommend/', {
            'zone_id': zone_id,
            'minutes': 30,
            'practice_type': 'right_turn',
            'level': 'beginner',
            'avoid': [],
        }, format='json')
        self.assertEqual(response.status_code, 200)
        course = response.json()['courses'][0]
        preview = self.client.get(f"/api/courses/{course['course_id']}/preview/")
        self.assertEqual(preview.status_code, 200)
        self.assertEqual(preview.json()['source'], 'stored_waypoints')
        self.assertGreaterEqual(len(preview.json()['route_coords']), 2)
        self.assertGreaterEqual(len(preview.json()['navigation_instructions']), 1)

    def test_feedback_is_only_allowed_after_finish(self):
        bootstrap = self.client.get('/api/app/bootstrap/').json()
        course_id = bootstrap['missions'][0]['course_id']
        started = self.client.post('/api/drives/start/', {'course_id': course_id}, format='json')
        self.assertEqual(started.status_code, 201)
        drive_id = started.json()['drive']['drive_id']

        blocked = self.client.post(f'/api/courses/{course_id}/feedback/', {
            'drive_record_id': drive_id,
            'verdict': 'good',
        }, format='json')
        self.assertEqual(blocked.status_code, 400)

        finished = self.client.post(f'/api/drives/{drive_id}/finish/', {'actual_minutes': 22}, format='json')
        self.assertEqual(finished.status_code, 200)
        self.assertGreater(finished.json()['drive']['xp_earned'], 0)

        feedback = self.client.post(f'/api/courses/{course_id}/feedback/', {
            'drive_record_id': drive_id,
            'verdict': 'good',
            'memo': '초보가 연습하기 좋아요.',
        }, format='json')
        self.assertEqual(feedback.status_code, 201)
        self.assertEqual(CourseFeedback.objects.count(), 1)
        self.assertEqual(PracticeDriveRecord.objects.get(drive_id=drive_id).status, 'completed')

    def test_community_post_and_like(self):
        self.client.get('/api/app/bootstrap/')
        created = self.client.post('/api/community/feed/', {
            'category': 'tip',
            'title': '테스트 운전 팁',
            'content': '출발 전에 사이드미러를 확인해요.',
        }, format='json')
        self.assertEqual(created.status_code, 201)
        post_id = created.json()['data']['post_id']
        liked = self.client.post(f'/api/community/posts/{post_id}/like/')
        self.assertEqual(liked.status_code, 200)
        self.assertEqual(liked.json()['likes'], 1)
