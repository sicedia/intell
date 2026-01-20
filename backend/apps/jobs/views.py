"""
API views for jobs app.
"""
import logging
import json
import traceback
import shutil

from rest_framework import viewsets, status, filters, serializers
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.shortcuts import get_object_or_404
from django.db import transaction, IntegrityError
from django.http import FileResponse
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from pathlib import Path
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample, OpenApiParameter, inline_serializer

from .models import Job, ImageTask, DescriptionTask, Tag, ImageGroup
from .helpers import assign_date_tag_to_image_task, ensure_date_tag_on_publish
from .serializers import (
    JobCreateSerializer, JobDetailSerializer,
    ImageTaskSerializer, DescriptionTaskSerializer,
    AIDescribeRequestSerializer,
    JobCreateResponseSerializer, JobCancelResponseSerializer,
    AIDescribeResponseSerializer, ErrorResponseSerializer,
    TagSerializer, ImageGroupSerializer, ImageTaskUpdateSerializer,
    ImageLibrarySerializer
)
from apps.artifacts.services import create_images_zip
from apps.datasets.normalizers import normalize, normalize_from_excel, get_sheet_for_algorithm, validate_espacenet_excel
from apps.ingestion.connectors import LensConnector
from apps.jobs.tasks import run_job
from apps.ai_descriptions.tasks import generate_description_task

logger = logging.getLogger(__name__)


