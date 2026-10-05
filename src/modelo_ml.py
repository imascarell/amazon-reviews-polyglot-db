#modelo_ml.py

"""
Alumnos:
    Yago Vallarino Fernández-Cavada
    Ignacio Mascarell Agúndez
"""

#imports
import pymysql
import math
import random
import configuracion


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


def calcular_correl_pearson(u1_ratings, u2_ratings):

    """
    Esta funcion calcula la correlacion de Pearson entre dos usuarios, devuelve el valor de la correlacion y el numero de articulos en comun.
    """

    #calcular comunes
    comunes = []
    for articulo in u1_ratings:
        if articulo in u2_ratings:
            comunes.append(articulo)

    if len(comunes) == 0:
        return 0, 0

    n_comunes = len(comunes)

    #medias
    suma_u1 = 0
    suma_u2 = 0
    for a in comunes:
        suma_u1 = suma_u1 + u1_ratings[a]
        suma_u2 = suma_u2 + u2_ratings[a]
    media1 = suma_u1 / n_comunes
    media2 = suma_u2 / n_comunes

    #numerador y denominadores
    num = 0
    denom_1_sucio = 0
    denom_2_sucio = 0
    for a in comunes:
        dif_1 = u1_ratings[a] - media1
        dif_2 = u2_ratings[a] - media2
        num = num + (dif_1 * dif_2)
        denom_1_sucio = denom_1_sucio + (dif_1 ** 2)
        denom_2_sucio = denom_2_sucio + (dif_2 ** 2)

    denom_1 = math.sqrt(denom_1_sucio)
    denom_2 = math.sqrt(denom_2_sucio)

    if denom_1 == 0 or denom_2 == 0:
        return 0, n_comunes

    resultado = num / (denom_1 * denom_2)
    return resultado, n_comunes


def obtener_datos():

    """
    Esta funcion obtiene los ratings de los usuarios más activos desde sql. Resultado limitado a 200.
    """

    conn = None

    #valor inicial
    data_ratings = {}

    try:

        #coenxión sql
        conn = obtener_conexion_sql()
        cursor = conn.cursor()

        #obtener los 200 usuarios con mas reviews
        cursor.execute(
            "SELECT id_usuario FROM reviews_meta "
            "GROUP BY id_usuario ORDER BY COUNT(*) DESC LIMIT 200"
        )
        usuarios = []
        for fila in cursor.fetchall():
            usuarios.append(fila[0])

        #obtener ratings de cada usuario
        for user_id in usuarios:
            cursor.execute(
                "SELECT asin, rating FROM reviews_meta WHERE id_usuario = %s",
                (user_id,)
            )
            ratings_usuario = {}
            for fila in cursor.fetchall():
                ratings_usuario[fila[0]] = fila[1]
            data_ratings[user_id] = ratings_usuario

    except pymysql.MySQLError as e:
        print("Error al obtener datos de MySQL: ", e)
    finally:
        if conn:
            conn.close()

    return data_ratings


def dividir_train_test(data_ratings, porcentaje_test=0.2):

    """
    Esta funcion divide los datos de cada usuario y sus ratings en train y test.
    Devuelve train_ratings, test_ratings (ambos dicts con la misma estructura).
    """

    #valores iniciales
    train = {}
    test = []

    for user_id in data_ratings:

        ratings = data_ratings[user_id]
        articulos = []
        for asin in ratings:
            articulos.append(asin)

        #mezclar para que sea aleatorio
        random.shuffle(articulos)

        #calcular cuantos van a test
        n_test = int(len(articulos) * porcentaje_test)
        if n_test == 0:
            n_test = 1

        #separar
        articulos_test = articulos[:n_test]
        articulos_train = articulos[n_test:]

        #guardar train
        train_usuario = {}
        for asin in articulos_train:
            train_usuario[asin] = ratings[asin]
        train[user_id] = train_usuario

        #guardar test
        for asin in articulos_test:
            test.append({
                "user_id": user_id,
                "asin": asin,
                "rating_real": ratings[asin]
            })

    return train, test


def predecir_rating(uid_objetivo, asin_objetivo, train_ratings, k_vecinos=10):

    """
    Esta funcion predice el rating que un usuario daria a un articulo usando los K vecinos mas similares que hayan puntuado ese articulo.
    Devuelve la prediccion o None si no se puede predecir.
    """

    #buscar usuarios que hayan puntuado ese articulo en train
    vecinos = []

    for otro_uid in train_ratings:
        if otro_uid == uid_objetivo:
            continue
        if asin_objetivo not in train_ratings[otro_uid]:
            continue

        #calcular similitud
        correl, n_comunes = calcular_correl_pearson(
            train_ratings[uid_objetivo],
            train_ratings[otro_uid]
        )

        if n_comunes > 0 and correl != 0:
            vecinos.append({
                "user_id": otro_uid,
                "sim": correl,
                "rating": train_ratings[otro_uid][asin_objetivo]
            })

    if len(vecinos) == 0:
        return None

    #ordenar por similitud absoluta (de mayor a menor)
    for i in range(len(vecinos)):
        for j in range(i + 1, len(vecinos)):
            if abs(vecinos[j]["sim"]) > abs(vecinos[i]["sim"]):

                #actualizar
                temp = vecinos[i]
                vecinos[i] = vecinos[j]
                vecinos[j] = temp

    #tomar los K mejores
    if len(vecinos) > k_vecinos:
        vecinos = vecinos[:k_vecinos]

    #media ponderada
    suma_ponderada = 0
    suma_pesos = 0
    for v in vecinos:
        peso = abs(v["sim"])
        suma_ponderada = suma_ponderada + (v["sim"] * v["rating"])
        suma_pesos = suma_pesos + peso

    if suma_pesos == 0:
        return None

    #calcular predicción
    pred_ini = suma_ponderada / suma_pesos
    pred_final = pred_ini

    #limitar entre 1 y 5
    if pred_ini < 1:
        pred_final = 1
    if pred_ini > 5:
        pred_final = 5

    return pred_final


