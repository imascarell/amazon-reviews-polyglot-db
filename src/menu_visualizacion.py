#menu_visualizacion.py

"""
Alumnos:
    Yago Vallarino Fernández-Cavada
    Ignacio Mascarell Agúndez
"""

#imports
import pymysql
import pymongo
import matplotlib.pyplot as plt
import configuracion
from wordcloud import WordCloud


def obtener_conexion_sql():

    """
    Esta función construye y devuelve una conexión a la base de datos MySQL.
    """

    return pymysql.connect(
        host=configuracion.MYSQL_HOST,
        user=configuracion.MYSQL_USER,
        password=configuracion.MYSQL_PASS,
        database=configuracion.MYSQL_DB
    )

def pedir_categoria(permitir_todo=True):

    """
    Esta función pide al usuario una categoría por pantalla y devuelve el nombre interno.
    """

    #posibles valores
    pos_elecciones = {
        "1": ("Videojuegos", "video_games"),
        "2": ("Juguetes", "toys_and_games"),
        "3": ("Música digital", "digital_music"),
        "4": ("Instrumentos", "musical_instruments"),
        "5": ("Deportes y aire libre", "sports_and_outdoors")
    }

    while True:

        #print informativo
        print("\nCategorías disponibles:"
        "\n\t1. Videojuegos"
        "\n\t2. Juguetes"
        "\n\t3. Música digital"
        "\n\t4. Instrumentos"
        "\n\t5. Deportes y aire libre")
        if permitir_todo:
            print("\t6. Todo")

        opcion = input("Elige una opción: ").strip()

        #validar
        if opcion in pos_elecciones:
            return pos_elecciones[opcion][1]
        elif opcion == "6" and permitir_todo:
            return "todo"
        else:
            print("Opción no válida. Inténtalo de nuevo.")


def graf_reviews_anual():

    """
    Esta función crea un histograma con el número de reviews por año y permite filtrar por categorías.
    """

    conn = None
    
    #categoría filtrado
    categoria = pedir_categoria()

    try:

        #conexiones
        conn = obtener_conexion_sql()
        cursor = conn.cursor()

        #obtener datos

        if categoria == "todo":
            cursor.execute(
                "SELECT fecha FROM reviews_meta "
                "WHERE fecha IS NOT NULL"
            )

        else:
            cursor.execute(
                "SELECT r.fecha FROM reviews_meta r "
                "JOIN productos p ON r.asin = p.asin "
                "WHERE p.categoria = %s AND r.fecha IS NOT NULL", (categoria,)
            )

        datos = cursor.fetchall()

        #agrupar por año en python
        conteo = {}
        for d in datos:
            anio = d[0].year
            if anio in conteo:
                conteo[anio] = conteo[anio] + 1
            else:
                conteo[anio] = 1

        #representar info
        if conteo:

            #ordenar por año
            anios_ord = sorted(conteo.keys())
            anios = []
            conteos = []
            for a in anios_ord:
                anios.append(str(a))
                conteos.append(conteo[a])

            plt.figure()
            plt.bar(anios, conteos, color='skyblue')
            plt.title(f"Reviews por año - {categoria}")
            plt.xlabel("Años")
            plt.ylabel("Número de reviews")
            plt.tight_layout()
            plt.show()

        else:
            print("No se encontraron datos.")

    except pymysql.MySQLError as e:
        print("Error al consultar MySQL: ", e)
    finally:
        if conn:
            conn.close()


def graf_popularidad():

    """
    Esta función construye una curva de popularidad de artículos ordenados de mayor a menor y permite filtrar por categorías.
    """

    conn = None

    #valores iniciales
    categoria = pedir_categoria()

    try:
        
        #conexiones
        conn = obtener_conexion_sql()
        cursor = conn.cursor()

        #obtener datos

        if categoria == "todo":
            cursor.execute(
                "SELECT asin, COUNT(*) as total FROM reviews_meta "
                "GROUP BY asin ORDER BY total DESC"
            )

        else:
            cursor.execute(
                "SELECT r.asin, COUNT(*) as total FROM reviews_meta r "
                "JOIN productos p ON r.asin = p.asin "
                "WHERE p.categoria = %s "
                "GROUP BY r.asin ORDER BY total DESC", (categoria,)
            )

        datos = cursor.fetchall()

        #representar datos
        if datos:

            conteos = []
            for d in datos:
                conteos.append(d[1])

            plt.figure()
            plt.plot(range(len(conteos)), conteos, color='red')
            plt.fill_between(range(len(conteos)), conteos, color='red', alpha=0.2)
            plt.title(f"Popularidad de artículos - {categoria}")
            plt.xlabel("Artículos (ordenados por popularidad)")
            plt.ylabel("Número de reviews")
            plt.tight_layout()
            plt.show()

        else:
            print("No se encontraron datos.")

    except pymysql.MySQLError as e:
        print("Error al consultar MySQL: ", e)
    finally:
        if conn:
            conn.close()


