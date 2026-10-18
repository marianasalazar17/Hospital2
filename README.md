# Fase 2 — Decisión, repetición, base de datos y estilos: Expedientes Digitales (Hospital de Diagnóstico)

**Socio Formador:** Hospital de Diagnóstico

**Integrantes:**

- Fernanda Pocasangre — usuario de GitHub: fernandapocaa-tech
- Alejandra Palma — usuario de GitHub: alepal1
- Mariana Salazar — usuario de GitHub: [usuario]
- Fiorella Funes — usuario de GitHub: [usuario]

---

## Qué hace este proyecto

Es la Fase 2 del sistema de la Tarea 2. Administra los expedientes digitales del personal del Hospital de Diagnóstico: por cada empleado y cada documento, dice si ese documento está **Completo**, **Pendiente**, o si **No aplica** a su perfil.

Ahora los datos ya no están fijos en el código: se guardan en una base de datos **SQLite**. El sistema permite:

- **Registrar** un empleado (con validación de datos).
- **Consultar** el listado de empleados con el estado de su expediente.
- **Modificar** el estado de un documento del expediente (con validación).
- **Eliminar** el registro de un empleado.
- Ver un **resumen** que recorre todos los empleados, clasifica cada expediente como completo o incompleto y cuenta cuántos hay de cada tipo.

---

## Cómo ejecutarlo

```
pip install flask
python crear_bd.py
python app.py
```

En Windows, si `pip` no se reconoce, usar `py -m pip install flask`, `py crear_bd.py` y `py app.py`.

El servidor corre en `http://127.0.0.1:5000/` y las páginas se abren en estas URL completas:

- Listado de expedientes: http://127.0.0.1:5000/empleados
- Registrar empleado: http://127.0.0.1:5000/empleados/nuevo
- Modificar un documento (ejemplo con el documento 1): http://127.0.0.1:5000/documentos/editar/1
- Resumen: http://127.0.0.1:5000/resumen

`crear_bd.py` se ejecuta **antes** de `app.py` y cada vez que se quiera volver a los datos de ejemplo (borra y vuelve a crear las tablas).

---

## Estructura de archivos

```
Hospital-Fase2/
|-- app.py            # rutas de Flask y lógica del sistema
|-- crear_bd.py       # crea las tablas y carga 5 empleados de ejemplo
|-- README.md         # esta documentación
|-- templates/
|   |-- base.html       # estructura común y menú (enlaza style.css)
|   |-- empleados.html  # listado de empleados y estado del expediente
|   |-- nuevo.html      # formulario de registro
|   |-- editar.html     # formulario para modificar el estado de un documento
|   |-- resumen.html    # resumen con contadores
|-- static/
|   |-- style.css       # única hoja de estilos del sitio
|-- capturas/         # capturas de pantalla de las pruebas
```

---

## Rutas

| Ruta | Método | Qué hace |
|---|---|---|
| `/` | GET | Redirige a `/empleados` |
| `/empleados` | GET | Consultar: lista empleados con el estado de cada documento y de su expediente |
| `/empleados/nuevo` | GET, POST | Registrar: GET muestra el formulario, POST valida y guarda |
| `/documentos/editar/<id>` | GET, POST | Modificar: GET muestra el formulario, POST valida y actualiza el estado |
| `/empleados/eliminar/<id>` | POST | Eliminar: borra al empleado y sus documentos (pide confirmación) |
| `/resumen` | GET | Recorre todos los empleados, los clasifica y cuenta cuántos hay de cada tipo |

---

## Base de datos (SQLite: `hospital.db`)

Se crea con `crear_bd.py`. Tiene tres tablas:

**Tabla `empleados`**

| Campo | Tipo | Descripción |
|---|---|---|
| id | entero (clave primaria) | Identificador del empleado |
| nombre | texto | Nombre del empleado |
| perfil | texto | administrativo, medico o enfermeria |
| fecha_ingreso | texto | Fecha de ingreso (AAAA-MM-DD) |
| correo | texto | Correo del empleado |

**Tabla `checklist`** (qué documentos exige cada perfil)

| Campo | Tipo | Descripción |
|---|---|---|
| id | entero (clave primaria) | Identificador |
| perfil | texto | Perfil al que aplica |
| documento | texto | Nombre del documento requerido |

**Tabla `documentos`** (el expediente de cada empleado)

| Campo | Tipo | Descripción |
|---|---|---|
| id | entero (clave primaria) | Identificador del documento |
| empleado_id | entero | Empleado al que pertenece |
| documento | texto | Nombre del documento |
| estado | texto | `Completo` o `Pendiente` |

### Checklist de documentos por perfil

| Perfil | Documentos requeridos |
|---|---|
| Administrativo | DUI, Título, Antecedentes Penal, Solvencia PNP |
| Médico | DUI, Título, Antecedentes Penal, Solvencia PNP, Colegiatura médica, Especialidad |
| Enfermería | DUI, Título, Antecedentes Penal, Solvencia PNP, Junta de Vigilancia |

