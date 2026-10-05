#neo4JProyecto.py

"""
Alumnos:
    Yago Vallarino Fernández-Cavada
    Ignacio Mascarell Agúndez
"""

#imports
from neo4j import GraphDatabase
import pymysql
import configuracion
import math
import random


def obtener_driver():

    """
    Esta función construye y devuelve un driver de conexión a Neo4J.
    """

    uri = f"neo4j://{configuracion.NEO4J_HOST}:{configuracion.NEO4J_PORT}"
    return GraphDatabase.driver(uri, auth=(configuracion.NEO4J_USER, configuracion.NEO4J_PASS))


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
        "5": ("Deportes y Aire Libre", "sports_and_outdoors")
    }

    while True:

        #print informativo
        print("\nCategorías disponibles:"
        "\n\t1. Videojuegos"
        "\n\t2. Juguetes"
        "\n\t3. Música digital"
        "\n\t4. Instrumentos"
        "\n\t5. Deportes y Aire Libre")
        if permitir_todo:
            print("  6. Todo")

        opcion = input("Elige una opción: ").strip()

        #validar
        if opcion in pos_elecciones:
            return pos_elecciones[opcion][1]
        elif opcion == "6" and permitir_todo:
            return "todo"
        else:
            print("Opción no válida. Inténtalo de nuevo.")


def calcular_correl_pearson(u1_ratings, u2_ratings):

    """
    Esta función calcula la correlación de Pearson entre dos usuarios y devuelve su valor de la correlación y el número de artículos en común.
    """

    #cálculo de comunes

    #valor inicial
    comunes = []

    for articulo in u1_ratings:
        
        #si está en ratings de u1 y de u2 -> añadir
        if articulo in u2_ratings:
            comunes.append(articulo)

    if len(comunes) == 0:
        return 0, 0
    
    #cálculo de fórmula de Pearson

    #cantidad de comunes
    n_comunes = len(comunes)

    #p1 -> calcular media de valoraciones

    #valores iniciales
    suma_u1 = 0
    suma_u2 = 0
    
    for a in comunes:

        suma_u1 = suma_u1 + u1_ratings[a]
        suma_u2 = suma_u2 + u2_ratings[a]
        
    media1 = suma_u1 / n_comunes
    media2 = suma_u2 / n_comunes

    #p2 -> calcular numerador y denominadores

    #valores iniciales
    num = 0
    denom_1_sucio = 0
    denom_2_sucio = 0
    
    for a in comunes:

        #dif entre nota del artículo y media del usuario
        dif_1 = u1_ratings[a] - media1
        dif_2 = u2_ratings[a] - media2
        
        #num = sumatorio prod de dif
        num = num + (dif_1 * dif_2)
        
        #denoms antes de raíz cuadrado = sumatorio de dif al cuadrado
        denom_1_sucio = denom_1_sucio + (dif_1 ** 2)
        denom_2_sucio = denom_2_sucio + (dif_2 ** 2)

    #aplicar raíz cuad a denoms
    denom_1 = math.sqrt(denom_1_sucio)
    denom_2 = math.sqrt(denom_2_sucio)

    #comprobación de seguridad
    if denom_1 == 0 or denom_2 == 0:
        return 0, n_comunes
    
    #sustituir en fórmula
    resultado = num / (denom_1 * denom_2)

    return resultado, n_comunes


