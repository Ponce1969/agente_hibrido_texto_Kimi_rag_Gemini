# 🍊 Configuración de Gunicorn para Orange Pi 5 Plus
# Optimizado para RK3588 con 8 cores y 16GB RAM

import multiprocessing
import os

# Binding
bind = "0.0.0.0:8000"
backlog = 2048

# Workers
# Fórmula: (2 × CPU) + 1, pero ajustado por carga de LLMs
workers = int(os.getenv("GUNICORN_WORKERS", "4"))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000  # Reciclar workers después de N requests
max_requests_jitter = 50  # Añadir aleatoriedad para evitar restart simultáneo

# Threads (solo si usas sync workers, no aplica para UvicornWorker)
threads = 1

# Timeouts
timeout = 120  # Importante para LLMs que pueden tardar
keepalive = 5
graceful_timeout = 30

# Logging
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "agente_hibrido_fastapi"

# Server mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# SSL (para futuro)
# keyfile = "/path/to/key.pem"
# certfile = "/path/to/cert.pem"

# Preload app (carga el código antes de fork, ahorra RAM)
preload_app = True

# Hooks
def on_starting(server):
    """Ejecutado antes de iniciar el master process"""
    print("🍊 Iniciando Gunicorn en Orange Pi 5 Plus...")
    print(f"   Workers: {workers}")
    print(f"   Worker class: {worker_class}")
    print(f"   Timeout: {timeout}s")

def on_reload(server):
    """Ejecutado cuando se recarga la configuración"""
    print("🔄 Recargando configuración...")

def when_ready(server):
    """Ejecutado cuando el servidor está listo"""
    print("✅ Servidor listo para recibir requests")

def worker_int(worker):
    """Ejecutado cuando un worker recibe SIGINT o SIGQUIT"""
    print(f"⚠️  Worker {worker.pid} interrumpido")

def worker_abort(worker):
    """Ejecutado cuando un worker recibe SIGABRT"""
    print(f"❌ Worker {worker.pid} abortado")

def pre_fork(server, worker):
    """Ejecutado antes de hacer fork de un worker"""
    pass

def post_fork(server, worker):
    """Ejecutado después de hacer fork de un worker"""
    print(f"👶 Worker spawned (pid: {worker.pid})")

def post_worker_init(worker):
    """Ejecutado después de inicializar un worker"""
    pass

def worker_exit(server, worker):
    """Ejecutado cuando un worker sale"""
    print(f"👋 Worker exited (pid: {worker.pid})")

def child_exit(server, worker):
    """Ejecutado cuando un child process sale"""
    pass

def nworkers_changed(server, new_value, old_value):
    """Ejecutado cuando cambia el número de workers"""
    print(f"📊 Workers changed: {old_value} → {new_value}")

def on_exit(server):
    """Ejecutado cuando el master process sale"""
    print("👋 Apagando Gunicorn...")
