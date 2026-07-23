import logging

from django.apps import apps

logger = logging.getLogger(__name__)


def run_thumbnail_job(model_label, instance_pk, force=True):
    """
    Run thumbnail generation by loading model instance inside worker process.
    """
    
    model_cls = apps.get_model(model_label)
    if model_cls is None:
        logger.error("Thumbnail job skipped: model not found (%s)", model_label)
        return

    instance = model_cls.objects.filter(pk=instance_pk).first()
    if instance is None:
        logger.warning(
            "Thumbnail job skipped: instance not found (%s:%s)",
            model_label,
            instance_pk,
        )
        return

    try:
        instance.create_thumbnails(force=force)
    except Exception as exc:
        logger.exception(
            "Thumbnail job failed for %s:%s (%s)",
            model_label,
            instance_pk,
            exc,
        )
        raise
