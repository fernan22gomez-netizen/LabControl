"""Prototipo local de gestión de equipos y mantenimiento para un laboratorio."""

from datetime import date, timedelta
from contextlib import contextmanager
import os
import sqlite3

from flask import Flask, flash, redirect, render_template, request, url_for


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "labcontrol.db")
DIAS_ALERTA_MANTENIMIENTO = 180

app = Flask(__name__)
app.secret_key = os.environ.get("LABCONTROL_SECRET_KEY", "labcontrol-prototipo-local")


def conectar_db():
    """Abre la base de datos y activa las relaciones entre tablas."""
    conexion = sqlite3.connect(DATABASE)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


@contextmanager
def sesion_db():
    """Cierra la conexión al terminar y revierte cambios si ocurre un error."""
    conexion = conectar_db()
    try:
        yield conexion
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def inicializar_db():
    """Crea las tablas la primera vez que se ejecuta el prototipo."""
    with sesion_db() as conexion:
        conexion.executescript(
            """
            CREATE TABLE IF NOT EXISTS equipos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL UNIQUE,
                nombre TEXT NOT NULL,
                estado TEXT NOT NULL,
                ubicacion TEXT NOT NULL,
                especificaciones TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS incidencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipo_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'Pendiente',
                FOREIGN KEY (equipo_id) REFERENCES equipos(id)
            );

            CREATE TABLE IF NOT EXISTS mantenimientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipo_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                tipo TEXT NOT NULL,
                notas TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (equipo_id) REFERENCES equipos(id)
            );
            """
        )


def obtener_equipos(conexion):
    return conexion.execute(
        "SELECT id, codigo, nombre, estado, ubicacion FROM equipos ORDER BY codigo"
    ).fetchall()


@app.route("/")
def inicio():
    hoy = date.today()
    fecha_limite = hoy - timedelta(days=DIAS_ALERTA_MANTENIMIENTO)

    with sesion_db() as conexion:
        equipos = conexion.execute(
            """
            SELECT e.*,
                   (SELECT MAX(m.fecha) FROM mantenimientos m
                    WHERE m.equipo_id = e.id) AS ultimo_mantenimiento
            FROM equipos e
            ORDER BY e.codigo
            """
        ).fetchall()
        incidencias = conexion.execute(
            """
            SELECT i.*, e.codigo AS equipo_codigo, e.nombre AS equipo_nombre
            FROM incidencias i
            JOIN equipos e ON e.id = i.equipo_id
            ORDER BY i.fecha DESC, i.id DESC
            LIMIT 8
            """
        ).fetchall()
        mantenimientos = conexion.execute(
            """
            SELECT m.*, e.codigo AS equipo_codigo, e.nombre AS equipo_nombre
            FROM mantenimientos m
            JOIN equipos e ON e.id = m.equipo_id
            ORDER BY m.fecha DESC, m.id DESC
            LIMIT 8
            """
        ).fetchall()
        equipos_con_mas_fallas = conexion.execute(
            """
            SELECT e.codigo, e.nombre, COUNT(i.id) AS total_fallas
            FROM equipos e
            JOIN incidencias i ON i.equipo_id = e.id
            GROUP BY e.id, e.codigo, e.nombre
            ORDER BY total_fallas DESC, e.codigo
            LIMIT 5
            """
        ).fetchall()
        total_equipos = conexion.execute(
            "SELECT COUNT(*) FROM equipos"
        ).fetchone()[0]
        incidencias_pendientes = conexion.execute(
            "SELECT COUNT(*) FROM incidencias WHERE estado != 'Resuelta'"
        ).fetchone()[0]

    equipos_atrasados = []
    for equipo in equipos:
        fecha_texto = equipo["ultimo_mantenimiento"]
        atrasado = not fecha_texto or date.fromisoformat(fecha_texto) < fecha_limite
        if atrasado:
            equipos_atrasados.append(equipo)

    return render_template(
        "index.html",
        equipos=equipos,
        incidencias=incidencias,
        mantenimientos=mantenimientos,
        equipos_con_mas_fallas=equipos_con_mas_fallas,
        equipos_atrasados=equipos_atrasados,
        total_equipos=total_equipos,
        incidencias_pendientes=incidencias_pendientes,
        dias_alerta=DIAS_ALERTA_MANTENIMIENTO,
        hoy=hoy.isoformat(),
    )


