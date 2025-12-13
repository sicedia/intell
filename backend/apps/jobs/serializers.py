"""
Serializers for jobs app.
"""
from rest_framework import serializers
from .models import Job, ImageTask, DescriptionTask
from apps.datasets.models import Dataset


class ImageTaskSerializer(serializers.ModelSerializer):
    """Serializer for ImageTask."""
    artifact_png_url = serializers.SerializerMethodField()
    artifact_svg_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ImageTask
        fields = [
            'id', 'job', 'algorithm_key', 'algorithm_version', 'params',
            'output_format', 'status', 'progress', 'artifact_png_url',
            'artifact_svg_url', 'chart_data', 'error_code', 'error_message',
            'trace_id', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'progress', 'artifact_png_url', 'artifact_svg_url',
            'chart_data', 'error_code', 'error_message', 'trace_id',
            'created_at', 'updated_at'
        ]
    
    def get_artifact_png_url(self, obj):
        """Get PNG artifact URL."""
        if obj.artifact_png:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.artifact_png.url)
            return obj.artifact_png.url
        return None
    
    def get_artifact_svg_url(self, obj):
        """Get SVG artifact URL."""
        if obj.artifact_svg:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.artifact_svg.url)
            return obj.artifact_svg.url
        return None


class DescriptionTaskSerializer(serializers.ModelSerializer):
    """Serializer for DescriptionTask."""
    
    class Meta:
        model = DescriptionTask
        fields = [
            'id', 'image_task', 'user_context', 'provider_used', 'model_used',
            'status', 'progress', 'result_text', 'prompt_snapshot',
            'error_code', 'error_message', 'trace_id', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'provider_used', 'model_used', 'status', 'progress',
            'result_text', 'prompt_snapshot', 'error_code', 'error_message',
            'trace_id', 'created_at', 'updated_at'
        ]


class JobDetailSerializer(serializers.ModelSerializer):
    """Serializer for Job detail view."""
    image_tasks = ImageTaskSerializer(many=True, read_only=True)
    description_tasks = serializers.SerializerMethodField()
    dataset_id = serializers.IntegerField(source='dataset.id', read_only=True)
    
    class Meta:
        model = Job
        fields = [
            'id', 'created_by', 'dataset_id', 'status', 'progress_total',
            'idempotency_key', 'image_tasks', 'description_tasks',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'progress_total', 'image_tasks', 'description_tasks',
            'created_at', 'updated_at'
        ]
    
    def get_description_tasks(self, obj):
        """Get description tasks through image tasks."""
        from apps.jobs.models import DescriptionTask
        description_tasks = DescriptionTask.objects.filter(
            image_task__job=obj
        ).select_related('image_task')
        return DescriptionTaskSerializer(description_tasks, many=True, context=self.context).data


class ImageTaskRequestSerializer(serializers.Serializer):
    """Serializer for image task request in job creation."""
    algorithm_key = serializers.CharField()
    algorithm_version = serializers.CharField(default='1.0')
    params = serializers.DictField()
    output_format = serializers.ChoiceField(
        choices=ImageTask.OutputFormat.choices,
        default=ImageTask.OutputFormat.BOTH
    )


class JobCreateSerializer(serializers.Serializer):
    """Serializer for job creation."""
    source_type = serializers.ChoiceField(
        choices=['lens', 'espacenet_excel', 'custom']
    )
    source_data = serializers.FileField(required=False)
    source_params = serializers.DictField(required=False)
    images = ImageTaskRequestSerializer(many=True)
    idempotency_key = serializers.CharField(required=False, allow_null=True)
    
    def validate(self, attrs):
        """Validate that source_data or source_params is provided."""
        source_type = attrs.get('source_type')
        source_data = attrs.get('source_data')
        source_params = attrs.get('source_params')
        
        if source_type == 'espacenet_excel' and not source_data:
            raise serializers.ValidationError(
                "source_data is required for espacenet_excel"
            )
        if source_type == 'lens' and not source_params:
            raise serializers.ValidationError(
                "source_params is required for lens"
            )
        
        return attrs


class AIDescribeRequestSerializer(serializers.Serializer):
    """Serializer for AI describe request."""
    image_task_id = serializers.IntegerField()
    user_context = serializers.CharField(required=False, allow_blank=True)
    provider_preference = serializers.ChoiceField(
        choices=['openai', 'anthropic', 'mock'],
        required=False
    )

