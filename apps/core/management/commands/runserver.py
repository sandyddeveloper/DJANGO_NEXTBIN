"""
Custom runserver command.
Extends Django's runserver to also start Redis and Celery in the background.
All services are shut down cleanly when the server is stopped (CTRL+C).
"""

import os
import sys
import shutil
import subprocess
import atexit
import signal
import time
from django.core.management.commands.runserver import Command as BaseRunserverCommand
from django.utils.termcolors import colorize


# Track background processes so we can kill them on exit
_background_procs = []


def _kill_all():
    """Terminate all background processes gracefully."""
    for proc in _background_procs:
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass


# Register cleanup on normal exit and SIGINT
atexit.register(_kill_all)


def _start_redis():
    """Start Redis server if available; searches PATH and common Windows install locations."""
    # Common Windows Redis install locations
    windows_redis_paths = [
        r"C:\Program Files\Redis\redis-server.exe",
        r"C:\Redis\redis-server.exe",
        r"C:\tools\redis\redis-server.exe",
    ]

    redis_bin = shutil.which("redis-server")
    if not redis_bin:
        for path in windows_redis_paths:
            if os.path.isfile(path):
                redis_bin = path
                break

    if not redis_bin:
        print(colorize(
            "  [runserver] WARNING: redis-server not found — skipping Redis startup.\n"
            "              Install Redis for Windows: https://github.com/tporadowski/redis/releases",
            fg="yellow"
        ))
        return None

    # Check if Redis is already responding
    redis_cli_paths = [shutil.which("redis-cli")] + [
        p.replace("redis-server.exe", "redis-cli.exe") for p in windows_redis_paths
    ]
    for redis_cli in redis_cli_paths:
        if redis_cli and os.path.isfile(redis_cli):
            result = subprocess.run(
                [redis_cli, "ping"],
                capture_output=True, text=True, timeout=2
            )
            if result.stdout.strip() == "PONG":
                print(colorize("  [runserver] Redis is already running ✓", fg="green"))
                return None
            break

    print(colorize("  [runserver] Starting Redis server...", fg="cyan"))
    proc = subprocess.Popen(
        [redis_bin],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )
    time.sleep(1.5)
    print(colorize("  [runserver] Redis started ✓", fg="green"))
    return proc



def _start_celery():
    """Start Celery worker as a background process."""
    celery_bin = shutil.which("celery")

    # Fallback: look inside the venv
    if not celery_bin:
        venv_celery = os.path.join(
            os.path.dirname(sys.executable), "celery"
        )
        if os.path.exists(venv_celery):
            celery_bin = venv_celery

    if not celery_bin:
        print(colorize(
            "  [runserver] WARNING: celery not found — skipping Celery startup.",
            fg="yellow"
        ))
        return None

    print(colorize("  [runserver] Starting Celery worker...", fg="cyan"))
    proc = subprocess.Popen(
        [celery_bin, "-A", "config", "worker", "--loglevel=info",
         "--concurrency=2", "-n", "worker@%h"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1)
    print(colorize("  [runserver] Celery worker started ✓", fg="green"))
    return proc


class Command(BaseRunserverCommand):
    help = (
        "Start Django development server along with Redis and Celery worker."
    )

    def handle(self, *args, **options):
        print(colorize("\n🚀 Nextbin Dev Server — starting all services\n", fg="magenta"))

        redis_proc = _start_redis()
        if redis_proc:
            _background_procs.append(redis_proc)

        celery_proc = _start_celery()
        if celery_proc:
            _background_procs.append(celery_proc)

        print(colorize("\n  [runserver] Starting Django...\n", fg="cyan"))

        try:
            super().handle(*args, **options)
        finally:
            print(colorize("\n\n  [runserver] Shutting down Redis and Celery...", fg="yellow"))
            _kill_all()
            print(colorize("  [runserver] All services stopped. Goodbye!\n", fg="green"))