Esto refleja una regla de negocio confirmada en la ficha del reto: el checklist no es el mismo para todos, varía según el perfil. Al registrar un empleado, el sistema le crea automáticamente un documento en estado `Pendiente` por cada documento que exige su perfil.

---

## 1. La conexión a la base de datos

```python
def conectar():
    conexion = sqlite3.connect("hospital.db")
    conexion.row_factory = sqlite3.Row
    return conexion
```

Abre `hospital.db`. Con `row_factory = sqlite3.Row` cada fila se puede leer por nombre de campo (por ejemplo `fila["nombre"]`) en lugar de por posición.

Todas las sentencias SQL del proyecto usan parámetros con `?` y nunca se concatena el texto escrito por el usuario dentro de la sentencia. Por ejemplo:

```python
conexion.execute("UPDATE documentos SET estado = ? WHERE id = ?", (estado, doc_id))
```

---

## 2. El script `crear_bd.py`

Antes, el checklist y los empleados estaban escritos dentro del código (`DOCUMENTOS_PERFIL` y `EMPLEADOS_DB` en `Hospital-T2.py`). Ahora `crear_bd.py` hace tres cosas:

1. Borra las tablas viejas (si existen) y crea `checklist`, `empleados` y `documentos`.
2. Guarda en `checklist` los documentos que exige cada perfil.
3. Inserta 5 empleados de ejemplo (Ana, Carlos, Maria, Luis y Sofia) y, para cada uno, un registro en `documentos` por cada documento de su perfil: `Completo` si ya lo entregó, `Pendiente` si no.

---

## 3. Consultar: el listado con el estado del expediente

```python
@app.route("/empleados")
def listar():
    conexion = conectar()
    empleados = conexion.execute("SELECT * FROM empleados ORDER BY id").fetchall()
    ...
    for emp in empleados:
        docs = conexion.execute(
            "SELECT id, documento, estado FROM documentos WHERE empleado_id = ?",
            (emp["id"],)).fetchall()
        ...
        for nombre_doc in todos:
            if nombre_doc in por_doc:
                ...
                celdas.append({"estado": d["estado"], "id": d["id"]})
            else:
                celdas.append({"estado": "No aplica", "id": None})

        if pendientes == 0:
            expediente = "Completo"
        else:
            expediente = "Incompleto"
```

Aquí hay un bucle dentro de otro bucle:

- El bucle de afuera (`for emp in empleados`) recorre cada empleado de la base de datos.
- El bucle de adentro (`for nombre_doc in todos`) recorre, para ese empleado, cada documento posible de la tabla.

Por cada documento la decisión es `if/else`:

- Si el documento está en el expediente del empleado, se toma su estado (`Completo` o `Pendiente`) y, si está pendiente, se suma 1 al contador `pendientes`.
- Si el documento no está en su expediente (no lo exige su perfil), el estado es `No aplica`.

Al terminar con los documentos del empleado, otra decisión clasifica su expediente: si `pendientes == 0` es **Completo**, si no es **Incompleto**.

---

## 4. Registrar: formulario con validación

```python
@app.route("/empleados/nuevo", methods=["GET", "POST"])
def nuevo():
    ...
    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        perfil = request.form["perfil"]
        fecha = request.form["fecha_ingreso"].strip()
        correo = request.form["correo"].strip()
        ...
        if nombre == "":
            error = "El nombre no puede estar vacío."
        elif perfil not in perfiles:
            error = "Elige un perfil de la lista."
        elif not fecha_valida:
            error = "La fecha debe tener el formato AAAA-MM-DD (ejemplo: 2024-05-20)."
        elif "@" not in correo or "." not in correo:
            error = "Escribe un correo válido (ejemplo: nombre@hospital.com)."
        else:
            # INSERT del empleado y de sus documentos en estado Pendiente
            ...
            return redirect("/empleados")
```

- Con `GET` se muestra el formulario vacío; con `POST` se procesan los datos con `request.form`.
- Antes de guardar se valida: nombre vacío, perfil que no existe, fecha con formato incorrecto o correo sin `@`. Si hay un error, se muestra el mensaje en rojo, **no se guarda nada** y el formulario conserva lo que el usuario escribió.
- Si todo es válido, se guarda el empleado, se le crean sus documentos pendientes según su perfil y se **redirige al listado**.

---

## 5. Modificar: actualizar el estado de un documento

```python
@app.route("/documentos/editar/<int:doc_id>", methods=["GET", "POST"])
def editar(doc_id):
    ...
    if request.method == "POST":
        estado = request.form["estado"]
        if estado != "Completo" and estado != "Pendiente":
            error = "Elige un estado: Completo o Pendiente."
        else:
            conexion.execute("UPDATE documentos SET estado = ? WHERE id = ?", (estado, doc_id))
            conexion.commit()
            conexion.close()
            return redirect("/empleados")
```

