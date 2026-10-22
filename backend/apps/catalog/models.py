from django.conf import settings
from django.db import models


class Direction(models.Model):
    """Направление подготовки (например, 09.03.04 Программная инженерия)."""

    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Код направления',
        help_text='Например: 09.03.04',
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Название направления',
        help_text='Например: Программная инженерия',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активно',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано',
    )

    class Meta:
        verbose_name = 'Направление подготовки'
        verbose_name_plural = 'Направления подготовки'
        ordering = ['code']

    def __str__(self):
        return f'{self.code} {self.title}'


class Topic(models.Model):
    """Тема ВКР, предлагаемая руководителем для выбора студентом."""

    class Status(models.TextChoices):
        FREE = 'free', 'Свободна'
        PENDING = 'pending', 'На согласовании'
        OCCUPIED = 'occupied', 'Занята'
        ARCHIVED = 'archived', 'В архиве'

    title = models.CharField(
        max_length=300,
        verbose_name='Название темы',
    )
    description = models.TextField(
        verbose_name='Описание',
    )
    requirements = models.TextField(
        blank=True,
        verbose_name='Требования к работе',
        help_text='Навыки, инструменты, ожидаемый результат',
    )
    tags = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Теги',
        help_text='Через запятую: веб, python, машинное обучение',
    )
    direction = models.ForeignKey(
        Direction,
        on_delete=models.PROTECT,
        related_name='topics',
        verbose_name='Направление подготовки',
    )
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='supervised_topics',
        verbose_name='Руководитель',
        limit_choices_to={'role': 'supervisor'},
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.FREE,
        verbose_name='Статус',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлено',
    )

    class Meta:
        verbose_name = 'Тема ВКР'
        verbose_name_plural = 'Темы ВКР'
        ordering = ['-created_at']

    def __str__(self):
        return self.title