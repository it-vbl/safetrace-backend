import logging

import django_rq
from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from penjualan.models import Lampiran
from utils.rq_jobs import run_thumbnail_job

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Lampiran)
def create_lampiran_thumbnails(sender, instance, **kwargs):
    """Automatically create thumbnails after save."""

    def _enqueue_thumbnail_job():
        try:
            queue = django_rq.get_queue('default')
            queue.enqueue(
                run_thumbnail_job,
                instance._meta.label,
                instance.pk,
                force=True,
            )
        except Exception as e:
            logger.error(f"Error enqueue thumbnail job: {e}")

    # Run in the background after the transaction commit to ensure the file has been saved
    transaction.on_commit(_enqueue_thumbnail_job)
