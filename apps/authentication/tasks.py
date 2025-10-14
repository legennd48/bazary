from __future__ import annotations

from celery import shared_task
import logging
from django.db import transaction

from .models import EmailVerificationToken, PasswordResetToken, User
from .utils import send_password_reset_email, send_verification_email


logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def send_verification_email_task(self, user_id: str, token_id: int) -> bool:
    logger.info(
        "task.start", extra={"task": "send_verification_email", "user_id": user_id, "token_id": token_id, "attempt": self.request.retries + 1}
    )
    # Ensure DB commit is done before sending (especially if enqueued in on_commit)
    def _send() -> bool:
        user = User.objects.get(id=user_id)
        token = EmailVerificationToken.objects.get(id=token_id)
        sent = send_verification_email(user, token)
        logger.info(
            "task.success",
            extra={
                "task": "send_verification_email",
                "user_id": user_id,
                "token_id": token_id,
                "sent": sent,
            },
        )
        return sent

    if transaction.get_connection().in_atomic_block:
        # Shouldn't happen in worker, but guard just in case
        transaction.on_commit(_send)
        return True
    return _send()


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def send_password_reset_email_task(self, user_id: str, token_id: int) -> bool:
    logger.info(
        "task.start", extra={"task": "send_password_reset_email", "user_id": user_id, "token_id": token_id, "attempt": self.request.retries + 1}
    )
    def _send() -> bool:
        user = User.objects.get(id=user_id)
        token = PasswordResetToken.objects.get(id=token_id)
        sent = send_password_reset_email(user, token)
        logger.info(
            "task.success",
            extra={
                "task": "send_password_reset_email",
                "user_id": user_id,
                "token_id": token_id,
                "sent": sent,
            },
        )
        return sent

    if transaction.get_connection().in_atomic_block:
        transaction.on_commit(_send)
        return True
    return _send()
