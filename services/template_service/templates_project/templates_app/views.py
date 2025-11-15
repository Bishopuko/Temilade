from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from .models import Template
from .serializers import TemplateSerializer, TemplateVersionSerializer
from .processor import render_template
import time

class TemplateViewSet(viewsets.ModelViewSet):
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer
    lookup_field = "template_code"  # FIXED

    @action(detail=True, methods=['get'])
    def versions(self, request, template_code=None):
        template = self.get_object()
        serializer = TemplateVersionSerializer(template.versions.all(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def render(self, request, template_code=None):
        template = self.get_object()
        variables = request.data.get("variables", {})
        rendered = render_template(template.content, variables)
        return Response({"rendered": rendered})


@api_view(['GET'])
def health_check(request):
    return Response({
        'status': 'healthy',
        'service': 'template_service',
        'timestamp': time.time()
    }, status=status.HTTP_200_OK)
