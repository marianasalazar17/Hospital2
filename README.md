# Expedientes Digitales del Personal – Hospital de Diagnóstico

Aplicación web en **Flask** (Python) conectada a una base de datos **MySQL**. Sirve para llevar el expediente digital de cada empleado del hospital: qué documentos exige su perfil, cuáles tiene, cuáles están vigentes, cuáles vencieron y cuáles faltan.

Los archivos (PDF, Word e imágenes) se guardan dentro de la base de datos como `LONGBLOB`, y cada vez que se sube un archivo nuevo se crea una **versión** que conserva las anteriores.

---

## 1. Problema que resuelve

Antes, los expedientes del personal estaban en papel. Para confirmar si un médico tenía su solvencia de la PNP o su colegiatura, el personal de recepción tenía que buscar entre carpetas, y muchas veces el documento no aparecía o estaba vencido sin que nadie lo notara.

Con esta aplicación:

- Cada empleado tiene un registro con los documentos que exige su perfil.
- El dashboard muestra de un vistazo cuántos expedientes están completos, cuántos documentos vencieron y cuántos todavía no tienen archivo.
- Los archivos se suben, se versionan y se descargan desde el mismo sistema.
- Solo se puede eliminar a un empleado si no tiene ningún avance, para no perder información por error.

---

## 2. Requisitos

| Herramienta | Para qué sirve |
|---|---|
| XAMPP (MySQL y phpMyAdmin) | Servidor de base de datos local |
| Python 3.10 o más reciente | Ejecutar la aplicación |
| `flask` y `mysql-connector-python` | Se instalan con `requirements.txt` |

---

## 3. Cómo ejecutarlo desde cero

**Paso 1. Iniciar MySQL.** Abrir **XAMPP Control Panel** y pulsar **Start** en **MySQL**. Apache no es necesario para la aplicación, pero sirve para entrar a phpMyAdmin.

**Paso 2. Crear la base de datos.** Abrir http://localhost/phpmyadmin, ir a la pestaña **Importar**, elegir el archivo `crear_bd.sql` y pulsar **Importar**. Este script crea la base `hospital`, sus cuatro tablas y los datos de ejemplo.

**Paso 3. Instalar dependencias y correr la aplicación.** En la carpeta del proyecto:

```
pip install -r requirements.txt
python app.py
```

En Windows, si `pip` no se reconoce, usar `py -m pip install -r requirements.txt` y `py app.py`.

**Paso 4. Abrir el sistema.** Entrar a http://127.0.0.1:5000. La página principal es el dashboard.

**Configuración de conexión.** La función `conectar()` de `app.py` usa `host="localhost"`, `user="root"`, `password=""` y `database="hospital"`. Son los valores por defecto de XAMPP. Si cambian el usuario o la contraseña de MySQL, este es el único lugar que hay que editar.

---

## 4. Páginas y rutas

| Ruta | Método | Función en `app.py` | Qué hace |
|---|---|---|---|
| `/` | GET | `inicio` | Muestra el dashboard (llama a `resumen`) |
| `/resumen` | GET | `resumen` | Dashboard: totales, portales por perfil y pestañas por tipo de documento |
| `/empleados` | GET | `listar` | Tabla de empleados con sus documentos. Acepta `?q=` (buscador) y `?perfil=` (filtro por perfil) |
| `/empleados/nuevo` | GET, POST | `nuevo` | Formulario de registro con validación |
| `/empleados/<id>` | GET | `detalle` | Datos del empleado y sus documentos, con versiones |
| `/empleados/eliminar/<id>` | POST | `eliminar` | Elimina al empleado solo si está vacío. Si no, responde con código 409 |
| `/documentos` | GET | `listar_documentos` | Todos los documentos de todos los empleados. Acepta `?tipo=` |
| `/documentos/<id>/subir` | GET, POST | `subir` | Formulario de subida con validaciones |
| `/documentos/<id>/versiones` | GET | `versiones` | Lista de versiones con su estado y botón de descarga |
| `/documentos/<id>/imagen` | GET | `imagen` | Página de imágenes del documento Título |
| `/documentos/editar/<id>` | GET, POST | `editar` | Cambia el estado del documento entre Pendiente y Completo |
| `/archivos/descargar/<id>` | GET | `descargar` | Descarga el archivo guardado con su nombre original |
| `/archivos/ver/<id>` | GET | `ver_archivo` | Muestra una imagen dentro de la página (no la descarga) |
| `/checklist` | GET | `ver_checklist` | Qué documentos exige cada perfil |

