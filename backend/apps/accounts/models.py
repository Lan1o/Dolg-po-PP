from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Кастомная модель пользователя с ролью в системе CampusThesis."""

    class Role(models.TextChoices):
        STUDENT = 'student', 'Студент'
        SUPERVISOR = 'supervisor', 'Руководитель'
        ADMIN = 'admin', 'Администратор'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        verbose_name='Роль',
    )
    group_name = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Учебная группа',
        help_text='Только для студентов, например: ИРИТ-РТФ-41',
    )
    position = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Должность',
        help_text='Только для руководителей, например: доцент кафедры ИТ',
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'