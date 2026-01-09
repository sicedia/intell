"""
Services for artifact operations.
"""
import zipfile
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    from apps.jobs.models import Job


def create_images_zip(
    job: "Job",
    include_png: bool = True,
    include_svg: bool = True
) -> BytesIO:
    """
    Creates a ZIP file with all successful images from a job.
    
    Args:
        job: Job instance to get images from
        include_png: Whether to include PNG files
        include_svg: Whether to include SVG files
        
    Returns:
        BytesIO buffer containing the ZIP file
        
    Raises:
        ValueError: If no images are available to download
    """
    from apps.jobs.models import ImageTask
    
    # Get successful image tasks
    successful_tasks = job.image_tasks.filter(status=ImageTask.Status.SUCCESS)
    
    if not successful_tasks.exists():
        raise ValueError("No successful images available to download")
    
    # Create ZIP in memory
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        files_added = 0
        
        for task in successful_tasks:
            algorithm_name = task.algorithm_key
            
            # Add PNG if requested and available
            if include_png and task.artifact_png:
                try:
                    png_path = Path(settings.MEDIA_ROOT) / task.artifact_png.name
                    if png_path.exists():
                        arcname = f"png/{algorithm_name}.png"
                        zip_file.write(png_path, arcname)
                        files_added += 1
                except Exception:
                    # Skip files that can't be read
                    pass
            
            # Add SVG if requested and available
            if include_svg and task.artifact_svg:
                try:
                    svg_path = Path(settings.MEDIA_ROOT) / task.artifact_svg.name
                    if svg_path.exists():
                        arcname = f"svg/{algorithm_name}.svg"
                        zip_file.write(svg_path, arcname)
                        files_added += 1
                except Exception:
                    # Skip files that can't be read
                    pass
        
        if files_added == 0:
            raise ValueError("No image files could be read")
    
    # Reset buffer position to beginning
    zip_buffer.seek(0)
    
    return zip_buffer
