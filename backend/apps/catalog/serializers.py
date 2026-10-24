from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Direction, Topic

User = get_user_model()


class DirectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Direction
        fields = ('id', 'code', 'title', 'description', 'is_active')


class SupervisorShortSerializer(serializers.Serializer):
    """Короткая информация о руководителе для карточки темы."""
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    position = serializers.CharField()


class TopicSerializer(serializers.ModelSerializer):
    direction = DirectionSerializer(read_only=True)
    supervisor = SupervisorShortSerializer(read_only=True)
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

    def get_applications_count(self, obj):
        return obj.applications.count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.supervisor:
            data['supervisor'] = {
                'id': instance.supervisor.id,
                'full_name': instance.supervisor.get_full_name() or instance.supervisor.username,
                'position': instance.supervisor.position,
            }
        return data