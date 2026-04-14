import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt

df = pd.read_excel("dados.xlsx")

# Cria geometria a partir das colunas de coordenadas
geometry = [Point(lon, lat) for lon, lat in zip(df["LONGITUDE"], df["LATITUDE"])]
gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

bairros = gpd.read_file("BR_bairros_CD2022.shp")

# Filtra só Teresina (código IBGE: 2211001)
teresina = bairros[bairros["CD_MUN"] == "2211001"]

# Garantir que os dois estão no mesmo CRS
teresina = teresina.to_crs(epsg=4326)

# Descobrir o candidato vencedor em cada local
candidatos = [
    "DIEGO GOMES MELO", "GERALDO DO NASCIMENTO CARVALHO",
    "GESSY KARLA LIMA BORGES FONSECA", "GUSTAVO HENRIQUE LEITE FEIJÓ",
    "MARIA DE LOURDES SOARES MELO", "MARIA MADALENA NUNES",
    "RAFAEL TAJRA FONTELES", "RAVENNA DE CASTRO LIMA AZEVEDO",
    "SILVIO MENDES DE OLIVEIRA FILHO"
]

gdf["vencedor"] = gdf[candidatos].idxmax(axis=1)

# ── NOVO: Associa cada local de votação ao respectivo bairro via spatial join ──
# Usa "within" para pontos dentro dos polígonos; pontos fora ficam com NaN
gdf_joined = gpd.sjoin(
    gdf,
    teresina[["NM_BAIRRO", "geometry"]],
    how="left",
    predicate="within"
)
gdf["BAIRRO"] = gdf_joined["NM_BAIRRO"].values

# Pontos que caíram fora de qualquer polígono (bordas, etc.) ficam como "Zona Rural"
gdf["BAIRRO"] = gdf["BAIRRO"].fillna("Zona Rural")

# Definir cores e plotar
cores = {
    "RAFAEL TAJRA FONTELES": "#e74c3c",
    "SILVIO MENDES DE OLIVEIRA FILHO": "#2980b9",
}

fig, ax = plt.subplots(figsize=(12, 12))

teresina.plot(ax=ax, color="lightgray", edgecolor="white", linewidth=0.5)

for candidato, grupo in gdf.groupby("vencedor"):
    cor = cores.get(candidato, "gray")
    grupo.plot(
        ax=ax,
        color=cor,
        markersize=grupo["TOTAL"] / grupo["TOTAL"].max() * 100,
        alpha=0.7,
        label=candidato
    )

ax.legend(loc="lower right", fontsize=7)
ax.set_title("Resultado por Local de Votação - Teresina")
ax.axis("off")
plt.tight_layout()

# Mantém só as colunas necessárias e exporta (agora inclui BAIRRO)
pct_cols = ["% " + c for c in candidatos]
gdf_export = gdf[
    ["LOCAL DE VOTAÇÃO", "BAIRRO", "TOTAL", "vencedor", "geometry"]
    + candidatos
    + pct_cols
].copy()
gdf_export.to_file("resultados.geojson", driver="GeoJSON")
