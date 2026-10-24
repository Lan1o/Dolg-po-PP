from .models import Notification, StatusHistory, ActionLog


def notify(user, type_, message, link=''):
    """Создаёт уведомление пользователю."""
    return Notification.objects.create(
        user=user,
        type=type_,
        message=message,
        link=link,
    )


def log_status(entity_type, entity_id, from_status, to_status, changed_by, comment=''):
    """Записывает изменение статуса в историю."""
    return StatusHistory.objects.create(
        entity_type=entity_type,
        entity_id=entity_id,
        from_status=from_status or '',
        to_status=to_status,
        changed_by=changed_by,
        comment=comment,
    )


def log_action(user, action, entity_type='', entity_id=None):
    """Записывает действие пользователя в лог."""
    return ActionLog.objects.create(
        user=user,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
    )