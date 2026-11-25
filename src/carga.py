import json
import logging
import subprocess
from datetime import datetime

import duckdb

from config import OURO, PRATA, RAIZ

log = logging.getLogger(__name__)


BANCO = OURO / "projeto.duckdb"

con = duckdb.connect(str(BANCO))

con.execute("CREATE SCHEMA IF NOT EXISTS prata")

con.execute("CREATE SCHEMA IF NOT EXISTS ouro")


TABELAS_PRATA = {
    "player_valuations": "player_valuations.parquet",
    "partidas": "partidas.parquet",
    "partidas_enriquecidas": "partidas_enriquecidas.parquet",
}


def carregar_prata():
    for tabela, arquivo in TABELAS_PRATA.items():
        caminho = PRATA / arquivo
        if not caminho.exists():
            log.warning("prata.%s: arquivo nao encontrado, pulando", tabela)
            continue
        con.execute(f"""
            CREATE OR REPLACE TABLE prata.{tabela} AS
            SELECT * FROM read_parquet('{caminho.as_posix()}')
        """)
        linhas = (con, f"SELECT COUNT(*) FROM prata.{tabela}")
        log.info("prata.%s: %s linhas", tabela, linhas)


    
