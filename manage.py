#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def _configure_rqworker_macos_fork_safety():
    """Prevent macOS Objective-C fork crash when running django-rq workers."""
    is_macos = sys.platform == 'darwin'
    is_rqworker_command = len(sys.argv) > 1 and sys.argv[1] == 'rqworker'

    if is_macos and is_rqworker_command:
        os.environ.setdefault('OBJC_DISABLE_INITIALIZE_FORK_SAFETY', 'YES')

        # Force non-fork worker on macOS to avoid objc_initializeAfterForkError.
        has_worker_class_arg = any(
            arg == '--worker-class' or arg.startswith('--worker-class=')
            for arg in sys.argv[2:]
        )
        if not has_worker_class_arg:
            sys.argv[2:2] = ['--worker-class', 'rq.SimpleWorker']


def main():
    """Run administrative tasks."""
    _configure_rqworker_macos_fork_safety()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safetrace.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
