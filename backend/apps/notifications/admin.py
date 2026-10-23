from django.contrib import admin

from .models import Notification, StatusHistory, ActionLog, Rating


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'is_read', 'created_at')
    list_filter = ('type', 'is_read')
    search_fields = ('user__username', 'message')
    autocomplete_fields = ('user',)


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('entity_type', 'entity_id', 'from_status', 'to_status', 'changed_by', 'created_at')
    list_filter = ('entity_type', 'to_status')
    search_fields = ('entity_type', 'from_status', 'to_status')
    autocomplete_fields = ('changed_by',)


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'entity_type', 'entity_id', 'created_at')
    list_filter = ('action',)
    search_fields = ('user__username', 'action')
    autocomplete_fields = ('user',)


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('supervisor', 'student', 'score', 'created_at')
    list_filter = ('score',)
    search_fields = ('supervisor__username', 'student__username')
    autocomplete_fields = ('supervisor', 'student')