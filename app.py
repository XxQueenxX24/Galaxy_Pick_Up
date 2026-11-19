import os
from functools import wraps

import psycopg2
from psycopg2.extras import RealDictCursor

from dotenv import load_dotenv

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

# CARGAR VARIABLES DEL ARCHIVO .ENV
load_dotenv()

# CONFIGURACIÓN DE FLASK
app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("Falta configurar SECRET_KEY en .env")


# DATOS DEL ADMINISTRADOR
USUARIO_ADMIN = os.getenv("USUARIO_ADMIN")
CONTRASENA_ADMIN = os.getenv("CONTRASENA_ADMIN")

if not USUARIO_ADMIN or not CONTRASENA_ADMIN:
    raise RuntimeError("Faltan las credenciales del administrador en .env")

CONTRASENA_HASH = generate_password_hash(CONTRASENA_ADMIN) 


# CONEXIÓN A SUPABASE
def conectar():
    return psycopg2.connect(
        os.environ["DATABASE_URL"],
        cursor_factory=RealDictCursor
    )


# PROTECCIÓN DEL ADMINISTRADOR
def administrador_requerido(func):
    @wraps(func)
    def decorada(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("login"))

        return func(*args, **kwargs)

    return decorada


# PÁGINA PRINCIPAL
@app.route("/")
def inicio():
    return render_template("pick_ups.html")

# MOSTRAR EVENTOS PÚBLICOS
@app.route("/eventos")
def eventos():

    with conectar() as conexion:
        with conexion.cursor() as cursor:

            cursor.execute("""
                SELECT *
                FROM eventos
                ORDER BY fecha, hora
            """)

            lista_eventos = cursor.fetchall()

    return render_template(
        "eventos.html",
        eventos=lista_eventos
    )


# INICIAR SESIÓN
@app.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":

        usuario = request.form["usuario"]
        contrasena = request.form["contrasena"]

        if usuario == USUARIO_ADMIN and check_password_hash(
            CONTRASENA_HASH, contrasena
        ):

            session["admin"] = True

            return redirect(url_for("admin"))

        error = "Usuario o contraseña incorrectos"

    return render_template(
        "login.html",
        error=error
    )


# PANEL DE ADMINISTRACIÓN
@app.route("/admin")
@administrador_requerido
def admin():

    with conectar() as conexion:
        with conexion.cursor() as cursor:

            cursor.execute("""
                SELECT *
                FROM eventos
                ORDER BY fecha, hora
            """)

            lista_eventos = cursor.fetchall()

    return render_template(
        "admin.html",
        eventos=lista_eventos
    )


# AGREGAR EVENTO
@app.route("/admin/agregar", methods=["POST"])
@administrador_requerido
def agregar_evento():

    datos = (
        request.form["pico"],
        request.form["evento"],
        request.form["fecha"],
        request.form["hora"],
        request.form["direccion"]
    )

    with conectar() as conexion:
        with conexion.cursor() as cursor:

            cursor.execute("""
                INSERT INTO eventos
                (pico, evento, fecha, hora, direccion)
                VALUES (%s, %s, %s, %s, %s)
            """, datos)

    return redirect(url_for("admin"))


# EDITAR EVENTO
@app.route("/admin/editar/<int:id>", methods=["GET", "POST"])
@administrador_requerido
def editar_evento(id):

    with conectar() as conexion:
        with conexion.cursor() as cursor:

            if request.method == "POST":

                cursor.execute("""
                    UPDATE eventos
                    SET pico=%s,
                        evento=%s,
                        fecha=%s,
                        hora=%s,
                        direccion=%s
                    WHERE id=%s
                """, (
                    request.form["pico"],
                    request.form["evento"],
                    request.form["fecha"],
                    request.form["hora"],
                    request.form["direccion"],
                    id
                ))

                return redirect(url_for("admin"))

            cursor.execute("""
                SELECT *
                FROM eventos
                WHERE id=%s
            """, (id,))

            evento = cursor.fetchone()

    if evento is None:
        return "Evento no encontrado", 404

    return render_template(
        "editar_evento.html",
        evento=evento
    )


# ELIMINAR EVENTO
@app.route("/admin/eliminar/<int:id>", methods=["POST"])
@administrador_requerido
def eliminar_evento(id):

    with conectar() as conexion:
        with conexion.cursor() as cursor:

            cursor.execute("""
                DELETE FROM eventos
                WHERE id=%s
            """, (id,))

    return redirect(url_for("admin"))


# CERRAR SESIÓN
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))

# REDES SOCIALES
@app.route("/redes_sociales")
def redes_sociales():
    return render_template("redes_sociales.html")

# PICK UPS
@app.route("/pick_ups")
def pick_ups():
    return render_template("pick_ups.html")

# EJECUTAR APLICACIÓN
if __name__ == "__main__":
    app.run(debug=True)