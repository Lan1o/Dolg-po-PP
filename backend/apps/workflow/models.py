from django.conf import settings
from django.db import models

from apps.catalog.models import Topic


class Application(models.Model):
    """Заявка студента на выбранную тему ВКР."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Черновик'
        SUBMITTED = 'submitted', 'Подана'
        UNDER_REVIEW = 'under_review', 'На рассмотрении'
        APPROVED = 'approved', 'Одобрена'
        REJECTED = 'rejected', 'Отклонена'

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='Студент',
        limit_choices_to={'role': 'student'},
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.PROTECT,
        related_name='applications',
        verbose_name='Тема',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
        verbose_name='Статус',
    )
    comment = models.TextField(
        blank=True,
        verbose_name='Комментарий студента',
    )
    supervisor_comment = models.TextField(
        blank=True,
        verbose_name='Комментарий руководителя',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Подана',
    )
    decided_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Решение принято',
    )

    class Meta:
        verbose_name = 'Заявка на тему'
        verbose_name_plural = 'Заявки на темы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заявка {self.student} → {self.topic}'


class Thesis(models.Model):
    """Работа студента над выбранной темой (создаётся после одобрения заявки)."""

    class Status(models.TextChoices):
        ACTIVE = 'active', 'В работе'
        ON_NORMCONTROL = 'on_normcontrol', 'На нормоконтроле'
        PREDEFENSE = 'predefense', 'Предзащита'
        DEFENDED = 'defended', 'Защищена'

    student = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='thesis',
        verbose_name='Студент',
    )
    topic = models.OneToOneField(
        Topic,
        on_delete=models.PROTECT,
        related_name='thesis',
        verbose_name='Тема',
    )
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='supervised_theses',
        verbose_name='Руководитель',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='Статус',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создана',
    )

    class Meta:
        verbose_name = 'ВКР'
        verbose_name_plural = 'ВКР'
        ordering = ['-created_at']

    def __str__(self):
        return f'ВКР: {self.student} — {self.topic.title}'


class Stage(models.Model):
    """Этап работы над ВКР с дедлайном и статусом."""

    class Type(models.TextChoices):
        PLAN = 'plan', 'План'
        CHAPTER1 = 'chapter1', 'Первая глава'
        CHAPTER2 = 'chapter2', 'Вторая глава'
        FULL_TEXT = 'full_text', 'Полный текст'
        NORMCONTROL = 'normcontrol', 'Нормоконтроль'
        PREDEFENSE = 'predefense', 'Предзащита'
        DEFENSE = 'defense', 'Защита'

    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', 'Не начат'
        IN_PROGRESS = 'in_progress', 'В работе'
        SUBMITTED = 'submitted', 'На проверке'
        APPROVED = 'approved', 'Одобрен'
        NEEDS_REVISION = 'needs_revision', 'Доработать'

    thesis = models.ForeignKey(
        Thesis,
        on_delete=models.CASCADE,
        related_name='stages',
        verbose_name='ВКР',
    )
    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        verbose_name='Тип этапа',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED,
        verbose_name='Статус',
    )
    deadline = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дедлайн',
    )
    order_index = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Порядковый номер',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создан',
    )

    class Meta:
        verbose_name = 'Этап ВКР'
        verbose_name_plural = 'Этапы ВКР'
        ordering = ['order_index']

    def __str__(self):
        return f'{self.get_type_display()} ({self.thesis})'


class File(models.Model):
    """Загруженный файл этапа ВКР."""

    stage = models.ForeignKey(
        Stage,
        on_delete=models.CASCADE,
        related_name='files',
        verbose_name='Этап',
    )
    file = models.FileField(
        upload_to='stages/%Y/%m/',
        verbose_name='Файл',
    )
    file_name = models.CharField(
        max_length=255,
        verbose_name='Имя файла',
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_files',
        verbose_name='Загрузил',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Загружен',
    )

    class Meta:
        verbose_name = 'Файл этапа'
        verbose_name_plural = 'Файлы этапов'
        ordering = ['-created_at']

    def __str__(self):
        return self.file_name


class Review(models.Model):
    """Отзыв руководителя по этапу ВКР."""

    class Decision(models.TextChoices):
        APPROVED = 'approved', 'Одобрено'
        NEEDS_REVISION = 'needs_revision', 'Доработать'

    stage = models.ForeignKey(
        Stage,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Этап',
    )
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='given_reviews',
        verbose_name='Руководитель',
    )
    text = models.TextField(
        verbose_name='Текст отзыва',
    )
    decision = models.CharField(
        max_length=20,
        choices=Decision.choices,
        verbose_name='Решение',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создан',
    )

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_decision_display()} — {self.stage}'