# Guía Manual de Pruebas - Funcionalidad de Cancelar y Reintentar

Esta guía te ayudará a probar manualmente todas las funcionalidades de cancelar y reintentar imágenes.

## Prerrequisitos

1. **Backend corriendo:**
   ```bash
   cd backend
   python manage.py runserver
   ```

2. **Celery Worker corriendo:**
   ```bash
   cd backend
   celery -A config worker -l info -Q ingestion_io,charts_cpu,ai
   ```

3. **Frontend corriendo:**
   ```bash
   cd frontend
   npm run dev
   ```

4. **Redis corriendo:**
   ```bash
   cd infrastructure
   docker-compose up -d redis
   ```

## Escenario 1: Probar con Script Automatizado

### Paso 1: Ejecutar el script de prueba

```bash
cd backend
python scripts/test_retry_cancel.py
```

El script creará un job de prueba con tareas en diferentes estados:
- ✅ SUCCESS (completada)
- ❌ FAILED (fallida)
- 🔄 RUNNING (atascada en 0%)
- ⏳ PENDING (pendiente)
- 🚫 CANCELLED (cancelada)

### Paso 2: Verificar en el Frontend

1. Abre el navegador en: `http://localhost:3000`
2. Navega al job creado (el script mostrará el ID)
3. Verifica que:
   - Las imágenes exitosas muestran la imagen
   - Las imágenes fallidas muestran el botón "Retry"
   - Las imágenes atascadas (RUNNING con 0%) muestran botones "Cancel" y "Retry"
   - Las imágenes pendientes muestran botones "Cancel" y "Retry"
   - Las imágenes canceladas muestran el botón "Retry"

## Escenario 2: Simular Imagen Atascada

### Paso 1: Crear un Job Real

1. Sube un archivo Excel desde el frontend
2. Espera a que algunas imágenes se generen
3. Si todas se generan exitosamente, continúa al siguiente escenario

### Paso 2: Simular una Tarea Atascada

**Opción A: Usando Django Shell**

```bash
cd backend
python manage.py shell
```

```python
from apps.jobs.models import ImageTask, Job

# Encuentra un job activo
job = Job.objects.filter(status='RUNNING').first()
if job:
    # Encuentra una tarea RUNNING
    task = job.image_tasks.filter(status='RUNNING').first()
    if task:
        # Simula que está atascada (ya debería estar en RUNNING)
        # Solo verifica que progress sea 0
        print(f"Task {task.id} está en estado {task.status} con {task.progress}% de progreso")
        print(f"Puedes cancelarla o reintentarla desde el frontend")
    else:
        # Crea una tarea RUNNING manualmente
        task = ImageTask.objects.create(
            job=job,
            algorithm_key='patent_trends_cumulative',
            algorithm_version='1.0',
            status=ImageTask.Status.RUNNING,
            progress=0
        )
        print(f"✅ Creada tarea atascada: {task.id}")
```

**Opción B: Detener el Worker Temporalmente**

1. Detén el Celery worker (Ctrl+C)
2. Crea un nuevo job desde el frontend
3. Las tareas quedarán en estado PENDING o RUNNING
4. Reinicia el worker cuando quieras que continúen

## Escenario 3: Probar Cancelar Imagen Individual

### Paso 1: Preparar el Estado

1. Crea un job con múltiples imágenes
2. Espera a que algunas estén en estado RUNNING o PENDING

### Paso 2: Cancelar una Imagen

1. En el frontend, localiza una imagen en estado RUNNING o PENDING
2. Haz clic en el botón "Cancel"
3. Verifica que:
   - El botón muestra "Cancelling..." mientras procesa
   - La imagen se mueve a la sección "Cancelled"
   - El estado cambia a CANCELLED
   - El WebSocket actualiza el estado en tiempo real

### Paso 3: Verificar en el Backend

```bash
python manage.py shell
```

```python
from apps.jobs.models import ImageTask

# Verifica que la tarea fue cancelada
task = ImageTask.objects.get(id=<TASK_ID>)
print(f"Status: {task.status}")  # Debería ser CANCELLED
```

## Escenario 4: Probar Reintentar Imagen Fallida

### Paso 1: Crear una Imagen Fallida

**Opción A: Usando Django Shell**

```python
from apps.jobs.models import ImageTask, Job

job = Job.objects.filter(status__in=['RUNNING', 'FAILED', 'PARTIAL_SUCCESS']).first()
if job:
    # Crea una tarea fallida
    task = ImageTask.objects.create(
        job=job,
        algorithm_key='top_patent_applicants',
        algorithm_version='1.0',
        status=ImageTask.Status.FAILED,
        progress=0,
        error_code='TEST_ERROR',
        error_message='Error simulado para pruebas'
    )
    print(f"✅ Creada tarea fallida: {task.id}")
```

**Opción B: Forzar un Error Real**

1. Modifica temporalmente un algoritmo para que falle
2. O usa datos inválidos que causen un error

### Paso 2: Reintentar la Imagen

