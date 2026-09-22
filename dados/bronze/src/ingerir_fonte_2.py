from pathlib import Path
import kagglehub
from datetime import date
import shutil
import json
from datetime import datetime

DATASET = "davidcariboo/player-scores"
BRONZE = Path("dados/bronze/football")
def baixar():
    pasta = kagglehub.dataset_download(DATASET)
    print("baixado em:", pasta)
    return Path(pasta)

def localizar(pasta, arquivo_nome):
    arquivo = pasta / arquivo_nome
    if not arquivo.is_file():
        encontrados = [a.name for a in pasta.glob("*.csv")]
        raise FileNotFoundError(
            f"Matches.csv não encontrado; CSVs disponíveis: {encontrados}"
        )
    return arquivo

def copiar(origem, destino_nome):
    BRONZE.mkdir(parents=True, exist_ok=True)
    hoje = date.today().strftime("%Y%m%d")
    destino = BRONZE / f"{destino_nome}_{hoje}.csv"
    shutil.copy(origem, destino)
    return destino

def registrar(origem, destino):
    info = {
    "fonte": DATASET,
    "arquivo_origem": origem.name,
    "arquivo_bronze": destino.name,
    "extraido_em": datetime.now().isoformat(),
    }
    (BRONZE / "proveniencia.json").write_text(json.dumps(info, indent=2))
    caminho = BRONZE / "proveniencia.jsonl"
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False)+ "\n")

def main():
    pasta = baixar()
    origem = localizar(pasta, "clubs.csv")
    destino = copiar(origem, "clubs")
    registrar(origem, destino)
    origem = localizar(pasta, "players.csv")
    destino = copiar(origem, "players")
    registrar(origem, destino)
    origem = localizar(pasta, "player_valuations.csv")
    destino = copiar(origem, "player_valuations")
    registrar(origem, destino)

if __name__ == "__main__":
    main()
