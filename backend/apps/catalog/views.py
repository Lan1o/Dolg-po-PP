from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Direction, Topic
from .serializers import DirectionSerializer, TopicSerializer

User = get_user_model()


class IsAdminOrSupervisor(permissions.BasePermission):
    """Разрешает изменение только администратору и руководителю."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role in ('admin', 'supervisor')


class DirectionViewSet(viewsets.ModelViewSet):
    """CRUD для направлений подготовки."""
    queryset = Direction.objects.all()
    serializer_class = DirectionSerializer
    permission_classes = [IsAdminOrSupervisor]


class TopicViewSet(viewsets.ModelViewSet):
    """
    Каталог тем ВКР.
    Поддерживает поиск по ключевым словам (q) и 4 фильтра:
    direction (id), supervisor (id), status, tags.
    """
    serializer_class = TopicSerializer
    permission_classes = [IsAdminOrSupervisor]

    def get_queryset(self):
        qs = Topic.objects.select_related('direction', 'supervisor').all()

        # Фильтр для личного кабинета руководителя (страница "Мои темы")
        if self.request.query_params.get('my') == 'true' and self.request.user.is_authenticated and self.request.user.role == 'supervisor':
            qs = qs.filter(supervisor=self.request.user)

        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(requirements__icontains=q)
            )

        direction = self.request.query_params.get('direction')
        if direction:
            qs = qs.filter(direction_id=direction)

        supervisor = self.request.query_params.get('supervisor')
        if supervisor:
            qs = qs.filter(supervisor_id=supervisor)

        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)

        tags = self.request.query_params.get('tags')
        if tags:
            qs = qs.filter(tags__icontains=tags)

        return qs

    def perform_create(self, serializer):
        # При создании темы руководителем, автоматически привязываем его как автора
        if self.request.user.role == 'supervisor':
            serializer.save(supervisor=self.request.user)
        else:
            serializer.save()

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def filters(self, request):
        """Возвращает доступные значения для фильтров."""
        directions = Direction.objects.filter(is_active=True).values('id', 'code', 'title')
        supervisors = User.objects.filter(role='supervisor').values(
            'id', 'first_name', 'last_name', 'position'
        )
        statuses = [{'value': k, 'label': v} for k, v in Topic.Status.choices]
        return Response({
            'directions': list(directions),
            'supervisors': list(supervisors),
            'statuses': statuses,
        })