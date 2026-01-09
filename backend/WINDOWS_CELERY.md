# Celery en Windows - Guía de Solución de Problemas

## Problema: Errores de "handle is invalid" o "Access is denied"

Si ves errores como:
```
OSError: [WinError 6] The handle is invalid
PermissionError: [WinError 5] Access is denied
```

Esto es un problema conocido de Celery en Windows. El pool de procesos por defecto (`prefork`) no funciona bien en Windows debido a cómo Windows maneja el forking de procesos.

## Solución: Usar Pool 'solo'

### Opción 1: Usar el script helper (Recomendado)

El script `start_celery_worker.ps1` ya está configurado para usar `--pool=solo`:

```powershell
.\scripts\start_celery_worker.ps1
```

### Opción 2: Comando manual

```powershell
celery -A config worker -l info -Q ingestion_io,charts_cpu,ai --pool=solo
```

### Opción 3: Configuración automática (Recomendado)

El archivo `config/celery.py` detecta automáticamente el sistema operativo:
- **Windows**: Usa `solo` pool automáticamente
- **Linux/macOS**: Usa `prefork` pool por defecto (mejor rendimiento)

No necesitas especificar `--pool` en la línea de comandos, la configuración lo maneja automáticamente.

## Limitaciones del Pool 'solo'

El pool `solo` ejecuta tareas en el hilo principal, lo que significa:

- ✅ Funciona en Windows sin errores
- ⚠️ Las tareas se ejecutan secuencialmente (una a la vez)
- ⚠️ No hay paralelización real de tareas

## Alternativas para Mejor Rendimiento en Windows

### Opción 1: WSL2 (Windows Subsystem for Linux)

WSL2 permite ejecutar Linux nativamente en Windows, donde Celery funciona perfectamente:

```bash
# En WSL2
celery -A config worker -l info -Q ingestion_io,charts_cpu,ai
```

### Opción 2: Docker

Ejecutar Celery en un contenedor Docker con Linux:

```dockerfile
# Dockerfile para Celery worker
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["celery", "-A", "config", "worker", "-l", "info"]
```

### Opción 3: Máquina Virtual Linux

Usar una VM con Linux para desarrollo.

## Verificación

Después de iniciar el worker con `--pool=solo`, deberías ver:

```
[INFO/MainProcess] Connected to redis://localhost:6379/0
[INFO/MainProcess] mingle: searching for neighbors
[INFO/MainProcess] mingle: all alone
[INFO/MainProcess] celery@HOSTNAME ready.
```

Sin errores de "handle is invalid" o "Access is denied".

## Configuración Permanente

Si quieres que siempre use `solo` en Windows, puedes agregar esto a tu `.env`:

```env
# Para desarrollo en Windows
CELERY_WORKER_POOL=solo
```

Y luego modificar el script para leer esta variable.

## Referencias

- [Celery Windows Documentation](https://docs.celeryq.dev/en/stable/faq.html#does-celery-work-on-windows)
- [Issue: Celery on Windows](https://github.com/celery/celery/issues/4081)
