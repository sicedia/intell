"""
Serializers for jobs app.
"""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from .models import Job, ImageTask, DescriptionTask


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
    description_tasks = serializers.SerializerMethodField(
        help_text='Lista de tareas de descripci?n asociadas al trabajo'
    )
    dataset_id = serializers.IntegerField(
        source='dataset.id',
        read_only=True,
        help_text='ID del dataset asociado al trabajo'
    )
    
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
        help_text='Versi?n del algoritmo a utilizar'
    )
    params = serializers.DictField(
        help_text='Par?metros espec?ficos del algoritmo en formato JSON'
    )
    output_format = serializers.ChoiceField(
        choices=ImageTask.OutputFormat.choices,
        default=ImageTask.OutputFormat.BOTH,
        help_text='Formato de salida: png, svg o both'
    )


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
        help_text='ID de la tarea de imagen para la cual generar la descripci?n'
    )
    user_context = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Contexto adicional proporcionado por el usuario para mejorar la descripci?n'
    )
    provider_preference = serializers.ChoiceField(
        choices=['openai', 'anthropic', 'mock'],
        required=False,
        help_text='Proveedor de IA preferido: openai, anthropic, o mock (para pruebas)'
    )


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

