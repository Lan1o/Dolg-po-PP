from django.conf import settings
from django.db import models


class Notification(models.Model):
    """Уведомление пользователю о событиях в системе."""

    class Type(models.TextChoices):
        APPLICATION = 'application', 'Заявка'
        STAGE = 'stage', 'Этап ВКР'
        REVIEW = 'review', 'Отзыв'
        DEADLINE = 'deadline', 'Дедлайн'
        SYSTEM = 'system', 'Системное'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Получатель',
    )
    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.SYSTEM,
        verbose_name='Тип',
    )
    message = models.TextField(
        verbose_name='Текст уведомления',
    )
    link = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Ссылка',
        help_text='Относительный путь во фронтенде, например /workspace',
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='Прочитано',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано',
    )

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.get_type_display()}'


class StatusHistory(models.Model):
    """История изменения статусов сущностей (заявка, этап, ВКР)."""

    entity_type = models.CharField(
        max_length=50,
        verbose_name='Тип сущности',
        help_text='application / thesis / stage',
    )
    entity_id = models.PositiveIntegerField(
        verbose_name='ID сущности',
    )
    from_status = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Из статуса',
    )
    to_status = models.CharField(
        max_length=30,
        verbose_name='В статус',
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='status_changes',
        verbose_name='Кто изменил',
    )
    comment = models.TextField(
        blank=True,
        verbose_name='Комментарий',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Когда',
    )

    class Meta:
        verbose_name = 'История статуса'
        verbose_name_plural = 'История статусов'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
        ]

    def __str__(self):
        return f'{self.entity_type}#{self.entity_id}: {self.from_status} → {self.to_status}'


class ActionLog(models.Model):
    """Лог действий пользователей для личного кабинета и аудита."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='actions',
        verbose_name='Пользователь',
    )
    action = models.CharField(
        max_length=100,
        verbose_name='Действие',
        help_text='Например: подал заявку, загрузил файл, оставил отзыв',
    )
    entity_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Тип сущности',
    )
    entity_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='ID сущности',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Когда',
    )

    class Meta:
        verbose_name = 'Действие пользователя'
        verbose_name_plural = 'Действия пользователей'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.action}'


class Rating(models.Model):
    """Оценка руководителя студентом после завершения работы."""

    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_ratings',
        verbose_name='Руководитель',
        limit_choices_to={'role': 'supervisor'},
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='given_ratings',
        verbose_name='Студент',
        limit_choices_to={'role': 'student'},
    )
    score = models.PositiveSmallIntegerField(
        verbose_name='Оценка',
        help_text='От 1 до 5',
    )
    comment = models.TextField(
        blank=True,
        verbose_name='Комментарий',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано',
    )

    class Meta:
        verbose_name = 'Оценка руководителя'
        verbose_name_plural = 'Оценки руководителей'
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(score__gte=1) & models.Q(score__lte=5),
                name='rating_score_1_5',
            ),
        ]

    def __str__(self):
        return f'{self.student} → {self.supervisor}: {self.score}/5'