En el listado, cada "Completo" o "Pendiente" es un enlace a esta ruta. El formulario muestra el empleado, el documento y su estado actual. Si no se elige un estado, muestra el error y no guarda. El `UPDATE` siempre lleva `WHERE id = ?` para modificar solamente ese documento. Si el documento no existe, redirige al listado.

---

## 6. Eliminar un empleado

```python
@app.route("/empleados/eliminar/<int:emp_id>", methods=["POST"])
def eliminar(emp_id):
    conexion = conectar()
    conexion.execute("DELETE FROM documentos WHERE empleado_id = ?", (emp_id,))
    conexion.execute("DELETE FROM empleados WHERE id = ?", (emp_id,))
    conexion.commit()
    conexion.close()
    return redirect("/empleados")
```

Solo acepta `POST` (el botón "Eliminar" del listado es un formulario). Antes de enviarlo, el navegador pide confirmación con una ventana. Primero se borran los documentos del empleado y luego el empleado; los dos `DELETE` llevan `WHERE`, por lo que nunca se borran todas las filas.

---

## 7. El resumen: repetición, decisión y contadores

```python
@app.route("/resumen")
def resumen():
    ...
    completos = 0
    incompletos = 0
    sin_checklist = 0

    for emp in empleados:
        docs = conexion.execute(
            "SELECT estado FROM documentos WHERE empleado_id = ?", (emp["id"],)).fetchall()
        total = len(docs)
        pendientes = 0
        for d in docs:
            if d["estado"] == "Pendiente":
                pendientes = pendientes + 1

        if total == 0:
            ... sin_checklist = sin_checklist + 1
        elif pendientes == 0:
            ... completos = completos + 1
        else:
            ... incompletos = incompletos + 1
```

**Qué recorre:** todos los empleados de la tabla `empleados` con un `for`, y para cada uno todos sus documentos con otro `for`.

**Qué decide:** con `if/elif/else`, cada expediente queda en una de tres clasificaciones:

| Condición | Clasificación | Color |
|---|---|---|
| El empleado no tiene documentos requeridos | Sin documentos requeridos | Amarillo |
| 0 documentos pendientes | Completo | Verde |
| 1 o más documentos pendientes | Incompleto | Rojo |

Tres contadores (`completos`, `incompletos`, `sin_checklist`) acumulan cuántos empleados hay de cada clasificación y se muestran en pantalla.

---

## 8. Las plantillas HTML (con Jinja)

Todas las páginas heredan de `base.html` (`{% extends "base.html" %}`), que enlaza **una sola** hoja de estilos externa y trae el menú de navegación:

```html
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
```

Las plantillas reciben los datos ya calculados desde Python y solo se encargan de dibujarlos. Por ejemplo, en el listado cada celda recibe una clase de CSS según su estado:

```html
<td class="{{ c.estado|lower|replace(' ', '') }}">
```

Así `Completo` se vuelve la clase `completo`, `Pendiente` la clase `pendiente` y `No aplica` la clase `noaplica`.

---

## 9. El CSS (`static/style.css`)

El CSS no calcula nada: solo le da color a las clases que las plantillas ya pusieron. Todos los estilos viven en este archivo, no repetidos dentro de las páginas:

```css
td.completo { background: #eaf7ea; color: #2f7a2f; font-weight: bold; }
td.pendiente { background: #fbe9e9; color: #b02a2a; font-weight: bold; }
td.noaplica { background: #f1f1f1; color: #888888; font-style: italic; }
td.sinchecklist { background: #fff4d6; color: #8a6500; font-weight: bold; }
```

- Tipografía y colores consistentes en todo el sitio.
- Formularios con etiquetas y botón con estilo.
- Tabla con encabezado azul oscuro diferenciado.
- En el resumen, cada clasificación tiene un color distinto (verde, rojo y amarillo).

---

## Cierre: lo que aplicamos en esta fase

| Habilidad | Dónde se aplicó |
|---|---|
| Sentencias repetitivas (`for`) | En el listado y en el resumen, para recorrer empleados y documentos |
| Decisiones `if/elif/else` | Para clasificar cada documento y cada expediente (Completo, Incompleto, No aplica) |
| Contadores y acumuladores | `pendientes`, `completos`, `incompletos`, `sin_checklist` |
| Base de datos SQLite | `crear_bd.py` y las consultas con el módulo `sqlite3` |
| Consultas parametrizadas | Todas las sentencias SQL usan `?`, nunca se concatena texto del usuario |
| Mantenimientos básicos | Registrar, consultar, modificar y eliminar |
| Formularios con validación | Registro y modificación con `request.form` y mensajes de error |
| Hoja de estilos externa | `static/style.css` aplicada en todas las páginas |
| Trabajo en equipo con GitHub | Commits individuales de cada integrante |

---
