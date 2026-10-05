#menu_interactivo.py

"""
Alumnos:
    Yago Vallarino Fernández-Cavada
    Ignacio Mascarell Agúndez
"""

#imports
import streamlit as st
import pymysql
import pymongo
import matplotlib.pyplot as plt
import configuracion
from wordcloud import WordCloud


def obtener_conexion_sql():

    """
    Esta funcion crea y devuelve una conexion a la base de datos MySQL.
    """

    return pymysql.connect(
        host=configuracion.MYSQL_HOST,
        user=configuracion.MYSQL_USER,
        password=configuracion.MYSQL_PASS,
        database=configuracion.MYSQL_DB
    )


def graf_reviews_anual():

    """
    Esta función realiza la primera gráfica: histograma de reviews por anio con filtro de categoria.
    """

    conn = None

    #valores iniciales
    categoria = st.selectbox(
        "Categoria",
        ["todo", "video_games", "toys_and_games", "digital_music", "musical_instruments", "sports_and_outdoors"],
        key="cat_anual"
    )

    if st.button("Generar grafica", key="btn_anual"):
        try:

            #conexión sql
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

            #representar datos
            if conteo:
                anios_ord = sorted(conteo.keys())
                anios = []
                conteos = []
                for a in anios_ord:
                    anios.append(str(a))
                    conteos.append(conteo[a])
                fig, ax = plt.subplots()
                ax.bar(anios, conteos, color='skyblue')
                ax.set_title(f"Reviews por anio - {categoria}")
                ax.set_xlabel("Anios")
                ax.set_ylabel("Numero de reviews")
                fig.tight_layout()
                st.pyplot(fig)
            else:
                st.warning("No se encontraron datos.")

        except pymysql.MySQLError as e:
            st.error(f"Error MySQL: {e}")
        finally:
            if conn:
                conn.close()


def graf_popularidad():

    """
    Esta función realiza la segunda gráfica: curva de popularidad de articulos
    """

    conn = None

    #valores iniciales
    categoria = st.selectbox(
        "Categoria",
        ["todo", "video_games", "toys_and_games", "digital_music", "musical_instruments", "sports_and_outdoors"],
        key="cat_pop"
    )

    if st.button("Generar grafica", key="btn_pop"):
        try:

            #conexión sql
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
                fig, ax = plt.subplots()
                ax.plot(range(len(conteos)), conteos, color='red')
                ax.fill_between(range(len(conteos)), conteos, color='red', alpha=0.2)
                ax.set_title(f"Popularidad de articulos - {categoria}")
                ax.set_xlabel("Articulos (ordenados por popularidad)")
                ax.set_ylabel("Numero de reviews")
                fig.tight_layout()
                st.pyplot(fig)
            else:
                st.warning("No se encontraron datos.")

        except pymysql.MySQLError as e:
            st.error(f"Error MySQL: {e}")
        finally:
            if conn:
                conn.close()


