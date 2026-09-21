"""
Actualiza Rating y Votes de IMDB-Movie-Data.csv con los datasets públicos de IMDb
(https://datasets.imdbws.com/, uso no comercial / educativo).

Uso:
    python actualizar_ratings.py
    python actualizar_ratings.py mi_archivo.csv salida.csv

Necesita: pandas y conexión a internet (descarga ~250 MB la primera vez).
NO actualiza Metascore ni Revenue: no están en los datasets de IMDb.
"""
import sys
import pandas as pd

ENTRADA = sys.argv[1] if len(sys.argv) > 1 else "IMDB-Movie-Data.csv"
SALIDA = sys.argv[2] if len(sys.argv) > 2 else "IMDB-Movie-Data-actualizado.csv"
BASICS = "https://datasets.imdbws.com/title.basics.tsv.gz"
RATINGS = "https://datasets.imdbws.com/title.ratings.tsv.gz"


def norm(s):
    return s.astype(str).str.lower().str.strip()


df = pd.read_csv(ENTRADA, encoding="utf-8")

print("Descargando datasets de IMDb...")
basics = pd.read_csv(
    BASICS, sep="\t", na_values="\\N", dtype=str,
    usecols=["tconst", "titleType", "primaryTitle", "originalTitle", "startYear"],
)
ratings = pd.read_csv(RATINGS, sep="\t", na_values="\\N")

basics = basics[basics["titleType"] == "movie"].copy()
basics["startYear"] = pd.to_numeric(basics["startYear"], errors="coerce")
basics = basics.merge(ratings, on="tconst", how="inner")

# Emparejamos por título (principal u original) + año exacto.
# Si hay varios candidatos, nos quedamos con el que tiene más votos.
df["_key"] = norm(df["Title"])
candidatos = []
for col in ("primaryTitle", "originalTitle"):
    tmp = basics.copy()
    tmp["_key"] = norm(tmp[col])
    candidatos.append(tmp)
cand = pd.concat(candidatos).drop_duplicates(["tconst", "_key"])

m = df.reset_index().merge(
    cand, left_on=["_key", "Year"], right_on=["_key", "startYear"], how="left"
)
m = m.sort_values("numVotes", ascending=False).drop_duplicates("index").sort_values("index")

out = df.copy()
out["Rating_original"] = df["Rating"]
out["Votes_original"] = df["Votes"]
out["imdb_id"] = m["tconst"].values
encontrado = m["averageRating"].notna().values
out.loc[encontrado, "Rating"] = m.loc[encontrado, "averageRating"].values
out.loc[encontrado, "Votes"] = m.loc[encontrado, "numVotes"].astype(int).values
out = out.drop(columns="_key")

out.to_csv(SALIDA, index=False, encoding="utf-8")

print(f"Actualizadas: {encontrado.sum()} de {len(df)}")
sin = out.loc[~encontrado, ["Rank", "Title", "Year"]]
if len(sin):
    print("\nNo encontradas (revísalas a mano):")
    print(sin.to_string(index=False))
print(f"\nGuardado en {SALIDA}")
