from rest_framework import serializers
from apps.catalog.models import Topic
from apps.catalog.serializers import TopicSerializer
from .models import Application, Thesis, Stage, File, Review


class FileSerializer(serializers.ModelSerializer):
    # Добавляем поле file_url, которое будет отдавать полный путь
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = ('id', 'file', 'file_name', 'created_at', 'file_url')

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url if obj.file else None


class ReviewSerializer(serializers.ModelSerializer):
    supervisor_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ('id', 'text', 'decision', 'created_at', 'supervisor_name')

    def get_supervisor_name(self, obj):
        return obj.supervisor.get_full_name() or obj.supervisor.username


class StageSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    files_count = serializers.SerializerMethodField()
    
    student_name = serializers.SerializerMethodField()
    files = FileSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Stage
        fields = (
            'id', 'type', 'type_display', 'status', 'status_display',
            'deadline', 'order_index', 'files_count', 'student_name', 'files', 'reviews'
        )

    def get_files_count(self, obj):
        return obj.files.count()
        
    def get_student_name(self, obj):
        return obj.thesis.student.get_full_name() or obj.thesis.student.username


class ApplicationSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    topic_title = serializers.CharField(source='topic.title', read_only=True)
    topic = TopicSerializer(read_only=True)
    topic_id = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.all(), source='topic', write_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Application
        fields = (
            'id', 'student', 'student_name', 'topic', 'topic_id', 'topic_title',
            'status', 'status_display', 'comment', 'supervisor_comment',
            'created_at', 'decided_at',
        )
        read_only_fields = ('id', 'student', 'status', 'supervisor_comment', 'created_at', 'decided_at')

    def get_student_name(self, obj):
        return obj.student.get_full_name() or obj.student.username


class ThesisSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    supervisor_name = serializers.SerializerMethodField()
    topic_title = serializers.CharField(source='topic.title', read_only=True)
    topic = TopicSerializer(read_only=True)
    stages = StageSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Thesis
        fields = (
            'id', 'student', 'student_name', 'topic', 'topic_title',
            'supervisor', 'supervisor_name', 'status', 'status_display',
            'stages', 'created_at',
        )

    def get_student_name(self, obj):
        return obj.student.get_full_name() or obj.student.username

    def get_supervisor_name(self, obj):
        return obj.supervisor.get_full_name() or obj.supervisor.username