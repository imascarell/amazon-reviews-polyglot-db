#recomendacion.py

"""
Alumnos:
    Yago Vallarino Fernández-Cavada
    Ignacio Mascarell Agúndez
"""

#imports
import pymysql
import configuracion


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


def recomendar_articulos(id_usuario, categoria):

    """
    Esta función recibe un id de usuario y una categoría, y devuelve los 10 artículos
    más populares de esa categoría que el usuario no ha consumido.
    """

    conn = None

    try:

		#conexión sql
        conn = obtener_conexion_sql()
        cursor = conn.cursor()

        #comprobar que el usuario existe
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        existe = cursor.fetchone()[0]

        if existe == 0:
            print(f"El usuario '{id_usuario}' no existe en la base de datos.")
            return

        #obtener 10 artículos más populares de esa categoría que el usuario no ha consumido (no tiene review)
        query = """
            SELECT p.asin, COUNT(r.id_review) AS num_reviews
            FROM productos p
            JOIN reviews_meta r ON p.asin = r.asin
            WHERE p.categoria = %s
            AND p.asin NOT IN (
                SELECT asin FROM reviews_meta WHERE id_usuario = %s
            )
            GROUP BY p.asin
            ORDER BY num_reviews DESC
            LIMIT 10
        """

        cursor.execute(query, (categoria, id_usuario))
        resultados = cursor.fetchall()

        #mostrar resultados
        if resultados:
            print(f"\nTop 10 artículos recomendados de '{categoria}' para el usuario '{id_usuario}':\n")
            posicion = 1
            for fila in resultados:
                asin = fila[0]
                num_reviews = fila[1]
                print(f"  {posicion}. ASIN: {asin}  ({num_reviews} reviews)")
                posicion = posicion + 1
        else:
            print(f"No se encontraron artículos de '{categoria}' que el usuario no haya consumido.")

    except pymysql.MySQLError as e:
        print("Error al consultar MySQL: ", e)
    finally:
        if conn:
            conn.close()


def main():

    """
    Esta función pide al usuario los datos necesarios y ejecuta la recomendación.
    """

    print('\n', '-'*15, 'RECOMENDACIÓN DE ARTÍCULOS', '-'*15)

    #pedir id de usuario
    id_usuario = input("\nIntroduce el identificador del usuario: ").strip()

    #pedir categoría
    categoria = pedir_categoria(permitir_todo=False)

    #ejecutar recomendación
    recomendar_articulos(id_usuario, categoria)


if __name__ == "__main__":
    main()