@extend_schema_view(
    create=extend_schema(
        summary='Crear un nuevo trabajo',
        description='Crea un nuevo trabajo de generaciรณn de grรกficos. El trabajo puede obtener datos desde Lens API o desde un archivo Excel de Espacenet.',
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
        description='Obtiene los detalles completos de un trabajo, incluyendo todas sus tareas de imagen y descripciรณn.',
        tags=['Jobs'],
        responses={
            200: JobDetailSerializer,
            404: ErrorResponseSerializer,
        },
    ),
    cancel=extend_schema(
        summary='Cancelar un trabajo',
        description='Cancela un trabajo en ejecuciรณn o pendiente.',
        tags=['Jobs'],
        responses={
            200: JobCancelResponseSerializer,
            404: ErrorResponseSerializer,
        },
    ),
    # TODO: Re-add download_zip schema after fixing the 404 issue
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
        for field in ['images', 'source_params', 'visualization_config']:
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
                    
                    # Save uploaded Excel file temporarily first for validation
                    import uuid
                    temp_dir = Path(settings.MEDIA_ROOT) / 'temp'
                    temp_dir.mkdir(parents=True, exist_ok=True)
                    temp_filename = f"temp_{uuid.uuid4().hex[:8]}.xlsx"
                    temp_path = temp_dir / temp_filename
                    
                    try:
                        with open(temp_path, 'wb') as f:
                            for chunk in source_data.chunks():
                                f.write(chunk)
                    except Exception as e:
                        logger.error(f"Failed to save temporary Excel file: {e}")
                        return Response(
                            {'error': f'Error al guardar el archivo temporal: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
                    
                    # Validate Excel structure before processing
                    try:
                        is_valid, error_message, validation_details = validate_espacenet_excel(str(temp_path))
                    except Exception as e:
                        logger.error(f"Error during Excel validation: {e}")
                        # Clean up temp file
                        try:
                            temp_path.unlink()
                        except Exception:
                            pass
                        return Response(
                            {'error': f'Error al validar el archivo Excel: {str(e)}'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    if not is_valid:
                        # Clean up temp file
                        try:
                            temp_path.unlink()
                        except Exception:
                            pass
                        return Response(
                            {
                                'error': error_message,
                                'validation_details': validation_details
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Move validated file to permanent location
                    # Add a delay to ensure file is fully closed (Windows issue)
                    import time
                    import gc
                    time.sleep(0.2)  # 200ms delay to ensure file handle is released
                    gc.collect()  # Force garbage collection to release file handles
                    
                    excel_filename = f"excel_{uuid.uuid4().hex[:8]}.xlsx"
                    excel_dir = Path(settings.MEDIA_ROOT) / 'uploads' / 'excel'
                    excel_dir.mkdir(parents=True, exist_ok=True)
                    excel_path = excel_dir / excel_filename
                    
                    # Move temp file to permanent location (use copy+delete for better error handling on Windows)
                    max_retries = 5
                    retry_delay = 0.3
                    moved = False
                    last_error = None
                    
                    for attempt in range(max_retries):
                        try:
                            # Try copy + delete instead of move (more reliable on Windows)
                            shutil.copy2(str(temp_path), str(excel_path))
                            # Small delay before deleting source
                            time.sleep(0.1)
                            temp_path.unlink()
                            moved = True
                            break
                        except (OSError, PermissionError) as e:
                            last_error = e
                            if attempt < max_retries - 1:
                                wait_time = retry_delay * (attempt + 1)
                                logger.warning(f"Failed to move Excel file (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                                time.sleep(wait_time)  # Exponential backoff
                                gc.collect()  # Force garbage collection between retries
                            else:
                                logger.error(f"Failed to move Excel file after {max_retries} attempts: {e}")
                                # Clean up temp file
                                try:
                                    temp_path.unlink()
                                except Exception:
                                    pass
                                return Response(
                                    {'error': f'Error al mover el archivo Excel después de {max_retries} intentos: {str(last_error)}'},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                                )
                    
                    if not moved:
                        # Clean up temp file
                        try:
                            temp_path.unlink()
                        except Exception:
                            pass
                        return Response(
                            {'error': f'Error al mover el archivo Excel: {str(last_error)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
                    
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
                            f"No se pudo crear ningรบn dataset del archivo Excel. "
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
                
                # Create Job with main dataset and visualization config
                visualization_config = data.get('visualization_config')
                job = Job.objects.create(
                    dataset=main_dataset,
                    created_by=created_by,
                    idempotency_key=idempotency_key,
                    visualization_config=visualization_config,
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
                    
                    image_task = ImageTask.objects.create(
                        job=job,
                        created_by=job.created_by,  # Associate user for statistics
                        algorithm_key=alg_key,
                        algorithm_version=image_req.get('algorithm_version', '1.0'),
                        params=task_params,
                        output_format=image_req.get('output_format', ImageTask.OutputFormat.BOTH),
                        status=ImageTask.Status.PENDING
                    )
                    # Assign date-based tag from Job
                    assign_date_tag_to_image_task(image_task)
                
                # Enqueue job asynchronously
                run_job.delay(job.id)
                
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
        except IntegrityError as e:
            # Handle idempotency constraint violation
            error_str = str(e)
            if 'unique_job_idempotency_scoped' in error_str or 'idempotency' in error_str.lower():
                # Try to find the existing job
                if idempotency_key:
                    if created_by:
                        existing_job = Job.objects.filter(
                            created_by=created_by,
                            idempotency_key=idempotency_key
                        ).first()
                    else:
                        existing_job = Job.objects.filter(
                            created_by__isnull=True,
                            idempotency_key=idempotency_key
                        ).first()
                    
                    if existing_job:
                        logger.info("Job already exists (caught IntegrityError) for idempotency_key=%s, returning existing job %d", idempotency_key, existing_job.id)
                        return Response({
                            'job_id': existing_job.id,
                            'status': existing_job.status,
                            'message': 'Job already exists (idempotency)'
                        }, status=status.HTTP_200_OK)
            
            logger.warning("Integrity error during job creation: %s", e)
            return Response(
                {'error': 'A job with the same parameters already exists. Please try again with different parameters.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except (ValidationError, DRFValidationError) as e:
            logger.warning("Validation error during job creation: %s", e)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception("Unexpected error during job creation: %s", str(e))
            # Include error message in response for debugging (in development) or generic message (in production)
            error_message = str(e) if settings.DEBUG else 'An unexpected error occurred while creating the job'
            return Response(
                {'error': error_message},
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
    
    @extend_schema(
        summary='Descargar imagenes como ZIP',
        description='Descarga todas las imagenes exitosas de un trabajo en un archivo ZIP.',
        tags=['Jobs'],
        parameters=[
            OpenApiParameter(
                name='image_format',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                default='both',
                enum=['both', 'png', 'svg'],
                description='Formato de imagenes a incluir: both (PNG + SVG), png, o svg',
            )
        ],
        responses={
            200: {
                'description': 'Archivo ZIP con las imagenes',
                'content': {'application/zip': {'schema': {'type': 'string', 'format': 'binary'}}}
            },
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    )
    @action(detail=True, methods=['get'], url_path='download-zip')
    def download_zip(self, request, pk=None):
        """Download all successful job images as a ZIP file."""
        job = get_object_or_404(Job, pk=pk)
        
        # Parse image_format parameter (not 'format' to avoid conflict with DRF's format negotiation)
        format_param = request.query_params.get('image_format', 'both').lower()
        if format_param not in ('both', 'png', 'svg'):
            return Response(
                {'error': f"Invalid image_format '{format_param}'. Must be 'both', 'png', or 'svg'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        include_png = format_param in ('both', 'png')
        include_svg = format_param in ('both', 'svg')
        
        try:
            zip_buffer = create_images_zip(job, include_png=include_png, include_svg=include_svg)
            
            # Generate filename with format suffix
            format_suffix = f"_{format_param}" if format_param != 'both' else ""
            filename = f"job_{job.id}_images{format_suffix}.zip"
            
            response = FileResponse(
                zip_buffer,
                as_attachment=True,
                filename=filename,
                content_type='application/zip'
            )
            return response
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception(f"Error creating ZIP for job {pk}")
            return Response(
                {'error': 'Failed to create ZIP file'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema_view(
    list=extend_schema(
        summary='Listar tareas de imagen',
        description='Obtiene una lista paginada de todas las tareas de generaciรณn de imรกgenes. Soporta filtros por status, tags, date_range, search y group.',
        tags=['Image Tasks'],
        parameters=[
            OpenApiParameter(
                name='status',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Filter by status (PENDING, RUNNING, SUCCESS, FAILED, CANCELLED)',
            ),
            OpenApiParameter(
                name='tags',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Filter by tag IDs (comma-separated)',
            ),
            OpenApiParameter(
                name='group',
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Filter by group ID',
            ),
            OpenApiParameter(
                name='search',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Search in title, algorithm_key, or user_description',
            ),
            OpenApiParameter(
                name='date_from',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Filter by created_at date (YYYY-MM-DD)',
            ),
            OpenApiParameter(
                name='date_to',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Filter by created_at date (YYYY-MM-DD)',
            ),
            OpenApiParameter(
                name='library',
                type=bool,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Use optimized library serializer (for gallery view)',
            ),
        ],
    ),
    retrieve=extend_schema(
        summary='Obtener detalles de una tarea de imagen',
        description='Obtiene los detalles completos de una tarea de generaciรณn de imagen, incluyendo URLs de artefactos y datos del grรกfico.',
        tags=['Image Tasks'],
        responses={
            200: ImageTaskSerializer,
            404: ErrorResponseSerializer,
        },
    ),
    update=extend_schema(
        summary='Actualizar metadata de imagen',
        description='Actualiza los metadatos de una imagen (title, user_description, tags, group).',
        tags=['Image Tasks'],
        request=ImageTaskUpdateSerializer,
        responses={
            200: ImageTaskSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    ),
    partial_update=extend_schema(
        summary='Actualizar metadata de imagen (parcial)',
        description='Actualiza parcialmente los metadatos de una imagen.',
        tags=['Image Tasks'],
        request=ImageTaskUpdateSerializer,
        responses={
            200: ImageTaskSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    ),
    retry=extend_schema(
        summary='Reintentar generaciรณn de imagen',
        description='Reintenta la generaciรณn de una imagen que fallรณ o quedรณ atascada. Resetea el estado de la tarea y la reencola para procesamiento. Permite reintentar tareas FAILED, RUNNING o PENDING.',
        tags=['Image Tasks'],
        responses={
            200: ImageTaskSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    ),
    cancel=extend_schema(
        summary='Cancelar generaciรณn de imagen',
        description='Cancela una tarea de generaciรณn de imagen individual. Solo permite cancelar tareas que estรกn en estado PENDING o RUNNING.',
        tags=['Image Tasks'],
        responses={
            200: ImageTaskSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    ),
)
class ImageTaskViewSet(viewsets.ModelViewSet):
    """ViewSet for ImageTask with library management capabilities."""
    queryset = ImageTask.objects.select_related('job', 'job__created_by', 'group', 'created_by').prefetch_related('tags').all()
    serializer_class = ImageTaskSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'updated_at', 'algorithm_key']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list' and self.request.query_params.get('library') == 'true':
            return ImageLibrarySerializer
        if self.action in ['update', 'partial_update']:
            return ImageTaskUpdateSerializer
        return ImageTaskSerializer
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by published status - library view shows only published by default
        library_param = self.request.query_params.get('library')
        published_param = self.request.query_params.get('published')
        
        if library_param == 'true':
            # Library view: show only published images by default
            if published_param is None:
                queryset = queryset.filter(is_published=True)
            elif published_param.lower() in ('true', 'false'):
                queryset = queryset.filter(is_published=(published_param.lower() == 'true'))
        else:
            # Non-library view: show all images unless published filter is explicitly set
            if published_param is not None:
                if published_param.lower() in ('true', 'false'):
                    queryset = queryset.filter(is_published=(published_param.lower() == 'true'))
        
        # Custom search implementation - handles null values properly and searches across multiple fields
        # Improved to search by individual words in the title and other fields
        search_param = self.request.query_params.get('search')
        if search_param:
            search_term = search_param.strip()
            if search_term:
                # Split search term into individual words for more flexible searching
                # This allows searching for "43" in "Image 43 - cpc_treemap"
                # Each word is searched independently across all fields
                search_words = search_term.split()
                
                # Build Q objects for case-insensitive search across multiple fields
                # Django's icontains handles null values correctly (won't match null fields)
                # We use OR logic between words: any word can match (more flexible for "any word" searches)
                word_queries = []
                
                for word in search_words:
                    word_query = Q()
                    
                    # Search in title (case-insensitive, handles null)
                    # This allows finding "43" in "Image 43 - cpc_treemap" or "Image 43"
                    word_query |= Q(title__icontains=word)
                    
                    # If the word is a number, also search by image ID
                    # This allows searching "43" to find image with ID 43 (which may have title "Image 43")
                    try:
                        image_id = int(word)
                        word_query |= Q(id=image_id)
                    except ValueError:
                        # Not a number, skip ID search
                        pass
                    
                    # Search in algorithm_key (always has a value)
                    word_query |= Q(algorithm_key__icontains=word)
                    
                    # Search in user_description (case-insensitive, handles null)
                    word_query |= Q(user_description__icontains=word)
                    
                    # Search in ai_context (case-insensitive, handles null)
                    word_query |= Q(ai_context__icontains=word)
                    
                    # Search in tag names (through many-to-many relationship)
                    word_query |= Q(tags__name__icontains=word)
                    
                    # Search in group name (through foreign key)
                    word_query |= Q(group__name__icontains=word)
                    
                    word_queries.append(word_query)
                
                # Combine all word queries with OR logic: any word can match in any field
                # This allows searching for "43" and finding "Image 43 - cpc_treemap" or "Image 43"
                if word_queries:
                    search_query = word_queries[0]
                    for word_query in word_queries[1:]:
                        search_query |= word_query
                    queryset = queryset.filter(search_query).distinct()
        
        # Filter by tags
        tags_param = self.request.query_params.get('tags')
        if tags_param:
            tag_ids = [int(tid) for tid in tags_param.split(',') if tid.strip().isdigit()]
            if tag_ids:
                queryset = queryset.filter(tags__id__in=tag_ids).distinct()
        
        # Filter by group
        group_param = self.request.query_params.get('group')
        if group_param:
            try:
                group_id = int(group_param)
                queryset = queryset.filter(group_id=group_id)
            except ValueError:
                pass
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            try:
                from datetime import datetime
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=date_from_obj)
            except ValueError:
                pass
        if date_to:
            try:
                from datetime import datetime
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=date_to_obj)
            except ValueError:
                pass
        
        # Order by job and created_at for grouping if requested
        group_by = self.request.query_params.get('group_by')
        if group_by == 'job':
            # Group by job - order by job first, then by created_at within each job
            queryset = queryset.select_related('job').order_by('job', '-created_at')
        else:
            # Default ordering
            queryset = queryset.select_related('job').order_by('-created_at')
        
        return queryset
    
    def get_serializer_context(self):
        """Add request to serializer context."""
        return {'request': self.request}
    
    def update(self, request, *args, **kwargs):
        """Update image metadata."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return full object with updated serializer
        return Response(
            ImageTaskSerializer(instance, context={'request': request}).data
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel an ImageTask.
        
        Only allows canceling tasks that are PENDING or RUNNING.
        """
        from apps.audit.helpers import emit_event
        from celery import current_app
        
        image_task = get_object_or_404(ImageTask, pk=pk)
        job = image_task.job
        
        # Only allow canceling pending or running tasks
        if image_task.status not in [ImageTask.Status.PENDING, ImageTask.Status.RUNNING]:
            return Response(
                {'error': f'Task status is {image_task.status}. Only PENDING or RUNNING tasks can be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if job is cancelled
        if job.status == Job.Status.CANCELLED:
            return Response(
                {'error': 'Cannot cancel task: Job is already cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Cancel the task
            image_task.status = ImageTask.Status.CANCELLED
            image_task.save(update_fields=['status', 'updated_at'])
            
            # Try to revoke the Celery task if it's still in queue
            # Note: This is best-effort, the task might already be executing
            try:
                # We need to find the task ID - this is tricky without storing it
                # For now, we'll just mark it as cancelled in the DB
                # The worker will check the status before processing
                pass
            except Exception as revoke_error:
                logger.warning(
                    f'Could not revoke Celery task for ImageTask {image_task.id}: {revoke_error}',
                    extra={'image_task_id': image_task.id}
                )
            
            # Emit cancel event
            emit_event(
                job_id=job.id,
                image_task_id=image_task.id,
                event_type='CANCELLED',
                level='INFO',
                message=f'Image generation cancelled for {image_task.algorithm_key}',
                progress=image_task.progress
            )
            
            # Check if all tasks are cancelled - update job status
            remaining_tasks = ImageTask.objects.filter(
                job=job,
                status__in=[ImageTask.Status.PENDING, ImageTask.Status.RUNNING]
            )
            
            if not remaining_tasks.exists():
                # All tasks are done or cancelled
                all_cancelled = ImageTask.objects.filter(
                    job=job
                ).exclude(status=ImageTask.Status.CANCELLED).exists() == False
                
                if all_cancelled:
                    job.status = Job.Status.CANCELLED
                    job.save(update_fields=['status', 'updated_at'])
                    
                    emit_event(
                        job_id=job.id,
                        event_type='job_status_changed',
                        level='INFO',
                        message='All tasks cancelled - Job cancelled',
                        progress=job.progress_total,
                        payload={'status': job.status}
                    )
            
            logger.info(
                f'ImageTask {image_task.id} cancelled',
                extra={
                    'image_task_id': image_task.id,
                    'job_id': job.id,
                    'algorithm_key': image_task.algorithm_key
                }
            )
            
            # Return updated task
            serializer = self.get_serializer(image_task)
            return Response({
                'image_task_id': image_task.id,
                'status': image_task.status,
                'message': 'Task cancelled successfully',
                'task': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(
                f'Failed to cancel ImageTask {image_task.id}: {str(e)}',
                exc_info=True,
                extra={'image_task_id': image_task.id, 'job_id': job.id}
            )
            
            emit_event(
                job_id=job.id,
                image_task_id=image_task.id,
                event_type='ERROR',
                level='ERROR',
                message=f'Failed to cancel task: {str(e)}',
                payload={'error': str(e), 'trace': error_trace}
            )
            
            return Response(
                {'error': f'Failed to cancel task: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """
        Retry an ImageTask.
        
        Allows retrying FAILED, RUNNING, or PENDING tasks.
        Resets the task status to PENDING, clears error information,
        and re-enqueues the task for processing.
        """
        from apps.jobs.tasks import generate_image_task
        from apps.audit.helpers import emit_event
        
        image_task = get_object_or_404(ImageTask, pk=pk)
        job = image_task.job
        
        # Allow retry for failed, running, pending, or cancelled tasks
        # This handles cases where tasks got stuck due to connection loss, etc.
        if image_task.status not in [
            ImageTask.Status.FAILED,
            ImageTask.Status.RUNNING,
            ImageTask.Status.PENDING,
            ImageTask.Status.CANCELLED
        ]:
            return Response(
                {'error': f'Task status is {image_task.status}. Only FAILED, RUNNING, PENDING, or CANCELLED tasks can be retried.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if job is cancelled
        if job.status == Job.Status.CANCELLED:
            return Response(
                {'error': 'Cannot retry task: Job is cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Reset task state
            image_task.status = ImageTask.Status.PENDING
            image_task.progress = 0
            image_task.error_code = None
            image_task.error_message = None
            image_task.trace_id = None
            
            # Optionally clear old artifacts (optional - can keep for debugging)
            # Uncomment if you want to delete old artifacts on retry:
            # if image_task.artifact_png:
            #     image_task.artifact_png.delete(save=False)
            # if image_task.artifact_svg:
            #     image_task.artifact_svg.delete(save=False)
            # image_task.chart_data = {}
            
            image_task.save(update_fields=[
                'status', 'progress', 'error_code', 'error_message', 
                'trace_id', 'updated_at'
            ])
            
            # Update job status if it was FAILED or PARTIAL_SUCCESS
            # Recalculate job progress based on all image tasks
            job_status_changed = False
            if job.status in [Job.Status.FAILED, Job.Status.PARTIAL_SUCCESS]:
                old_status = job.status
                job.status = Job.Status.RUNNING
                job_status_changed = True
                
                # Recalculate progress from all image tasks
                image_tasks = ImageTask.objects.filter(job=job)
                if image_tasks.exists():
                    total_progress = sum(task.progress for task in image_tasks)
                    task_count = image_tasks.count()
                    job.progress_total = int(total_progress / task_count) if task_count > 0 else 0
                
                job.save(update_fields=['status', 'progress_total', 'updated_at'])
                
                # Emit job status changed event
                emit_event(
                    job_id=job.id,
                    event_type='job_status_changed',
                    level='INFO',
                    message=f'Job status changed from {old_status} to {job.status} due to task retry',
                    progress=job.progress_total,
                    payload={'status': job.status, 'previous_status': old_status}
                )
            
            # Emit retry event
            emit_event(
                job_id=job.id,
                image_task_id=image_task.id,
                event_type='RETRY',
                level='INFO',
                message=f'Retrying image generation for {image_task.algorithm_key}',
                progress=0
            )
            
            # Re-enqueue the task
            generate_image_task.delay(image_task.id)
            
            logger.info(
                f'ImageTask {image_task.id} retry requested - task re-enqueued',
                extra={
                    'image_task_id': image_task.id,
                    'job_id': job.id,
                    'algorithm_key': image_task.algorithm_key
                }
            )
            
            # Return updated task
            serializer = self.get_serializer(image_task)
            return Response({
                'image_task_id': image_task.id,
                'status': image_task.status,
                'message': 'Task retry initiated',
                'task': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(
                f'Failed to retry ImageTask {image_task.id}: {str(e)}',
                exc_info=True,
                extra={'image_task_id': image_task.id, 'job_id': job.id}
            )
            
            emit_event(
                job_id=job.id,
                image_task_id=image_task.id,
                event_type='ERROR',
                level='ERROR',
                message=f'Failed to retry task: {str(e)}',
                payload={'error': str(e), 'trace': error_trace}
            )
            
            return Response(
                {'error': f'Failed to retry task: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary='Publicar/despublicar imagen',
        description='Publica o despublica una imagen en la librería. Las imágenes publicadas aparecen en la galería.',
        tags=['Image Tasks'],
        request=inline_serializer(
            name='PublishImageRequest',
            fields={
                'publish': serializers.BooleanField(help_text='True para publicar, False para despublicar'),
            },
        ),
        responses={
            200: inline_serializer(
                name='PublishImageResponse',
                fields={
                    'id': serializers.IntegerField(),
                    'is_published': serializers.BooleanField(),
                    'published_at': serializers.DateTimeField(allow_null=True),
                    'message': serializers.CharField(),
                },
            ),
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    )
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """
        Publish or unpublish an image to/from the library.
        
        Request body: {"publish": true} or {"publish": false}
        """
        # Ensure job is loaded with select_related to avoid extra queries
        image_task = get_object_or_404(ImageTask.objects.select_related('job'), pk=pk)
        
        # Only allow publishing successful images
        if image_task.status != ImageTask.Status.SUCCESS:
            return Response(
                {'error': f'Cannot publish image: status is {image_task.status}. Only SUCCESS images can be published.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        publish = request.data.get('publish', True)
        
        try:
            with transaction.atomic():
                if publish:
                    image_task.publish()
                    message = 'Imagen publicada exitosamente en la librería'
                else:
                    image_task.unpublish()
                    message = 'Imagen despublicada (convertida a borrador)'
            
            # Ensure date tag is assigned when publishing (outside transaction to avoid blocking)
            # This is done after the transaction commits to avoid blocking the publish operation
            if publish:
                # Re-fetch with job relationship to ensure it's loaded after save
                image_task = ImageTask.objects.select_related('job').get(pk=image_task.pk)
                # Try to assign tag, but don't fail if it doesn't work
                try:
                    ensure_date_tag_on_publish(image_task)
                except Exception as tag_error:
                    # Log tag assignment error but don't fail the publish
                    logger.warning(
                        f'Failed to assign date tag during publish for ImageTask {image_task.id}: {str(tag_error)}',
                        extra={'image_task_id': image_task.id}
                    )
            
            # Refresh from DB to get latest state (including published_at)
            image_task.refresh_from_db()
            
            # Check and update job status if all images are complete
            # This ensures the job status is updated even if finalize_job didn't run
            if publish:
                from apps.jobs.tasks import _check_and_update_job_status
                try:
                    _check_and_update_job_status(image_task.job)
                except Exception as check_error:
                    # Log but don't fail the publish operation
                    logger.warning(
                        f'Failed to check job status after publish for ImageTask {image_task.id}: {str(check_error)}',
                        extra={'image_task_id': image_task.id, 'job_id': image_task.job.id}
                    )
            
            # Serialize published_at safely
            published_at_str = None
            if image_task.published_at:
                try:
                    published_at_str = image_task.published_at.isoformat()
                except (AttributeError, ValueError):
                    published_at_str = str(image_task.published_at) if image_task.published_at else None
            
            return Response({
                'id': image_task.id,
                'is_published': image_task.is_published,
                'published_at': published_at_str,
                'message': message,
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(
                f'Error publishing/unpublishing image {image_task.id}: {str(e)}',
                exc_info=True,
                extra={'image_task_id': image_task.id, 'trace': error_trace}
            )
            return Response(
                {'error': f'Error al publicar/despublicar imagen: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def perform_destroy(self, instance):
        """
        Delete an ImageTask instance.
        
        Ensures only the user who created the image can delete it.
        Deletes artifact files (PNG/SVG) before deleting the model instance.
        Emits audit event for tracking.
        """
        from apps.audit.helpers import emit_event
        from rest_framework.exceptions import PermissionDenied
        
        # Check permissions: only the user who created the image (or the job) can delete it
        # Handle cases where created_by might be None (fallback to job.created_by)
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied('Authentication required to delete images')
        
        # Check ownership: either through image_task.created_by or job.created_by
        is_owner = False
        if instance.created_by_id is not None:
            # Direct ownership through image_task.created_by
            is_owner = (instance.created_by_id == user.id)
        else:
            # Fallback: check if user owns the job
            # Access job.created_by_id - Django will fetch if not already loaded
            if instance.job.created_by_id is not None:
                is_owner = (instance.job.created_by_id == user.id)
        
        if not is_owner:
            raise PermissionDenied('You can only delete your own images')
        
        # Store image info for audit event (before deletion)
        image_id = instance.id
        job_id = instance.job_id
        algorithm_key = instance.algorithm_key
        
        try:
            # Emit audit event BEFORE deleting (emit_event may try to update the ImageTask)
            emit_event(
                job_id=job_id,
                image_task_id=image_id,
                event_type='image_deleted',
                level='INFO',
                message=f'Image deleted: {algorithm_key}',
                payload={'image_task_id': image_id, 'algorithm_key': algorithm_key}
            )
            
            # Delete artifact files before deleting the model
            if instance.artifact_png:
                try:
                    instance.artifact_png.delete(save=False)
                except Exception as e:
                    logger.warning(
                        f'Error deleting PNG artifact for ImageTask {instance.id}: {str(e)}',
                        extra={'image_task_id': instance.id}
                    )
            
            if instance.artifact_svg:
                try:
                    instance.artifact_svg.delete(save=False)
                except Exception as e:
                    logger.warning(
                        f'Error deleting SVG artifact for ImageTask {instance.id}: {str(e)}',
                        extra={'image_task_id': instance.id}
                    )
            
            # Delete the model instance
            instance.delete()
            
            logger.info(
                f'ImageTask {image_id} deleted by user {self.request.user.id}',
                extra={
                    'image_task_id': image_id,
                    'job_id': job_id,
                    'user_id': self.request.user.id,
                    'algorithm_key': algorithm_key
                }
            )
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(
                f'Error deleting ImageTask {image_id}: {str(e)}',
                exc_info=True,
                extra={'image_task_id': image_id, 'job_id': job_id, 'trace': error_trace}
            )
            # Re-raise the exception so DRF can handle it properly
            raise


@extend_schema_view(
    list=extend_schema(
        summary='Listar tareas de descripciรณn',
        description='Obtiene una lista paginada de todas las tareas de generaciรณn de descripciones con IA.',
        tags=['Description Tasks'],
    ),
    retrieve=extend_schema(
        summary='Obtener detalles de una tarea de descripciรณn',
        description='Obtiene los detalles completos de una tarea de generaciรณn de descripciรณn, incluyendo el texto generado y el prompt utilizado.',
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
        summary='Generar descripciรณn con IA',
        description='Crea una nueva tarea para generar una descripciรณn de un grรกfico usando inteligencia artificial. La tarea se procesa de forma asรญncrona.',
        tags=['AI'],
        request=AIDescribeRequestSerializer,
        responses={
            201: AIDescribeResponseSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                'Ejemplo bรกsico',
                value={
                    'image_task_id': 1,
                    'user_context': 'Este grรกfico muestra tendencias de patentes en inteligencia artificial',
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
        model_preference = data.get('model_preference')
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
        
        # Store preferences in task metadata
        # model_preference takes priority over provider_preference
        prompt_snapshot = {}
        if model_preference:
            prompt_snapshot['model_preference'] = model_preference
            # If model is specified, set provider to litellm
            prompt_snapshot['provider_preference'] = 'litellm'
        elif provider_preference:
            prompt_snapshot['provider_preference'] = provider_preference
        
        if prompt_snapshot:
            description_task.prompt_snapshot = prompt_snapshot
            description_task.save(update_fields=['prompt_snapshot'])
        
        # Enqueue task
        generate_description_task.delay(description_task.id)
        
        return Response({
            'description_task_id': description_task.id,
            'status': description_task.status,
            'message': 'Description task created and enqueued',
            'model_preference': model_preference,
            'provider_preference': prompt_snapshot.get('provider_preference') if prompt_snapshot else provider_preference,
            'job_id': image_task.job_id  # Include job_id for WebSocket connection
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


@extend_schema(
    summary='Validar archivo Excel de Espacenet',
    description='Valida que un archivo Excel tenga la estructura esperada de un export de Espacenet antes de procesarlo.',
    tags=['Jobs'],
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'file': {
                    'type': 'string',
                    'format': 'binary',
                    'description': 'Archivo Excel a validar'
                }
            },
            'required': ['file']
        }
    },
    responses={
        200: inline_serializer(
            name='ExcelValidationResponse',
            fields={
                'is_valid': serializers.BooleanField(help_text='Si el archivo es válido'),
                'message': serializers.CharField(help_text='Mensaje de validación'),
                'details': serializers.DictField(help_text='Detalles de la validación', required=False),
            }
        ),
        400: ErrorResponseSerializer,
    },
)
@api_view(['POST'])
def validate_excel(request):
    """Validate that an uploaded Excel file has the expected Espacenet structure."""
    if 'file' not in request.FILES:
        return Response(
            {'error': 'No se proporcionó ningún archivo. Por favor, suba un archivo Excel.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    excel_file = request.FILES['file']
    
    # Validate file extension
    if not excel_file.name.endswith(('.xlsx', '.xls')):
        return Response(
            {'error': 'El archivo debe ser un archivo Excel (.xlsx o .xls)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Save file temporarily for validation
    import tempfile
    import uuid
    
    temp_dir = Path(settings.MEDIA_ROOT) / 'temp'
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_filename = f"validation_{uuid.uuid4().hex[:8]}.xlsx"
    temp_path = temp_dir / temp_filename
    
    try:
        # Save uploaded file
        with open(temp_path, 'wb') as f:
            for chunk in excel_file.chunks():
                f.write(chunk)
        
        # Validate the file
        is_valid, error_message, validation_details = validate_espacenet_excel(str(temp_path))
        
        # Clean up temp file
        try:
            temp_path.unlink()
        except Exception:
            pass  # Ignore cleanup errors
        
        if is_valid:
            return Response({
                'is_valid': True,
                'message': 'El archivo Excel es válido y tiene la estructura esperada de Espacenet.',
                'details': validation_details
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'is_valid': False,
                'message': error_message,
                'details': validation_details
            }, status=status.HTTP_200_OK)  # 200 because validation completed, even if invalid
            
    except Exception as e:
        # Clean up temp file on error
        try:
            if temp_path.exists():
                temp_path.unlink()
        except Exception:
            pass
        
        logger.error(f"Error validating Excel file: {str(e)}", exc_info=True)
        return Response(
            {'error': f'Error al validar el archivo Excel: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema_view(
    list=extend_schema(
        summary='Listar tags',
        description='Obtiene una lista de todos los tags disponibles.',
        tags=['Tags'],
    ),
    create=extend_schema(
        summary='Crear tag',
        description='Crea un nuevo tag.',
        tags=['Tags'],
        request=TagSerializer,
        responses={
            201: TagSerializer,
            400: ErrorResponseSerializer,
        },
    ),
)
class TagViewSet(viewsets.ModelViewSet):
    """ViewSet for Tag management."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    http_method_names = ['get', 'post', 'head', 'options']
    
    def get_queryset(self):
        """Return all tags for list view."""
        return Tag.objects.all()
    
    def perform_create(self, serializer):
        """Set created_by to current user."""
        serializer.save(created_by=self.request.user if self.request.user.is_authenticated else None)


@extend_schema_view(
    list=extend_schema(
        summary='Listar grupos de imágenes',
        description='Obtiene una lista de grupos de imágenes del usuario actual.',
        tags=['Image Groups'],
    ),
    create=extend_schema(
        summary='Crear grupo de imágenes',
        description='Crea un nuevo grupo de imágenes.',
        tags=['Image Groups'],
        request=ImageGroupSerializer,
        responses={
            201: ImageGroupSerializer,
            400: ErrorResponseSerializer,
        },
    ),
    retrieve=extend_schema(
        summary='Obtener detalles de grupo',
        description='Obtiene los detalles de un grupo de imágenes.',
        tags=['Image Groups'],
        responses={
            200: ImageGroupSerializer,
            404: ErrorResponseSerializer,
        },
    ),
    update=extend_schema(
        summary='Actualizar grupo',
        description='Actualiza un grupo de imágenes.',
        tags=['Image Groups'],
        request=ImageGroupSerializer,
        responses={
            200: ImageGroupSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    ),
    partial_update=extend_schema(
        summary='Actualizar grupo (parcial)',
        description='Actualiza parcialmente un grupo de imágenes.',
        tags=['Image Groups'],
        request=ImageGroupSerializer,
        responses={
            200: ImageGroupSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    ),
    destroy=extend_schema(
        summary='Eliminar grupo',
        description='Elimina un grupo de imágenes.',
        tags=['Image Groups'],
        responses={
            204: None,
            404: ErrorResponseSerializer,
        },
    ),
)
class ImageGroupViewSet(viewsets.ModelViewSet):
    """ViewSet for ImageGroup management."""
    queryset = ImageGroup.objects.all()
    serializer_class = ImageGroupSerializer
    
    def get_queryset(self):
        """Filter groups by current user."""
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            queryset = queryset.filter(created_by=self.request.user)
        # Allow unauthenticated users to see empty list (for development)
        return queryset
    
    def perform_create(self, serializer):
        """Set created_by to current user."""
        if not self.request.user.is_authenticated:
            from rest_framework.exceptions import NotAuthenticated
            raise NotAuthenticated('Authentication required')
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Ensure user owns the group."""
        instance = self.get_object()
        user = self.request.user
        if not user.is_authenticated:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Authentication required to update groups')
        if instance.created_by_id != user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You can only update your own groups')
        serializer.save()
    
    def perform_destroy(self, instance):
        """Ensure user owns the group."""
        user = self.request.user
        if not user.is_authenticated:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Authentication required to delete groups')
        if instance.created_by_id != user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You can only delete your own groups')
        instance.delete()


@extend_schema(
    summary='Dashboard statistics',
    description='Get dashboard statistics including total images, published images, AI described images, and active users.',
    tags=['Dashboard'],
    responses={
        200: inline_serializer(
            name='DashboardStatsResponse',
            fields={
                'total_images': serializers.IntegerField(help_text='Total number of successfully generated images'),
                'total_published_images': serializers.IntegerField(help_text='Total number of published images'),
                'total_ai_described_images': serializers.IntegerField(help_text='Total number of images with AI-generated descriptions'),
                'total_active_users_this_month': serializers.IntegerField(help_text='Number of unique users who created content this month'),
                'images_this_month': serializers.IntegerField(help_text='Images generated this month'),
                'published_this_month': serializers.IntegerField(help_text='Published images this month'),
            },
        ),
    },
)
@api_view(['GET'])
def dashboard_stats(request):
    """Get dashboard statistics."""
    from django.db.models import Count, Q
    from django.utils import timezone
    from django.contrib.auth import get_user_model
    from datetime import timedelta
    
    User = get_user_model()
    
    # Get current month start
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Total images (successful only)
    total_images = ImageTask.objects.filter(status=ImageTask.Status.SUCCESS).count()
    
    # Total published images
    total_published_images = ImageTask.objects.filter(
        is_published=True,
        status=ImageTask.Status.SUCCESS
    ).count()
    
    # Total images described by AI (images with user_description, which indicates AI description was generated)
    total_ai_described_images = ImageTask.objects.filter(
        user_description__isnull=False,
        user_description__gt=''  # Exclude empty strings
    ).count()
    
    # Total active users this month (users who created jobs or image tasks this month)
    # Get unique users from both Job and ImageTask created this month using union
    from django.db.models import Q
    job_user_ids = Job.objects.filter(
        created_at__gte=month_start,
        created_by__isnull=False
    ).values_list('created_by', flat=True).distinct()
    
    image_task_user_ids = ImageTask.objects.filter(
        created_at__gte=month_start,
        created_by__isnull=False
    ).values_list('created_by', flat=True).distinct()
    
    # Combine and get unique count (using set union for efficiency)
    all_active_user_ids = set(job_user_ids) | set(image_task_user_ids)
    total_active_users_this_month = len(all_active_user_ids)
    
    # Images this month
    images_this_month = ImageTask.objects.filter(
        status=ImageTask.Status.SUCCESS,
        created_at__gte=month_start
    ).count()
    
    # Published this month
    published_this_month = ImageTask.objects.filter(
        is_published=True,
        status=ImageTask.Status.SUCCESS,
        created_at__gte=month_start
    ).count()
    
    return Response({
        'total_images': total_images,
        'total_published_images': total_published_images,
        'total_ai_described_images': total_ai_described_images,
        'total_active_users_this_month': total_active_users_this_month,
        'images_this_month': images_this_month,
        'published_this_month': published_this_month,
    })


@extend_schema(
    summary='Latest published images',
    description='Get the latest published images for the dashboard.',
    tags=['Dashboard'],
    parameters=[
        OpenApiParameter(
            name='limit',
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
            default=8,
            description='Number of images to return (default: 8)',
        ),
    ],
    responses={
        200: ImageLibrarySerializer(many=True),
    },
)
@api_view(['GET'])
def latest_published_images(request):
    """Get latest published images."""
    limit = int(request.query_params.get('limit', 8))
    
    images = ImageTask.objects.filter(
        is_published=True,
        status=ImageTask.Status.SUCCESS
    ).select_related('job', 'job__created_by', 'group', 'created_by').prefetch_related('tags').order_by('-published_at', '-created_at')[:limit]
    
    serializer = ImageLibrarySerializer(images, many=True, context={'request': request})
    return Response(serializer.data)

