from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from apps.catalog.models import Topic
from apps.notifications.models import Notification
from apps.notifications.services import notify, log_status, log_action

from .models import Application, Thesis, Stage, File, Review
from .serializers import (
    ApplicationSerializer, ThesisSerializer, StageSerializer, ReviewSerializer
)

STAGE_ORDER = [
    Stage.Type.PLAN, Stage.Type.CHAPTER1, Stage.Type.CHAPTER2,
    Stage.Type.FULL_TEXT, Stage.Type.NORMCONTROL, Stage.Type.PREDEFENSE, Stage.Type.DEFENSE
]


class ApplicationViewSet(viewsets.ModelViewSet):
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
        user = self.request.user
        
        # Проверка: есть ли у студента уже активная ВКР?
        if Thesis.objects.filter(student=user).exists():
            raise permissions.PermissionDenied('У вас уже есть активная ВКР. Вы не можете подать новую заявку.')
            
        topic = serializer.validated_data['topic']
        if topic.status != Topic.Status.FREE:
            raise permissions.PermissionDenied('Тема уже занята или на согласовании.')
            
        app = serializer.save(student=user, status=Application.Status.SUBMITTED)
        topic.status = Topic.Status.PENDING
        topic.save(update_fields=['status'])
        log_status('application', app.id, '', app.status, user)
        log_action(user, 'Подал(а) заявку на тему', 'application', app.id)
        notify(topic.supervisor, Notification.Type.APPLICATION, f'{user.get_full_name() or user.username} подал(а) заявку на тему «{topic.title}».', link='/supervisor/inbox')

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
        qs = self.get_queryset()
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

        thesis = Thesis.objects.create(student=app.student, topic=topic, supervisor=request.user if request.user.role == 'supervisor' else topic.supervisor, status=Thesis.Status.ACTIVE)
        for i, stage_type in enumerate(STAGE_ORDER, start=1):
            Stage.objects.create(thesis=thesis, type=stage_type, status=Stage.Status.NOT_STARTED, deadline=date.today() + timedelta(days=21 * i), order_index=i)

        log_status('application', app.id, old_status, app.status, request.user, app.supervisor_comment)
        log_action(request.user, 'Одобрил(а) заявку', 'application', app.id)
        notify(app.student, Notification.Type.APPLICATION, f'Ваша заявка на тему «{topic.title}» одобрена.', link='/workspace')
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
        notify(app.student, Notification.Type.APPLICATION, f'Ваша заявка на тему «{topic.title}» отклонена.', link='/catalog')
        return Response(self.get_serializer(app).data)


class ThesisViewSet(viewsets.ReadOnlyModelViewSet):
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
    serializer_class = StageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser) # <-- ИСПРАВЛЕНО ЗДЕСЬ

    def get_queryset(self):
        user = self.request.user
        qs = Stage.objects.select_related('thesis', 'thesis__student', 'thesis__supervisor').prefetch_related('files', 'reviews')
        if user.role == 'student':
            return qs.filter(thesis__student=user)
        if user.role == 'supervisor':
            return qs.filter(thesis__supervisor=user)
        return qs

    @action(detail=True, methods=['post'])
    def upload(self, request, pk=None):
        stage = self.get_object()
        if request.user.role == 'student' and stage.thesis.student != request.user:
            return Response({'detail': 'Нет прав.'}, status=403)

        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'detail': 'Файл не передан.'}, status=400)

        file_name = request.data.get('file_name', file_obj.name)
        File.objects.create(stage=stage, file=file_obj, file_name=file_name, uploaded_by=request.user)
        
        # Меняем статус на "На проверке"
        stage.status = Stage.Status.SUBMITTED
        stage.save()
        
        notify(stage.thesis.supervisor, Notification.Type.STAGE, f'{request.user.get_full_name() or request.user.username} загрузил(а) файл на этап «{stage.get_type_display()}».', link='/supervisor/inbox')
        return Response({'status': 'ok', 'message': 'Файл загружен.'})

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def review(self, request, pk=None):
        """Создание отзыва руководителем."""
        stage = self.get_object()
        if request.user.role not in ('supervisor', 'admin'):
            return Response({'detail': 'Только для руководителей.'}, status=403)

        decision = request.data.get('decision')
        text = request.data.get('text')

        if not decision or not text:
            return Response({'detail': 'Нужны decision и text.'}, status=400)

        review = Review.objects.create(stage=stage, supervisor=request.user, decision=decision, text=text)

        old_status = stage.status
        if decision == 'approved':
            stage.status = Stage.Status.APPROVED
            next_stage = stage.thesis.stages.filter(order_index__gt=stage.order_index, status=Stage.Status.NOT_STARTED).first()
            if next_stage:
                next_stage.status = Stage.Status.IN_PROGRESS
                next_stage.save()
        else:
            stage.status = Stage.Status.NEEDS_REVISION
        
        stage.save()
        log_status('stage', stage.id, old_status, stage.status, request.user, text)
        log_action(request.user, f'Оставил(а) отзыв на этап {stage.get_type_display()}', 'stage', stage.id)
        notify(stage.thesis.student, Notification.Type.REVIEW, f'Руководитель оставил(а) отзыв на этап «{stage.get_type_display()}»: {decision}', link='/workspace')

        return Response(ReviewSerializer(review).data, status=201)

    @action(detail=True, methods=['get'], url_path='files/(?P<file_id>[^/.]+)/download')
    def download_file(self, request, pk=None, file_id=None):
        """Принудительное скачивание файла этапа."""
        stage = self.get_object()
        file_obj = get_object_or_404(File, id=file_id, stage=stage)

        response = FileResponse(
            file_obj.file.open('rb'),
            as_attachment=True,
            filename=file_obj.file_name
        )
        return response