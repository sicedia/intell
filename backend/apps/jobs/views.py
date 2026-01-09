"""
API views for jobs app.
"""
import logging
import json

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.http import FileResponse
from django.conf import settings
from django.core.exceptions import ValidationError
from pathlib import Path
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample

from .models import Job, ImageTask, DescriptionTask
from .serializers import (
    JobCreateSerializer, JobDetailSerializer,
    ImageTaskSerializer, DescriptionTaskSerializer,
    AIDescribeRequestSerializer,
    JobCreateResponseSerializer, JobCancelResponseSerializer,
    AIDescribeResponseSerializer, ErrorResponseSerializer
)
from apps.datasets.normalizers import normalize, normalize_from_excel, get_sheet_for_algorithm
from apps.ingestion.connectors import LensConnector
from apps.jobs.tasks import run_job
from apps.ai_descriptions.tasks import generate_description_task

logger = logging.getLogger(__name__)


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
        import tempfile
        import os
        
        # Make data mutable and strictly a standard dict to handle JSON parsing
        # QueryDict (multipart) doesn't handle list/dict values well
        if hasattr(request.data, 'dict'):
            data = request.data.dict()
        else:
            data = request.data.copy()
        
        logger.debug("Job creation request received: keys=%s", list(data.keys()))

        # Parse JSON fields if they are strings (common in multipart/form-data)
        for field in ['images', 'source_params']:
            if field in data and isinstance(data[field], str):
                try:
                    parsed_val = json.loads(data[field])
                    data[field] = parsed_val
                    logger.debug("Successfully parsed JSON field '%s'", field)
                except json.JSONDecodeError as e:
                    logger.debug("Failed to parse JSON for field '%s': %s", field, e)
                    # Let serializer handle the validation error

        serializer = JobCreateSerializer(data=data)
        if not serializer.is_valid():
            logger.debug("Serializer validation failed: %s", serializer.errors)
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
                logger.info("Returning existing job %d for idempotency_key=%s", existing_job.id, idempotency_key)
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
                    
                    # Save uploaded Excel file permanently (for multi-sheet access)
                    import uuid
                    excel_filename = f"excel_{uuid.uuid4().hex[:8]}.xlsx"
                    excel_dir = Path(settings.MEDIA_ROOT) / 'uploads' / 'excel'
                    excel_dir.mkdir(parents=True, exist_ok=True)
                    excel_path = excel_dir / excel_filename
                    
                    with open(excel_path, 'wb') as f:
                        for chunk in source_data.chunks():
                            f.write(chunk)
                    
                    # Get unique sheets needed by requested algorithms
                    requested_algorithms = [img['algorithm_key'] for img in data['images']]
                    unique_sheets = set()
                    algorithm_to_sheet = {}
                    for alg_key in requested_algorithms:
                        sheet = get_sheet_for_algorithm(alg_key)
                        unique_sheets.add(sheet)
                        algorithm_to_sheet[alg_key] = sheet
                    
                    # Create one dataset per unique sheet needed
                    sheet_to_dataset = {}
                    for sheet_name in unique_sheets:
                        try:
                            dataset = normalize_from_excel(str(excel_path), sheet_name=sheet_name)
                            # Store excel path in metadata for future reference
                            dataset.summary_stats['excel_path'] = str(excel_path)
                            dataset.summary_stats['sheet_name'] = sheet_name
                            dataset.save(update_fields=['summary_stats'])
                            sheet_to_dataset[sheet_name] = dataset
                        except Exception as e:
                            logger.warning(f"Failed to create dataset for sheet '{sheet_name}': {e}")
                            # Continue with other sheets
                    
                    if not sheet_to_dataset:
                        raise ValueError(
                            f"No se pudo crear ningún dataset del archivo Excel. "
                            f"Verifique que el archivo contenga las hojas requeridas para los algoritmos seleccionados."
                        )
                    
                    # Use the first dataset as the Job's main dataset
                    # (for backwards compatibility)
                    main_dataset = list(sheet_to_dataset.values())[0]
                
                elif source_type == 'lens':
                    source_params = data['source_params']
                    connector = LensConnector()
                    response = connector.fetch(source_params)
                    raw_data = connector.parse(response)
                    main_dataset = normalize('lens', raw_data)
                    # For Lens, all algorithms use the same dataset
                    sheet_to_dataset = None
                    algorithm_to_sheet = None
                
                else:
                    return Response(
                        {'error': f'Unsupported source_type: {source_type}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Create Job with main dataset
                job = Job.objects.create(
                    dataset=main_dataset,
                    created_by=created_by,
                    idempotency_key=idempotency_key,
                    status=Job.Status.PENDING
                )
                
                # Create ImageTasks with correct dataset reference
                for image_req in data['images']:
                    alg_key = image_req['algorithm_key']
                    task_params = dict(image_req.get('params', {}))
                    
                    # For Excel source, store the correct dataset_id in params
                    if sheet_to_dataset and algorithm_to_sheet:
                        sheet = algorithm_to_sheet.get(alg_key)
                        if sheet and sheet in sheet_to_dataset:
                            correct_dataset = sheet_to_dataset[sheet]
                            task_params['_dataset_id'] = correct_dataset.id
                    
                    ImageTask.objects.create(
                        job=job,
                        algorithm_key=alg_key,
                        algorithm_version=image_req.get('algorithm_version', '1.0'),
                        params=task_params,
                        output_format=image_req.get('output_format', ImageTask.OutputFormat.BOTH),
                        status=ImageTask.Status.PENDING
                    )
                
                # Enqueue job
                run_job(job.id)
                
                logger.info("Job %d created successfully with %d image tasks", job.id, len(data['images']))
                
                return Response({
                    'job_id': job.id,
                    'status': job.status,
                    'message': 'Job created and enqueued'
                }, status=status.HTTP_201_CREATED)
        
        except FileNotFoundError as e:
            logger.warning("File not found during job creation: %s", e)
            return Response(
                {'error': 'Source file not found or could not be processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except (ValidationError, DRFValidationError) as e:
            logger.warning("Validation error during job creation: %s", e)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception("Unexpected error during job creation")
            return Response(
                {'error': 'An unexpected error occurred while creating the job'},
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


# TEMPORARY: Test endpoint to serve Excel file for automated testing
# TODO: Remove after testing
@api_view(['GET'])
def serve_test_excel(request):
    """Temporary endpoint to serve test Excel file for automated testing."""
    if not settings.DEBUG:
        return Response({'error': 'Not available in production'}, status=status.HTTP_404_NOT_FOUND)
    
    # Path to test Excel file
    # views.py is at backend/apps/jobs/views.py
    # Go up 3 levels: views.py -> jobs/ -> apps/ -> backend/
    base_dir = Path(__file__).resolve().parent.parent.parent  # Go from views.py to backend/
    excel_path = base_dir / 'context' / 'excels' / 'Filters_20250331_1141.xlsx'
    
    if not excel_path.exists():
        return Response({
            'error': f'Test file not found at {excel_path}',
            'base_dir': str(base_dir),
            'checked_path': str(excel_path),
            'file_exists': excel_path.exists()
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        file_handle = open(excel_path, 'rb')
        return FileResponse(
            file_handle,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename='Filters_20250331_1141.xlsx'
        )
    except Exception as e:
        return Response({'error': f'Error serving file: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

