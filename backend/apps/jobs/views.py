"""
API views for jobs app.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample

from .models import Job, ImageTask, DescriptionTask
from .serializers import (
    JobCreateSerializer, JobDetailSerializer,
    ImageTaskSerializer, DescriptionTaskSerializer,
    AIDescribeRequestSerializer,
    JobCreateResponseSerializer, JobCancelResponseSerializer,
    AIDescribeResponseSerializer, ErrorResponseSerializer
)
from apps.datasets.normalizers import normalize, normalize_from_excel
from apps.ingestion.connectors import LensConnector
from apps.jobs.tasks import run_job
from apps.ai_descriptions.tasks import generate_description_task


@extend_schema_view(
    create=extend_schema(
        summary='Crear un nuevo trabajo',
        description='Crea un nuevo trabajo de generación de gráficos. El trabajo puede obtener datos desde Lens API o desde un archivo Excel de Espacenet.',
        tags=['Jobs'],
        request=JobCreateSerializer,
        responses={
            201: JobCreateResponseSerializer,
            200: JobCreateResponseSerializer,
            400: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                'Ejemplo con Lens',
                value={
                    'source_type': 'lens',
                    'source_params': {
                        'query': 'artificial intelligence',
                        'date_published': '2020-01-01',
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
                },
                request_only=True,
            ),
            OpenApiExample(
                'Ejemplo con Excel',
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
                },
                request_only=True,
            ),
        ],
    ),
    retrieve=extend_schema(
        summary='Obtener detalles de un trabajo',
        description='Obtiene los detalles completos de un trabajo, incluyendo todas sus tareas de imagen y descripción.',
        tags=['Jobs'],
        responses={
            200: JobDetailSerializer,
            404: ErrorResponseSerializer,
        },
    ),
    cancel=extend_schema(
        summary='Cancelar un trabajo',
        description='Cancela un trabajo en ejecución o pendiente.',
        tags=['Jobs'],
        responses={
            200: JobCancelResponseSerializer,
            404: ErrorResponseSerializer,
        },
    ),
)
class JobViewSet(viewsets.ViewSet):
    """ViewSet for Job operations."""
    
    def create(self, request):
        """Create a new job."""
        # Make data mutable and strictly a standard dict to handle JSON parsing
        # QueryDict (multipart) doesn't handle list/dict values well
        if hasattr(request.data, 'dict'):
            data = request.data.dict()
        else:
            data = request.data.copy()
        
        print(f"DEBUG: Raw data received: keys={list(data.keys())}")

        # Parse JSON fields if they are strings (common in multipart/form-data)
        import json
        for field in ['images', 'source_params']:
            if field in data and isinstance(data[field], str):
                try:
                    parsed_val = json.loads(data[field])
                    data[field] = parsed_val
                    print(f"DEBUG: Successfully parsed {field}: {type(parsed_val)}")
                except json.JSONDecodeError as e:
                    print(f"DEBUG: Failed to parse JSON for {field}: {e}, Value: {data[field]}")
                    pass # Let serializer handle the validation error
            elif field not in data:
                 print(f"DEBUG: Field {field} MISSING in data")

        print(f"DEBUG: Data passed to serializer: source_type={data.get('source_type')}")
        
        serializer = JobCreateSerializer(data=data)
        if not serializer.is_valid():
            print(f"DEBUG: Serializer Errors: {serializer.errors}")
            serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        source_type = data['source_type']
        idempotency_key = data.get('idempotency_key')
        created_by = request.user if request.user.is_authenticated else None
        
        # Check idempotency
        if idempotency_key:
            if created_by:
                existing_job = Job.objects.filter(
                    created_by=created_by,
                    idempotency_key=idempotency_key
                ).first()
            else:
                # Global idempotency if no user
                existing_job = Job.objects.filter(
                    created_by__isnull=True,
                    idempotency_key=idempotency_key
                ).first()
            
            if existing_job:
                return Response({
                    'job_id': existing_job.id,
                    'status': existing_job.status,
                    'message': 'Job already exists (idempotency)'
                }, status=status.HTTP_200_OK)
        
        # Create Dataset
        try:
            with transaction.atomic():
                if source_type == 'espacenet_excel':
                    source_data = data['source_data']
                    # Save uploaded file temporarily
                    import tempfile
                    import os
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                        for chunk in source_data.chunks():
                            tmp_file.write(chunk)
                        tmp_file_path = tmp_file.name
                    
                    try:
                        dataset = normalize_from_excel(tmp_file_path)
                    finally:
                        os.unlink(tmp_file_path)
                
                elif source_type == 'lens':
                    source_params = data['source_params']
                    connector = LensConnector()
                    response = connector.fetch(source_params)
                    raw_data = connector.parse(response)
                    dataset = normalize('lens', raw_data)
                
                else:
                    return Response(
                        {'error': 'Unsupported source_type'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Create Job
                job = Job.objects.create(
                    dataset=dataset,
                    created_by=created_by,
                    idempotency_key=idempotency_key,
                    status=Job.Status.PENDING
                )
                
                # Create ImageTasks
                for image_req in data['images']:
                    ImageTask.objects.create(
                        job=job,
                        algorithm_key=image_req['algorithm_key'],
                        algorithm_version=image_req.get('algorithm_version', '1.0'),
                        params=image_req['params'],
                        output_format=image_req.get('output_format', ImageTask.OutputFormat.BOTH),
                        status=ImageTask.Status.PENDING
                    )
                
                # Enqueue job
                run_job(job.id)
                
                return Response({
                    'job_id': job.id,
                    'status': job.status,
                    'message': 'Job created and enqueued'
                }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, pk=None):
        """Get job details."""
        job = get_object_or_404(Job.objects.prefetch_related('image_tasks', 'image_tasks__description_tasks'), pk=pk)
        serializer = JobDetailSerializer(job, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a job."""
        job = get_object_or_404(Job, pk=pk)
        job.cancel()
        return Response({
            'job_id': job.id,
            'status': job.status,
            'message': 'Job cancelled'
        })


