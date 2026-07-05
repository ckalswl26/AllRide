# api/admin.py
from django.contrib import admin
from .models import (
    User, Quest, QuestRecord, Badge,
    Route, DangerZone, FavoriteRoute,
    CommunityPost, Comment
)

admin.site.register(User)
admin.site.register(Quest)
admin.site.register(QuestRecord)
admin.site.register(Badge)
admin.site.register(Route)
admin.site.register(DangerZone)
admin.site.register(FavoriteRoute)
admin.site.register(CommunityPost)
admin.site.register(Comment)
