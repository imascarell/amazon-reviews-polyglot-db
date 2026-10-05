#inserta_dataset

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


def insertar_datos_quinto_dataset():

    """
    Esta función carga un fichero JSON de reviews y lo inserta en una BBDD ya creada. 
    """

    #valores iniciales
    archivo_json = configuracion.RUTA_QUINTO_JSON
    nombre_categoria = configuracion.CATEGORIA_QUINTO
    conn_sql = None
    client_mongo = None
    cursor = None

    try:

        #conexión sql
        conn_sql = pymysql.connect(
            host=configuracion.MYSQL_HOST,
            user=configuracion.MYSQL_USER,
            password=configuracion.MYSQL_PASS,
            database=configuracion.MYSQL_DB
        )
        cursor = conn_sql.cursor()

        #conexión mongodb
        client_mongo = MongoClient(configuracion.MONGO_URI)
        db_mongo = client_mongo[configuracion.MONGO_DB]
        coll_mongo = db_mongo[configuracion.MONGO_COLL]

        #valores iniciales y print informativo
        contador = 0
        print(f"Iniciar carga de categoría {nombre_categoria}")

        with open(archivo_json, "r", encoding="utf-8") as fichero:

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

                #p3 -> insertar en sql
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

                    #si no existe -> insertarS
                    if cursor.fetchone()[0] == 0:
                        cursor.execute(
                            "INSERT INTO productos (asin, categoria) VALUES (%s, %s)",
                            (asin, nombre_categoria)
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

                #p4 -> insertar en mongodb

                #crear doc mongo
                doc_mongo = {
                    "id_sql": id_review,
                    "reviewText": data.get('reviewText', ""),
                    "summary": data.get('summary', ""),
                    "helpful": data.get('helpful', [0, 0]),
                    "reviewTime": review_time_dt,
                    "categoria": nombre_categoria
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
                    print(f"  Registros procesados: {contador}...")

        conn_sql.commit()
        print(f"Insertados {contador} registros cargados de '{nombre_categoria}'.")

    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{archivo_json}'.")
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
    insertar_datos_quinto_dataset()
    print("\nCarga del quinto dataset finalizada.")