from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.catalog.models import Topic
from apps.notifications.models import Notification
from apps.notifications.services import notify, log_status, log_action

from .models import Application, Thesis, Stage
from .serializers import ApplicationSerializer, ThesisSerializer, StageSerializer


STAGE_ORDER = [
    Stage.Type.PLAN,
    Stage.Type.CHAPTER1,
    Stage.Type.CHAPTER2,
    Stage.Type.FULL_TEXT,
    Stage.Type.NORMCONTROL,
    Stage.Type.PREDEFENSE,
    Stage.Type.DEFENSE,
]


class ApplicationViewSet(viewsets.ModelViewSet):
    """
    Заявки на темы:
    - student: создаёт заявку, видит свои (my)
    - supervisor: видит инбокс (inbox), одобряет/отклоняет
    """
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'student':
            return Application.objects.filter(student=user).select_related('topic', 'student')
        if user.role == 'supervisor':
            return Application.objects.filter(topic__supervisor=user).select_related('topic', 'student')
        return Application.objects.all().select_related('topic', 'student')

    def perform_create(self, serializer):
        topic = serializer.validated_data['topic']
        if topic.status != Topic.Status.FREE:
            raise permissions.PermissionDenied('Тема уже занята или на согласовании.')
        app = serializer.save(student=self.request.user, status=Application.Status.SUBMITTED)
        topic.status = Topic.Status.PENDING
        topic.save(update_fields=['status'])
        log_status('application', app.id, '', app.status, self.request.user)
        log_action(self.request.user, 'Подал(а) заявку на тему', 'application', app.id)
        notify(
            topic.supervisor,
            Notification.Type.APPLICATION,
            f'{self.request.user.get_full_name() or self.request.user.username} подал(а) заявку на тему «{topic.title}».',
            link='/supervisor/inbox',
        )

    @action(detail=False, methods=['get'])
    def my(self, request):
        if request.user.role != 'student':
            return Response({'detail': 'Только для студентов.'}, status=403)
        qs = self.get_queryset()
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def inbox(self, request):
        if request.user.role != 'supervisor':
            return Response({'detail': 'Только для руководителей.'}, status=403)
        qs = self.get_queryset().filter(status=Application.Status.SUBMITTED)
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=True, methods=['patch'])
    @transaction.atomic
    def approve(self, request, pk=None):
        app = self.get_object()
        if request.user.role not in ('supervisor', 'admin'):
            return Response({'detail': 'Нет прав.'}, status=403)
        if app.status != Application.Status.SUBMITTED:
            return Response({'detail': 'Заявка уже обработана.'}, status=400)

        old_status = app.status
        app.status = Application.Status.APPROVED
        app.supervisor_comment = request.data.get('comment', 'Тема согласована.')
        app.decided_at = timezone.now()
        app.save()

        topic = app.topic
        topic.status = Topic.Status.OCCUPIED
        topic.save(update_fields=['status'])

        # Создаём ВКР + 7 этапов
        thesis = Thesis.objects.create(
            student=app.student,
            topic=topic,
            supervisor=request.user if request.user.role == 'supervisor' else topic.supervisor,
            status=Thesis.Status.ACTIVE,
        )
        base_date = date.today()
        for i, stage_type in enumerate(STAGE_ORDER, start=1):
            Stage.objects.create(
                thesis=thesis,
                type=stage_type,
                status=Stage.Status.NOT_STARTED,
                deadline=base_date + timedelta(days=21 * i),
                order_index=i,
            )

        log_status('application', app.id, old_status, app.status, request.user, app.supervisor_comment)
        log_action(request.user, 'Одобрил(а) заявку', 'application', app.id)
        notify(
            app.student,
            Notification.Type.APPLICATION,
            f'Ваша заявка на тему «{topic.title}» одобрена. Работа создана.',
            link='/workspace',
        )
        return Response(self.get_serializer(app).data)

    @action(detail=True, methods=['patch'])
    @transaction.atomic
    def reject(self, request, pk=None):
        app = self.get_object()
        if request.user.role not in ('supervisor', 'admin'):
            return Response({'detail': 'Нет прав.'}, status=403)
        if app.status != Application.Status.SUBMITTED:
            return Response({'detail': 'Заявка уже обработана.'}, status=400)

        old_status = app.status
        app.status = Application.Status.REJECTED
        app.supervisor_comment = request.data.get('comment', 'Заявка отклонена.')
        app.decided_at = timezone.now()
        app.save()

        topic = app.topic
        if topic.status == Topic.Status.PENDING:
            topic.status = Topic.Status.FREE
            topic.save(update_fields=['status'])

        log_status('application', app.id, old_status, app.status, request.user, app.supervisor_comment)
        log_action(request.user, 'Отклонил(а) заявку', 'application', app.id)
        notify(
            app.student,
            Notification.Type.APPLICATION,
            f'Ваша заявка на тему «{topic.title}» отклонена: {app.supervisor_comment}',
            link='/catalog',
        )
        return Response(self.get_serializer(app).data)


class ThesisViewSet(viewsets.ReadOnlyModelViewSet):
    """Просмотр ВКР: студент видит свою, руководитель — своих студентов."""
    serializer_class = ThesisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'student':
            return Thesis.objects.filter(student=user).prefetch_related('stages')
        if user.role == 'supervisor':
            return Thesis.objects.filter(supervisor=user).prefetch_related('stages')
        return Thesis.objects.all().prefetch_related('stages')

    @action(detail=False, methods=['get'])
    def my(self, request):
        if request.user.role != 'student':
            return Response({'detail': 'Только для студентов.'}, status=403)
        thesis = Thesis.objects.filter(student=request.user).prefetch_related('stages').first()
        if not thesis:
            return Response({'detail': 'У вас пока нет ВКР.'}, status=404)
        return Response(self.get_serializer(thesis).data)


class StageViewSet(viewsets.ModelViewSet):
    """Этапы ВКР: смена статуса, список."""
    serializer_class = StageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Stage.objects.select_related('thesis', 'thesis__student', 'thesis__supervisor')
        if user.role == 'student':
            return qs.filter(thesis__student=user)
        if user.role == 'supervisor':
            return qs.filter(thesis__supervisor=user)
        return qs