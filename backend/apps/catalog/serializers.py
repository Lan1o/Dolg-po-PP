from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Direction, Topic

User = get_user_model()


class DirectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Direction
        fields = ('id', 'code', 'title', 'description', 'is_active')


class TopicSerializer(serializers.ModelSerializer):
    direction = DirectionSerializer(read_only=True)
    supervisor = serializers.SerializerMethodField()
    direction_id = serializers.PrimaryKeyRelatedField(
        queryset=Direction.objects.all(), source='direction', write_only=True
    )
    supervisor_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='supervisor'),
        source='supervisor', write_only=True,
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    applications_count = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = (
            'id', 'title', 'description', 'requirements', 'tags',
            'direction', 'direction_id',
            'supervisor', 'supervisor_id',
            'status', 'status_display',
            'applications_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_supervisor(self, obj):
        if not obj.supervisor:
            return None
        return {
            'id': obj.supervisor.id,
            'full_name': obj.supervisor.get_full_name() or obj.supervisor.username,
            'position': obj.supervisor.position,
        }

    def get_applications_count(self, obj):
        return obj.applications.count()