1. En el frontend, localiza la imagen fallida
2. Haz clic en el botón "Retry"
3. Verifica que:
   - El botón muestra "Retrying..." mientras procesa
   - La imagen se mueve a la sección "In Progress"
   - El estado cambia a RUNNING
   - El progreso se resetea a 0%
   - El mensaje de error desaparece
   - El WebSocket actualiza el estado en tiempo real
   - La tarea se reencola y procesa

## Escenario 5: Probar Reintentar Imagen Atascada

### Paso 1: Identificar Imagen Atascada

1. Busca una imagen en estado RUNNING con 0% de progreso
2. Debería mostrar el mensaje: "Task may be stuck. You can retry or cancel."

### Paso 2: Reintentar

1. Haz clic en el botón "Retry"
2. Verifica que:
   - El estado cambia a RUNNING
   - El progreso se resetea
   - La tarea se reencola
   - El worker la procesa nuevamente

## Escenario 6: Probar Reintentar Imagen Cancelada

### Paso 1: Cancelar una Imagen

Sigue el Escenario 3 para cancelar una imagen

### Paso 2: Reintentar

1. En la sección "Cancelled", localiza la imagen cancelada
2. Haz clic en el botón "Retry"
3. Verifica que:
   - La imagen se mueve a "In Progress"
   - El estado cambia a RUNNING
   - La tarea se reencola y procesa

## Escenario 7: Verificar Actualización en Tiempo Real

### Paso 1: Abrir Consola del Navegador

1. Abre las herramientas de desarrollador (F12)
2. Ve a la pestaña "Console"
3. Filtra por "WebSocket" o "WS"

### Paso 2: Observar Eventos

1. Realiza una acción (cancelar o reintentar)
2. Verifica que aparezcan eventos en la consola:
   - `RETRY` event cuando se reintenta
   - `CANCELLED` event cuando se cancela
   - `job_status_changed` event si el job cambia de estado

### Paso 3: Verificar Actualización de UI

1. La UI debería actualizarse automáticamente sin recargar
2. La barra de progreso debería actualizarse
3. Las imágenes deberían moverse entre secciones

## Escenario 8: Probar Validaciones

### Paso 1: Intentar Cancelar Imagen Exitosa

1. Intenta cancelar una imagen en estado SUCCESS
2. Verifica que NO aparece el botón "Cancel"

### Paso 2: Intentar Reintentar Imagen Exitosa

1. Intenta reintentar una imagen en estado SUCCESS
2. Verifica que NO aparece el botón "Retry"

### Paso 3: Intentar Cancelar Imagen Fallida

1. Intenta cancelar una imagen en estado FAILED
2. Verifica que NO aparece el botón "Cancel"

## Verificación de Logs

### Backend Logs

```bash
# En la terminal donde corre el servidor Django
# Deberías ver logs como:
# [INFO] ImageTask X retry requested - task re-enqueued
# [INFO] ImageTask X cancelled
```

### Celery Worker Logs

```bash
# En la terminal donde corre el worker
# Deberías ver:
# [INFO] Task apps.jobs.tasks.generate_image_task[X] received
# [INFO] ImageTask X is cancelled - skipping execution (si fue cancelada)
```

## Checklist de Pruebas

- [ ] ✅ Crear job con script automatizado
- [ ] ✅ Verificar botones en diferentes estados
- [ ] ✅ Cancelar imagen RUNNING
- [ ] ✅ Cancelar imagen PENDING
- [ ] ✅ Reintentar imagen FAILED
- [ ] ✅ Reintentar imagen RUNNING (atascada)
- [ ] ✅ Reintentar imagen PENDING
- [ ] ✅ Reintentar imagen CANCELLED
- [ ] ✅ Verificar actualización en tiempo real (WebSocket)
- [ ] ✅ Verificar que botones no aparecen en estados incorrectos
- [ ] ✅ Verificar que la barra de progreso se actualiza
- [ ] ✅ Verificar que las imágenes se mueven entre secciones
- [ ] ✅ Verificar logs del backend
- [ ] ✅ Verificar logs del Celery worker

## Solución de Problemas

### El botón no aparece

1. Verifica que el estado de la tarea es correcto
2. Revisa la consola del navegador por errores
3. Verifica que la API responde correctamente

### El WebSocket no actualiza

1. Verifica que el WebSocket está conectado (consola del navegador)
2. Revisa los logs del backend para eventos emitidos
3. Verifica que Redis está corriendo

### La tarea no se procesa después de reintentar

1. Verifica que el Celery worker está corriendo
2. Revisa los logs del worker
3. Verifica que la tarea fue reencolada correctamente

## Próximos Pasos

Después de completar todas las pruebas:

1. ✅ Verifica que todas las funcionalidades trabajan correctamente
2. ✅ Documenta cualquier problema encontrado
3. ✅ Prueba con datos reales (archivos Excel grandes)
4. ✅ Prueba con múltiples usuarios simultáneos (si aplica)