def graf_histograma_overall():

    """
    Esta función realiza la tercera gráfica: histograma por nota con opcion de filtrar por categoria o asin.
    """

    conn = None

    #preguntar modo
    modo = st.radio("Filtrar por:", ["Categoria", "ASIN"], key="modo_nota")

    if modo == "ASIN":

        #op 1 -> filtrado por asin
        asin_buscar = st.text_input("Introduce el asin del articulo:", key="asin_input")

        if st.button("Generar grafica", key="btn_nota_asin"):
            if not asin_buscar.strip():
                st.warning("Debes introducir un ASIN.")
                return

            try:

                #conexión sql
                conn = obtener_conexion_sql()
                cursor = conn.cursor()

                #comprobar que asin existe
                cursor.execute("SELECT COUNT(*) FROM productos WHERE asin = %s", (asin_buscar,))
                existe = cursor.fetchone()[0]
                if existe == 0:
                    st.warning(f"El articulo '{asin_buscar}' no existe.")
                    return

                #obtener datos
                cursor.execute(
                    "SELECT rating, COUNT(*) FROM reviews_meta "
                    "WHERE asin = %s GROUP BY rating ORDER BY rating", (asin_buscar,)
                )
                datos = cursor.fetchall()

                #representar datos
                if datos:
                    notas = []
                    conteos = []
                    for d in datos:
                        notas.append(str(d[0]))
                        conteos.append(d[1])
                    fig, ax = plt.subplots()
                    ax.bar(notas, conteos, color='green')
                    ax.set_title(f"Histograma por nota - {asin_buscar}")
                    ax.set_xlabel("Puntuacion")
                    ax.set_ylabel("Numero de reviews")
                    fig.tight_layout()
                    st.pyplot(fig)
                else:
                    st.warning("No se encontraron datos.")

            except pymysql.MySQLError as e:
                st.error(f"Error MySQL: {e}")
            finally:
                if conn:
                    conn.close()

    else:

        #valor inicial
        categoria = st.selectbox(
            "Categoria",
            ["todo", "video_games", "toys_and_games", "digital_music", "musical_instruments", "sports_and_outdoors"],
            key="cat_nota"
        )

        if st.button("Generar grafica", key="btn_nota_cat"):
            try:

                #conexión sql
                conn = obtener_conexion_sql()
                cursor = conn.cursor()

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

                datos = cursor.fetchall()

                #representar datos
                if datos:
                    notas = []
                    conteos = []
                    for d in datos:
                        notas.append(str(d[0]))
                        conteos.append(d[1])
                    fig, ax = plt.subplots()
                    ax.bar(notas, conteos, color='green')
                    ax.set_title(f"Histograma por nota - {categoria}")
                    ax.set_xlabel("Puntuacion")
                    ax.set_ylabel("Numero de reviews")
                    fig.tight_layout()
                    st.pyplot(fig)
                else:
                    st.warning("No se encontraron datos.")

            except pymysql.MySQLError as e:
                st.error(f"Error MySQL: {e}")
            finally:
                if conn:
                    conn.close()


def graf_evol_temp():

    """
    Esta función realiza la cuarta gráfica: evolucion temporal acumulada por categorias.
    """

    conn = None

    if st.button("Generar grafica", key="btn_evol"):
        try:

            #conexión sql
            conn = obtener_conexion_sql()
            cursor = conn.cursor()

            cursor.execute("SELECT DISTINCT categoria FROM productos")
            categorias = []
            for fila in cursor.fetchall():
                categorias.append(fila[0])

            fig, ax = plt.subplots(figsize=(10, 6))

            #obtener datos
            for categoria in categorias:
                cursor.execute(
                    "SELECT r.fecha FROM reviews_meta r "
                    "JOIN productos p ON r.asin = p.asin "
                    "WHERE p.categoria = %s AND r.fecha IS NOT NULL "
                    "ORDER BY r.fecha", (categoria,)
                )
                datos = cursor.fetchall()

                #añadir a futura representación
                if datos:
                    timestamps = []
                    for d in datos:
                        timestamps.append(d[0])
                    acumulado = list(range(1, len(timestamps) + 1))
                    ax.plot(timestamps, acumulado, label=categoria)

            ax.set_title("Evolucion de reviews a lo largo del tiempo")
            ax.set_xlabel("Tiempo (timestamp)")
            ax.set_ylabel("Numero de reviews acumuladas")
            ax.legend()
            ax.grid(True, linestyle=':', alpha=0.6)
            fig.tight_layout()
            st.pyplot(fig)

        except pymysql.MySQLError as e:
            st.error(f"Error MySQL: {e}")
        finally:
            if conn:
                conn.close()


def graf_reviews_user():

    """
    Esta función realiza la quinta gráfica: distribucion de reviews por usuario.
    """

    conn = None

    if st.button("Generar grafica", key="btn_user"):
        try:

            #conexión sql
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
                fig, ax = plt.subplots()
                ax.hist(conteos, bins=50, color='orange', log=True)
                ax.set_title("Distribucion de reviews por usuario")
                ax.set_xlabel("Numero de reviews realizadas")
                ax.set_ylabel("Numero de usuarios (log)")
                fig.tight_layout()
                st.pyplot(fig)
            else:
                st.warning("No se encontraron datos.")

        except pymysql.MySQLError as e:
            st.error(f"Error MySQL: {e}")
        finally:
            if conn:
                conn.close()


