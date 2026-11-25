from datetime import datetime
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
BRONZE = ROOT / "dados" / "bronze" / "football"
PRATA = ROOT / "dados" / "prata"
PADRAO = "football_*.csv"
COLUNAS = [
    "Division",
    "MatchDate",
    "HomeTeam",
    "AwayTeam",
    "FTResult",
    "FTHome",
    "FTAway",
]
LIGAS = ["E0", "F1", "SP1", "I1", "D1", "BRA"]
LIGAS_EUROPA = ["E0", "F1", "SP1", "I1", "D1"]


def carregar():
    arquivos = sorted(BRONZE.glob(PADRAO))
    if not arquivos:
        raise FileNotFoundError(f"nenhum arquivo {PADRAO} encontrado em {BRONZE}")
    caminho = arquivos[-1]
    df = pd.read_csv(caminho, usecols=COLUNAS)
    print("lido:", caminho.name, df.shape)
    return df, caminho


def transformar(df):
    partidas = df.loc[df["Division"].isin(LIGAS), COLUNAS].copy()
    partidas["MatchDate"] = pd.to_datetime(partidas["MatchDate"], errors="coerce")
    return partidas


def temporadas_europa(df):
    for i in range(2010, 2019):
        europa1 = df[(df["MatchDate"] >= pd.Timestamp(f"{i}-07-25")) & (df["MatchDate"] <= pd.Timestamp(f"{i + 1}-06-15")) & (df["Division"].isin(LIGAS_EUROPA))]
        for divisao in LIGAS_EUROPA:
            temporada = europa1[europa1["Division"] == divisao]
            print(f"{i}-{i + 1} {divisao}: {len(temporada)} partidas")

    print()
    for i in range(2022, 2026):
            europa2 = df[(df["MatchDate"] >= pd.Timestamp(f"{i}-07-25")) & (df["MatchDate"] <= pd.Timestamp(f"{i + 1}-06-15")) & (df["Division"].isin(LIGAS_EUROPA))]
            for divisao in LIGAS_EUROPA:
                temporada = europa2[europa2["Division"] == divisao]
                print(f"{i}-{i + 1} {divisao}: {len(temporada)} partidas")
    print()
    blocos = []

    for ano in list(range(2010, 2019)) + list(range(2022, 2026)):
        filtro = (
            df["MatchDate"].between(
                pd.Timestamp(f"{ano}-07-25"),
                pd.Timestamp(f"{ano + 1}-06-15"),
            )
            & df["Division"].isin(LIGAS_EUROPA)
        )
        blocos.append(df.loc[filtro])

    europa = pd.concat(blocos, ignore_index=True)
    
    
    psg_monaco = pd.DataFrame([{
        "Division": "F1",
        "MatchDate": pd.Timestamp("2024-12-18"),  
        "HomeTeam": "Monaco",
        "AwayTeam": "Paris SG",
        "FTResult": "A",  
        "FTHome": 2,     
        "FTAway": 4,
    }], columns=COLUNAS)
        
    duplicada = (
        (europa["MatchDate"] == psg_monaco.loc[0, "MatchDate"])
        & (europa["HomeTeam"] == "Monaco")
        & (europa["AwayTeam"] == "Paris SG")
    ).any()
    
    if not duplicada:
        ligas_europa = pd.concat([europa, psg_monaco], ignore_index=True)
        ligas_europa = ligas_europa.sort_values("MatchDate").reset_index(drop=True)
        
    return ligas_europa
    
    

def temporada_2024_2025_franca(df):
    temporada = df[(df["MatchDate"] >= pd.Timestamp("2024-07-25")) & (df["MatchDate"] <= pd.Timestamp("2025-06-15")) & (df["Division"] == "F1")]
    print(f"Temporada 2024-2025 França: {len(temporada)} partidas")
    print()
    for time in temporada["HomeTeam"].unique():
        partidas_time = temporada[(temporada["HomeTeam"] == time) | (temporada["AwayTeam"] == time)]
        print(f"{time}: {len(partidas_time)} partidas")
    print()
    


def temporadas_brasil(df):
    for i in range(2012, 2020):
        brasil1 = df[(df["MatchDate"] >= pd.Timestamp(f"{i}-01-01")) & (df["MatchDate"] <= pd.Timestamp(f"{i}-12-31")) & (df["Division"] == "BRA")]
        temporada = brasil1[brasil1["Division"] == "BRA"]
        print(f"{i} {"BRA"}: {len(temporada)} partidas")
    
    print()
    for i in range(2022, 2024):
            brasil2 = df[(df["MatchDate"] >= pd.Timestamp(f"{i}-01-01")) & (df["MatchDate"] <= pd.Timestamp(f"{i}-12-31")) & (df["Division"] == "BRA")]
            temporada = brasil2[brasil2["Division"] == "BRA"]
            print(f"{i} {"BRA"}: {len(temporada)} partidas")
    print()
    liga_brasil = pd.concat([brasil1, brasil2], ignore_index=True)
    liga_brasil = liga_brasil.sort_values("MatchDate").reset_index(drop=True)

    blocos = []

    for ano in list(range(2012, 2020)) + list(range(2022, 2024)):
        filtro = (
            df["MatchDate"].between(
                pd.Timestamp(f"{ano}-01-01"),
                pd.Timestamp(f"{ano}-12-31"),
            )
            & df["Division"].eq("BRA")
        )
        blocos.append(df.loc[filtro])

    liga_brasil = pd.concat(blocos, ignore_index=True)

    return liga_brasil

def final(df1, df2):
    final = pd.concat([df1, df2], ignore_index=True)
    final = final.sort_values("MatchDate").reset_index(drop=True)
    return final





def salvar(df):
    destino = PRATA / "partidas.parquet"
    df.to_parquet(destino, index=False)
    print("salvo em:", destino, df.shape)
    #salvar em CSV para conferência
    destino_csv = PRATA / "partidas.csv"
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
    df, origem = carregar()
    inicial = len(df)
    partidas = transformar(df)
    temporada_2024_2025_franca(partidas)
    partidas_europa = temporadas_europa(partidas)
    liga_brasil = temporadas_brasil(partidas)
    partidas_final = final(partidas_europa, liga_brasil)
    print()
    salvar(partidas_final)
    print()
    print(f"partidas finais: {len(partidas_final)}")
    df = pd.read_parquet("dados/prata/partidas.parquet")

    print()
    print(df.columns.tolist())
    print()
    print(df.head())
    
    registrar(origem, PRATA / "partidas.parquet", inicial, len(partidas_final), ["Selecionadas as 5 principais ligas da Europa e o Brasileirão", "Selecionadas as temporadas de 2010-2019 e 2022-2026 para as ligas da Europa", "Selecionadas as temporadas de 2012-2019 e 2022-2023 para o Brasileirão", "Adicionada partida PSG x Monaco de 18/12/2024"])
if __name__ == "__main__":
    main()