def cargar_4_1_similitudes():

    """
    Esta función completa la parte de carga de datos del apartado 4.1.
    Obtiene los top N usuarios con más reviews, calcula similitud de Pearson entre ellos y carga nodos y relaciones en Neo4J.
    """

    conn = None
    driver = None
    
    #val inicial y print informativo
    top_n = configuracion.TOP_N_USUARIOS
    print(f"Apartado 4.1. Calculando  y cargando en Neo4J similitudes Pearson de Top {top_n} usuarios")

    try:

        #conexion sql
        conn = obtener_conexion_sql()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id_usuario FROM reviews_meta "
            "GROUP BY id_usuario ORDER BY COUNT(*) DESC LIMIT %s", (top_n,)
        )

        #obtener top usuarios
        usuarios = []
        filas = cursor.fetchall()
        for f in filas:
            usuarios.append(f[0])

        #obtener ratings para calcular pearson
        data_ratings = {}

        for user_id in usuarios:
            cursor.execute(
                "SELECT asin, rating FROM reviews_meta WHERE id_usuario = %s",
                (user_id,)
            )

            filas = cursor.fetchall()
            ratings_usuario = {}

            for f in filas:
                ratings_usuario[f[0]] = f[1]

            data_ratings[user_id] = ratings_usuario

        #carga de datos en neo4j
        driver = obtener_driver()
        with driver.session() as session:

            #borrar datos anteriores
            session.run("MATCH (n) DETACH DELETE n")

            for usuario_id in usuarios:
                session.run("CREATE (:Usuario {id: $id})", id=usuario_id)

            for i in range(len(usuarios)):
                for j in range(i + 1, len(usuarios)):

                    #calcular pearson
                    correl, n_comunes = calcular_correl_pearson(data_ratings[usuarios[i]], data_ratings[usuarios[j]])

                    #guardar datos si tienen comunes
                    if n_comunes > 0:
                        session.run(
                        """
                            MATCH (a:Usuario {id: $id1}), (b:Usuario {id: $id2})
                            CREATE (a)-[:SIMILAR {valor: $sim}]->(b)
                            CREATE (b)-[:SIMILAR {valor: $sim}]->(a)
                        """, 
                        id1=usuarios[i], id2=usuarios[j], sim=correl)

        print("Carga de datos del apartado 4.1 completada.\n")

    except (pymysql.MySQLError, Exception) as e:
        print("Error en 4.1: ", e)
    finally:
        if conn:
            conn.close()
        if driver:
            driver.close()


def consulta_4_1_vecinos():

    """
    Esta función completa el apartado 4.1. 
    Muestra por pantalla el usuario con más vecinos en Neo4J. 
    """

    driver = None

    try:

        driver = obtener_driver()
        with driver.session() as session:
            
            #obtener usuario
            query = """
                MATCH (u:Usuario)-[:SIMILAR]->(v:Usuario)
                RETURN u.id AS id, COUNT(v) AS num_vecinos
                ORDER BY num_vecinos DESC LIMIT 1
            """

            usuarios_resultantes = session.run(query)
            lista_usuarios = usuarios_resultantes.data()

            #mostrar usuario encontrado
            if lista_usuarios:
                usuario_n_vecinos_max = lista_usuarios[0]
                print(f"\nUsuario con más vecinos: {usuario_n_vecinos_max['id']} con {usuario_n_vecinos_max['num_vecinos']} vecinos"
                      "\nApartado 4.1 completado.")

    except Exception as e:
        print("Error en consulta 4.1: ", e)
    finally:
        if driver:
            driver.close()


def cargar_4_2_aleatorios():

    """
    Esta función realiza el apartado 4.2.
    Selecciona N artículos alteadorios de una categoría y muestra en Neo4J cada artículo y los usuarios que le han hecho una review.
    """

    #obtener categoría y n artículos
    categoria_db = pedir_categoria(permitir_todo=False) 
    n = obtener_n_articulos_4_2()

    #print informativo
    print(f"Apartado 4.2. Obteniendo y cargando en Neo4J {n} artículos aleatorios de categoría {categoria_db}")

    conn = None
    driver = None

    try:

        #conexión sql
        conn = obtener_conexion_sql()
        cursor = conn.cursor()
        cursor.execute("SELECT asin FROM productos WHERE categoria = %s", (categoria_db,))
        
        #obtener todos los artículos y seleccionar n aleatorios
        todos_articulos = []
        for row in cursor.fetchall():
            todos_articulos.append(row[0])

        #selección aleatoria en python
        if n > len(todos_articulos):
            n = len(todos_articulos)
        articulos = random.sample(todos_articulos, n)

        #cargar en neo4j
        driver = obtener_driver()
        with driver.session() as session:

            #borrar datos anteriores
            session.run("MATCH (n) DETACH DELETE n")

            for asin in articulos:
                
                #crear nodo para asin
                session.run("CREATE (:Articulo {asin: $asin})", asin=asin)

                #obtener datos de asin desde sql
                cursor.execute("SELECT id_usuario, rating, fecha FROM reviews_meta WHERE asin = %s", (asin,))

                for review in cursor.fetchall():

                    #añadir datos a neo4j
                    session.run(
                        "MERGE (u:Usuario {id: $usuario_id}) "
                        "WITH u MATCH (a:Articulo {asin: $asin}) "
                        "CREATE (u)-[:PUNTUO {nota: $nota, fecha: $fecha}]->(a)",
                        usuario_id=review[0], asin=asin, nota=review[1], fecha=str(review[2])
                    )

        print("Carga 4.2 completada." \
        "\nApartado 4.2 completado.")

    except (pymysql.MySQLError, Exception) as e:
        print("Error en 4.2: ", e)
    finally:
        if conn:
            conn.close()
        if driver:
            driver.close()


