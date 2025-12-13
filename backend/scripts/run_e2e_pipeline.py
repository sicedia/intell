"""
Script to run end-to-end pipeline with all algorithms.
Creates Dataset, Job, and ImageTasks for all 8 algorithms.
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.datasets.models import Dataset
from apps.datasets.normalizers import normalize_from_excel
from apps.jobs.models import Job, ImageTask
from apps.jobs.tasks import generate_image_task
from django.conf import settings


def main():
    """Run end-to-end pipeline."""
    print("=" * 80)
    print("Running End-to-End Pipeline with All Algorithms")
    print("=" * 80)
    
    # Step 1: Find Excel file
    excel_paths = [
        BASE_DIR / 'context' / 'excels' / 'Filters_20250522_1212.xlsx',
        BASE_DIR / 'context' / 'excels' / 'Filters_20250331_1141.xlsx',
        BASE_DIR / 'context' / 'Filters_20250522_1212.xlsx',
    ]
    
    excel_file = None
    for path in excel_paths:
        if path.exists():
            excel_file = path
            break
    
    if not excel_file:
        print("ERROR: Excel file not found!")
        return
    
    print(f"\n1. Using Excel file: {excel_file}")
    
    # Step 2: Create Datasets for different sheets
    print("\n2. Creating Datasets from Excel sheets...")
    
    datasets = {}
    sheet_configs = [
        ("Countries (family)", "top_patent_countries"),
        ("Inventors", "top_patent_inventors"),
        ("Applicants", "top_patent_applicants"),
        ("Earliest publication date (fam", "patent_evolution"),
        ("CPC subgroups", "cpc_treemap"),
    ]
    
    for sheet_name, algo_key in sheet_configs:
        try:
            print(f"   - Creating dataset for sheet: {sheet_name}")
            dataset = normalize_from_excel(str(excel_file), sheet_name=sheet_name)
            datasets[algo_key] = dataset
            print(f"     [OK] Dataset created: ID={dataset.id}, Path={dataset.storage_path}")
        except Exception as e:
            print(f"     [ERROR] Error creating dataset: {e}")
    
    # Use publication date dataset for time series algorithms
    if "patent_evolution" in datasets:
        datasets["patent_cumulative"] = datasets["patent_evolution"]
        datasets["patent_trends_cumulative"] = datasets["patent_evolution"]
        datasets["patent_forecast"] = datasets["patent_evolution"]
    
    # Step 3: Create Jobs and ImageTasks
    print("\n3. Creating Jobs and ImageTasks...")
    
    jobs = []
    image_tasks_config = [
        ("top_patent_countries", {"top_n": 10}, "Countries (family)"),
        ("top_patent_inventors", {"top_n": 10}, "Inventors"),
        ("top_patent_applicants", {"top_n": 10}, "Applicants"),
        ("patent_evolution", {}, "Earliest publication date (fam"),
        ("patent_cumulative", {}, "Earliest publication date (fam"),
        ("patent_trends_cumulative", {}, "Earliest publication date (fam"),
        ("patent_forecast", {}, "Earliest publication date (fam"),
        ("cpc_treemap", {"num_groups": 15}, "CPC subgroups"),
    ]
    
    for algo_key, params, sheet_name in image_tasks_config:
        if algo_key not in datasets:
            print(f"   [SKIP] Skipping {algo_key}: dataset not available")
            continue
        
        try:
            dataset = datasets[algo_key]
            
            # Create Job
            job = Job.objects.create(
                dataset=dataset,
                status=Job.Status.PENDING,
                progress_total=0
            )
            jobs.append(job)
            
            # Create ImageTask
            image_task = ImageTask.objects.create(
                job=job,
                algorithm_key=algo_key,
                algorithm_version="1.0",
                params=params,
                output_format=ImageTask.OutputFormat.BOTH,
                status=ImageTask.Status.PENDING,
                progress=0
            )
            
            print(f"   [OK] Created Job {job.id} with ImageTask {image_task.id} for {algo_key}")
            
            # Execute task synchronously for testing
            print(f"     -> Executing algorithm {algo_key}...")
            try:
                generate_image_task.apply(args=[image_task.id])
                image_task.refresh_from_db()
                
                if image_task.status == ImageTask.Status.SUCCESS:
                    print(f"     [OK] Success! Images generated")
                else:
                    print(f"     [FAILED] Failed: {image_task.status} - {image_task.error_message}")
            except Exception as e:
                print(f"     [ERROR] Error executing task: {e}")
                image_task.refresh_from_db()
                if image_task.error_message:
                    print(f"       Error message: {image_task.error_message}")
        
        except Exception as e:
            print(f"   [ERROR] Error creating job for {algo_key}: {e}")
            import traceback
            traceback.print_exc()
    
    # Step 4: Collect results and print links
    print("\n4. Generated Images and Links:")
    print("=" * 80)
    
    all_image_tasks = ImageTask.objects.filter(job__in=jobs).order_by('id')
    
    for image_task in all_image_tasks:
        print(f"\n[ALGORITHM] {image_task.algorithm_key} (Job {image_task.job.id}, Task {image_task.id})")
        print(f"   Status: {image_task.status}")
        
        if image_task.status == ImageTask.Status.SUCCESS:
            # PNG
            if image_task.artifact_png:
                png_path = image_task.artifact_png.path
                png_url = image_task.artifact_png.url
                if os.path.exists(png_path):
                    size = os.path.getsize(png_path)
                    print(f"   [PNG] http://localhost:8000{png_url}")
                    print(f"      Path: {png_path}")
                    print(f"      Size: {size:,} bytes")
                else:
                    print(f"   [WARNING] PNG: http://localhost:8000{png_url} (file not found)")
            
            # SVG
            if image_task.artifact_svg:
                svg_path = image_task.artifact_svg.path
                svg_url = image_task.artifact_svg.url
                if os.path.exists(svg_path):
                    size = os.path.getsize(svg_path)
                    print(f"   [SVG] http://localhost:8000{svg_url}")
                    print(f"      Path: {svg_path}")
                    print(f"      Size: {size:,} bytes")
                else:
                    print(f"   [WARNING] SVG: http://localhost:8000{svg_url} (file not found)")
        else:
            print(f"   [FAILED] Failed: {image_task.error_message or 'Unknown error'}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_jobs = len(jobs)
    successful_tasks = all_image_tasks.filter(status=ImageTask.Status.SUCCESS).count()
    total_tasks = all_image_tasks.count()
    
    print(f"Total Jobs created: {total_jobs}")
    print(f"Total ImageTasks: {total_tasks}")
    print(f"Successful: {successful_tasks}")
    print(f"Failed: {total_tasks - successful_tasks}")
    
    # Print all URLs
    print("\n" + "=" * 80)
    print("ALL IMAGE URLs")
    print("=" * 80)
    
    base_url = "http://localhost:8000"
    
    for image_task in all_image_tasks.filter(status=ImageTask.Status.SUCCESS):
        if image_task.artifact_png:
            print(f"{base_url}{image_task.artifact_png.url}")
        if image_task.artifact_svg:
            print(f"{base_url}{image_task.artifact_svg.url}")
    
    print("\n" + "=" * 80)
    print("Pipeline completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()

