import logging
import sys
import time
import config
import carga

def etapa_ingestao():
    import ingerir
    import ingerir_fonte_2

    ingerir.main()
    ingerir_fonte_2.main()

def etapa_transformacao():
    import transformar_jogadores
    import transformar_partidas
    
    transformar_jogadores.main()
    transformar_partidas.main()
    
def etapa_enriquecimento():
    import enriquecer
    enriquecer.main()
    

def etapa_carga():
    import carga
    carga.main()

import subprocess


def etapa_modelagem():
    subprocess.run(
    ["dbt", "run"],
    cwd=config.RAIZ / "ecox14",
    check=True,
    )
    ("modelagem", etapa_modelagem), # era None
    conferencias = carga.conferir_ouro()

    carga.registrar_ouro(conferencias)


log = logging.getLogger(__name__)

ETAPAS = [
    ("ingestao", etapa_ingestao),
    ("transformacao", etapa_transformacao),
    ("enriquecimento", etapa_enriquecimento),
    ("carga", etapa_carga),     
    ("modelagem", etapa_modelagem),
]


def executar(nome, funcao):

    log.info("etapa %s: inicio", nome)
    comeco = time.perf_counter()
    try:
        funcao()
    except Exception:
        log.exception("etapa %s falhou", nome)
        raise
    duracao = time.perf_counter() - comeco
    log.info("etapa %s: fim em %.0fs", nome, duracao)
    
def main(a_partir_de=None):
    config.configurar_log()
    config.criar_pastas()

    nomes = [nome for nome, _ in ETAPAS]
    if a_partir_de and a_partir_de not in nomes:
        log.error("etapa desconhecida: %s", a_partir_de)
        log.error("etapas validas: %s", ", ".join(nomes))
        return 1

    comecou = a_partir_de is None
    for nome, funcao in ETAPAS:
        if nome == a_partir_de:
            comecou = True
        if not comecou:
            log.info("etapa %s: pulada", nome)
            continue
        if funcao is None:
            log.warning("etapa %s: ainda nao implementada", nome)
            continue
        executar(nome, funcao)

    log.info("pipeline concluido")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))