@extend_schema_view(
    list=extend_schema(
        summary='Listar tareas de imagen',
        description='Obtiene una lista paginada de todas las tareas de generación de imágenes.',
        tags=['Image Tasks'],
    ),
    retrieve=extend_schema(
        summary='Obtener detalles de una tarea de imagen',
        description='Obtiene los detalles completos de una tarea de generación de imagen, incluyendo URLs de artefactos y datos del gráfico.',
        tags=['Image Tasks'],
        responses={
            200: ImageTaskSerializer,
            404: ErrorResponseSerializer,
        },
    ),
)
class ImageTaskViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ImageTask (read-only)."""
    queryset = ImageTask.objects.all()
    serializer_class = ImageTaskSerializer
    
    def get_serializer_context(self):
        """Add request to serializer context."""
        return {'request': self.request}


@extend_schema_view(
    list=extend_schema(
        summary='Listar tareas de descripción',
        description='Obtiene una lista paginada de todas las tareas de generación de descripciones con IA.',
        tags=['Description Tasks'],
    ),
    retrieve=extend_schema(
        summary='Obtener detalles de una tarea de descripción',
        description='Obtiene los detalles completos de una tarea de generación de descripción, incluyendo el texto generado y el prompt utilizado.',
        tags=['Description Tasks'],
        responses={
            200: DescriptionTaskSerializer,
            404: ErrorResponseSerializer,
        },
    ),
)
class DescriptionTaskViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for DescriptionTask (read-only)."""
    queryset = DescriptionTask.objects.all()
    serializer_class = DescriptionTaskSerializer


@extend_schema_view(
    create=extend_schema(
        summary='Generar descripción con IA',
        description='Crea una nueva tarea para generar una descripción de un gráfico usando inteligencia artificial. La tarea se procesa de forma asíncrona.',
        tags=['AI'],
        request=AIDescribeRequestSerializer,
        responses={
            201: AIDescribeResponseSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                'Ejemplo básico',
                value={
                    'image_task_id': 1,
                    'user_context': 'Este gráfico muestra tendencias de patentes en inteligencia artificial',
                    'provider_preference': 'openai'
                },
                request_only=True,
            ),
        ],
    ),
)
class AIDescribeView(viewsets.ViewSet):
    """View for AI description generation."""
    
    def create(self, request):
        """Create a description task and enqueue it."""
        serializer = AIDescribeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        image_task_id = data['image_task_id']
        user_context = data.get('user_context', '')
        provider_preference = data.get('provider_preference')
        
        # Get ImageTask
        image_task = get_object_or_404(ImageTask, id=image_task_id)
        
        if not image_task.chart_data:
            return Response(
                {'error': 'ImageTask has no chart_data'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create DescriptionTask
        description_task = DescriptionTask.objects.create(
            image_task=image_task,
            user_context=user_context,
            status=DescriptionTask.Status.PENDING
        )
        
        # Store provider_preference in task metadata for use in generate_description_task
        # We'll pass it via the task's kwargs or store it temporarily
        # For simplicity, we'll store it in the description_task's prompt_snapshot as metadata
        if provider_preference:
            description_task.prompt_snapshot = {'provider_preference': provider_preference}
            description_task.save(update_fields=['prompt_snapshot'])
            # Also store it as an attribute for easy access in the task
            description_task._provider_preference = provider_preference
        
        # Enqueue task
        generate_description_task.delay(description_task.id)
        
        return Response({
            'description_task_id': description_task.id,
            'status': description_task.status,
            'message': 'Description task created and enqueued',
            'provider_preference': provider_preference
        }, status=status.HTTP_201_CREATED)

