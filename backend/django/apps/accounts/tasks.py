from celery import shared_task

from apps.accounts.sessions import purge_expired_session_history


@shared_task(queue="retention")
def purge_session_history_task():
    return purge_expired_session_history()
