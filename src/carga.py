import json
import logging
import subprocess
from datetime import datetime

import duckdb

from config import OURO, PRATA, RAIZ

log = logging.getLogger(__name__)


BANCO = OURO / "projeto.duckdb"
PROVENIENCIA_OURO = OURO / "proveniencia.jsonl"
RESULTADOS_DBT = RAIZ / "ecox14" / "target" / "run_results.json"



ORIGENS_OURO = ["partidas.parquet", "partidas_enriquecidas.parquet"]



TABELAS_PRATA = {
    "player_valuations": "player_valuations.parquet",
    "partidas": "partidas.parquet",
    "partidas_enriquecidas": "partidas_enriquecidas.parquet",
}

def um_valor(con, sql):
    return con.execute(sql).fetchone()[0]

def carregar_prata(con):
    for tabela, arquivo in TABELAS_PRATA.items():
        caminho = PRATA / arquivo
        if not caminho.exists():
            log.warning("prata.%s: arquivo nao encontrado, pulando", tabela)
            continue
        con.execute(f"""
            CREATE OR REPLACE TABLE prata.{tabela} AS
            SELECT * FROM read_parquet('{caminho.as_posix()}')
        """)
        linhas = um_valor(con, f"SELECT COUNT(*) FROM prata.{tabela}")
        log.info("prata.%s: %s linhas", tabela, linhas)
        
def ultima_da_prata(arquivo_prata):
    caminho = PRATA / "proveniencia.jsonl"
    if not caminho.exists():
        return None
    ultimo = None
    with caminho.open(encoding="utf-8") as f:
        for linha in f:
            if not linha.strip():
                continue
            registro = json.loads(linha)
            if registro.get("arquivo_prata") == arquivo_prata:
                ultimo = registro
    if ultimo is None:
        return None
    origem = ultimo.get("origem") or [
        ultimo.get("origem_esquerda"), ultimo.get("origem_direita")
    ]
    return {
        "arquivo_prata": arquivo_prata,
        "origem": origem,
        "transformado_em": ultimo.get("transformado_em"),
    }


def execucao_dbt():
    if not RESULTADOS_DBT.exists():
        return None
    resultados = json.loads(RESULTADOS_DBT.read_text(encoding="utf-8"))
    comando = resultados.get("args", {}).get("which")
    if comando != "run":
        log.warning("run_results.json veio de 'dbt %s', nao de 'dbt run'",
                    comando)
        return None
    meta = resultados["metadata"]
    return {
        "versao": meta.get("dbt_version"),
        "invocation_id": meta.get("invocation_id"),
        "concluido_em": meta.get("generated_at"),
        "modelos": {
            r["unique_id"].split(".")[-1]: r["status"]
            for r in resultados.get("results", [])
        },
    }

def conferir(con):
    grao_repetido = um_valor(con, """
        SELECT COUNT(*) FROM (
            SELECT liga_id, temporada, clube_nome
            FROM ouro.fato_desempenho_temporadas
            GROUP BY liga_id, temporada, clube_nome
            HAVING COUNT(*) > 1
        )
    """)

    orfaos = um_valor(con, """
        SELECT COUNT(*)
        FROM ouro.fato_desempenho_temporadas f
        LEFT JOIN ouro.liga d USING (liga_id)
        WHERE d.liga_id IS NULL
    """)

    log.info("registros clube-liga-temporada repetidos: %s (esperado 0)", grao_repetido)
    log.info("fatos sem dimensao (liga)             : %s (esperado 0)", orfaos)

    if grao_repetido or orfaos:
        raise ValueError(
            f"modelo inconsistente: {grao_repetido} repetidos, "
            f"{orfaos} orfaos"
        )

    return {
        "registros_repetidos": grao_repetido,
        "fatos_sem_dimensao": orfaos,
    }
    
def conectar(somente_leitura=False):
    BANCO.parent.mkdir(parents=True, exist_ok=True)
    log.info("banco: %s", BANCO)
    return duckdb.connect(str(BANCO), read_only=somente_leitura)

def conferir_ouro():
    con = conectar(somente_leitura=True)
    try:
        conferencias = conferir(con)
    finally:
        con.close()
    return conferencias

def registrar_ouro(conferencias):
    info = {
        "camada": "ouro",
        "banco": BANCO.name,
        "origens_prata": [ultima_da_prata(a) for a in ORIGENS_OURO],
        "dbt": execucao_dbt(),
        "conferencias": conferencias,
        "construido_em": datetime.now().isoformat(timespec="seconds"),
    }
    OURO.mkdir(parents=True, exist_ok=True)
    with PROVENIENCIA_OURO.open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")
    log.info("proveniencia: %s", PROVENIENCIA_OURO)
    return info

def main():
    con = conectar()
    try:
        con.execute("CREATE SCHEMA IF NOT EXISTS prata")

        con.execute("CREATE SCHEMA IF NOT EXISTS ouro")
        carregar_prata(con)
    finally:
        con.close()
    log.info("carga concluida")
if __name__ == "__main__":
    import config

    config.configurar_log()
    main()