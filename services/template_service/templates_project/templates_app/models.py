from django.db import models
import uuid

class Template(models.Model):
    template_code = models.CharField(max_length=100, unique=True, default="new_template_code")
    name = models.CharField(max_length=255)
    content = models.TextField()
    language = models.CharField(max_length=10, default='en')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def latest_version_number(self):
        last = self.versions.order_by('-version_number').first()
        return last.version_number if last else 0


class TemplateVersion(models.Model):
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(Template, related_name='versions', on_delete=models.CASCADE)
    version_number = models.IntegerField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
