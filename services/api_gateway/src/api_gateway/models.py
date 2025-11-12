from django.db import models
from django.utils import timezone
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


class NotificationStatus(str, Enum):
    delivered = "delivered"
    pending = "pending"
    failed = "failed"


@dataclass
class NotificationStatusData:
    notification_id: str
    status: NotificationStatus
    timestamp: Optional[datetime] = None
    error: Optional[str] = None


class Notification(models.Model):
    """Persistent storage for notification status tracking"""
    notification_id = models.CharField(max_length=255, unique=True, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.value) for status in NotificationStatus],
        default=NotificationStatus.pending.value
    )
    user_id = models.CharField(max_length=255, db_index=True)
    notification_type = models.CharField(max_length=50)  # email, push
    template_code = models.CharField(max_length=255)
    variables = models.JSONField(default=dict)
    priority = models.IntegerField(default=1)
    metadata = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user_id', 'status']),
        ]

    def __str__(self):
        return f"{self.notification_id} - {self.status}"

    def to_dataclass(self) -> NotificationStatusData:
        """Convert model instance to dataclass for backward compatibility"""
        return NotificationStatusData(
            notification_id=self.notification_id,
            status=NotificationStatus(self.status),
            timestamp=self.updated_at,
            error=self.error_message
        )
