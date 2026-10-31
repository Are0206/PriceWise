# Informe de pruebas

## Entorno

- macOS, Python 3.14.6, Django 6.0.7 y Pillow 12.3.0 en el entorno local (versiones de partida).
- Venv temporal con Django 6.0.8, Pillow 13.0.0 y requests 2.34.2 (versiones finales de `requirements.txt`).
- Base de datos real del proyecto para mediciones: 5.043 productos, 6.540 precios, 6.790 filas de historial.
- Navegador: Chromium integrado en la app de escritorio, servidor `runserver` en `localhost:8765`.

## Comandos

```bash
python manage.py test
python manage.py makemigrations --check --dry-run
python manage.py check --deploy            # con DJANGO_ENV=production y variables de ejemplo
python manage.py sqlmigrate products 0013
pip-audit -r requirements.txt              # en un venv temporal
```

## Resultados

| Prueba | Antes | Después |
|---|---|---|
| Suite completa | 60 tests, OK | 129 tests, OK (Django 6.0.7 y 6.0.8) |
| `makemigrations --check` | Sin cambios | Sin cambios (después de crear `0013`) |
| `check --deploy` | 7 avisos | Perfil de desarrollo: 6 (esperado, W020 desaparece por los hosts por defecto); perfil de producción: 2 aceptados (W005, W021) |
| `pip-audit` | 42 avisos (Pillow 39, Django 3) | 0 |
| Consultas del catálogo | 27 por página | 4 (fijado con `assertNumQueries`) |
| Migración `0013` sobre copia | — | 20 tablas con los mismos conteos; `PRAGMA integrity_check` ok |

### Tests por archivo

| Archivo | Antes | Después | Qué cubren los nuevos |
|---|---|---|---|
| `pricewise/tests.py` | 0 | 19 | Booleanos estrictos, lectura de `.env`, validación de producción, perfiles en subproceso limpio, `check --deploy`, plantilla 500 |
| `products/tests.py` | 24 | 52 | Precios no finitos, favoritos (alterna, GET no cambia nada, redirección segura, vuelve a la tarjeta, `aria-pressed`), filtros combinados, mensajes de reseña, integridad (`PROTECT`, rango de calificación), autorización negativa, precio más barato con y sin precarga, número de consultas, 404 propia, admin |
| `products/test_client.py` | 0 | 12 | Política de reintentos: 5xx con backoff, límite de reintentos, red y timeout, 429 con `Retry-After`, espera excesiva, 4xx sin reintento, JSON inválido, clave inválida, clave oculta en errores |
| `products/test_loaders.py` | 7 | 8 | Conflicto de nombre de supermercado |
| `products/test_pipeline.py` | 7 | 11 | Doble ejecución sin duplicados, historial conservado, rollback por producto, tope de páginas reportado |
| `shopping_lists/tests.py` | 11 | 16 | Tarjetas como fragmento o página completa, enlaces sin JS, error de cantidad, autorización negativa |
| `accounts/tests.py` | 5 | 5 | — |
| `products/test_remove_demo_data.py` | 3 | 3 | — |
| `shopping_lists/test_services.py` | 3 | 3 | — |
| **Total** | **60** | **129** | |

## Pruebas en navegador

| Página o flujo | 375 | 768 | 1024 | 1280 | 1920 | Resultado |
|---|---|---|---|---|---|---|
| Catálogo con sesión | ✓ | ✓ | ✓ | ✓ | ✓ | Sin scroll horizontal; 2/4/3/4/5 columnas; primer producto bajo el header |
| Filtros combinados (`category` + `sort`) | ✓ | | | ✓ | | Los 6 parámetros viajan en el formulario |
| Filtros en el celular | ✓ | ✓ | | | | Plegados sin filtros activos, abiertos con filtro activo |
| Panel de listas con teclado | ✓ | | | | | Abre, foco en "Cerrar listas", Escape cierra, foco vuelve a "Listas", `inert` al cerrar |
| Diálogo de compartir con teclado | | | | ✓ | | Modal, foco en "Cerrar", Escape cierra, foco vuelve a "Compartir" |
| Detalle, comparar, favoritos, supermercados, detalle y creación de lista | ✓ | | | | | Sin scroll horizontal; un `<h1>` por página |
| Consola sin sesión | | | | ✓ | | Sin errores (antes: `TypeError` en cada página) |

## Limitaciones y pruebas pendientes

- Sin cobertura medida: `coverage` no está instalado.
- Solo Chromium; sin Safari, Firefox ni dispositivos reales.
- Sin lector de pantalla real.
- La página 404 propia no se vio en el navegador porque el servidor de desarrollo corre con `DEBUG` encendido; se comprobó con test.
- La integración con Los Precios se probó con clientes falsos; no se ejecutó una sincronización real para no gastar la cuota de la API.
- Logout y el envío del formulario de registro siguen sin test.
- El workflow de CI todavía no ha corrido en GitHub.
- Durante las pruebas, el navegador mantuvo CSS viejo en caché (ver PER-06); se forzó la recarga para verificar.
