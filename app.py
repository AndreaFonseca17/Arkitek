from flask import Flask, render_template, request, redirect, session, send_from_directory, url_for
from flask_mysqldb import MySQL
from datetime import datetime
import os
from flask import make_response


app = Flask(__name__, static_folder='arkitel-frontend/build', static_url_path='/')

app.secret_key = "develoteca"

# Configuración de MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'sitio'
mysql = MySQL(app)

@app.route('/')
def inicio():
    return render_template('sitio/index.html')

@app.route('/img/<imagen>')
def imagenes(imagen):
    print(imagen)
    return send_from_directory(os.path.join('templates/sitio/img'),imagen)

@app.route("/css/<archivocss>")
def css_link(archivocss):
    return send_from_directory(os.path.join('templates/sitio/css'), archivocss)

@app.errorhandler(404)
def not_found(error):
    resp = make_response(render_template('error.html'), 404)
    resp.headers['X-Something'] = 'A value'
    return resp

@app.route('/productos')
def productos():
    return render_template('sitio/productos.html')

@app.route('/login')
def login():
    conexion=mysql.connection
    print(conexion)
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `login`")
    login = cursor.fetchall()
    cursor.close()  # Cerrar el cursor después de su uso
    print(login)
    return render_template('sitio/login.html', login=login)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        cedula = request.form['cedula']
        direccion = request.form['direccion']
        telefono = request.form['telefono']
        fecha_de_nacimiento = request.form['fecha_de_nacimiento']
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        confirmar_contraseña = request.form['confirmar_contraseña']

        # Verificar si el usuario ya existe en la base de datos
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM registros WHERE correo = %s", (correo,))
        usuario_existente = cursor.fetchone()

        if usuario_existente:
            return "El usuario ya existe. Por favor, pruebe con otro correo electrónico."

        # Verificar si las contraseñas coinciden
        if contraseña != confirmar_contraseña:
            return "Las contraseñas no coinciden. Por favor, inténtalo de nuevo."

        # Insertar el nuevo usuario en la base de datos
        cursor.execute("INSERT INTO registros (nombre, apellido, cedula, direccion, telefono, fecha_de_nacimiento, correo, contraseña) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                       (nombre, apellido, cedula, direccion, telefono, fecha_de_nacimiento, correo, contraseña))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('inicio'))

    return render_template('sitio/registro.html')

@app.route('/cotizacion')
def cotizacion():
    return render_template('sitio/cotizacion.html')

@app.route('/contratacion')
def contratacion():
    return render_template('sitio/contratacion.html')

@app.route('/contactanos')
def contactanos():
    return render_template('sitio/contactanos.html')

@app.route('/admin/')
def admin_index():
    if not 'login' in session:  # noqa: E713
        return redirect("/admin/login")
    return render_template('admin/index.html')

@app.route('/admin/login')
def admin_login():
    return render_template('admin/login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    _usuario=request.form['txtUsuario']
    _password=request.form['txtPassword']
    print(_usuario)
    print(_password)
    
    if _usuario=="admin" and _password=="123":
        session["login"]=True
        session["usuario"]="Administrador"
        return redirect("/admin")
    return render_template('admin/login.html', mensaje="Acceso Denegado")

@app.route('/admin/cerrar')
def admin_login_cerrar():
    session.clear()
    return redirect('/admin/login')


@app.route('/admin/productos')
def admin_productos():
    
    if not 'login' in session:  # noqa: E713
        return redirect("/admin/login")
    
    conexion = mysql.connection
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `productos`")
    productos = cursor.fetchall()
    cursor.close()  # Cerrar el cursor después de su uso
    print(productos)
    return render_template('admin/productos.html', productos=productos)

@app.route('/admin/productos/guardar', methods=['POST'])
def admin_productos_guardar():
    
    if not 'login' in session:  # noqa: E713
        return redirect("/admin/login")
    
    _nombre = request.form['txtProductos']
    _url = request.form['txtUrl']
    _archivo = request.files['txtImagen']
    
    tiempo = datetime.now()
    horaActual = tiempo.strftime('%Y%H%M%S')
    
    if _archivo.filename != "":   
        nuevoNombre = horaActual + "_" + _archivo.filename
        _archivo.save("templates/sitio/img/" + nuevoNombre)

    sql = "INSERT INTO productos (Producto, imagen, url) VALUES (%s, %s, %s)"
    datos = (_nombre, nuevoNombre, _url)

    conexion = mysql.connection 
    cursor = conexion.cursor()
    cursor.execute(sql, datos)
    conexion.commit()

    print(_nombre)
    print(_url)
    print(_archivo)

    return redirect('/admin/productos')

@app.route('/admin/productos/borrar', methods=['POST'])
def admin_productos_borrar():
    
    if not 'login' in session:  # noqa: E713
        return redirect("/admin/login")
    
    if request.method == 'POST':
        _id = request.form.get('txtID')  # Obtener el ID del producto de la solicitud POST
        if _id:
            # Verificar si el producto existe antes de eliminarlo
            with mysql.connection.cursor() as cursor:
                cursor.execute("SELECT imagen FROM `productos` WHERE IDPro=%s", (_id,))
                producto = cursor.fetchone()
                if producto:
                    # El producto existe, continuar con la eliminación
                    print(f"Producto a eliminar: {producto}")
                    
                    # Verificar y eliminar el archivo de imagen
                    if os.path.exists(os.path.join('templates', 'sitio', 'img', producto[0])):
                        os.unlink(os.path.join('templates', 'sitio', 'img', producto[0]))
                    
                    # Eliminar la entrada de la base de datos
                    cursor.execute("DELETE FROM `productos` WHERE `productos`.`IDPro` = %s", (_id,))
                    mysql.connection.commit()
                    
                    return redirect('/admin/productos')
                else:
                    # El producto no existe, mostrar un mensaje de error
                    return 'Error: El producto no existe'
        else:
            # ID del producto no especificado, mostrar un mensaje de error
            return 'Error: ID del producto no especificado'
    else:
        # Método de solicitud no permitido, mostrar un mensaje de error
        return 'Error: Método no permitido'


if __name__ == '__main__':
    app.run(debug=True, port=8000)



