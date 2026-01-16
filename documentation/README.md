# Documentación - Intelli

Esta carpeta contiene toda la documentación del proyecto Intelli organizada en orden de lectura recomendado.

## Orden de Lectura Recomendado

Sigue este orden para una mejor comprensión del proyecto:

1. **[a-README.md](a-README.md)** - Introducción general al proyecto
   - Estructura del proyecto
   - Quick Start para desarrollo
   - Guía rápida de inicio

2. **[b-DEPLOYMENT.md](b-DEPLOYMENT.md)** - Guía completa de deployment en producción
   - Requisitos previos
   - Preparación del servidor
   - Configuración inicial
   - Configuración de SSL
   - Deployment
   - Verificación y mantenimiento
   - Troubleshooting

3. **[c-DEPLOYMENT_SCRIPTS.md](c-DEPLOYMENT_SCRIPTS.md)** - Documentación de scripts de deployment
   - Descripción de cada script
   - Uso de cada script
   - Orden de ejecución recomendado
   - Troubleshooting

4. **[d-ENV_SETUP.md](d-ENV_SETUP.md)** - Configuración de variables de entorno
   - Configuración de variables de entorno
   - Generación de SECRET_KEY
   - Configuración de CORS y CSRF

5. **[e-ENV_FILES_README.md](e-ENV_FILES_README.md)** - Variables de entorno de infraestructura
   - Archivos `.docker.env` y `.django.env`
   - Configuración de producción
   - Variables críticas

6. **[f-INFRASTRUCTURE_README.md](f-INFRASTRUCTURE_README.md)** - Infraestructura y Docker Compose
   - Configuración de servicios
   - Quick Start
   - Desarrollo y producción

7. **[g-BACKEND_README.md](g-BACKEND_README.md)** - Documentación del backend
   - Estructura del backend
   - Configuración de Django
   - APIs disponibles

8. **[h-FRONTEND_README.md](h-FRONTEND_README.md)** - Documentación del frontend
   - Estructura del frontend
   - Configuración de Next.js
   - Características

9. **[i-TRANSLATION_CHECK.md](i-TRANSLATION_CHECK.md)** - Verificación de traducciones
   - Guía para verificar traducciones
   - Herramientas de traducción

## Guía Rápida

- **¿Primera vez?** → Empieza con [a-README.md](a-README.md)
- **¿Desplegar en producción?** → Lee [b-DEPLOYMENT.md](b-DEPLOYMENT.md) y [c-DEPLOYMENT_SCRIPTS.md](c-DEPLOYMENT_SCRIPTS.md)
- **¿Configurar variables de entorno?** → Consulta [d-ENV_SETUP.md](d-ENV_SETUP.md) y [e-ENV_FILES_README.md](e-ENV_FILES_README.md)
- **¿Desarrollo local?** → Revisa [f-INFRASTRUCTURE_README.md](f-INFRASTRUCTURE_README.md)

## Documentación Técnica Adicional

La documentación técnica adicional (README.md en subcarpetas de backend y frontend) se mantiene en sus respectivas ubicaciones dentro del código para referencia rápida durante el desarrollo.