Los filtros se combinan con la ruta. Por ejemplo, `/empleados?perfil=medico` muestra solo los médicos, y `/documentos?tipo=Solvencia PNP` muestra solo ese documento para todo el personal.

---

## 5. Reglas de negocio

### 5.1 Registro de empleados (`nuevo`)

Antes de guardar, se revisa en este orden:

1. El nombre no puede estar vacío y debe tener al menos 3 letras.
2. El perfil debe estar en la lista de perfiles del `checklist`.
3. La fecha de ingreso debe tener el formato `AAAA-MM-DD`.
4. El correo debe tener `@` y un punto.
5. El correo no puede estar repetido en la tabla `empleados`.

Si todo está bien, se inserta el empleado y, por cada documento que exige su perfil en `checklist`, se crea una fila en `documentos` con estado **Pendiente**.

### 5.2 Subida de archivos (`subir`)

Cada subida pasa por tres bloques de validación:

**Archivo:**
- Debe haberse elegido un archivo.
- La extensión debe ser `.pdf`, `.doc` o `.docx`. Para el Título también se aceptan `.png`, `.jpg` y `.jpeg`.
- No puede estar vacío.
- No puede pesar más de **500 KB** (`TAMANO_MAXIMO`). Este límite está por debajo del `max_allowed_packet` de 1 MB que trae XAMPP por defecto.
- Si es imagen, el contenido debe empezar con la firma real de un PNG (`\x89PNG`) o de un JPG (`\xff\xd8`). Así no basta con cambiar la extensión de un archivo para que pase.

**Fecha de vencimiento:**
- Si se escribe, debe tener el formato `AAAA-MM-DD`.
- Es **obligatoria** para los documentos de la lista `DOCUMENTOS_CON_VENCIMIENTO` (por ahora, el DUI).

**Versión:**
- La nueva versión es `MAX(version) + 1` para ese documento. La primera es la 1.
- Se marca el documento como **Completo**.
- Si el archivo es imagen, se redirige a `/documentos/<id>/imagen`. Si no, a `/documentos/<id>/versiones`.

Si alguna validación falla, la página vuelve a mostrar el formulario con el mensaje de error y no se guarda nada.

### 5.3 Estado de cada versión (`estado_version`)

| Condición | Estado |
|---|---|
| No es la versión más reciente | **Versión anterior** |
| Es la más reciente y tiene fecha de vencimiento anterior a hoy | **Vencido** |
| Es la más reciente y no ha vencido (o no tiene fecha) | **Vigente** |

### 5.4 Clasificación del expediente

Hay dos lugares donde se clasifica, y usan criterios distintos a propósito:

- **Dashboard (`resumen`).** Un empleado está **Completo** si todos sus documentos requeridos tienen una versión vigente. Si no tiene documentos requeridos, aparece como **Sin documentos requeridos**. En cualquier otro caso, **Incompleto**.
- **Tabla de empleados (`listar`).** Un empleado está **Completo** si ninguno de sus documentos sigue en Pendiente.

### 5.5 Eliminar empleados (`eliminar`)

Un empleado solo se elimina si **ninguno** de sus documentos tiene avance. Se cuenta como avance cualquier documento que:

- esté en un estado distinto de Pendiente, o
- tenga al menos un archivo subido.

Si hay avance, la aplicación responde con la página `no_eliminar.html` y código HTTP **409**, y no borra nada. Si no hay avance, se borra el empleado y sus documentos se eliminan por `ON DELETE CASCADE`.

---

## 6. Base de datos (`hospital`)

El script `crear_bd.sql` crea cuatro tablas:

