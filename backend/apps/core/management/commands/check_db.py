"""
Management command to check database connectivity.

This command is useful for:
- Container health checks (liveness/readiness probes)
- Deployment verification
- Troubleshooting database connectivity issues
- CI/CD pipeline validation

Usage:
    # Basic check
    python manage.py check_db
    
    # Wait for database to be available (useful in Docker/Kubernetes)
    python manage.py check_db --wait --timeout 60
    
    # Check specific database
    python manage.py check_db --database replica
    
    # Verbose output with connection details
    python manage.py check_db --verbose
"""

import sys
import time
from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from apps.core.db import (
    check_database_connection,
    get_database_status,
    wait_for_database,
    DatabaseHealthStatus,
)


class Command(BaseCommand):
    help = 'Check database connectivity with optional retry and detailed status'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--database',
            '-d',
            default='default',
            help='Database alias to check (default: "default")',
        )
        parser.add_argument(
            '--wait',
            '-w',
            action='store_true',
            help='Wait for the database to become available',
        )
        parser.add_argument(
            '--timeout',
            '-t',
            type=float,
            default=60.0,
            help='Maximum time to wait in seconds (default: 60)',
        )
        parser.add_argument(
            '--interval',
            '-i',
            type=float,
            default=2.0,
            help='Check interval when waiting (default: 2 seconds)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed connection information',
        )
        parser.add_argument(
            '--all',
            '-a',
            action='store_true',
            help='Check all configured databases',
        )
        parser.add_argument(
            '--quiet',
            '-q',
            action='store_true',
            help='Suppress output, only set exit code',
        )
    
    def handle(self, *args, **options):
        database = options['database']
        wait = options['wait']
        timeout = options['timeout']
        interval = options['interval']
        verbose = options['verbose']
        check_all = options['all']
        quiet = options['quiet']
        
        if check_all:
            return self._check_all_databases(verbose, quiet)
        
        if wait:
            return self._wait_for_database(database, timeout, interval, quiet)
        
        return self._check_single_database(database, verbose, quiet)
    
    def _check_single_database(self, database: str, verbose: bool, quiet: bool):
        """Check a single database connection."""
        status = get_database_status(
            database=database,
            include_details=verbose,
        )
        
        if not quiet:
            self._print_status(status, verbose)
        
        if status.is_healthy():
            if not quiet:
                self.stdout.write(
                    self.style.SUCCESS(f'[OK] Database "{database}" is healthy')
                )
            return
        
        if status.status == DatabaseHealthStatus.DEGRADED:
            if not quiet:
                self.stdout.write(
                    self.style.WARNING(f'[WARN] Database "{database}" is degraded')
                )
            sys.exit(1)
        
        if not quiet:
            self.stderr.write(
                self.style.ERROR(f'[FAIL] Database "{database}" is unhealthy')
            )
        sys.exit(2)
    
    def _wait_for_database(
        self,
        database: str,
        timeout: float,
        interval: float,
        quiet: bool,
    ):
        """Wait for database to become available."""
        if not quiet:
            self.stdout.write(
                f'Waiting for database "{database}" (timeout: {timeout}s)...'
            )
        
        start_time = time.time()
        attempt = 0
        
        while (time.time() - start_time) < timeout:
            attempt += 1
            is_healthy, message = check_database_connection(
                database=database,
                timeout=interval,
            )
            
            if is_healthy:
                elapsed = time.time() - start_time
                if not quiet:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'[OK] Database "{database}" is available '
                            f'(took {elapsed:.1f}s, {attempt} attempts)'
                        )
                    )
                return
            
            if not quiet:
                self.stdout.write(
                    f'  Attempt {attempt}: {message}',
                    ending='\r'
                )
            
            time.sleep(interval)
        
        if not quiet:
            self.stderr.write('')  # Clear the line
            self.stderr.write(
                self.style.ERROR(
                    f'[FAIL] Timeout waiting for database "{database}" '
                    f'after {timeout}s ({attempt} attempts)'
                )
            )
        sys.exit(2)
    
    def _check_all_databases(self, verbose: bool, quiet: bool):
        """Check all configured databases."""
        all_healthy = True
        
        for alias in connections:
            status = get_database_status(
                database=alias,
                include_details=verbose,
            )
            
            if not quiet:
                self._print_status(status, verbose)
                
                if status.is_healthy():
                    self.stdout.write(
                        self.style.SUCCESS(f'  [OK] {alias}: healthy')
                    )
                elif status.status == DatabaseHealthStatus.DEGRADED:
                    self.stdout.write(
                        self.style.WARNING(f'  [WARN] {alias}: degraded')
                    )
                    all_healthy = False
                else:
                    self.stdout.write(
                        self.style.ERROR(f'  [FAIL] {alias}: unhealthy')
                    )
                    all_healthy = False
        
        if not quiet:
            self.stdout.write('')  # Empty line
        
        if all_healthy:
            if not quiet:
                self.stdout.write(
                    self.style.SUCCESS('All databases are healthy')
                )
            return
        
        if not quiet:
            self.stderr.write(
                self.style.ERROR('Some databases are unhealthy')
            )
        sys.exit(2)
    
    def _print_status(self, status, verbose: bool):
        """Print detailed status information."""
        self.stdout.write('')
        self.stdout.write(f'Database: {status.database_alias}')
        self.stdout.write(f'Status: {status.status.value}')
        self.stdout.write(f'Message: {status.message}')
        
        if status.response_time_ms is not None:
            self.stdout.write(f'Response time: {status.response_time_ms:.2f}ms')
        
        if verbose and status.details:
            self.stdout.write('Details:')
            for key, value in status.details.items():
                if isinstance(value, dict):
                    self.stdout.write(f'  {key}:')
                    for k, v in value.items():
                        self.stdout.write(f'    {k}: {v}')
                else:
                    self.stdout.write(f'  {key}: {value}')
