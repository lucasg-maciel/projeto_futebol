from datetime import datetime
import json
from pathlib import Path
import re
import unicodedata

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BRONZE = ROOT / "dados" / "bronze" / "football"
PRATA = ROOT / "dados" / "prata"
PADRAO = "football_*.csv"

# 1. No topo do arquivo, importe os dicionários do enriquecer_2:
from enriquecer import DE_PARA_TRANSFERMARKT, TODOS_CLUBES_TRANSFERMARKT

# 2. Atualize TIMES_BRASIL adicionando as grafias alternativas do Transfermarkt:
TIMES_BRASIL = {
    "América Futebol Clube (MG)",
    "Club Athletico Paranaense",
    "Atlético Paranaense",
    "Atlético Clube Goianiense",
    "Clube Atlético Mineiro",
    "Avaí FC",
    "Avaí Futebol Clube",
    "Esporte Clube Bahia",
    "Botafogo de Futebol e Regatas",
    "Red Bull Bragantino",
    "Clube Atlético Bragantino (SP)",
    "Centro Sportivo Alagoano (AL)",
    "Ceará Sporting Club",
    "Associação Chapecoense de Futebol",
    "Sport Club Corinthians Paulista",
    "Coritiba Foot Ball Club",
    "Criciúma Esporte Clube",
    "Cruzeiro Esporte Clube",
    "Cuiabá Esporte Clube (MT)",
    "Figueirense Futebol Clube",
    "CR Flamengo",
    "Clube de Regatas do Flamengo",
    "Fluminense Football Club",
    "Joinville Esporte Clube (SC)",
    "Fortaleza Esporte Clube",
    "Goiás EC",
    "Goiás Esporte Clube",
    "Grêmio Foot-Ball Porto Alegrense",
    "Sport Club Internacional",
    "Esporte Clube Juventude",
    "Clube Náutico Capibaribe",
    "Sociedade Esportiva Palmeiras",
    "Paraná Clube",
    "Associação Atlética Ponte Preta",
    "Portuguesa",
    "Santa Cruz FC (PE)",
    "Santa Cruz Futebol Clube (PE)",
    "Santos FC",
    "São Paulo Futebol Clube",
    "Clube de Regatas Vasco da Gama",
    "Esporte Clube Vitória",
}



def carregar():
    arquivos = sorted(BRONZE.glob(PADRAO))
    if not arquivos:
        raise FileNotFoundError(f"nenhum arquivo {PADRAO} encontrado em {BRONZE}")
    caminho = arquivos[-1]
    df = pd.read_csv(caminho, usecols=["Division", "MatchDate", "HomeTeam", "AwayTeam"])
    df2 = pd.read_csv(BRONZE / "player_valuations_20260924.csv" )
    print("lido:", caminho.name, df.shape)
    return df, df2, caminho

def times_temporada_inglaterra(df, ano):
    df["MatchDate"] = pd.to_datetime(df["MatchDate"], errors="coerce")
    europa = df[(df["MatchDate"] >= pd.Timestamp(f"{ano}-07-25")) & (df["MatchDate"] <= pd.Timestamp(f"{ano + 1}-06-15")) & (df["Division"].isin(["E0"]))]
    times = europa["HomeTeam"].unique()
    return times

def times_temporada_italia(df, ano):
    df["MatchDate"] = pd.to_datetime(df["MatchDate"], errors="coerce")
    europa = df[(df["MatchDate"] >= pd.Timestamp(f"{ano}-07-25")) & (df["MatchDate"] <= pd.Timestamp(f"{ano + 1}-06-15")) & (df["Division"].isin(["I1"]))]
    times = europa["HomeTeam"].unique()
    return times

def times_temporada_espanha(df, ano):
    df["MatchDate"] = pd.to_datetime(df["MatchDate"], errors="coerce")
    europa = df[(df["MatchDate"] >= pd.Timestamp(f"{ano}-07-25")) & (df["MatchDate"] <= pd.Timestamp(f"{ano + 1}-06-15")) & (df["Division"].isin(["SP1"]))]
    times = europa["HomeTeam"].unique()
    return times

