import pandas as pd
import geopandas as gpd
from pathlib import Path
from shapely.geometry import Point

# ── Configurações ─────────────────────────────────────────────────────────────

ARQUIVO_BAIRROS = Path("shapefile/BR_bairros_CD2022.shp")
CODIGO_TERESINA = "2211001"
CRS_PADRAO      = "EPSG:4326"

ELEICOES = {
    "municipais_2024_prefeito": {
        "arquivo": Path("data/municipais_2024/prefeito.xlsx"),
        "saida":   Path("data/municipais_2024/prefeito_2024.geojson"),
        "candidatos": [
            "FABIO NUNEZ NOVO (PT)",
            "FRANCINALDO SILVA LEÃO (PSOL)",
            "GERALDO DO NASCIMENTO CARVALHO (PSTU)",
            "JOSE SANTIAGO BELIZARIO (UP)",
            "JOSÉ PESSOA LEAL (PRD)",
            "MARIA DE LOURDES SOARES MELO (PCO)",
            "SILVIO MENDES DE OLIVEIRA FILHO (UNIAO)",
            "TELSÍRIO CARVALHO LIMA ALENCAR (MOBI)",
            "TONNY KERLEY DE ALENCAR RODRIGUES (NOVO)",
        ],
    },
    "gerais_2022_governador": {
        "arquivo": Path("data/gerais_2022/governador.xlsx"),   # ajuste o nome do arquivo
        "saida":   Path("data/gerais_2022/governador_2022.geojson"),
        "candidatos": [
            "DIEGO GOMES MELO",
            "GERALDO DO NASCIMENTO CARVALHO",
            "GESSY KARLA LIMA BORGES FONSECA",
            "GUSTAVO HENRIQUE LEITE FEIJÓ",
            "MARIA DE LOURDES SOARES MELO",
            "MARIA MADALENA NUNES",
            "RAFAEL TAJRA FONTELES",
            "RAVENNA DE CASTRO LIMA AZEVEDO",
            "SILVIO MENDES DE OLIVEIRA FILHO",
        ],
    },
}


# ── Carregamento ──────────────────────────────────────────────────────────────

def carregar_dados(arquivo: Path) -> pd.DataFrame:
    dados = pd.read_excel(arquivo)
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

def identificar_vencedor(gdf: gpd.GeoDataFrame, candidatos: list) -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    gdf["vencedor"] = gdf[candidatos].idxmax(axis=1)
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

def exportar_resultado(
    locais_gdf: gpd.GeoDataFrame,
    saida: Path,
    candidatos: list,
) -> None:
    pct_cols = [f"% {c}" for c in candidatos]
    colunas  = ["LOCAL DE VOTAÇÃO", "BAIRRO", "TOTAL", "vencedor", "geometry"]
    colunas += candidatos + pct_cols
    saida.parent.mkdir(parents=True, exist_ok=True)
    locais_gdf[colunas].to_file(saida, driver="GeoJSON")


# ── Orquestração ──────────────────────────────────────────────────────────────

def processar(chave: str) -> None:
    cfg = ELEICOES[chave]

    print(f"Processando: {chave}")
    dados      = carregar_dados(cfg["arquivo"])
    locais_gdf = criar_geodataframe(dados)
    teresina   = carregar_bairros_teresina()

    locais_gdf = identificar_vencedor(locais_gdf, cfg["candidatos"])
    locais_gdf = associar_bairros(locais_gdf, teresina)

    exportar_resultado(locais_gdf, cfg["saida"], cfg["candidatos"])
    print(f"Exportado: {cfg['saida']}")


def main() -> None:
    # Para processar todas as eleições configuradas:
    for chave in ELEICOES:
        processar(chave)

    # Ou para processar apenas uma eleição específica, comente o loop acima
    # e descomente a linha abaixo:
    # processar("municipais_2024_prefeito")


if __name__ == "__main__":
    main()