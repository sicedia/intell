"""
Serializers for jobs app.
"""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from .models import Job, ImageTask, DescriptionTask, Tag, ImageGroup
from apps.audit.models import EventLog


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Tarea de imagen exitosa',
            value={
                'id': 1,
                'job': 1,
                'algorithm_key': 'patent_trends_cumulative',
                'algorithm_version': '1.0',
                'params': {'year_range': [2020, 2023]},
                'output_format': 'both',
                'status': 'SUCCESS',
                'progress': 100,
                'artifact_png_url': 'http://example.com/media/artifacts/png/image_1.png',
                'artifact_svg_url': 'http://example.com/media/artifacts/svg/image_1.svg',
                'chart_data': {'type': 'line', 'data': []},
                'error_code': None,
                'error_message': None,
                'trace_id': 'abc123',
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:05:00Z'
            }
        ),
    ]
)
class ImageTaskSerializer(serializers.ModelSerializer):
    """
    Serializer for ImageTask.
    
    Representa una tarea de generaci?n de imagen de gr?fico.
    Incluye URLs de artefactos generados y datos estructurados del gr?fico.
    """
    artifact_png_url = serializers.SerializerMethodField(
        help_text='URL del artefacto PNG generado'
    )
    artifact_svg_url = serializers.SerializerMethodField(
        help_text='URL del artefacto SVG generado'
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=False,
        help_text='Tags associated with this image'
    )
    group = serializers.PrimaryKeyRelatedField(
        queryset=ImageGroup.objects.all(),
        required=False,
        allow_null=True,
        help_text='Group this image belongs to'
    )
    created_by_username = serializers.SerializerMethodField(
        help_text='Username of the user who created this image'
    )
    created_by_email = serializers.SerializerMethodField(
        help_text='Email of the user who created this image'
    )
    
    def get_created_by_username(self, obj):
        """Get username of the user who created this image."""
        if obj.created_by:
            return obj.created_by.username
        # Fallback: try to get from job if created_by is not set
        if hasattr(obj, 'job') and obj.job and obj.job.created_by:
            return obj.job.created_by.username
        return None
    
    def get_created_by_email(self, obj):
        """Get email of the user who created this image."""
        if obj.created_by:
            return obj.created_by.email
        # Fallback: try to get from job if created_by is not set
        if hasattr(obj, 'job') and obj.job and obj.job.created_by:
            return obj.job.created_by.email
        return None
    
    class Meta:
        model = ImageTask
        fields = [
            'id', 'job', 'created_by', 'created_by_username', 'created_by_email',
            'algorithm_key', 'algorithm_version', 'params',
            'output_format', 'status', 'progress', 'artifact_png_url',
            'artifact_svg_url', 'chart_data', 'error_code', 'error_message',
            'trace_id', 'title', 'user_description', 'ai_context', 'group', 'tags',
            'is_published', 'published_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_by', 'created_by_username', 'created_by_email',
            'status', 'progress', 'artifact_png_url', 'artifact_svg_url',
            'chart_data', 'error_code', 'error_message', 'trace_id',
            'is_published', 'published_at', 'created_at', 'updated_at'
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


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Tarea de descripci?n exitosa',
            value={
                'id': 1,
                'image_task': 1,
                'user_context': 'Este gr?fico muestra tendencias de patentes',
                'provider_used': 'openai',
                'model_used': 'gpt-4',
                'status': 'SUCCESS',
                'progress': 100,
                'result_text': 'Este gr?fico muestra las tendencias acumulativas de patentes...',
                'prompt_snapshot': {'prompt': 'Describe este gr?fico...'},
                'error_code': None,
                'error_message': None,
                'trace_id': 'def456',
                'created_at': '2024-01-01T00:10:00Z',
                'updated_at': '2024-01-01T00:12:00Z'
            }
        ),
    ]
)
class DescriptionTaskSerializer(serializers.ModelSerializer):
    """
    Serializer for DescriptionTask.
    
    Representa una tarea de generaci?n de descripci?n con IA para un gr?fico.
    Incluye el texto generado, el proveedor y modelo utilizados, y el prompt enviado.
    """
    
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


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Event Log',
            value={
                'id': 1,
                'event_type': 'PROGRESS',
                'level': 'INFO',
                'message': 'Generating image...',
                'progress': 50,
                'created_at': '2024-01-01T00:00:00Z'
            }
        ),
    ]
)
class EventLogSerializer(serializers.ModelSerializer):
    """Serializer for EventLog."""
    progress = serializers.SerializerMethodField()

    class Meta:
        model = EventLog
        fields = ['id', 'event_type', 'level', 'message', 'progress', 'created_at', 'payload']
    
    def get_progress(self, obj):
        """Get progress from payload."""
        return obj.payload.get('progress', 0)


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Trabajo completo con tareas',
            value={
                'id': 1,
                'created_by': None,
                'dataset_id': 1,
                'status': 'SUCCESS',
                'progress_total': 100,
                'idempotency_key': 'unique-key-123',
                'image_tasks': [
                    {
                        'id': 1,
                        'algorithm_key': 'patent_trends_cumulative',
                        'status': 'SUCCESS',
                        'artifact_png_url': 'http://example.com/media/artifacts/png/image_1.png'
                    }
                ],
                'description_tasks': [
                    {
                        'id': 1,
                        'image_task': 1,
                        'status': 'SUCCESS',
                        'result_text': 'Descripci?n generada...'
                    }
                ],
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:15:00Z'
            }
        ),
    ]
)
class JobDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for Job detail view.
    
    Incluye todas las tareas de imagen y descripci?n asociadas al trabajo.
    """
    image_tasks = ImageTaskSerializer(
        many=True,
        read_only=True,
        help_text='Lista de tareas de imagen asociadas al trabajo'
    )
    images = serializers.SerializerMethodField(
        help_text='Alias for image_tasks (frontend compatibility)'
    )
    description_tasks = serializers.SerializerMethodField(
        help_text='Lista de tareas de descripci?n asociadas al trabajo'
    )
    dataset_id = serializers.IntegerField(
        source='dataset.id',
        read_only=True,
        help_text='ID del dataset asociado al trabajo'
    )
    source_type = serializers.SerializerMethodField(
        help_text='Source type from dataset (lens, espacenet_excel, custom)'
    )
    progress = serializers.IntegerField(
        source='progress_total',
        read_only=True,
        help_text='Overall progress (0-100), alias for progress_total'
    )
    events = EventLogSerializer(
        source='event_logs',
        many=True,
        read_only=True,
        help_text='Historial de eventos del trabajo'
    )
    
    class Meta:
        model = Job
        fields = [
            'id', 'created_by', 'dataset_id', 'status', 'progress_total', 'progress',
            'idempotency_key', 'image_tasks', 'images', 'description_tasks', 'events',
            'source_type', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'progress_total', 'progress', 'image_tasks', 'images',
            'description_tasks', 'events', 'source_type', 'created_at', 'updated_at'
        ]
    
    def get_images(self, obj):
        """Get images as alias for image_tasks (frontend compatibility)."""
        return ImageTaskSerializer(
            obj.image_tasks.all(),
            many=True,
            context=self.context
        ).data
    
    def get_source_type(self, obj):
        """Get source_type from dataset."""
        if obj.dataset:
            return obj.dataset.source_type
        return None
    
    def get_description_tasks(self, obj):
        """Get description tasks through image tasks."""
        from apps.jobs.models import DescriptionTask
        description_tasks = DescriptionTask.objects.filter(
            image_task__job=obj
        ).select_related('image_task')
        return DescriptionTaskSerializer(description_tasks, many=True, context=self.context).data


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Ejemplo de tarea de imagen',
            value={
                'algorithm_key': 'patent_trends_cumulative',
                'algorithm_version': '1.0',
                'params': {
                    'year_range': [2020, 2023],
                    'group_by': 'year'
                },
                'output_format': 'both'
            }
        ),
    ]
)
class ImageTaskRequestSerializer(serializers.Serializer):
    """Serializer for image task request in job creation."""
    algorithm_key = serializers.CharField(
        help_text='Identificador del algoritmo a utilizar (ej: patent_trends_cumulative, patent_evolution)'
    )
    algorithm_version = serializers.CharField(
        default='1.0',
        help_text='Versión del algoritmo a utilizar'
    )
    params = serializers.DictField(
        help_text='Parámetros específicos del algoritmo en formato JSON'
    )
    output_format = serializers.ChoiceField(
        choices=ImageTask.OutputFormat.choices,
        default=ImageTask.OutputFormat.BOTH,
        help_text='Formato de salida: png, svg o both'
    )
    
    def validate(self, attrs):
        """Validate that algorithm exists in registry."""
        from apps.algorithms.registry import AlgorithmRegistry
        
        algorithm_key = attrs.get('algorithm_key')
        algorithm_version = attrs.get('algorithm_version', '1.0')
        
        registry = AlgorithmRegistry()
        algorithm = registry.get(algorithm_key, algorithm_version)
        
        if algorithm is None:
            raise serializers.ValidationError({
                'algorithm_key': f"Algorithm '{algorithm_key}' version '{algorithm_version}' not found in registry. "
                                 f"Available algorithms: {list(registry.list_algorithms().keys())}"
            })
        
        return attrs


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Crear trabajo con Lens',
            value={
                'source_type': 'lens',
                'source_params': {
                    'query': 'artificial intelligence',
                    'date_published': '2020-01-01',
                    'jurisdiction': 'EP'
                },
                'images': [
                    {
                        'algorithm_key': 'patent_trends_cumulative',
                        'algorithm_version': '1.0',
                        'params': {},
                        'output_format': 'both'
                    }
                ],
                'idempotency_key': 'unique-key-123'
            }
        ),
        OpenApiExample(
            'Crear trabajo con Excel',
            value={
                'source_type': 'espacenet_excel',
                'source_data': '<archivo_excel>',
                'images': [
                    {
                        'algorithm_key': 'patent_evolution',
                        'algorithm_version': '1.0',
                        'params': {'year_range': [2020, 2023]},
                        'output_format': 'png'
                    }
                ]
            }
        ),
    ]
)
class JobCreateSerializer(serializers.Serializer):
    """Serializer for job creation."""
    source_type = serializers.ChoiceField(
        choices=['lens', 'espacenet_excel', 'custom'],
        help_text='Tipo de fuente de datos: lens (Lens API), espacenet_excel (archivo Excel de Espacenet), o custom'
    )
    source_data = serializers.FileField(
        required=False,
        help_text='Archivo Excel de Espacenet (requerido si source_type es espacenet_excel)'
    )
    source_params = serializers.DictField(
        required=False,
        help_text='Par?metros para la consulta a Lens API (requerido si source_type es lens)'
    )
    images = ImageTaskRequestSerializer(
        many=True,
        help_text='Lista de tareas de imagen a generar'
    )
    idempotency_key = serializers.CharField(
        required=False,
        allow_null=True,
        help_text='Clave de idempotencia para prevenir duplicados (opcional)'
    )
    visualization_config = serializers.DictField(
        required=False,
        allow_null=True,
        help_text='Configuracion de visualizacion para todas las graficas (color_palette, font_size, custom_params)'
    )
    
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


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Generar descripci?n con contexto',
            value={
                'image_task_id': 1,
                'user_context': 'Este gr?fico muestra tendencias de patentes en inteligencia artificial durante los ?ltimos 5 a?os',
                'provider_preference': 'openai'
            }
        ),
        OpenApiExample(
            'Generar descripci?n b?sica',
            value={
                'image_task_id': 1,
                'provider_preference': 'anthropic'
            }
        ),
    ]
)
class AIDescribeRequestSerializer(serializers.Serializer):
    """Serializer for AI describe request."""
    image_task_id = serializers.IntegerField(
        help_text='ID de la tarea de imagen para la cual generar la descripción'
    )
    user_context = serializers.CharField(
        required=True,
        allow_blank=True,
        help_text='Contexto adicional proporcionado por el usuario para mejorar la descripción'
    )
    provider_preference = serializers.ChoiceField(
        choices=['litellm', 'openai', 'anthropic', 'mock'],
        required=False,
        help_text='Proveedor de IA preferido: litellm, openai, anthropic, o mock (para pruebas). Si se especifica model_preference, este campo se ignora.'
    )
    model_preference = serializers.CharField(
        required=False,
        allow_blank=False,
        help_text='Modelo específico de LiteLLM a usar (ej: openai/gpt-5.2-chat-latest, gemini/gemini-3-flash-preview). Si se especifica, tiene prioridad sobre provider_preference.'
    )
    
    def validate_model_preference(self, value):
        """Validate that model_preference is a valid LiteLLM model."""
        if value:
            from apps.ai_descriptions.providers import LITELLM_MODELS
            if value not in LITELLM_MODELS:
                raise serializers.ValidationError(
                    f"Model '{value}' is not available. Available models: {', '.join(LITELLM_MODELS[:5])}..."
                )
        return value


# Response serializers for API documentation
@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Trabajo creado exitosamente',
            value={
                'job_id': 1,
                'status': 'PENDING',
                'message': 'Job created and enqueued'
            }
        ),
    ]
)
class JobCreateResponseSerializer(serializers.Serializer):
    """Response serializer for job creation."""
    job_id = serializers.IntegerField(help_text='ID del trabajo creado')
    status = serializers.CharField(help_text='Estado actual del trabajo')
    message = serializers.CharField(help_text='Mensaje descriptivo')


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Trabajo cancelado',
            value={
                'job_id': 1,
                'status': 'CANCELLED',
                'message': 'Job cancelled'
            }
        ),
    ]
)
class JobCancelResponseSerializer(serializers.Serializer):
    """Response serializer for job cancellation."""
    job_id = serializers.IntegerField(help_text='ID del trabajo cancelado')
    status = serializers.CharField(help_text='Estado del trabajo después de cancelar')
    message = serializers.CharField(help_text='Mensaje descriptivo')


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Tarea de descripción creada',
            value={
                'description_task_id': 1,
                'status': 'PENDING',
                'message': 'Description task created and enqueued',
                'provider_preference': 'openai'
            }
        ),
    ]
)
class AIDescribeResponseSerializer(serializers.Serializer):
    """Response serializer for AI describe request."""
    description_task_id = serializers.IntegerField(help_text='ID de la tarea de descripción creada')
    status = serializers.CharField(help_text='Estado actual de la tarea')
    message = serializers.CharField(help_text='Mensaje descriptivo')
    provider_preference = serializers.CharField(
        required=False,
        allow_null=True,
        help_text='Proveedor de IA que se utilizará'
    )


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Error de validación',
            value={
                'error': 'source_data is required for espacenet_excel'
            }
        ),
        OpenApiExample(
            'Error de servidor',
            value={
                'error': 'Internal server error message'
            }
        ),
    ]
)
class ErrorResponseSerializer(serializers.Serializer):
    """Response serializer for error responses."""
    error = serializers.CharField(help_text='Mensaje de error descriptivo')


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Tag example',
            value={
                'id': 1,
                'name': 'patents',
                'color': '#6366f1',
                'created_by': 1,
                'created_at': '2024-01-01T00:00:00Z'
            }
        ),
    ]
)
class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag."""
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'created_by', 'created_at']
        read_only_fields = ['id', 'created_at']


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'ImageGroup example',
            value={
                'id': 1,
                'name': 'Q1 2024 Analysis',
                'description': 'All charts from Q1 2024 analysis',
                'created_by': 1,
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z'
            }
        ),
    ]
)
class ImageGroupSerializer(serializers.ModelSerializer):
    """Serializer for ImageGroup."""
    image_count = serializers.SerializerMethodField(
        help_text='Number of images in this group'
    )
    
    class Meta:
        model = ImageGroup
        fields = ['id', 'name', 'description', 'created_by', 'image_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'image_count', 'created_at', 'updated_at']
    
    def get_image_count(self, obj):
        """Get count of images in this group."""
        return obj.images.count()


class ImageTaskUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating ImageTask metadata."""
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=False,
        help_text='Tags associated with this image'
    )
    
    class Meta:
        model = ImageTask
        fields = ['title', 'user_description', 'group', 'tags']
    
    def validate_group(self, value):
        """Ensure user owns the group."""
        if value and self.context.get('request'):
            user = self.context['request'].user
            if value.created_by != user:
                raise serializers.ValidationError("You can only assign images to your own groups.")
        return value


class ImageLibrarySerializer(serializers.ModelSerializer):
    """
    Optimized serializer for image library listing.
    Includes only essential fields for gallery view.
    """
    artifact_png_url = serializers.SerializerMethodField()
    artifact_svg_url = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    job_id = serializers.IntegerField(source='job.id', read_only=True)
    created_by_username = serializers.SerializerMethodField(
        help_text='Username of the user who created this image'
    )
    created_by_email = serializers.SerializerMethodField(
        help_text='Email of the user who created this image'
    )
    
    def get_created_by_username(self, obj):
        """Get username of the user who created this image."""
        if obj.created_by:
            return obj.created_by.username
        # Fallback: try to get from job if created_by is not set
        if hasattr(obj, 'job') and obj.job and obj.job.created_by:
            return obj.job.created_by.username
        return None
    
    def get_created_by_email(self, obj):
        """Get email of the user who created this image."""
        if obj.created_by:
            return obj.created_by.email
        # Fallback: try to get from job if created_by is not set
        if hasattr(obj, 'job') and obj.job and obj.job.created_by:
            return obj.job.created_by.email
        return None
    
    class Meta:
        model = ImageTask
        fields = [
            'id', 'job_id', 'created_by', 'created_by_username', 'created_by_email',
            'title', 'algorithm_key', 'status',
            'artifact_png_url', 'artifact_svg_url', 'user_description', 'ai_context',
            'tags', 'group', 'group_name', 'is_published', 'published_at',
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