def times_temporada_franca(df, ano):
    df["MatchDate"] = pd.to_datetime(df["MatchDate"], errors="coerce")
    europa = df[(df["MatchDate"] >= pd.Timestamp(f"{ano}-07-25")) & (df["MatchDate"] <= pd.Timestamp(f"{ano + 1}-06-15")) & (df["Division"].isin(["F1"]))]
    times = europa["HomeTeam"].unique()
    return times

def times_temporada_alemanha(df, ano):
    df["MatchDate"] = pd.to_datetime(df["MatchDate"], errors="coerce")
    europa = df[(df["MatchDate"] >= pd.Timestamp(f"{ano}-07-25")) & (df["MatchDate"] <= pd.Timestamp(f"{ano + 1}-06-15")) & (df["Division"].isin(["D1"]))]
    times = europa["HomeTeam"].unique()
    return times

def times_temporada_brasil(df, ano):
    df["MatchDate"] = pd.to_datetime(df["MatchDate"], errors="coerce")
    brasil = df[(df["MatchDate"] >= pd.Timestamp(f"{ano}-01-01")) & (df["MatchDate"] <= pd.Timestamp(f"{ano}-12-31")) & (df["Division"].isin(["BRA"]))]
    times = brasil["HomeTeam"].unique()
    return times

def filtrar_jogadores(df2):
    df_filtrado = df2.copy()
    df_filtrado["date"] = pd.to_datetime(df_filtrado["date"], errors="coerce")
    periodo = (
        df_filtrado["date"].between("2010-07-01", "2020-06-15")
        | df_filtrado["date"].between("2022-01-01", "2026-06-15")
    )
    df_filtrado = df_filtrado.loc[
        df_filtrado["current_club_name"].isin(TODOS_CLUBES_TRANSFERMARKT) & periodo
    ].copy()

    e_brasil = (
        df_filtrado["current_club_name"].isin(TIMES_BRASIL)
    )
    
    ano = df_filtrado["date"].dt.year
    
    inicio_temporada_europeia = ano.where(
        df_filtrado["date"].dt.month >= 7,
        ano - 1,
    )
    df_filtrado["temporada"] = inicio_temporada_europeia.astype("Int64").astype(str)
    df_filtrado.loc[e_brasil, "temporada"] = ano.loc[e_brasil].astype("Int64").astype(str)

    chaves = ["player_id", "current_club_name", "temporada"]
    df_filtrado = (
        df_filtrado.sort_values(chaves + ["date"], kind="stable")
        .drop_duplicates(subset=chaves, keep="last")
        .sort_index()
    )
    return df_filtrado

def estatisticas_jogadores_por_clube_temporada(df_filtrado):
    colunas_obrigatorias = {
        "player_id",
        "current_club_name",
        "temporada",
    }
    colunas_faltantes = colunas_obrigatorias.difference(df_filtrado.columns)
    if colunas_faltantes:
        raise ValueError(
            "df_filtrado não possui as colunas obrigatórias: "
            + ", ".join(sorted(colunas_faltantes))
        )

    contagens = (
        df_filtrado.groupby(
            ["temporada", "current_club_name"],
            as_index=False,
        )["player_id"]
        .nunique()
        .rename(columns={"player_id": "quantidade_jogadores"})
        .sort_values(
            ["temporada", "current_club_name"],
            kind="stable",
        )
        .reset_index(drop=True)
    )

    quantidade_grupos = len(contagens)
    quantidade_primeiro_quartil = max(1, int(np.ceil(quantidade_grupos * 0.25)))
    menores_grupos = contagens.nsmallest(
        quantidade_primeiro_quartil,
        columns="quantidade_jogadores",
    )

    return {
        "media_jogadores_por_clube_temporada": contagens[
            "quantidade_jogadores"
        ].mean(),
        "media_primeiro_quartil_clubes": menores_grupos[
            "quantidade_jogadores"
        ].mean(),
        "quantidade_grupos": quantidade_grupos,
        "quantidade_grupos_primeiro_quartil": quantidade_primeiro_quartil,
        "contagens": contagens,
        "menores_grupos": menores_grupos,
    }

def salvar_times(df):

    #salvar em CSV para conferência
    destino_csv = PRATA / "times.csv"
    df.to_csv(destino_csv, index=False)
    print("salvo em:", destino_csv, df.shape)
    return destino_csv