def evaluar_modelo(train_ratings, test_ratings):

    """
    Esta funcion evalua el modelo calculando el RMSE sobre el conjunto de test.
    """

    #valores iniciales
    errores = []
    predicciones_ok = 0
    predicciones_fallo = 0

    print(f"\nEvaluando modelo con {len(test_ratings)} reviews de test.")

    for i in range(len(test_ratings)):

        #obtenre valores
        item = test_ratings[i]
        user_id = item["user_id"]
        asin = item["asin"]
        rating_real = item["rating_real"]

        #obtener predición
        prediccion = predecir_rating(user_id, asin, train_ratings)

        #actualizar errores/aciertos
        if prediccion is not None:
            error = (prediccion - rating_real) ** 2
            errores.append(error)
            predicciones_ok = predicciones_ok + 1
        else:
            predicciones_fallo = predicciones_fallo + 1

        #progreso
        if (i + 1) % 50 == 0:
            print(f"Procesadas {i + 1} / {len(test_ratings)} reviews.")

    #calcular RMSE
    if len(errores) > 0:
        suma_errores = 0
        for e in errores:
            suma_errores = suma_errores + e
        rmse = math.sqrt(suma_errores / len(errores))
    else:
        rmse = None

    return rmse, predicciones_ok, predicciones_fallo


def mostrar_ejemplo_recomendacion(train_ratings):

    """
    Esta funcion muestra un ejemplo de recomendacion para el primer usuario del train.
    """

    #seleccionar el primer usuario
    primer_user_id = list(train_ratings.keys())[0]

    if primer_user_id is None:
        print("No hay usuarios para recomendar.")
        return
    
    print(f"\nEjemplo de recomendacion para usuario: {primer_user_id}"
          f"\nArticulos ya puntuados: {len(train_ratings[primer_user_id])}")

    #coger todos los artículos
    todos_articulos = {}
    for user_id in train_ratings:
        for asin in train_ratings[user_id]:

            #evitar duplicados
            if asin not in todos_articulos:
                todos_articulos[asin] = True

    #coger los no puntuados
    no_puntuados = []
    for asin in todos_articulos:

        #si no está entre los raitings -> no se ha puntuado
        if asin not in train_ratings[primer_user_id]:
            no_puntuados.append(asin)

    print(f"Articulos candidatos (no puntuados): {len(no_puntuados)}")

    #predecir rating para algunos (limitado a 50)
    if len(no_puntuados) > 50:
        random.shuffle(no_puntuados)
        no_puntuados = no_puntuados[:50]

    #construir recomendaciones con predicciones
    recomendaciones = []
    for asin in no_puntuados:
        pred = predecir_rating(primer_user_id, asin, train_ratings)
        if pred is not None:
            recomendaciones.append({"asin": asin, "pred": pred})

    #ordenar de mayor a menor prediccion
    for i in range(len(recomendaciones)):
        for j in range(i + 1, len(recomendaciones)):
            if recomendaciones[j]["pred"] > recomendaciones[i]["pred"]:
                temp = recomendaciones[i]
                recomendaciones[i] = recomendaciones[j]
                recomendaciones[j] = temp

    #mostrar top 5
    print("\nTop 5 articulos recomendados:")
    limite = 5
    if len(recomendaciones) < limite:
        limite = len(recomendaciones)

    for i in range(limite):
        r = recomendaciones[i]
        print(f"  {i+1}. ASIN: {r['asin']}  (prediccion: {r['pred']:.2f})")

    if len(recomendaciones) == 0:
        print("  No se pudieron generar recomendaciones.")


def main():

    """
    Esta funcion ejecuta el modelo completo: obtener datos, dividir, evaluar y recomendar.
    """

    print("\n", "-"*15, "MODELO DE RECOMENDACIÓN (ML - KNN)", "-"*15)

    #p1 -> obtener datos
    print("\nObtener datos de MySQL.")
    data_ratings = obtener_datos()
    print(f"Usuarios obtenidos: {len(data_ratings)}")

    if len(data_ratings) == 0:
        print("No se encontraron datos. Abortando.")
        return

    #p2 -> dividir train/test
    print("\nDividir dataset en 80% train / 20% test.")
    train, test = dividir_train_test(data_ratings, 0.2)
    print(f"Reviews en test: {len(test)}")

    #p3 -> evaluar modelo
    rmse, ok, fallo = evaluar_modelo(train, test)

    print("\n", "-"*15, "RESULTADOS", "-"*15, "\n")
    if rmse is not None:
        print(f"\t1. RMSE: {rmse:.4f}")
    print(f"\n\t2. Predicciones realizadas: {ok}"
          f"\n\t3. Predicciones imposibles (sin vecinos): {fallo}")

    #p4 -> ejemplo de recomendacion
    mostrar_ejemplo_recomendacion(train)


if __name__ == "__main__":
    main()