def graf_histograma_overall():

    """
    Esta función construye un histograma por overall y permite filtrar por categorías o buscar por asin.
    """

    conn = None

    #valores iniciales
    modo = None
    
    while True:
        print("\nOpciones de filtrado:" \
        "\n\t1. Por categoría o todas" \
        "\n\t2. Por asin")
        modo = input("Elige una opción: ").strip()
        if modo not in ["1", "2"]:
            print("Opción no válida.")
        else:
            break

    try:

        #conexión sql
        conn = obtener_conexion_sql()
        cursor = conn.cursor()

        if modo == "2":

            #buscar por artículo individual
            asin_seleccionado = input("Introduce el asin del artículo: ").strip()

            #comprobar si el artículo existe
            cursor.execute("SELECT COUNT(*) FROM productos WHERE asin = %s", (asin_seleccionado,))
            existencia = cursor.fetchone()[0]

            if existencia == 0:
                print(f"El artículo {asin_seleccionado} no existe en la base de datos.")
                return

            #si asin existe -> obtener datos
            cursor.execute(
                "SELECT rating, COUNT(*) FROM reviews_meta "
                "WHERE asin = %s GROUP BY rating ORDER BY rating", (asin_seleccionado,)
            )

            titulo = f"Histograma por overall - Artículo {asin_seleccionado}"

        else:

            #buscar por categoría
            categoria = pedir_categoria()

            #obtener datos
            if categoria == "todo":
                cursor.execute(
                    "SELECT rating, COUNT(*) FROM reviews_meta "
                    "GROUP BY rating ORDER BY rating"
                )

            else:
                cursor.execute(
                    "SELECT r.rating, COUNT(*) FROM reviews_meta r "
                    "JOIN productos p ON r.asin = p.asin "
                    "WHERE p.categoria = %s "
                    "GROUP BY r.rating ORDER BY r.rating", (categoria,)
                )
            titulo = f"Histograma por nota - {categoria}"

        datos = cursor.fetchall()
        
        #representar datos
        if datos:
            notas = [str(d[0]) for d in datos]
            conteos = [d[1] for d in datos]
            plt.figure()
            plt.bar(notas, conteos, color='green')
            plt.title(titulo)
            plt.xlabel("Puntuación")
            plt.ylabel("Número de reviews")
            plt.tight_layout()
            plt.show()

        else:
            print("No se encontraron datos.")

    except pymysql.MySQLError as e:
        print("Error al consultar MySQL: ", e)
    finally:
        if conn:
            conn.close()


def graf_evol_temp():

    """
    Esta función crea una representación de la evolución acumulada de reviews a lo largo del tiempo.
    """

    conn = None

    try:

        #conexión
        conn = obtener_conexion_sql()
        cursor = conn.cursor()

        #obtener las categorías disponibles
        cursor.execute("SELECT DISTINCT categoria FROM productos")
        categorias = []
        for fila in cursor.fetchall():
            categorias.append(fila[0])

        plt.figure(figsize=(10, 6))

        for categoria in categorias:

            #obtener datos y ordenar tiempos
            cursor.execute(
                "SELECT r.fecha FROM reviews_meta r "
                "JOIN productos p ON r.asin = p.asin "
                "WHERE p.categoria = %s AND r.unix_time IS NOT NULL "
                "ORDER BY r.unix_time", (categoria,)
            )
            datos = cursor.fetchall()

            #representar
            if datos:
                timestamps = []
                for d in datos:
                    timestamps.append(d[0])
                acumulado = list(range(1, len(timestamps) + 1)) #Evolución del número total de reviews realizadas en una categoría hasta un momento de tiempo determinado.
                plt.plot(timestamps, acumulado, label=categoria)

        plt.title("Evolución de reviews a lo largo del tiempo")
        plt.xlabel("Tiempo")
        plt.ylabel("Número de reviews acumuladas")
        plt.legend()
        plt.grid(True, linestyle=':', alpha=0.6)
        plt.tight_layout()
        plt.show()

    except pymysql.MySQLError as e:
        print("Error al consultar MySQL: ", e)
    finally:
        if conn:
            conn.close()


def graf_reviews_user():

    """
    Esta función crea un histograma sobre el número de reviews y de usuarios.
    """

    conn = None

    try:

        #conexión
        conn = obtener_conexion_sql()
        cursor = conn.cursor()

        #obtener datos
        cursor.execute(
            "SELECT id_usuario, COUNT(*) as total FROM reviews_meta "
            "GROUP BY id_usuario ORDER BY total DESC"
        )
        datos = cursor.fetchall()

        #representar gráficamente
        if datos:
            conteos = []
            for d in datos:
                conteos.append(d[1])
            plt.figure()
            plt.hist(conteos, bins=50, color='orange', log=True)
            plt.title("Distribución de reviews por usuario")
            plt.xlabel("Número de reviews realizadas")
            plt.ylabel("Número de usuarios (log)")
            plt.tight_layout()
            plt.show()

        else:
            print("No se encontraron datos.")

    except pymysql.MySQLError as e:
        print("Error al consultar MySQL: ", e)
    finally:
        if conn:
            conn.close()


