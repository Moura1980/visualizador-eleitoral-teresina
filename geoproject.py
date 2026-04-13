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
teresina = teresina.to_crs(epsg=4326)  # mesmo CRS do gdf

# Descobrir o candidato vencedor em cada local
candidatos = [
    "DIEGO GOMES MELO", "GERALDO DO NASCIMENTO CARVALHO",
    "GESSY KARLA LIMA BORGES FONSECA", "GUSTAVO HENRIQUE LEITE FEIJÓ",
    "MARIA DE LOURDES SOARES MELO", "MARIA MADALENA NUNES",
    "RAFAEL TAJRA FONTELES", "RAVENNA DE CASTRO LIMA AZEVEDO",
    "SILVIO MENDES DE OLIVEIRA FILHO"
]

gdf["vencedor"] = gdf[candidatos].idxmax(axis=1)

# Definir cores e plotar
cores = {
    "RAFAEL TAJRA FONTELES": "#e74c3c",       # vermelho
    "SILVIO MENDES DE OLIVEIRA FILHO": "#2980b9",  # azul
    # adicione os outros se quiser
}

fig, ax = plt.subplots(figsize=(12, 12))

# 1. Mapa base
teresina.plot(ax=ax, color="lightgray", edgecolor="white", linewidth=0.5)

# 2. Pontos eleitorais
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
# plt.show()

# Mantém só as colunas necessárias e exporta
gdf_export = gdf[["LOCAL DE VOTAÇÃO", "TOTAL", "vencedor", "geometry"] + candidatos].copy()
gdf_export.to_file("resultados.geojson", driver="GeoJSON")