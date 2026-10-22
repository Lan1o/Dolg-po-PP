from django.contrib import admin

from .models import Direction, Topic


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('code', 'title')


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'direction', 'supervisor', 'status', 'created_at')
    list_filter = ('status', 'direction')
    search_fields = ('title', 'description', 'tags')
    autocomplete_fields = ('supervisor',)
    fieldsets = (
        (None, {
            'fields': ('title', 'direction', 'supervisor', 'status'),
        }),
        ('Содержание', {
            'fields': ('description', 'requirements', 'tags'),
        }),
    )