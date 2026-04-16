import pandas as pd
import geopandas as gpd
from pathlib import Path
from shapely.geometry import Point

# ── Configurações ─────────────────────────────────────────────────────────────

ARQUIVO_DADOS    = Path("dados.xlsx")
ARQUIVO_BAIRROS  = Path("BR_bairros_CD2022.shp")
ARQUIVO_SAIDA    = Path("resultados.geojson")

CODIGO_TERESINA  = "2211001"
CRS_PADRAO       = "EPSG:4326"

CANDIDATOS = [
    "DIEGO GOMES MELO",
    "GERALDO DO NASCIMENTO CARVALHO",
    "GESSY KARLA LIMA BORGES FONSECA",
    "GUSTAVO HENRIQUE LEITE FEIJÓ",
    "MARIA DE LOURDES SOARES MELO",
    "MARIA MADALENA NUNES",
    "RAFAEL TAJRA FONTELES",
    "RAVENNA DE CASTRO LIMA AZEVEDO",
    "SILVIO MENDES DE OLIVEIRA FILHO",
]


# ── Carregamento ──────────────────────────────────────────────────────────────

def carregar_dados() -> pd.DataFrame:
    dados = pd.read_excel(ARQUIVO_DADOS)
    dados["LONGITUDE"] = pd.to_numeric(dados["LONGITUDE"], errors="coerce")
    dados["LATITUDE"]  = pd.to_numeric(dados["LATITUDE"],  errors="coerce")
    return dados.dropna(subset=["LONGITUDE", "LATITUDE"])


def criar_geodataframe(dados: pd.DataFrame) -> gpd.GeoDataFrame:
    geometry = [Point(lon, lat) for lon, lat in zip(dados["LONGITUDE"], dados["LATITUDE"])]
    return gpd.GeoDataFrame(dados, geometry=geometry, crs=CRS_PADRAO)


def carregar_bairros_teresina() -> gpd.GeoDataFrame:
    bairros = gpd.read_file(ARQUIVO_BAIRROS)
    bairros["CD_MUN"] = bairros["CD_MUN"].astype(str)
    teresina = bairros[bairros["CD_MUN"] == CODIGO_TERESINA].copy()
    return teresina.to_crs(CRS_PADRAO)


# ── Transformações ────────────────────────────────────────────────────────────

def identificar_vencedor(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    gdf["vencedor"] = gdf[CANDIDATOS].idxmax(axis=1)
    return gdf


def associar_bairros(
    locais_gdf: gpd.GeoDataFrame,
    teresina: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    joined = gpd.sjoin(
        locais_gdf,
        teresina[["NM_BAIRRO", "geometry"]],
        how="left",
        predicate="within",
    )
    # Remove duplicatas geradas quando um ponto toca mais de um polígono
    joined = joined[~joined.index.duplicated(keep="first")]

    locais_gdf = locais_gdf.copy()
    locais_gdf["BAIRRO"] = joined["NM_BAIRRO"].reindex(locais_gdf.index).fillna("Zona Rural")
    return locais_gdf


# ── Exportação ────────────────────────────────────────────────────────────────

def exportar_resultado(locais_gdf: gpd.GeoDataFrame) -> None:
    pct_cols = [f"% {c}" for c in CANDIDATOS]
    colunas  = ["LOCAL DE VOTAÇÃO", "BAIRRO", "TOTAL", "vencedor", "geometry"]
    colunas += CANDIDATOS + pct_cols
    locais_gdf[colunas].to_file(ARQUIVO_SAIDA, driver="GeoJSON")


# ── Orquestração ──────────────────────────────────────────────────────────────

def main() -> None:
    dados      = carregar_dados()
    locais_gdf = criar_geodataframe(dados)
    teresina   = carregar_bairros_teresina()

    locais_gdf = identificar_vencedor(locais_gdf)
    locais_gdf = associar_bairros(locais_gdf, teresina)

    exportar_resultado(locais_gdf)
    print(f"Exportado: {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()