import logging
from pathlib import Path

# config.py
RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados"
BRONZE = DADOS / "bronze"
PRATA = DADOS / "prata"
OURO = DADOS / "ouro"
DATASET_1 = "adamgbor/club-football-match-data-2000-2025"
DATASET_2 = "davidcariboo/player-scores"


def configurar_log():
    logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
    logging.FileHandler(RAIZ / "pipeline.log"),
    logging.StreamHandler(),
    ],
    )

