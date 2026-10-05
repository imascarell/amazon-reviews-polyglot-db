"""
Alumnos:
    Yago Vallarino Fernández-Cavada
    Ignacio Mascarell Agúndez
"""

import os

DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))

#rutas de los 4 ficheros json (descargar en data/, ver README)
RUTAS_JSON = {
    "toys_and_games": os.path.join(DATA_DIR, "Toys_and_Games_5.json"),
    "video_games": os.path.join(DATA_DIR, "Video_Games_5.json"),
    "digital_music": os.path.join(DATA_DIR, "Digital_Music_5.json"),
    "musical_instruments": os.path.join(DATA_DIR, "Musical_Instruments_5.json")
}

#ruta del quinto dataset
RUTA_QUINTO_JSON = os.path.join(DATA_DIR, "Sports_and_Outdoors_5.json")
CATEGORIA_QUINTO = "sports_and_outdoors"

#datos mysql
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASS = os.getenv("MYSQL_PASS", "")
MYSQL_DB = "Amazon_Reviews_DB"

#datos mongodb
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = "Amazon_Reviews_Mongo"
MONGO_COLL = "review_details"

#datos neo4j
NEO4J_HOST = os.getenv("NEO4J_HOST", "localhost")
NEO4J_PORT = os.getenv("NEO4J_PORT", "7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "")

#param carga
BATCH_SIZE = 1000

#param neo4j
TOP_N_USUARIOS = 30