def graf_nube_palabras():

    """
    Esta función realiza la sexta gráfica: nube de palabras por categoria desde MongoDB.
    """
    
    client = None
    
    #valor inicial
    categoria = st.selectbox(
        "Categoria (obligatorio)",
        ["video_games", "toys_and_games", "digital_music", "musical_instruments", "sports_and_outdoors"],
        key="cat_nube"
    )

    if st.button("Generar nube", key="btn_nube"):
        try:

            #conexión mongodb
            client = pymongo.MongoClient(configuracion.MONGO_URI)
            db = client[configuracion.MONGO_DB]

            cursor_mongo = db[configuracion.MONGO_COLL].find(
                {"categoria": categoria},
                {"summary": 1}
            )

            #obtener datos
            lista_palabras = []
            for doc in cursor_mongo:
                summary = doc.get('summary', '')
                palabras_sucias = str(summary).split()
                for p in palabras_sucias:
                    if len(p) > 3:
                        lista_palabras.append(p)

            texto = " ".join(lista_palabras)

            #representar datos
            try:
                wordcloud = WordCloud(width=800, height=400, background_color='white').generate(texto)
                fig, ax = plt.subplots()
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis("off")
                ax.set_title(f"Nube de palabras - {categoria}")
                fig.tight_layout()
                st.pyplot(fig)
            except ValueError:
                st.warning("No se encontraron datos para esa categoría.")

        except pymongo.errors.PyMongoError as e:
            st.error(f"Error MongoDB: {e}")
        finally:
            if client:
                client.close()


def graf_rating_medio():

    """"
    Esta función realiza la séptima gráfica: rating medio por categoria.
    """

    conn = None

    if st.button("Generar grafica", key="btn_rating"):
        try:

            #conexión sql
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
                    "digital_music": "Musica",
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
                fig, ax = plt.subplots(figsize=(10, 6))
                bars = ax.barh(categorias, medias, color='salmon', edgecolor='darkred')

                for bar in bars:
                    ax.text(bar.get_width() - 0.3, bar.get_y() + bar.get_height()/2,
                            f'{bar.get_width():.2f}', va='center', color='white', fontweight='bold')

                ax.set_title("Rating medio por categoria")
                ax.set_xlabel("Puntuacion media (0-5)")
                ax.set_xlim(0, 5)
                ax.grid(axis='x', linestyle='--', alpha=0.3)
                fig.tight_layout()
                st.pyplot(fig)
            else:
                st.warning("No se encontraron datos.")

        except pymysql.MySQLError as e:
            st.error(f"Error MySQL: {e}")
        finally:
            if conn:
                conn.close()

if __name__ == '__main__':

    #pagina principal
    st.title("VISUALIZADOR DE DATOS")
    st.markdown("**Amazon Reviews - MySQL, MongoDB y Neo4J**")

    #menu lateral
    opcion = st.sidebar.radio(
        "Selecciona una grafica:",
        [
            "1. Reviews por anio",
            "2. Popularidad de articulos",
            "3. Histograma por nota",
            "4. Evolucion temporal",
            "5. Reviews por usuario",
            "6. Nube de palabras",
            "7. Rating medio por categoria"
        ]
    )

    if opcion.startswith("1"):
        graf_reviews_anual()
    elif opcion.startswith("2"):
        graf_popularidad()
    elif opcion.startswith("3"):
        graf_histograma_overall()
    elif opcion.startswith("4"):
        graf_evol_temp()
    elif opcion.startswith("5"):
        graf_reviews_user()
    elif opcion.startswith("6"):
        graf_nube_palabras()
    elif opcion.startswith("7"):
        graf_rating_medio()