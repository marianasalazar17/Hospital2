# app.py - Expedientes Digitales, Hospital de Diagnóstico (Desafío 2: MySQL)
import mysql.connector
from datetime import datetime
from flask import Flask, render_template, request, redirect

app = Flask(__name__)


# ---------------------------------------------------------------
# MARIANA SALAZAR: conexión a MySQL (XAMPP: usuario root, sin contraseña)
# ---------------------------------------------------------------
def conectar():
    return mysql.connector.connect(host="localhost", user="root", password="", database="hospital")


def obtener_perfiles(cursor):
    cursor.execute("SELECT perfil FROM checklist GROUP BY perfil ORDER BY MIN(id)")
    lista = []
    for fila in cursor.fetchall():
        lista.append(fila["perfil"])
    return lista

@app.errorhandler(mysql.connector.Error)
def error_base_datos(error):
    # Si MySQL está apagado, la página sigue viva y avisa en vez de romperse
    return render_template("error_bd.html"), 503

@app.route("/")
def inicio():
    return redirect("/empleados")

# ---------------------------------------------------------------
# FIORELLA FUNES: registrar empleado (con validación) y eliminar
# ---------------------------------------------------------------
@app.route("/empleados/nuevo", methods=["GET", "POST"])
def nuevo():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    perfiles = obtener_perfiles(cursor)
    error = ""
    datos = {"nombre": "", "perfil": "", "fecha_ingreso": "", "correo": ""}

    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        perfil = request.form["perfil"]
        fecha = request.form["fecha_ingreso"].strip()
        correo = request.form["correo"].strip()
        datos = {"nombre": nombre, "perfil": perfil, "fecha_ingreso": fecha, "correo": correo}

        fecha_valida = True
        try:
            datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            fecha_valida = False
            
        cursor.execute("SELECT id FROM empleados WHERE correo = %s", (correo,))
        correo_repetido = cursor.fetchone() is not None
        if nombre == "":
            error = "El nombre no puede estar vacío."
        elif len(nombre) < 3:
            error = "El nombre debe tener al menos 3 letras."
        elif perfil not in perfiles:
            error = "Elige un perfil de la lista."
        elif not fecha_valida:
            error = "La fecha debe tener el formato AAAA-MM-DD (ejemplo: 2024-05-20)."
        elif "@" not in correo or "." not in correo:
            error = "Escribe un correo válido (ejemplo: nombre@hospital.com)."
        elif correo_repetido:
            error = "Ya existe un empleado con ese correo."
        else:
            cursor.execute(
                "INSERT INTO empleados (nombre, perfil, fecha_ingreso, correo) VALUES (%s, %s, %s, %s)",
                (nombre, perfil, fecha, correo))
            emp_id = cursor.lastrowid
            cursor.execute("SELECT documento FROM checklist WHERE perfil = %s", (perfil,))
            for r in cursor.fetchall():
                cursor.execute(
                    "INSERT INTO documentos (empleado_id, documento, estado) VALUES (%s, %s, %s)",
                    (emp_id, r["documento"], "Pendiente"))
            conexion.commit()
            cursor.close()
            conexion.close()
            return redirect("/empleados")

    cursor.close()
    conexion.close()
    return render_template("nuevo.html", error=error, perfiles=perfiles, datos=datos)


