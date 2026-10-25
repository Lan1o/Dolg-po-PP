"""
Команда наполнения базы реалистичными демо-данными.
Запуск:
    python manage.py seed          # создать данные (если пусто)
    python manage.py seed --reset  # удалить и создать заново
"""
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User
from apps.catalog.models import Direction, Topic
from apps.workflow.models import Application, Thesis, Stage, File, Review
from apps.notifications.models import Notification, StatusHistory, ActionLog, Rating


class Command(BaseCommand):
    help = 'Наполняет базу реалистичными демо-данными CampusThesis'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Удалить старые данные')

    @transaction.atomic
    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Удаляю старые данные...')
            Rating.objects.all().delete()
            ActionLog.objects.all().delete()
            StatusHistory.objects.all().delete()
            Notification.objects.all().delete()
            Review.objects.all().delete()
            File.objects.all().delete()
            Stage.objects.all().delete()
            Thesis.objects.all().delete()
            Application.objects.all().delete()
            Topic.objects.all().delete()
            Direction.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        if User.objects.filter(is_superuser=False).exists():
            self.stdout.write(self.style.WARNING('Данные уже есть. Используй --reset.'))
            return

        self.stdout.write('Создаю направления...')
        directions = self._create_directions()

        self.stdout.write('Создаю руководителей...')
        supervisors = self._create_supervisors()

        self.stdout.write('Создаю студентов...')
        students = self._create_students()

        self.stdout.write('Создаю темы...')
        topics = self._create_topics(directions, supervisors)

        self.stdout.write('Создаю заявки...')
        applications = self._create_applications(students, topics)

        self.stdout.write('Создаю ВКР и этапы...')
        theses = self._create_theses(applications)

        self.stdout.write('Создаю отзывы, уведомления, рейтинги...')
        self._create_reviews_and_notifications(theses, students)

        self.stdout.write(self.style.SUCCESS('Демо-данные успешно созданы!'))

    def _create_directions(self):
        data = [
            ('09.03.04', 'Программная инженерия', 'Разработка ПО, архитектура, тестирование.'),
            ('09.03.02', 'Информационные системы и технологии', 'Проектирование ИС.'),
            ('09.03.01', 'Информатика и вычислительная техника', 'Алгоритмы, вычислительные системы.'),
            ('10.03.01', 'Информационная безопасность', 'Защита информации, криптография.'),
            ('01.03.02', 'Прикладная математика и информатика', 'Математические модели, ML.'),
        ]
        return [Direction.objects.create(code=c, title=t, description=d) for c, t, d in data]

    def _create_supervisors(self):
        data = [
            ('ivanov', 'Иван', 'Иванов', 'ivanov@campus.ru', 'Доцент кафедры ИТ'),
            ('petrova', 'Елена', 'Петрова', 'petrova@campus.ru', 'Профессор кафедры ПИ'),
            ('sidorov', 'Алексей', 'Сидоров', 'sidorov@campus.ru', 'Старший преподаватель'),
            ('kuznetsova', 'Мария', 'Кузнецова', 'kuznetsova@campus.ru', 'Доцент кафедры ИБ'),
            ('morozov', 'Дмитрий', 'Морозов', 'morozov@campus.ru', 'Заведующий кафедрой ПМИ'),
        ]
        return [User.objects.create_user(
            username=u, email=e, password='Supervisor2026!', 
            first_name=f, last_name=l, role=User.Role.SUPERVISOR, position=p
        ) for u, f, l, e, p in data]

    def _create_students(self):
        data = [
            ('smirnov', 'Андрей', 'Смирнов', 'smirnov@campus.ru', 'ИРИТ-РТФ-41'),
            ('volkova', 'Анна', 'Волкова', 'volkova@campus.ru', 'ИРИТ-РТФ-41'),
            ('kozlov', 'Никита', 'Козлов', 'kozlov@campus.ru', 'ИРИТ-РТФ-42'),
            ('lebedeva', 'Софья', 'Лебедева', 'lebedeva@campus.ru', 'ИРИТ-РТФ-42'),
            ('novikov', 'Максим', 'Новиков', 'novikov@campus.ru', 'ИРИТ-РТФ-43'),
            ('sokolova', 'Екатерина', 'Соколова', 'sokolova@campus.ru', 'ИРИТ-РТФ-43'),
            ('popov', 'Артём', 'Попов', 'popov@campus.ru', 'ИРИТ-РТФ-44'),
            ('fedorova', 'Дарья', 'Фёдорова', 'fedorova@campus.ru', 'ИРИТ-РТФ-44'),
            ('vasiliev', 'Григорий', 'Васильев', 'vasiliev@campus.ru', 'ИРИТ-РТФ-45'),
            ('pavlova', 'Ксения', 'Павлова', 'pavlova@campus.ru', 'ИРИТ-РТФ-45'),
            ('egorov', 'Илья', 'Егоров', 'egorov@campus.ru', 'ИРИТ-РТФ-46'),
            ('frolova', 'Анастасия', 'Фролова', 'frolova@campus.ru', 'ИРИТ-РТФ-46'),
        ]
        return [User.objects.create_user(
            username=u, email=e, password='Student2026!', 
            first_name=f, last_name=l, role=User.Role.STUDENT, group_name=g
        ) for u, f, l, e, g in data]

    def _create_topics(self, directions, supervisors):
        data = [
            ('Платформа управления ВКР', '09.03.04', 'ivanov', 'Сервис для управления ВКР.', 'Python, Django', 'веб, python'),
            ('Система рекомендаций курсов', '09.03.04', 'petrova', 'Рекомендательная система.', 'ML, scikit-learn', 'ml'),
            ('Мобильное приложение расписания', '09.03.02', 'sidorov', 'Кроссплатформенное приложение.', 'Flutter', 'мобильное'),
            ('Анализ защищённости веб-приложений', '10.03.01', 'kuznetsova', 'Аудит безопасности.', 'OWASP', 'безопасность'),
            ('Моделирование транспортных потоков', '01.03.02', 'morozov', 'Численные методы.', 'NumPy', 'математика'),
            ('Портал бронирования аудиторий', '09.03.02', 'sidorov', 'Веб-сервис бронирования.', 'Django, Postgres', 'веб'),
            ('Чат-бот поддержки студентов', '09.03.04', 'ivanov', 'Бот для ответов на вопросы.', 'Telegram API', 'бот'),
            ('Криптографический модуль подписи', '10.03.01', 'kuznetsova', 'Электронная подпись.', 'cryptography', 'криптография'),
            ('Визуализация успеваемости', '09.03.01', 'petrova', 'Дашборд с аналитикой.', 'Vue, D3.js', 'визуализация'),
            ('Система контроля версий', '09.03.04', 'morozov', 'Платформа для хранения проектов.', 'Go, Git', 'git'),
        ]
        res = []
        for title, d_code, s_user, desc, req, tags in data:
            d = next(x for x in directions if x.code == d_code)
            s = next(x for x in supervisors if x.username == s_user)
            res.append(Topic.objects.create(
                title=title, description=desc, requirements=req, tags=tags,
                direction=d, supervisor=s, status=Topic.Status.FREE
            ))
        return res

    def _create_applications(self, students, topics):
        # 3 одобрены, 1 на рассмотрении, 2 отклонены
        configs = [
            (students[0], topics[0], Application.Status.APPROVED),
            (students[1], topics[1], Application.Status.APPROVED),
            (students[2], topics[5], Application.Status.APPROVED),
            (students[3], topics[2], Application.Status.SUBMITTED),
            (students[4], topics[3], Application.Status.REJECTED),
            (students[5], topics[7], Application.Status.REJECTED),
        ]
        res = []
        for student, topic, status in configs:
            app = Application.objects.create(student=student, topic=topic, status=status, comment='Прошу закрепить тему.')
            if status == Application.Status.APPROVED:
                app.supervisor_comment = 'Согласовано.'
                app.decided_at = date.today() - timedelta(days=10)
                topic.status = Topic.Status.OCCUPIED
                topic.save()
            elif status == Application.Status.REJECTED:
                app.supervisor_comment = 'Тема занята.'
                app.decided_at = date.today() - timedelta(days=5)
            app.save()
            res.append(app)
        return res

    def _create_theses(self, applications):
        approved = [a for a in applications if a.status == Application.Status.APPROVED]
        stages_list = [
            Stage.Type.PLAN, Stage.Type.CHAPTER1, Stage.Type.CHAPTER2,
            Stage.Type.FULL_TEXT, Stage.Type.NORMCONTROL, Stage.Type.PREDEFENSE, Stage.Type.DEFENSE
        ]
        res = []
        for app in approved:
            thesis = Thesis.objects.create(
                student=app.student, topic=app.topic, supervisor=app.topic.supervisor
            )
            for i, st in enumerate(stages_list, start=1):
                Stage.objects.create(
                    thesis=thesis, type=st, status=Stage.Status.NOT_STARTED,
                    deadline=date.today() + timedelta(days=20*i), order_index=i
                )
            res.append(thesis)
        return res

    def _create_reviews_and_notifications(self, theses, students):
        if theses:
            thesis = theses[0]
            stages = list(thesis.stages.all())
            if len(stages) >= 2:
                plan = stages[0]
                plan.status = Stage.Status.APPROVED
                plan.save()
                Review.objects.create(
                    stage=plan, supervisor=thesis.supervisor,
                    text='План логичный, структура верная.', decision=Review.Decision.APPROVED
                )
                ch1 = stages[1]
                ch1.status = Stage.Status.SUBMITTED
                ch1.save()
                
                Rating.objects.create(supervisor=thesis.supervisor, student=thesis.student, score=5, comment='Отличный руководитель.')

        for student in students:
            Notification.objects.create(
                user=student, type=Notification.Type.SYSTEM,
                message='Добро пожаловать в CampusThesis! Выберите тему.', link='/catalog'
            )