```
checklist                       empleados
---------                       ---------
id           PK                 id           PK
perfil                          nombre
documento                       perfil
                                fecha_ingreso
                                correo

documentos                      archivos
----------                      --------
id              PK              id                PK
empleado_id     FK ──────────►  empleados.id       documento_id   FK ──► documentos.id
documento                       tipo_documento
estado                          nombre_original
                                version           (UNIQUE con documento_id)
                                fecha_vencimiento
                                contenido         LONGBLOB
                                fecha_subida
```

| Tabla | Qué guarda | Relaciones |
|---|---|---|
| `checklist` | Qué documentos exige cada perfil. Es la plantilla del sistema | Ninguna |
| `empleados` | Datos del personal | Un empleado tiene muchos documentos |
| `documentos` | Un registro por cada documento de cada empleado, con su estado | `empleado_id` → `empleados.id`, con `ON DELETE CASCADE` |
| `archivos` | Cada versión subida de un documento, con el contenido del archivo | `documento_id` → `documentos.id`, con `ON DELETE CASCADE`. La pareja `(documento_id, version)` es única |

**Por qué `archivos` guarda el contenido.** La práctica del curso pide guardar los archivos en MySQL. Como el contenido es un `LONGBLOB`, las consultas de listado nunca lo traen. Solo se pide el contenido en `descargar` y `ver_archivo`, que atienden un archivo a la vez.

**Consultas con JOIN.** El listado de empleados (`listar`) usa un `LEFT JOIN` entre `empleados` y `documentos`, para que aparezcan también los empleados sin documentos. La tabla de documentos (`listar_documentos`) usa un `JOIN` con `archivos` y un `GROUP BY` para contar las versiones de cada documento con `COUNT(a.id)`.

---

## 7. Búsqueda

El buscador de `/empleados?q=texto` filtra por tres condiciones unidas con `OR`:

1. El nombre del empleado contiene el texto (`LIKE`).
2. El perfil contiene el texto (`LIKE`).
3. Alguno de sus archivos tiene ese texto en el nombre original (`EXISTS` sobre `archivos.nombre_original`).

Todas las consultas usan parámetros `%s` en lugar de concatenar texto, para evitar inyección SQL.

---

## 8. Manejo de errores

- Si MySQL no está encendido o la conexión falla, la aplicación no se cae. Un manejador global (`@app.errorhandler(mysql.connector.Error)`) muestra la página `error_bd.html` con código **503**.
- Si un documento o archivo no existe, la aplicación responde con código **404**.
- Si se intenta eliminar un empleado con avance, responde con código **409**.

---

## 9. Estructura de archivos

```
app.py              rutas de Flask, validaciones y consultas SQL
crear_bd.sql        crea la base hospital, sus tablas y los datos de ejemplo
requirements.txt    flask y mysql-connector-python
README.md           esta documentación
templates/          plantillas HTML (base, dashboard, empleados, documentos,
                    versiones, imagen, subir, editar, detalle, checklist, nuevo,
                    no_eliminar, error_bd)
static/style.css    única hoja de estilos, con los colores del Hospital de Diagnóstico
```

---

## 10. Diseño visual

La interfaz usa los colores azules del logo del hospital, la tipografía de Google Fonts, y muestra el pie de página con las tres sedes (Colonia Médica, Colonia Escalón y Santa Elena) y los valores de la institución. Toda la estilación está en `static/style.css`.

---

## 11. Integrantes y aportes

| Integrante | GitHub | Aporte principal |
|---|---|---|
| Mariana Salazar | `marianasalazar17` | Conexión a MySQL, página de detalle del empleado y checklist |
| Fiorella Funes | `Fiore463` | Registro con validación, subida de archivos con validaciones y regla para eliminar |
| Fernanda Pocasangre | `fernandapocaa-tech` | Listado de versiones con estado, descarga, página de imagen del Título, buscador y pestañas por perfil |
| Alejandra Palma | `alepal1` | Dashboard, tabla de documentos y resumen |

Cada integrante trabajó en su propia rama y abrió su propio pull request.

---

## 12. Datos de prueba

Los empleados, los documentos y los archivos de ejemplo son inventados. Este repositorio es público, así que no se deben subir documentos reales.
