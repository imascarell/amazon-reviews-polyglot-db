#load_data.py

"""
Alumnos:
    Yago Vallarino Fernández-Cavada
    Ignacio Mascarell Agúndez
"""

#imports
import json
import pymysql
import datetime
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import configuracion


def create_infrastructure():

    """
    Esta función crea la base de datos de MySQL y sus tablas necesarias.
    """

    conn = None
    
    try:


        #conexión a SQL
        conn = pymysql.connect(
            host=configuracion.MYSQL_HOST, 
            user=configuracion.MYSQL_USER, 
            password=configuracion.MYSQL_PASS)
        cursor = conn.cursor()

        #crear bbdd (si ya existe, se conecta y limpia tablas)
        try:
            cursor.execute(f"CREATE DATABASE {configuracion.MYSQL_DB}")
        except pymysql.MySQLError:
            pass

        cursor.execute(f"USE {configuracion.MYSQL_DB}")

        #eliminar tablas existentes en orden correcto (por claves foráneas)
        try:
            cursor.execute("DROP TABLE reviews_meta")
        except pymysql.MySQLError:
            pass
        try:
            cursor.execute("DROP TABLE productos")
        except pymysql.MySQLError:
            pass
        try:
            cursor.execute("DROP TABLE usuarios")
        except pymysql.MySQLError:
            pass

        #tabla usuarios: id y nombre de cada reviewer
        cursor.execute("""
            CREATE TABLE usuarios (
                id_usuario VARCHAR(50) PRIMARY KEY,
                nombre VARCHAR(255)
            )
        """)

        #tabla productos: identificador asin y categoría de cada producto
        cursor.execute("""
            CREATE TABLE productos (
                asin VARCHAR(50) PRIMARY KEY,
                categoria VARCHAR(50)
            )
        """)

        #tabla reviews: datos de cada review
        cursor.execute("""
            CREATE TABLE reviews_meta (
                id_review INT AUTO_INCREMENT PRIMARY KEY,
                id_usuario VARCHAR(50),
                asin VARCHAR(50),
                rating FLOAT,
                fecha DATE,
                unix_time BIGINT,
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
                FOREIGN KEY (asin) REFERENCES productos(asin)
            )
        """)

        conn.commit()
        print("BBDD y tablas SQL creadas correctamente.")

    except pymysql.MySQLError as e:
        print("Error al crear BBDD y tablas de SQL: ", e)
    finally:
        if conn:
            conn.close()


def load_data():

    """
    Esta función carga los 4 ficheros JSON de reviews de Amazon. Reparte la info entre MySQL y MongoDB.
    """

    #valores iniciales
    conn_sql = None
    client_mongo = None
    cursor = None

    try:
        
        #conexión sql
        conn_sql = pymysql.connect(host=configuracion.MYSQL_HOST, user=configuracion.MYSQL_USER, password=configuracion.MYSQL_PASS, database=configuracion.MYSQL_DB)
        cursor = conn_sql.cursor()

        #conexión mongodb
        client_mongo = MongoClient(configuracion.MONGO_URI)
        db_mongo = client_mongo[configuracion.MONGO_DB]
        coll_mongo = db_mongo[configuracion.MONGO_COLL]

        #limpiar colección de mongodb -> evitar duplicados
        coll_mongo.drop()

        #lectura de ficheros
        for categoria, ruta in configuracion.RUTAS_JSON.items():
            
            #valor inicial
            contador = 0

            try:

                with open(ruta, "r", encoding="utf-8") as fichero:

                    for linea in fichero:
                        linea = linea.strip()
                        if not linea:
                            continue

                        #p1 -> obtener json
                        try:
                            data = json.loads(linea)
                        except json.JSONDecodeError:
                            continue

                        #p2 -> extraer datos
                        uid = data.get('reviewerID')
                        name = data.get('reviewerName', 'Anónimo')
                        asin = data.get('asin')
                        rating = data.get('overall')
                        unix_time = data.get('unixReviewTime')

                        #convertir fecha a tipo date
                        if unix_time:
                            fecha_dt = datetime.date.fromtimestamp(unix_time) 
                        else:
                            fecha_dt = None

                        # convertir reviewTime a fecha para MongoDB
                        review_time_str = data.get('reviewTime')

                        if review_time_str:
                            try:
                                review_time_dt = datetime.datetime.strptime(review_time_str, "%m %d, %Y")
                            except ValueError:
                                review_time_dt = None
                        else:
                            review_time_dt = None

                        #p3 -> insertar datos
                        try:   

                            #p3.1 -> insertar usuario si no existe
                            cursor.execute(
                                "SELECT COUNT(*) FROM usuarios WHERE id_usuario = %s",
                                (uid,)
                            )

                            #si no existe -> insertar
                            if cursor.fetchone()[0] == 0:
                                cursor.execute(
                                    "INSERT INTO usuarios (id_usuario, nombre) VALUES (%s, %s)",
                                    (uid, name)
                                )

                            #p3.2 -> insertar producto si no existe
                            cursor.execute(
                                "SELECT COUNT(*) FROM productos WHERE asin = %s",
                                (asin,)
                            )

                            #si no existe -> insertar
                            if cursor.fetchone()[0] == 0:
                                cursor.execute(
                                    "INSERT INTO productos (asin, categoria) VALUES (%s, %s)",
                                    (asin, categoria)
                                )

                            #p3.3 -> insertar review
                            cursor.execute(
                                "INSERT INTO reviews_meta "
                                "(id_usuario, asin, rating, fecha, unix_time) "
                                "VALUES (%s, %s, %s, %s, %s)",
                                (uid, asin, rating, fecha_dt, unix_time)
                            )

                            #guardar id para añadir en mongo
                            id_review = cursor.lastrowid

                        except pymysql.MySQLError as e:
                            print("Error al insertar dato SQL: ", e)
                            continue

                        #p3.2 -> insertar en mongodb

                        #crear doc mongo
                        doc_mongo = {
                            "id_sql": id_review,
                            "reviewText": data.get('reviewText', ""),
                            "summary": data.get('summary', ""),
                            "helpful": data.get('helpful', [0, 0]),
                            "reviewTime": review_time_dt,
                            "categoria": categoria
                        }

                        #insertar doc
                        try:
                            coll_mongo.insert_one(doc_mongo)

                        #fallo mongo db -> eliminar datos de sql
                        except PyMongoError as e:
                            print("Error al insertar datos en MongoDB: ", e)
                            try:
                                cursor.execute(
                                    "DELETE FROM reviews_meta WHERE id_review = %s",
                                    (id_review,)
                                )
                            except pymysql.MySQLError as e_del:
                                print("Error al borrar la review de SQL: ", e_del)
                            continue

                        #final -> ambas inserciones correctas
                        contador += 1

                        #commit por lotes
                        if contador % configuracion.BATCH_SIZE == 0:
                            conn_sql.commit()
                            print(f"  Registros procesados: {contador} de la categoría {categoria}...")

                conn_sql.commit()
                print(f"Insertados {contador} registros cargados de '{categoria}'.")

            except FileNotFoundError:
                print("Error, no se encontró el archivo en la ruta: ", ruta)
                continue

    except pymysql.MySQLError as e:
        print("Error de conexión con MySQL: ", e)
    except PyMongoError as e:
        print("Error de conexión con MongoDB: ", e)
    finally:
        if cursor:
            cursor.close()
        if conn_sql:
            conn_sql.close()
        if client_mongo:
            client_mongo.close()


if __name__ == "__main__":
    create_infrastructure()
    load_data()
    print("\nCarga de datos finalizada.")