def salvar_jogadores(df):
    destino = PRATA / "player_valuations.parquet"
    df.to_parquet(destino, index=False)
    print("salvo em:", destino, df.shape)
    #salvar em CSV para conferência
    destino_csv = PRATA / "player_valuations.csv"
    df.to_csv(destino_csv, index=False)
    print("salvo em:", destino_csv, df.shape)
    return destino

def registrar(origem, destino, antes, depois, decisoes):
    info = {
    "origem": origem.name,
    "arquivo_prata": destino.name,
    "linhas_antes": antes,
    "linhas_depois": depois,
    "decisoes": decisoes,
    }
    caminho = PRATA / "proveniencia.jsonl"
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")


def main():
    df, df2, caminho = carregar()
    
    
    times_brasil = np.concatenate([times_temporada_brasil(df, ano) for ano in range(2022, 2024)])
    times_brasil2 = np.concatenate([times_temporada_brasil(df, ano) for ano in range(2012, 2020)])
    times_brasil = np.concatenate((times_brasil, times_brasil2))
    times_brasil = np.unique(times_brasil)
    
    
    times_inglaterra = np.concatenate([times_temporada_inglaterra(df, ano) for ano in range(2010, 2019)])
    times_inglaterra2 = np.concatenate([times_temporada_inglaterra(df, ano) for ano in range(2022, 2026)])
    times_inglaterra = np.concatenate((times_inglaterra, times_inglaterra2))
    times_inglaterra = np.unique(times_inglaterra)
    
    times_italia = np.concatenate([times_temporada_italia(df, ano) for ano in range(2010, 2019)])
    times_italia2 = np.concatenate([times_temporada_italia(df, ano) for ano in range(2022, 2026)])
    times_italia = np.concatenate((times_italia, times_italia2))
    times_italia = np.unique(times_italia)
    
    times_espanha = np.concatenate([times_temporada_espanha(df, ano) for ano in range(2010, 2019)])
    times_espanha2 = np.concatenate([times_temporada_espanha(df, ano) for ano in range(2022, 2026)])
    times_espanha = np.concatenate((times_espanha, times_espanha2))
    times_espanha = np.unique(times_espanha)
    
    times_franca = np.concatenate([times_temporada_franca(df, ano) for ano in range(2010, 2019)])
    times_franca2 = np.concatenate([times_temporada_franca(df, ano) for ano in range(2022, 2026)])
    times_franca = np.concatenate((times_franca, times_franca2))
    times_franca = np.unique(times_franca)
    
    times_alemanha = np.concatenate([times_temporada_alemanha(df, ano) for ano in range(2010, 2019)])
    times_alemanha2 = np.concatenate([times_temporada_alemanha(df, ano) for ano in range(2022, 2026)])
    times_alemanha = np.concatenate((times_alemanha, times_alemanha2))
    times_alemanha = np.unique(times_alemanha)
    
    df_times = pd.DataFrame({
        "Times_Brasil": pd.Series(times_brasil),
        "Times_Inglaterra": pd.Series(times_inglaterra),
        "Times_Italia": pd.Series(times_italia),
        "Times_Espanha": pd.Series(times_espanha),
        "Times_Franca": pd.Series(times_franca),
        "Times_Alemanha": pd.Series(times_alemanha)
    })
    
    salvar_times(df_times)
    
    
    df3 = pd.read_csv(PRATA / "competicoes_e_temporadas_times.csv")
    
    df2_filtrado = filtrar_jogadores(df2)
    salvar_jogadores(df2_filtrado)
    estatisticas = estatisticas_jogadores_por_clube_temporada(df2_filtrado)
    print(
        "média de jogadores por clube/temporada:",
        estatisticas["media_jogadores_por_clube_temporada"],
    )
    print(
        "média do primeiro quartil de clubes:",
        estatisticas["media_primeiro_quartil_clubes"],
    )
    print("jogadores filtrados:", df2_filtrado.shape)
    
    registrar(
        origem=caminho,
        destino=PRATA / "player_valuations.parquet",
        antes=df2.shape[0],
        depois=df2_filtrado.shape[0],
        decisoes= {"filtrado por clubes e datas": df2_filtrado.shape[0]},
    )


if __name__ == "__main__":
    main()
    
