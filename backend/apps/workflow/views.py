from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import PermissionDenied

from apps.catalog.models import Topic
from apps.notifications.models import Notification, ActionLog
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
        
        if Thesis.objects.filter(student=user).exists():
            raise PermissionDenied('У вас уже есть активная ВКР. Вы не можете подать новую заявку.')
            
        topic = serializer.validated_data['topic']
        if topic.status != Topic.Status.FREE:
            raise PermissionDenied('Тема уже занята или на согласовании.')
            
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


class ThesisViewSet(viewsets.ModelViewSet):
    serializer_class = ThesisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'student':
            return Thesis.objects.filter(student=user).prefetch_related('stages')
        if user.role == 'supervisor':
            return Thesis.objects.filter(supervisor=user).prefetch_related('stages')
        return Thesis.objects.all().prefetch_related('stages')

    def update(self, request, *args, **kwargs):
        thesis = self.get_object()
        
        # Проверка прав: либо руководитель, либо сам студент
        if request.user != thesis.supervisor and request.user != thesis.student and request.user.role != 'admin':
            return Response({'detail': 'Нет прав на редактирование.'}, status=403)
        
        thesis.description = request.data.get('description', thesis.description)
        thesis.relevance = request.data.get('relevance', thesis.relevance)
        thesis.goal = request.data.get('goal', thesis.goal)
        thesis.expected_result = request.data.get('expected_result', thesis.expected_result)
        thesis.save()
        
        return Response(self.get_serializer(thesis).data)

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
    parser_classes = (MultiPartParser, FormParser, JSONParser)

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
        
        stage.status = Stage.Status.SUBMITTED
        stage.save()
        
        notify(stage.thesis.supervisor, Notification.Type.STAGE, f'{request.user.get_full_name() or request.user.username} загрузил(а) файл на этап «{stage.get_type_display()}».', link='/supervisor/inbox')
        return Response({'status': 'ok', 'message': 'Файл загружен.'})

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def review(self, request, pk=None):
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
        stage = self.get_object()
        file_obj = get_object_or_404(File, id=file_id, stage=stage)

        response = FileResponse(
            file_obj.file.open('rb'),
            as_attachment=True,
            filename=file_obj.file_name
        )
        return response

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        stage = self.get_object()
        reviews = stage.reviews.all().order_by('-created_at')
        data = [
            {
                'id': r.id,
                'text': r.text,
                'decision': r.decision,
                'created_at': r.created_at,
                'supervisor': r.supervisor.get_full_name() or r.supervisor.username
            } for r in reviews
        ]
        return Response(data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def student_history(request, thesis_id):
    """Получение истории действий по ВКР (доступно руководителю и самому студенту)."""
    try:
        if request.user.role == 'supervisor':
            thesis = Thesis.objects.get(id=thesis_id, supervisor=request.user)
        else:
            thesis = Thesis.objects.get(id=thesis_id, student=request.user)
    except Thesis.DoesNotExist:
        return Response({'detail': 'ВКР не найдена или нет прав.'}, status=404)

    logs = ActionLog.objects.filter(user=thesis.student).order_by('-created_at')
    
    data = [
        {
            'id': log.id,
            'action': log.action,
            'entity_type': log.entity_type,
            'entity_id': log.entity_id,
            'created_at': log.created_at
        } for log in logs
    ]
    return Response(data)