# Expedientes Digitales – Hospital de Diagnóstico (Tarea 3: archivos con versiones)

## Qué hace el sistema
Administra los expedientes digitales del personal del Hospital de Diagnóstico con una base de datos MySQL. La página principal es el **Dashboard**, con el estado de los expedientes y botones a las tablas de Empleados, Documentos y Checklist por perfil.

Permite registrar empleados, consultar y modificar el estado de sus documentos y **subir archivos** (PDF o Word; el documento Título también acepta PNG o JPG). Los archivos se guardan dentro de MySQL y **cada subida es una versión nueva**: nunca se reemplaza la anterior. Cada versión se marca como Vigente, Vencida o Versión anterior, y se puede descargar. El Título abre una página con su imagen.

Un empleado **solo se puede eliminar si está vacío**: todos sus documentos en Pendiente y sin archivos subidos.

## Cómo ejecutarlo desde cero
1. Abrir **XAMPP Control Panel** y pulsar **Start** en **MySQL** y en **Apache** (Apache es para phpMyAdmin).
2. Abrir http://localhost/phpmyadmin → pestaña **Importar** → elegir el archivo `crear_bd.sql` → **Importar**. Esto crea la base `hospital` con sus 4 tablas y los datos de ejemplo.
3. En la terminal, dentro de la carpeta del proyecto:
```
pip install -r requirements.txt
python app.py
```
(En Windows, si `pip` no se reconoce: `py -m pip install -r requirements.txt` y `py app.py`.)
4. Abrir en el navegador:
- http://127.0.0.1:5000/  (Dashboard, página principal)
- http://127.0.0.1:5000/empleados
- http://127.0.0.1:5000/empleados?perfil=medico  (solo un perfil)
- http://127.0.0.1:5000/empleados?q=ana  (búsqueda por nombre, perfil o archivo)
- http://127.0.0.1:5000/documentos
- http://127.0.0.1:5000/checklist
- http://127.0.0.1:5000/empleados/nuevo
- http://127.0.0.1:5000/documentos/1/subir  (subir un archivo al DUI de Ana)

La conexión usa `host=localhost, user=root, password=""` (valores por defecto de XAMPP).

El tamaño máximo de archivo es **500 KB** (`TAMANO_MAXIMO`), por debajo del `max_allowed_packet` de 1 MB que trae XAMPP. Para pruebas se usan solo archivos inventados, nunca documentos reales.

## Estructura de archivos
```
app.py            rutas de Flask y lógica (mysql-connector-python, parámetros %s)
crear_bd.sql      crea la base, las 4 tablas y carga los datos de ejemplo
requirements.txt  flask y mysql-connector-python
README.md         documentación
templates/        base.html, resumen.html (dashboard), empleados.html, detalle.html, nuevo.html,
                  editar.html, documentos.html, checklist.html, subir.html, versiones.html,
                  imagen.html, no_eliminar.html, error_bd.html
static/           style.css, logo_blanco.png, marca_blanca.png, favicon.png, titulo_ejemplo.png
```

## Rutas
| Ruta | Método | Qué hace |
|---|---|---|
| `/` | GET | Dashboard (página principal): expedientes completos/incompletos, documentos vigentes/vencidos y botones a las tablas |
| `/resumen` | GET | El mismo Dashboard |
| `/empleados` | GET | Lista empleados y documentos (consulta con JOIN). `?perfil=` filtra por perfil y `?q=` busca por nombre, perfil o nombre de archivo |
| `/empleados/<id>` | GET | Detalle de un empleado con sus documentos y número de versiones |
| `/empleados/nuevo` | GET, POST | Registro con validación |
| `/empleados/eliminar/<id>` | POST | Elimina solo si el empleado está vacío; si no, muestra "No se puede eliminar" (409) |
| `/documentos` | GET | Tabla de todos los documentos; `?tipo=` muestra solo un tipo |
| `/documentos/editar/<id>` | GET, POST | Modifica el estado de un documento con validación |
| `/documentos/<id>/subir` | GET, POST | Sube un archivo con validaciones y crea una versión nueva |
| `/documentos/<id>/versiones` | GET | Lista las versiones con su estado (Vigente, Vencido, Versión anterior) |
| `/documentos/<id>/imagen` | GET | Página del Título con su imagen y opción para agregar otra |
| `/archivos/descargar/<id>` | GET | Descarga un archivo guardado en MySQL |
| `/archivos/ver/<id>` | GET | Muestra una imagen guardada en MySQL |
| `/checklist` | GET | Qué documentos exige cada perfil |

## Base de datos (MySQL: `hospital`)
- `checklist` (id PK, perfil, documento): documentos que exige cada perfil.
- `empleados` (id PK, nombre, perfil, fecha_ingreso, correo): tabla principal.
- `documentos` (id PK, empleado_id FK, documento, estado): un documento requerido de un empleado.
- `archivos` (id PK, documento_id FK, tipo_documento, nombre_original, version, fecha_vencimiento, contenido LONGBLOB, fecha_subida): cada archivo subido es una fila; `UNIQUE (documento_id, version)`.

Relaciones: `documentos.empleado_id` → `empleados(id)` y `archivos.documento_id` → `documentos(id)`, ambas con `ON DELETE CASCADE`, así que no quedan registros huérfanos.

## Cómo funciona la subida de archivos
1. El formulario lleva `enctype="multipart/form-data"`; el archivo llega con `request.files.get("archivo")`.
2. Validaciones en orden: que haya archivo, extensión permitida, que no esté vacío, que no pase 500 KB, que una imagen sea PNG o JPG de verdad (primeros bytes) y la fecha de vencimiento en formato AAAA-MM-DD (obligatoria para el DUI). Si una falla, no se guarda nada.
3. Versión: `SELECT MAX(version)`; si no hay ninguna es 1, si hay es la última + 1. Se inserta una fila nueva con `%s` (evita la inyección SQL).

## Cómo funciona el Dashboard
Recorre a todos los empleados con `for` y, para cada uno, la última versión de cada documento. Decide con `if/elif/else` si cada documento está vigente, vencido o sin archivo, y si el expediente está completo o incompleto. Los contadores se muestran en tarjetas, junto con el porcentaje de expedientes completos.

## Integrantes (una rama y un pull request por integrante)
- **Mariana Salazar** (GitHub: `marianasalazar17`): conexión a MySQL, tabla `archivos`, constantes, diseño del Hospital de Diagnóstico, Dashboard como página principal, detalle del empleado y Checklist.
- **Fiorella Funes** (GitHub: `Fiore463`): registro con validación y eliminación. Mejora: validaciones extra al registrar (nombre de mínimo 3 letras y correo no repetido), subida de archivos con validaciones y eliminación solo de empleados vacíos.
- **Fernanda Pocasangre** (GitHub: `fernandapocaa-tech`): consulta con JOIN y modificación con validación. Mejora: versiones con estados, descarga, página de imagen del Título y búsqueda por nombre, perfil o nombre de archivo.
- **Alejandra Palma** (GitHub: `alepal1`): Dashboard con archivos reales, tabla Documentos y porcentaje de expedientes completos con barra de progreso.

## Video
Enlace de YouTube: (pendiente)
