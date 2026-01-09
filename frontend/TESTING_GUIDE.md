# Guía de Pruebas Frontend - Cancelar y Reintentar Imágenes

Esta guía te ayudará a probar la funcionalidad de cancelar y reintentar imágenes desde el frontend.

## Prerrequisitos

1. Backend corriendo en `http://localhost:8000`
2. Frontend corriendo en `http://localhost:3000`
3. Celery worker activo
4. Redis corriendo

## Pruebas Visuales

### 1. Verificar Estados de Imágenes

1. Abre `http://localhost:3000`
2. Crea un nuevo job o navega a un job existente
3. Verifica que las imágenes se muestran en secciones correctas:
   - **Generated Images**: Imágenes exitosas (verde)
   - **In Progress**: Imágenes en proceso (azul)
   - **Failed**: Imágenes fallidas (rojo)
   - **Cancelled**: Imágenes canceladas (gris)

### 2. Verificar Botones por Estado

#### Imagen SUCCESS
- ✅ NO debe mostrar botón "Cancel"
- ✅ NO debe mostrar botón "Retry"
- ✅ Debe mostrar botones "Download PNG" y "Download SVG" (si existen)

#### Imagen FAILED
- ✅ NO debe mostrar botón "Cancel"
- ✅ SÍ debe mostrar botón "Retry"
- ✅ Debe mostrar el mensaje de error

#### Imagen RUNNING (con progreso > 0)
- ✅ SÍ debe mostrar botón "Cancel"
- ✅ SÍ debe mostrar botón "Retry"
- ✅ Debe mostrar el spinner y el porcentaje de progreso

#### Imagen RUNNING (con progreso = 0%, atascada)
- ✅ SÍ debe mostrar botón "Cancel"
- ✅ SÍ debe mostrar botón "Retry"
- ✅ Debe mostrar mensaje: "Task may be stuck. You can retry or cancel."

#### Imagen PENDING
- ✅ SÍ debe mostrar botón "Cancel"
- ✅ SÍ debe mostrar botón "Retry"
- ✅ Debe mostrar el spinner

#### Imagen CANCELLED
- ✅ NO debe mostrar botón "Cancel"
- ✅ SÍ debe mostrar botón "Retry"
- ✅ Debe mostrar mensaje: "Generation Cancelled"

## Pruebas de Funcionalidad

### Prueba 1: Cancelar Imagen RUNNING

**Pasos:**
1. Localiza una imagen en estado RUNNING
2. Haz clic en "Cancel"
3. Observa el comportamiento

**Resultado Esperado:**
- El botón cambia a "Cancelling..." con spinner
- La imagen se mueve a la sección "Cancelled"
- El estado cambia a CANCELLED
- El WebSocket actualiza el estado en tiempo real
- La tarea se cancela en el backend

### Prueba 2: Cancelar Imagen PENDING

**Pasos:**
1. Localiza una imagen en estado PENDING
2. Haz clic en "Cancel"
3. Observa el comportamiento

**Resultado Esperado:**
- Similar a Prueba 1
- La imagen se cancela antes de empezar a procesarse

### Prueba 3: Reintentar Imagen FAILED

**Pasos:**
1. Localiza una imagen en estado FAILED
2. Haz clic en "Retry"
3. Observa el comportamiento

**Resultado Esperado:**
- El botón cambia a "Retrying..." con spinner
- La imagen se mueve a "In Progress"
- El estado cambia a RUNNING
- El mensaje de error desaparece
- El progreso se resetea a 0%
- El WebSocket actualiza el estado
- La tarea se reencola y procesa

### Prueba 4: Reintentar Imagen Atascada (RUNNING 0%)

**Pasos:**
1. Localiza una imagen RUNNING con 0% de progreso
2. Verifica que muestra el mensaje de advertencia
3. Haz clic en "Retry"
4. Observa el comportamiento

**Resultado Esperado:**
- Similar a Prueba 3
- La tarea se resetea y reencola
- El worker la procesa nuevamente

### Prueba 5: Reintentar Imagen CANCELLED

**Pasos:**
1. Cancela una imagen primero (Prueba 1)
2. Localiza la imagen en la sección "Cancelled"
3. Haz clic en "Retry"
4. Observa el comportamiento

**Resultado Esperado:**
- La imagen se mueve a "In Progress"
- El estado cambia a RUNNING
- La tarea se reencola y procesa

### Prueba 6: Múltiples Acciones Simultáneas

**Pasos:**
1. Cancela múltiples imágenes a la vez
2. Reintenta múltiples imágenes a la vez
3. Observa el comportamiento

**Resultado Esperado:**
- Cada acción se procesa independientemente
- Los estados se actualizan correctamente
- No hay conflictos entre acciones

