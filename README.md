# Amazon Reviews — Polyglot Persistence (MySQL · MongoDB · Neo4j)

Final project for **Databases** (iMAT, ICAI, Universidad Pontificia Comillas, 2025/26).
Authors: **Yago Vallarino Fernández-Cavada** and **Ignacio Mascarell Agúndez**.

A hybrid data system to analyse Amazon review data across several product categories, splitting each review between the store that suits it best and using Python as the ETL bridge.

## Architecture

| Store | What it holds | Why |
|-------|---------------|-----|
| **MySQL** | `usuarios`, `productos`, `reviews_meta` (rating, date, FKs) | Structured fields, referential integrity, efficient JOINs/aggregations |
| **MongoDB** | review text, summary, helpfulness, parsed date | Semi-structured / free text |
| **Neo4j** | user–user similarity graph, user–product relations | Graph queries (Pearson similarity, popular items, neighbourhoods) |

## Features

- `load_data.py` — batch ETL of the JSON files into MySQL + MongoDB with duplicate checks.
- `inserta_dataset.py` — adds a new category dataset incrementally.
- `menu_visualizacion.py` — terminal menu with analytics charts (reviews per year, product popularity, rating histograms, reviews per user, word clouds…).
- `menu_interactivo.py` — interactive **Streamlit** dashboard.
- `neo4JProyecto.py` — loads graph data; Pearson similarity between the most active users, random-item and popular-item queries.
- `modelo_ml.py` — user-based **collaborative filtering** recommender on the 200 most active users, evaluated with RMSE on an 80/20 split.
- `recomendacion.py` — top-10 popular items per category for a given user.

Report: [`report/memoria.pdf`](report/memoria.pdf) · Poster: [`report/poster.pdf`](report/poster.pdf) (Spanish).

## Setup

1. Run MySQL, MongoDB and Neo4j locally.
2. Download the data (see [`data/README.md`](data/README.md)) — not included in the repo.
3. Set credentials as environment variables (see `.env.example`); nothing is hard-coded.
4. Run:

```bash
pip install -r src/requirements.txt
cd src
python load_data.py              # ETL into MySQL + MongoDB
python neo4JProyecto.py          # graph
python menu_visualizacion.py     # terminal analytics
streamlit run menu_interactivo.py
python modelo_ml.py              # recommender + RMSE
```
