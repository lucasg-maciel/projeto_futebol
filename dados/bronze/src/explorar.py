from pathlib import Path
import pandas as pd
from data_profiling import ProfileReport

ROOT = Path(__file__).resolve().parents[3]
BRONZE = ROOT / "dados" / "bronze" / "football"
PADRAO = "*.csv"
def mais_recente():
    arquivos = sorted(BRONZE.glob(PADRAO))
    if not arquivos:
        raise FileNotFoundError("bronze vazia")
    return arquivos[-1]



RELATORIOS = ROOT / "relatorios"
def gerar(caminho):
    df = pd.read_csv(caminho)
    perfil = ProfileReport(df, title=caminho.name)
    RELATORIOS.mkdir(exist_ok=True)
    saida = RELATORIOS / f"{caminho.stem}.html"
    perfil.to_file(saida)
    return saida

def main():
    caminho = BRONZE / "player_valuations_20260924.csv"
    print("perfilando:", caminho.name)
    print(gerar(caminho))
    caminho = BRONZE / "players_20260924.csv"
    print("perfilando:", caminho.name)
    print(gerar(caminho))
    caminho = BRONZE / "football_20260924.csv"
    print("perfilando:", caminho.name)
    print(gerar(caminho))
    caminho = BRONZE / "clubs_20260924.csv"
    print("perfilando:", caminho.name)
    print(gerar(caminho))

if __name__ == "__main__":
    main()
