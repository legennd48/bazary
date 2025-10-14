"""
Management command to check and display Celery worker status.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from bazary.celery import app


class Command(BaseCommand):
    help = 'Check Celery worker status and configuration'

    def handle(self, *args, **options):
        self.stdout.write('=' * 70)
        self.stdout.write(self.style.SUCCESS('🔍 CELERY STATUS CHECK'))
        self.stdout.write('=' * 70)
        
        # Check configuration
        self.stdout.write('\n📋 Configuration:')
        self.stdout.write(f'  Broker URL: {settings.CELERY_BROKER_URL}')
        self.stdout.write(f'  Result Backend: {settings.CELERY_RESULT_BACKEND}')
        self.stdout.write(f'  Task Always Eager: {settings.CELERY_TASK_ALWAYS_EAGER}')
        
        # Check if eager mode is enabled
        if settings.CELERY_TASK_ALWAYS_EAGER:
            self.stdout.write('\n' + self.style.WARNING(
                '⚠️  CELERY_TASK_ALWAYS_EAGER is TRUE'
            ))
            self.stdout.write(self.style.WARNING(
                '   Tasks run synchronously (blocking) without worker.'
            ))
            self.stdout.write(self.style.WARNING(
                '   Good for development, not for production!\n'
            ))
        else:
            self.stdout.write('\n' + self.style.SUCCESS(
                '✅ CELERY_TASK_ALWAYS_EAGER is FALSE'
            ))
            self.stdout.write('   Tasks are sent to broker (requires worker)\n')
        
        # Check for active workers
        self.stdout.write('🔍 Checking for active workers...\n')
        
        try:
            # Ping workers
            inspect = app.control.inspect()
            active_workers = inspect.ping()
            
            if active_workers:
                self.stdout.write(self.style.SUCCESS(
                    f'✅ Found {len(active_workers)} active worker(s):\n'
                ))
                for worker_name, response in active_workers.items():
                    self.stdout.write(f'   - {worker_name}: {response}')
                
                # Get registered tasks
                self.stdout.write('\n📦 Registered Tasks:')
                registered = inspect.registered()
                if registered:
                    for worker, tasks in registered.items():
                        self.stdout.write(f'\n  Worker: {worker}')
                        for task in tasks:
                            if 'bazary' in task or 'apps' in task:
                                self.stdout.write(f'    • {task}')
                
                self.stdout.write('\n' + '=' * 70)
                self.stdout.write(self.style.SUCCESS('✅ Celery is running properly!\n'))
                
            else:
                self.stdout.write(self.style.ERROR('❌ No active Celery workers found!\n'))
                self._show_worker_instructions()
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error connecting to Celery: {e}\n'))
            self._show_worker_instructions()
    
    def _show_worker_instructions(self):
        """Show instructions for starting Celery worker."""
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.WARNING('⚠️  CELERY WORKER NOT RUNNING'))
        self.stdout.write('=' * 70)
        
        self.stdout.write('\n📝 To start Celery worker, choose ONE option:\n')
        
        self.stdout.write(self.style.SUCCESS('Option 1: Run Celery Worker (Recommended)'))
        self.stdout.write('  Open a new terminal and run:')
        self.stdout.write(self.style.HTTP_INFO('  $ cd /home/legennd/Software_repos/bazary'))
        self.stdout.write(self.style.HTTP_INFO('  $ source bazary_env/bin/activate'))
        self.stdout.write(self.style.HTTP_INFO('  $ celery -A bazary worker -l info'))
        self.stdout.write('  Keep this terminal running alongside your Django server.\n')
        
        self.stdout.write(self.style.SUCCESS('Option 2: Enable Eager Mode (Development Only)'))
        self.stdout.write('  Edit .env file and set:')
        self.stdout.write(self.style.HTTP_INFO('  CELERY_TASK_ALWAYS_EAGER=true'))
        self.stdout.write('  Then restart Django server.')
        self.stdout.write(self.style.WARNING('  ⚠️  Tasks will run synchronously (slower, blocking).\n'))
        
        self.stdout.write(self.style.SUCCESS('Option 3: Use Docker Compose'))
        self.stdout.write('  Run the entire stack with worker:')
        self.stdout.write(self.style.HTTP_INFO('  $ docker-compose up'))
        self.stdout.write('  This starts Django + Celery worker + Redis automatically.\n')
        
        self.stdout.write('=' * 70 + '\n')