## Pruebas de WebSocket

### Verificar Conexión WebSocket

1. Abre las herramientas de desarrollador (F12)
2. Ve a la pestaña "Console"
3. Busca mensajes relacionados con WebSocket:
   - "WebSocket connected"
   - "WebSocket message received"

### Verificar Eventos en Tiempo Real

1. Realiza una acción (cancelar o reintentar)
2. Observa la consola del navegador
3. Deberías ver eventos como:
   ```javascript
   {
     event_type: "RETRY",
     entity_type: "image_task",
     entity_id: 123,
     ...
   }
   ```

### Verificar Actualización de UI

1. Realiza una acción
2. Observa que la UI se actualiza sin recargar la página
3. Verifica que:
   - Las imágenes se mueven entre secciones
   - Los estados cambian
   - La barra de progreso se actualiza

## Pruebas de Errores

### Prueba 1: Error de Red

**Simulación:**
1. Detén el servidor backend temporalmente
2. Intenta cancelar o reintentar una imagen
3. Reinicia el servidor

**Resultado Esperado:**
- Se muestra un error en la consola
- El botón vuelve a su estado normal
- El usuario puede intentar nuevamente

### Prueba 2: Tarea Ya Cancelada

**Simulación:**
1. Cancela una imagen
2. Intenta cancelarla nuevamente (si el botón aún aparece)

**Resultado Esperado:**
- El backend devuelve un error 400
- Se muestra el error en la consola
- El estado no cambia

### Prueba 3: Tarea Ya Completada

**Simulación:**
1. Espera a que una imagen se complete
2. Intenta cancelarla o reintentarla

**Resultado Esperado:**
- Los botones no aparecen para imágenes SUCCESS
- No se puede realizar la acción

## Pruebas de Rendimiento

### Prueba 1: Múltiples Imágenes

1. Crea un job con 10+ imágenes
2. Cancela/reintenta múltiples imágenes
3. Observa el rendimiento

**Resultado Esperado:**
- La UI responde rápidamente
- No hay lag o congelamiento
- Los estados se actualizan correctamente

### Prueba 2: Actualizaciones Rápidas

1. Cancela/reintenta imágenes rápidamente
2. Observa el comportamiento

**Resultado Esperado:**
- Cada acción se procesa correctamente
- No hay conflictos
- Los estados se mantienen consistentes

## Checklist de Pruebas Frontend

- [ ] ✅ Verificar que los botones aparecen en los estados correctos
- [ ] ✅ Verificar que los botones NO aparecen en estados incorrectos
- [ ] ✅ Probar cancelar imagen RUNNING
- [ ] ✅ Probar cancelar imagen PENDING
- [ ] ✅ Probar reintentar imagen FAILED
- [ ] ✅ Probar reintentar imagen RUNNING (atascada)
- [ ] ✅ Probar reintentar imagen PENDING
- [ ] ✅ Probar reintentar imagen CANCELLED
- [ ] ✅ Verificar actualización en tiempo real (WebSocket)
- [ ] ✅ Verificar mensajes de error
- [ ] ✅ Verificar estados de loading
- [ ] ✅ Verificar que las imágenes se mueven entre secciones
- [ ] ✅ Verificar que la barra de progreso se actualiza
- [ ] ✅ Probar con múltiples imágenes
- [ ] ✅ Probar acciones rápidas
- [ ] ✅ Verificar manejo de errores de red

## Herramientas de Depuración

### React DevTools

1. Instala React DevTools en el navegador
2. Inspecciona los componentes
3. Verifica el estado de los componentes

### Redux DevTools (si aplica)

1. Abre Redux DevTools
2. Observa las acciones dispatchadas
3. Verifica el estado del store

### Network Tab

1. Abre la pestaña "Network" en DevTools
2. Filtra por "XHR" o "Fetch"
3. Observa las peticiones a la API:
   - `POST /api/image-tasks/{id}/cancel/`
   - `POST /api/image-tasks/{id}/retry/`

## Comandos Útiles

### Ver Logs del Frontend

```bash
# En la terminal donde corre el frontend
# Los logs aparecerán automáticamente
```

### Limpiar Cache del Navegador

1. Abre DevTools (F12)
2. Click derecho en el botón de recargar
3. Selecciona "Empty Cache and Hard Reload"

### Ver Estado de React Query

1. Abre DevTools
2. Busca la extensión React Query DevTools
3. Observa el estado de las queries

## Próximos Pasos

Después de completar las pruebas:

1. ✅ Documenta cualquier bug encontrado
2. ✅ Verifica que todas las funcionalidades trabajan
3. ✅ Prueba en diferentes navegadores
4. ✅ Prueba en diferentes tamaños de pantalla (responsive)
