from pathlib import Path
import kagglehub
from datetime import date
import shutil
import json
from datetime import datetime

DATASET = "adamgbor/club-football-match-data-2000-2025"
BRONZE = Path("dados/bronze/football")
def baixar():
    pasta = kagglehub.dataset_download(DATASET)
    print("baixado em:", pasta)
    return Path(pasta)

def localizar(pasta):
    arquivo = pasta / "Matches.csv"
    if not arquivo.is_file():
        encontrados = [a.name for a in pasta.glob("*.csv")]
        raise FileNotFoundError(
            f"Matches.csv não encontrado; CSVs disponíveis: {encontrados}"
        )
    return arquivo

def copiar(origem):
    BRONZE.mkdir(parents=True, exist_ok=True)
    hoje = date.today().strftime("%Y%m%d")
    destino = BRONZE / f"football_{hoje}.csv"
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
    origem = localizar(pasta)
    destino = copiar(origem)
    registrar(origem, destino)

if __name__ == "__main__":
    main()