@app.post("/equipos")
def registrar_equipo():
    codigo = request.form.get("codigo", "").strip().upper()
    nombre = request.form.get("nombre", "").strip()
    estado = request.form.get("estado", "").strip()
    ubicacion = request.form.get("ubicacion", "").strip()
    especificaciones = request.form.get("especificaciones", "").strip()
    estados_validos = {"Operativo", "En reparación", "Fuera de servicio"}

    if not all((codigo, nombre, ubicacion)) or estado not in estados_validos:
        flash("Completa el código, nombre, ubicación y un estado válido.", "error")
        return redirect(url_for("inicio") + "#equipos")

    try:
        with sesion_db() as conexion:
            conexion.execute(
                """INSERT INTO equipos (codigo, nombre, estado, ubicacion, especificaciones)
                   VALUES (?, ?, ?, ?, ?)""",
                (codigo, nombre, estado, ubicacion, especificaciones),
            )
        flash(f"Equipo {codigo} registrado correctamente.", "exito")
    except sqlite3.IntegrityError:
        flash(f"Ya existe un equipo con el código {codigo}.", "error")
    return redirect(url_for("inicio") + "#equipos")


@app.post("/incidencias")
def registrar_incidencia():
    equipo_id = request.form.get("equipo_id", type=int)
    fecha = request.form.get("fecha", "").strip()
    descripcion = request.form.get("descripcion", "").strip()

    if not equipo_id or not descripcion:
        flash("Selecciona un equipo y describe la falla.", "error")
        return redirect(url_for("inicio") + "#incidencias")
    try:
        date.fromisoformat(fecha)
    except ValueError:
        flash("La fecha de la incidencia no es válida.", "error")
        return redirect(url_for("inicio") + "#incidencias")

    with sesion_db() as conexion:
        existe = conexion.execute(
            "SELECT id FROM equipos WHERE id = ?", (equipo_id,)
        ).fetchone()
        if not existe:
            flash("El equipo seleccionado no existe.", "error")
        else:
            conexion.execute(
                "INSERT INTO incidencias (equipo_id, fecha, descripcion) VALUES (?, ?, ?)",
                (equipo_id, fecha, descripcion),
            )
            flash("Incidencia registrada. El encargado puede darle seguimiento.", "exito")
    return redirect(url_for("inicio") + "#incidencias")


@app.post("/mantenimientos")
def registrar_mantenimiento():
    equipo_id = request.form.get("equipo_id", type=int)
    fecha = request.form.get("fecha", "").strip()
    tipo = request.form.get("tipo", "").strip()
    notas = request.form.get("notas", "").strip()

    if not equipo_id or tipo not in {"Preventivo", "Correctivo"}:
        flash("Selecciona un equipo y un tipo de mantenimiento válido.", "error")
        return redirect(url_for("inicio") + "#mantenimientos")
    try:
        date.fromisoformat(fecha)
    except ValueError:
        flash("La fecha del mantenimiento no es válida.", "error")
        return redirect(url_for("inicio") + "#mantenimientos")

    with sesion_db() as conexion:
        existe = conexion.execute(
            "SELECT id FROM equipos WHERE id = ?", (equipo_id,)
        ).fetchone()
        if not existe:
            flash("El equipo seleccionado no existe.", "error")
        else:
            conexion.execute(
                """INSERT INTO mantenimientos (equipo_id, fecha, tipo, notas)
                   VALUES (?, ?, ?, ?)""",
                (equipo_id, fecha, tipo, notas),
            )
            flash("Mantenimiento registrado correctamente.", "exito")
    return redirect(url_for("inicio") + "#mantenimientos")


@app.post("/incidencias/<int:incidencia_id>/resolver")
def resolver_incidencia(incidencia_id):
    with sesion_db() as conexion:
        resultado = conexion.execute(
            "UPDATE incidencias SET estado = 'Resuelta' WHERE id = ?",
            (incidencia_id,),
        )
    if resultado.rowcount:
        flash("Incidencia marcada como resuelta.", "exito")
    else:
        flash("No se encontró esa incidencia.", "error")
    return redirect(url_for("inicio") + "#incidencias")


if __name__ == "__main__":
    inicializar_db()
    # En la computadora anfitriona se abre http://127.0.0.1:5000.
    # Los demás equipos de la red local usan http://IP-DEL-ANFITRION:5000.
    app.run(host="0.0.0.0", port=5000, debug=False)