def obtener_n_articulos_4_2():

    """
    Esta función maneja la selección de artículos para el apartado 4.2.
    """

    #selección y validación
    n_str = input("Introduce la cantidad de artículos seleccionada: ").strip()
    valid = False
    while not valid:
        if n_str.isnumeric() and int(n_str) > 0:
            valid = True
        else:
            print("Debes introducir un valor numérico válido y mayor que 0.")
            n_str = input("Introduce la cantidad de artículos seleccionada: ").strip()
            
    return int(n_str)

    
def cargar_4_3_categoria():

    """
    Esta función realiza el apartado 4.3, seleccionando los primeros 400 ususarios ordenados por nombre.
    Si el usuario ha puntuado artículos de 2 o más categorías, se muestra en Neo4J.
    """

    conn = None
    driver = None

    #print informativo
    print("Apartado 4.3. Obteniendo 400 usuarios ordenados y filtrando para cargar en Neo4J.")

    try:

        #conexión sql
        conn = obtener_conexion_sql()
        cursor = conn.cursor()
        
        #obtener 400 usuarios ordenados por nombre -> agrupar según usuario y categoría
        query = """
                    SELECT r.id_usuario, p.categoria, COUNT(r.asin) as num_articulos
                    FROM reviews_meta r
                    JOIN productos p ON r.asin = p.asin
                    WHERE r.id_usuario IN (
                        SELECT id_usuario FROM (
                            SELECT u2.id_usuario
                            FROM usuarios u2
                            JOIN reviews_meta r2 ON u2.id_usuario = r2.id_usuario
                            GROUP BY u2.id_usuario, u2.nombre
                            ORDER BY u2.nombre
                            LIMIT 400
                        ) as t
                    )
                    GROUP BY r.id_usuario, p.categoria
                """

        #obtener datos
        cursor.execute(query)
        datos = cursor.fetchall()

        #organizar datos en dict
        usuarios_dict = {}
        for usuario_id, categoria, cant in datos:
            if usuario_id not in usuarios_dict:
                usuarios_dict[usuario_id] = []
            usuarios_dict[usuario_id].append({"categoria": categoria, "cant": cant})

        #cargar en neo4j
        driver = obtener_driver()
        with driver.session() as session:

            #eliminar datos anteriores
            session.run("MATCH (n) DETACH DELETE n")

            for usuario_id, info_categorias in usuarios_dict.items():
                
                #filtrar usuarios -> review en 2 o más categorías distintas
                if len(info_categorias) >= 2:
                    session.run("MERGE (u:Usuario {id: $usuario_id})", usuario_id=usuario_id)

                    for item in info_categorias:

                        #filtro seguridad
                        session.run("MERGE (c:TipoArticulo {nombre: $categoria})", categoria=item["categoria"])

                        #añadir usuario
                        session.run("""
                            MATCH (u:Usuario {id: $usuario_id})
                            MATCH (c:TipoArticulo {nombre: $categoria})
                            MERGE (u)-[r:PUNTUO_CATEGORIA]->(c)
                            SET r.cantidad = $cant
                        """, usuario_id=usuario_id, categoria=item["categoria"], cant=item["cant"])

        print("Carga 4.3 finalizada.")

    except (pymysql.MySQLError, Exception) as e:
        print("Error en 4.3: ", e)
    finally:
        if conn:
            conn.close()
        if driver:
            driver.close()