@app.route("/empleados/eliminar/<int:emp_id>", methods=["POST"])
def eliminar(emp_id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    # Regla nueva: solo se elimina un empleado "vacío":
    # todos sus documentos en Pendiente y sin ningún archivo subido
    cursor.execute("SELECT nombre FROM empleados WHERE id = %s", (emp_id,))
    emp = cursor.fetchone()
    if emp is None:
        cursor.close()
        conexion.close()
        return redirect("/empleados")
    cursor.execute(
        "SELECT d.estado, COUNT(a.id) AS archivos FROM documentos d "
        "LEFT JOIN archivos a ON a.documento_id = d.id "
        "WHERE d.empleado_id = %s GROUP BY d.id, d.estado", (emp_id,))
    docs = cursor.fetchall()
    con_avance = 0
    for d in docs:
        if d["estado"] != "Pendiente" or d["archivos"] > 0:
            con_avance = con_avance + 1
    if con_avance > 0:
        cursor.close()
        conexion.close()
        return render_template("no_eliminar.html", emp=emp, con_avance=con_avance), 409

    # ON DELETE CASCADE borra solo los documentos del empleado (no quedan huérfanos)
    cursor.execute("DELETE FROM empleados WHERE id = %s", (emp_id,))
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect("/empleados")


# ---------------------------------------------------------------
# FIORELLA FUNES: subir un archivo (PDF, Word o imagen del Título) con validaciones y versiones
# ---------------------------------------------------------------
@app.route("/documentos/<int:doc_id>/subir", methods=["GET", "POST"])
def subir(doc_id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(
        "SELECT d.id, d.documento, d.estado, e.nombre FROM documentos d "
        "JOIN empleados e ON e.id = d.empleado_id WHERE d.id = %s", (doc_id,))
    doc = cursor.fetchone()
    if doc is None:
        cursor.close()
        conexion.close()
        abort(404)

    con_imagen = doc["documento"] in DOCUMENTOS_CON_IMAGEN
    error = ""
    if request.method == "POST":
        archivo = request.files.get("archivo")
        vencimiento = request.form.get("fecha_vencimiento", "").strip()
        fecha_venc = None
        contenido = b""

        # 1) Validar el archivo: elegido, extensión, vacío, tamaño y (si es imagen) que sea imagen de verdad
        if archivo is None or archivo.filename == "":
            error = "Elige un archivo para subir."
        elif not extension_valida(archivo.filename, doc["documento"]):
            if con_imagen:
                error = "Solo se permiten archivos .pdf, .doc, .docx, .png o .jpg."
            else:
                error = "Solo se permiten archivos .pdf, .doc o .docx."
        else:
            contenido = archivo.read()
            if len(contenido) == 0:
                error = "El archivo está vacío."
            elif len(contenido) > TAMANO_MAXIMO:
                error = "El archivo supera el tamaño máximo de " + str(TAMANO_MAXIMO // 1024) + " KB."
            elif es_imagen(archivo.filename) and not (contenido.startswith(b"\x89PNG") or
                                                      contenido.startswith(b"\xff\xd8")):
                error = "El archivo no es una imagen válida (PNG o JPG)."

        # 2) Validar la fecha de vencimiento (obligatoria para el DUI)
        if error == "":
            if vencimiento != "":
                try:
                    fecha_venc = datetime.strptime(vencimiento, "%Y-%m-%d").date()
                except ValueError:
                    error = "La fecha de vencimiento debe tener el formato AAAA-MM-DD."
            elif doc["documento"] in DOCUMENTOS_CON_VENCIMIENTO:
                error = "La fecha de vencimiento es obligatoria para este documento."

        # 3) Si todo está bien: calcular la versión siguiente y guardar
        if error == "":
            cursor.execute("SELECT MAX(version) AS ultima FROM archivos WHERE documento_id = %s", (doc_id,))
            ultima = cursor.fetchone()["ultima"]
            if ultima is None:
                nueva = 1
            else:
                nueva = ultima + 1
            cursor.execute(
                "INSERT INTO archivos (documento_id, tipo_documento, nombre_original, version, "
                "fecha_vencimiento, contenido) VALUES (%s, %s, %s, %s, %s, %s)",
                (doc_id, doc["documento"], archivo.filename, nueva, fecha_venc, contenido))
            cursor.execute("UPDATE documentos SET estado = %s WHERE id = %s", ("Completo", doc_id))
            conexion.commit()
            cursor.close()
            conexion.close()
            if es_imagen(archivo.filename):
                return redirect("/documentos/" + str(doc_id) + "/imagen")
            return redirect("/documentos/" + str(doc_id) + "/versiones")

    cursor.close()
    conexion.close()
    requiere_fecha = doc["documento"] in DOCUMENTOS_CON_VENCIMIENTO
    return render_template("subir.html", doc=doc, error=error, tamano_kb=TAMANO_MAXIMO // 1024,
                           requiere_fecha=requiere_fecha, con_imagen=con_imagen)


# ---------------------------------------------------------------
# FERNANDA POCASANGRE: consultar con JOIN
# ---------------------------------------------------------------
@app.route("/empleados")
def listar():
    # MEJORA INDIVIDUAL: el texto escrito en el buscador (?q=...) filtra por nombre o perfil
    q = request.args.get("q", "").strip()
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("SELECT documento FROM checklist GROUP BY documento ORDER BY MIN(id)")
    todos = []
    for fila in cursor.fetchall():
        todos.append(fila["documento"])

    # Consulta con JOIN: cada empleado junto con sus documentos
    consulta = ("SELECT e.id, e.nombre, e.perfil, d.id AS doc_id, d.documento, d.estado "
                "FROM empleados e LEFT JOIN documentos d ON d.empleado_id = e.id ")
    if q != "":
        consulta = consulta + "WHERE e.nombre LIKE %s OR e.perfil LIKE %s "
        cursor.execute(consulta + "ORDER BY e.id, d.id", ("%" + q + "%", "%" + q + "%"))
    else:
        cursor.execute(consulta + "ORDER BY e.id, d.id")
    registros = cursor.fetchall()
    cursor.close()
    conexion.close()

    # Se agrupan las filas del JOIN por empleado
    empleados = {}
    for r in registros:
        if r["id"] not in empleados:
            empleados[r["id"]] = {"emp": r, "docs": {}}
        if r["documento"] is not None:
            empleados[r["id"]]["docs"][r["documento"]] = r

    filas = []
    for emp_id in empleados:
        info = empleados[emp_id]
        celdas = []
        pendientes = 0
        for nombre_doc in todos:
            if nombre_doc in info["docs"]:
                d = info["docs"][nombre_doc]
                if d["estado"] == "Pendiente":
                    pendientes = pendientes + 1
                celdas.append({"estado": d["estado"], "id": d["doc_id"]})
            else:
                celdas.append({"estado": "No aplica", "id": None})

        if pendientes == 0:
            expediente = "Completo"
        else:
            expediente = "Incompleto"
        filas.append({"emp": info["emp"], "celdas": celdas, "expediente": expediente})
    return render_template("empleados.html", filas=filas, documentos=todos, q=q)

# --------------------------------------------------------------
# MARIANA SALAZAR (mejora): página de detalle de un empleado 
# --------------------------------------------------------------
@app.route("/empleados/<int:emp_id>")
def detalle(emp_id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM empleados WHERE id = %s", (emp_id,))
    emp = cursor.fetchone()
    if emp is None:
        cursor.close()
        conexion.close()
        return redirect("/empleados")
    cursor.execute("SELECT id, documento, estado FROM documentos WHERE empleado_id = %s ORDER BY id", (emp_id,))
    docs = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template("detalle.html", emp=emp, docs=docs)
# ---------------------------------------------------------------
# FERNANDA POCASANGRE: modificar el estado de un documento (con validación)
# ---------------------------------------------------------------
@app.route("/documentos/editar/<int:doc_id>", methods=["GET", "POST"])
def editar(doc_id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(
        "SELECT d.id, d.documento, d.estado, e.nombre FROM documentos d "
        "JOIN empleados e ON e.id = d.empleado_id WHERE d.id = %s", (doc_id,))
    doc = cursor.fetchone()
    if doc is None:
        cursor.close()
        conexion.close()
        return redirect("/empleados")

    error = ""
    if request.method == "POST":
        estado = request.form["estado"]
        if estado != "Completo" and estado != "Pendiente":
            error = "Elige un estado: Completo o Pendiente."
        else:
            cursor.execute("UPDATE documentos SET estado = %s WHERE id = %s", (estado, doc_id))
            conexion.commit()
            cursor.close()
            conexion.close()
            return redirect("/empleados")

    cursor.close()
    conexion.close()
    return render_template("editar.html", doc=doc, error=error)


# ---------------------------------------------------------------
# ALEJANDRA PALMA: resumen con repetición, decisión y contadores
# ---------------------------------------------------------------
@app.route("/resumen")
def resumen():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM empleados ORDER BY id")
    empleados = cursor.fetchall()

    completos = 0
    incompletos = 0
    sin_checklist = 0
    detalle = []

    for emp in empleados:
        cursor.execute("SELECT estado FROM documentos WHERE empleado_id = %s", (emp["id"],))
        docs = cursor.fetchall()
        total = len(docs)
        pendientes = 0
        for d in docs:
            if d["estado"] == "Pendiente":
                pendientes = pendientes + 1

        if total == 0:
            clase = "sinchecklist"
            texto = "Sin documentos requeridos"
            sin_checklist = sin_checklist + 1
        elif pendientes == 0:
            clase = "completo"
            texto = "Completo"
            completos = completos + 1
        else:
            clase = "incompleto"
            texto = "Incompleto"
            incompletos = incompletos + 1

        detalle.append({"nombre": emp["nombre"], "perfil": emp["perfil"],
                        "pendientes": pendientes, "total": total,
                        "clase": clase, "texto": texto})

    cursor.close()
    conexion.close()
    if len(empleados) > 0:
        porcentaje = round(completos / len(empleados) * 100)
    else:
        porcentaje = 0
    return render_template("resumen.html", detalle=detalle, completos=completos,
                           incompletos=incompletos, sin_checklist=sin_checklist,
                           total=len(empleados), porcentaje=porcentaje)


if __name__ == "__main__":
    app.run(debug=True)
