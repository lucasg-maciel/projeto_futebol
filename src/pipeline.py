import logging
import sys
import time
import config



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