def cargar_4_4_populares():

    """
    Esta función realiza el apartado 4.4. 
    Selecciona los 5 artículos más populares con menos de 40 reviews y carga información a Neo4J según los usuarios que les han hecho alfuna review.
    """

    conn = None
    driver = None

    #print informativo
    print("\nApartado 4.4. Seleccionando 5 artículos más populares con menos de 40 reviews y cargando información a Neo4J.")

    try:

        #conexión sql
        conn = obtener_conexion_sql()
        cursor = conn.cursor()

        #obtener artículos con filtrado
        query_articulos = """
            SELECT asin, COUNT(*) as total
            FROM reviews_meta
            GROUP BY asin
            HAVING total < 40
            ORDER BY total DESC
            LIMIT 5
        """

        cursor.execute(query_articulos)
        articulos_populares = cursor.fetchall()

        #cargar info en neo4j
        driver = obtener_driver()
        with driver.session() as session:

            #borrar datos anteriores
            session.run("MATCH (n) DETACH DELETE n")

            for articulo in articulos_populares:

                asin_val = articulo[0]

                #crear nodo artículo
                session.run("MERGE (a:Articulo {asin: $asin})", asin=asin_val)

                #buscar ususarios de artículo
                cursor.execute("SELECT id_usuario FROM reviews_meta WHERE asin = %s", (asin_val,))
                usuarios = cursor.fetchall()

                for user in usuarios:

                    usuario_id = user[0]
                    
                    #crear ususario y relación con artículo
                    session.run("""
                        MERGE (u:Usuario {id: $usuario_id})
                        WITH u
                        MATCH (a:Articulo {asin: $asin})
                        MERGE (u)-[:PUNTUO]->(a)
                    """, usuario_id=usuario_id, asin=asin_val)

            #realación entre usuarios que comparten artículos puntuados en común
            session.run("""
                MATCH (u1:Usuario)-[:PUNTUO]->(a:Articulo)<-[:PUNTUO]-(u2:Usuario)
                WHERE u1.id < u2.id
                WITH u1, u2, COUNT(a) as comunes
                MERGE (u1)-[r:COMPARTEN_GUSTOS]->(u2)
                SET r.cantidad = comunes
            """)

        print("Carga 4.4 completada.")

    except (pymysql.MySQLError, Exception) as e:
        print("Error MySQL: ", e)
    finally:
        if conn:
            conn.close()
        if driver:
            driver.close()


def menu():

    """
    Esta función muestra el menú de opciones de Neo4J en bucle hasta que el usuario elija salir.
    """

    while True:

        print("\n", "-"*15, "MENÚ PROYECTO NEO4J", "-"*15, "\n")

        print("\t1. Apartado 4.1: Similitudes Pearson y Usuario con más vecinos" \
        "\n\t2. Apartado 4.2: Enlaces Aleatorios (Usuario -> Artículo)" \
        "\n\t3. Apartado 4.3: Usuarios por Categoría" \
        "\n\t4. Apartado 4.4: Artículos Populares" \
        "\n\t5. Salir")

        #seleccionar y validar opción
        op = None
        while True:
            op = input("\nSeleccione una opción (1, 2, 3, 4, 5): ")
            if op in ["1", "2", "3", "4", "5"]:
                break
            else:
                print("Opción no válida.")

        if op == "1":
            cargar_4_1_similitudes()
            consulta_4_1_vecinos()
        elif op == "2":
            cargar_4_2_aleatorios()
        elif op == "3":
            cargar_4_3_categoria()
        elif op == "4":
            cargar_4_4_populares()
        elif op == "5":
            break
        else:
            print("Opción no válida.")


if __name__ == "__main__":
    menu()