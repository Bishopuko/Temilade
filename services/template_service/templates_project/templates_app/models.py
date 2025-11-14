from django.db import models

# Create your models here.
from django.db import models

class Template(models.Model):
    name = models.CharField(max_length=255)
    content = models.TextField()
    language = models.CharField(max_length=10, default='en')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class TemplateVersion(models.Model):
    template = models.ForeignKey(Template, related_name='versions', on_delete=models.CASCADE)
    version_number = models.IntegerField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