def graf_nube_palabras():

    """
    Esta función crea una nube de palabras (de más de 3 caracteres) a partir del campo 'summary' de mongodb.
    """
    
    client = None

    #valores iniciales
    categoria = pedir_categoria(permitir_todo=False)

    try:

        #conexión a mongodb
        client = pymongo.MongoClient(configuracion.MONGO_URI)
        db = client[configuracion.MONGO_DB]

        #filtrado por categoría
        cursor_mongo = db[configuracion.MONGO_COLL].find(
            {"categoria": categoria},
            {"summary": 1}
        )

        #obtener palabras 
        lista_palabras = []
        for doc in cursor_mongo:

            summary = doc.get('summary', '')
            palabras_sucias = str(summary).split()  #palabras individuales
            
            #filtrar palabras por longitud
            for p in palabras_sucias:
                if len(p) > 3:
                    lista_palabras.append(p)
                    
        #unir todas las palabras en str
        texto = " ".join(lista_palabras)

        #representar datos
        try:
            wordcloud = WordCloud(width=800, height=400, background_color='white').generate(texto)
            plt.figure()
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis("off")
            plt.title(f"Nube de palabras - {categoria}")
            plt.tight_layout()
            plt.show()
        except ValueError:
            print("No se encontraron datos para esa categoría.")
            pass

    except pymongo.errors.PyMongoError as e:
        print("Error al consultar MongoDB: ", e)
    finally:
        if client:
            client.close()


def graf_rating_medio_categoria():

    """
    Esta función representa en un grafico de barras horizontales el rating medio por categoría
    """

    conn = None

    try:

        #conexión a sql
        conn = obtener_conexion_sql()
        cursor = conn.cursor()

        #obtener datos
        cursor.execute(
            "SELECT p.categoria, AVG(r.rating) as media "
            "FROM reviews_meta r "
            "JOIN productos p ON r.asin = p.asin "
            "GROUP BY p.categoria ORDER BY media DESC"
        )
        datos = cursor.fetchall()

        #representar
        if datos:
            nombres = {
                "video_games": "Videojuegos",
                "toys_and_games": "Juguetes",
                "digital_music": "Música",
                "musical_instruments": "Instrumentos",
                "sports_and_outdoors": "Deportes"
            }

            #valores iniciales
            categorias = []
            medias = []

            #recorrer datos y extraer info
            for d in datos:
                
                nombre_interno = d[0]
                valor_media = d[1]
                
                #buscar si nombre tiene traducción
                if nombre_interno in nombres:
                    nombre_final = nombres[nombre_interno]
                else:
                    nombre_final = nombre_interno
                
                #añadir info
                categorias.append(nombre_final)
                medias.append(valor_media)

            #representar gráficamente
            plt.figure(figsize=(10, 6))
            bars = plt.barh(categorias, medias, color='salmon', edgecolor='darkred')

            for bar in bars:
                plt.text(bar.get_width() - 0.3, bar.get_y() + bar.get_height()/2,
                         f'{bar.get_width():.2f}', va='center', color='white', fontweight='bold')

            plt.title("Rating medio por categoría")
            plt.xlabel("Puntuación media (0-5)")
            plt.xlim(0, 5)
            plt.grid(axis='x', linestyle='--', alpha=0.3)
            plt.tight_layout()
            plt.show()

        else:
            print("No se encontraron datos.")

    except pymysql.MySQLError as e:
        print("Error al consultar MySQL: ", e)
    finally:
        if conn:
            conn.close()


def mostrar_menu():

    """
    Esta función muestra el menú de opciones de visualización en bucle hasta que el usuario elija salir.
    """

    while True:

        print("\n", "-"*15, "\nVISUALIZADOR DE DATOS\n", "-"*15, "\n")
        print("1. Reviews por año" \
        "\n2. Popularidad de artículos" \
        "\n3. Histograma por nota" \
        "\n4. Evolución temporal por categorías" \
        "\n5. Reviews por usuario" \
        "\n6. Nube de palabras" \
        "\n7. Rating medio por categoría" \
        "\n8. Salir")

        op = input("\nSeleccione una opción: ").strip()

        if op == "1": 
            graf_reviews_anual()
        elif op == "2": 
            graf_popularidad()
        elif op == "3": 
            graf_histograma_overall()
        elif op == "4": 
            graf_evol_temp()
        elif op == "5": 
            graf_reviews_user()
        elif op == "6": 
            graf_nube_palabras()
        elif op == "7": 
            graf_rating_medio_categoria()
        elif op == "8":
            print("Saliendo de las gráficas.")
            break
        
        #validar opción
        else:
            print("Opción no válida.")


if __name__ == "__main__":
    mostrar_menu()