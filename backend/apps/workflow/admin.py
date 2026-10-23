from django.contrib import admin

from .models import Application, Thesis, Stage, File, Review


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'topic', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('student__username', 'topic__title')
    autocomplete_fields = ('student', 'topic')


@admin.register(Thesis)
class ThesisAdmin(admin.ModelAdmin):
    list_display = ('student', 'topic', 'supervisor', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('student__username', 'topic__title', 'supervisor__username')
    autocomplete_fields = ('student', 'topic', 'supervisor')


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('thesis', 'type', 'status', 'deadline', 'order_index')
    list_filter = ('type', 'status')
    search_fields = ('thesis__student__username',)
    autocomplete_fields = ('thesis',)


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'stage', 'uploaded_by', 'created_at')
    search_fields = ('file_name',)
    autocomplete_fields = ('stage', 'uploaded_by')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('stage', 'supervisor', 'decision', 'created_at')
    list_filter = ('decision',)
    search_fields = ('supervisor__username', 'text')
    autocomplete_fields = ('stage', 'supervisor')