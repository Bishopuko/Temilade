from rest_framework import serializers
from .models import Template, TemplateVersion

class TemplateVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateVersion
        fields = "__all__"


class TemplateSerializer(serializers.ModelSerializer):
    versions = TemplateVersionSerializer(many=True, read_only=True)

    class Meta:
        model = Template
        fields = [
            "template_code",
            "name",
            "content",
            "language",
            "created_at",
            "updated_at",
            "versions"
        ]

    def update(self, instance, validated_data):
        # Save template update
        instance = super().update(instance, validated_data)

        # Create new template version
        TemplateVersion.objects.create(
            template=instance,
            version_number=instance.latest_version_number() + 1,
            content=instance.content,
        )
        return instance
