"""
Core models for the bazary project.
"""

from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base model that provides self-updating
    'created_at' and 'updated_at' fields.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Abstract base model that provides soft delete functionality.
    """

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Soft delete the object."""
        from django.utils import timezone

        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(using=using)

    def hard_delete(self, using=None, keep_parents=False):
        """Permanently delete the object."""
        super().delete(using=using, keep_parents=keep_parents)


class BaseModel(TimeStampedModel, SoftDeleteModel):
    """
    Base model that combines timestamp and soft delete functionality.
    """

    class Meta:
        abstract = True
