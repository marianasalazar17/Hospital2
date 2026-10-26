# Expedientes Digitales – Hospital de Diagnóstico (Desafío 2: MySQL)

## Qué hace el sistema
Administra los expedientes digitales del personal del hospital con una base de datos MySQL. Permite registrar empleados, consultar el estado de sus documentos (según su perfil), modificar el estado de un documento y eliminar empleados. El resumen clasifica cada expediente como completo o incompleto y cuenta cuántos hay de cada tipo.

## Cómo ejecutarlo desde cero
1. Abrir **XAMPP Control Panel** y pulsar **Start** en **MySQL** (también se puede iniciar Apache para usar phpMyAdmin).
2. Abrir http://localhost/phpmyadmin → pestaña **Importar** → elegir el archivo `crear_bd.sql` → **Importar**. Esto crea la base `hospital` con sus tablas y datos de ejemplo.
3. En la terminal, dentro de la carpeta del proyecto:
```
pip install -r requirements.txt
python app.py
```
(En Windows, si `pip` no se reconoce: `py -m pip install -r requirements.txt` y `py app.py`.)
4. Abrir en el navegador:
- http://127.0.0.1:5000/empleados
- http://127.0.0.1:5000/empleados?q=ana  (búsqueda)
- http://127.0.0.1:5000/empleados/nuevo

La conexión usa `host=localhost, user=root, password=""` (valores por defecto de XAMPP).

## Estructura de archivos
```
app.py            rutas de Flask y lógica (mysql-connector-python, parámetros %s)
crear_bd.sql      crea la base, las tablas y carga los datos de ejemplo
requirements.txt  flask y mysql-connector-python
README.md         documentación
templates/        base.html, empleados.html, nuevo.html, editar.html, resumen.html, detalle.html
static/           style.css (única hoja de estilos)
```

## Rutas
| Ruta | Método | Qué hace |
|---|---|---|
| `/empleados` | GET | Lista empleados y documentos (consulta con JOIN). |
| `/empleados/nuevo` | GET, POST | Registro con validación |
| `/empleados/eliminar/<id>` | POST | Elimina un empleado; sus documentos se borran solos (ON DELETE CASCADE) |
| `/documentos/editar/<id>` | GET, POST | Modifica el estado de un documento con validación |
| `/resumen` | GET | Clasifica y cuenta los expedientes |

## Base de datos (MySQL: `hospital`)
- `checklist` (id PK, perfil, documento): documentos que exige cada perfil.
- `empleados` (id PK, nombre, perfil, fecha_ingreso, correo): tabla principal, 5 registros.
- `documentos` (id PK, empleado_id FK, documento, estado): tabla relacionada, más de 5 registros.

Relación: `documentos.empleado_id` → `FOREIGN KEY REFERENCES empleados(id) ON DELETE CASCADE`. Un empleado tiene muchos documentos; al eliminar al empleado MySQL borra sus documentos, así que no quedan registros huérfanos.

Consulta con JOIN (listado): `SELECT ... FROM empleados e LEFT JOIN documentos d ON d.empleado_id = e.id`.

## Cómo funciona el resumen
Lee todos los empleados y los recorre con `for`. Para cada uno consulta sus documentos y, con otro `for`, cuenta los pendientes. Luego decide con `if/elif/else`: sin documentos requeridos, completo (0 pendientes) o incompleto (1 o más). Tres contadores acumulan cuántos hay de cada clasificación y se muestran con colores distintos.

## Mejoras individuales (una rama y un pull request por integrante)
- **Mariana Salazar** (GitHub: `marianasalazar17`): conexión a MySQL y estructura del repositorio. Mejora: página de detalle de cada empleado (/empleados/<id>) con sus datos y el estado de sus documentos.
- **Fiorella Funes** (GitHub: _(completar)_): registro con validación y eliminación. Mejora: _(completar)_
- **Fernanda Pocasangre** (GitHub: `fernandapocaa-tech`): consulta con JOIN y modificación con validación. Mejora: búsqueda por texto en el listado (/empleados?q=...) con LIKE; filtra por nombre o perfil.
- **Alejandra Palma** (GitHub: alepal1): resumen (bucle, decisión y contadores). Mejora: porcentaje de expedientes completos con barra de progreso en el
resumen."
