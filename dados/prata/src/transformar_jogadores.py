
from __future__ import annotations

from collections import defaultdict
from difflib import SequenceMatcher
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

try:  # funciona ao importar como pacote ou executar este arquivo diretamente
    from .club_aliases import ALIASES_TIME_PARTIDAS
except ImportError:
    from club_aliases import ALIASES_TIME_PARTIDAS


ROOT = Path(__file__).resolve().parents[3]
BRONZE = ROOT / "dados" / "bronze" / "football"
PRATA = ROOT / "dados" / "prata"

COMPETICAO_POR_DIVISAO = {
    "E0": "GB1",
    "F1": "FR1",
    "SP1": "ES1",
    "I1": "IT1",
    "D1": "L1",
    "BRA": "BRA1",
}
ANOS_EUROPA = set(range(2010, 2019)) | set(range(2022, 2026))
ANOS_BRASIL = set(range(2012, 2020)) | {2022, 2023}
TOKENS_GENERICOS = {
    "a", "ac", "afc", "as", "association", "associacao", "b v", "bv", "CA", "AC",
    "cf", "club", "clube", "da", "das", "de", "del", "do", "dos",
    "esporte", "fc", "FC", "football", "futebol", "fk", "if", "sc", "sk",
    "ss", "sv", "the",
}


def normalizar_nome(valor) -> str:
    """Normaliza pontuação e acentos sem apagar identificadores regionais."""
    if pd.isna(valor):
        return ""
    texto = unicodedata.normalize("NFKD", str(valor).casefold())
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = texto.replace("&", " and ")
    texto = texto.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


def chave_nucleo(valor) -> str:
    tokens = normalizar_nome(valor).split()
    tokens = [token for token in tokens if token not in TOKENS_GENERICOS]
    return " ".join(tokens)


def carregar_csv(caminho: Path, **kwargs) -> pd.DataFrame:
    # Os CSVs são UTF-8, mas alguns bytes isolados inválidos aparecem em campos
    # auxiliares. A substituição desses bytes mantém intactos os nomes válidos.
    return pd.read_csv(
        caminho, encoding="utf-8", encoding_errors="replace", low_memory=False, **kwargs
    )


def localizar_arquivo(padrao: str) -> Path:
    arquivos = sorted(BRONZE.glob(padrao))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo {padrao} encontrado em {BRONZE}")
    return arquivos[-1]


def ler_partidas() -> tuple[pd.DataFrame, str]:
    parquet = PRATA / "partidas.parquet"
    if parquet.exists():
        try:
            partidas = pd.read_parquet(
                parquet, columns=["Division", "MatchDate", "HomeTeam", "AwayTeam"]
            )
            return partidas, parquet.name
        except (ImportError, ValueError, OSError) as erro:
            print(f"Não foi possível ler {parquet.name} ({erro}); tentando o CSV prata antes do CSV bruto.")

    prata_csv = PRATA / "partidas.csv"
    if prata_csv.exists():
        partidas = carregar_csv(
            prata_csv,
            usecols=["Division", "MatchDate", "HomeTeam", "AwayTeam"],
        )
        return partidas, prata_csv.name

    origem = localizar_arquivo("football_*.csv")
    partidas = carregar_csv(
        origem,
        usecols=["Division", "MatchDate", "HomeTeam", "AwayTeam"],
    )
    return partidas, origem.name


def temporada_partida(linhas: pd.DataFrame) -> pd.DataFrame:
    partidas = linhas.copy()
    partidas["Division"] = partidas["Division"].astype("string").str.strip().str.upper()
    partidas["MatchDate"] = pd.to_datetime(partidas["MatchDate"], errors="coerce")
    partidas = partidas[
        partidas["Division"].isin(COMPETICAO_POR_DIVISAO)
        & partidas["MatchDate"].notna()
    ].copy()

    eh_brasil = partidas["Division"].eq("BRA")
    partidas["tipo_temporada"] = eh_brasil.map({True: "BRA", False: "EUROPA"})
    partidas["ano_temporada"] = partidas["MatchDate"].dt.year
    partidas.loc[~eh_brasil & partidas["MatchDate"].dt.month.lt(7), "ano_temporada"] -= 1

    inicio_temporada_europa = pd.to_datetime(
        partidas["ano_temporada"].astype("Int64").astype("string") + "-07-25",
        errors="coerce",
    )
    fim_temporada_europa = pd.to_datetime(
        (partidas["ano_temporada"] + 1).astype("Int64").astype("string") + "-06-15",
        errors="coerce",
    )
    dentro_janela_europa = partidas["MatchDate"].between(
        inicio_temporada_europa, fim_temporada_europa
    )

    selecionada = (
        (partidas["tipo_temporada"].eq("EUROPA") & partidas["ano_temporada"].isin(ANOS_EUROPA))
        | (partidas["tipo_temporada"].eq("BRA") & partidas["ano_temporada"].isin(ANOS_BRASIL))
    ) & (eh_brasil | dentro_janela_europa)
    partidas = partidas.loc[selecionada].copy()

    # Mantém a partida incluída manualmente em transformar_partidas.py quando
    # este script precisa refazer a seleção usando o CSV bruto.
    jogo_adicionado = {
        "Division": "F1",
        "MatchDate": pd.Timestamp("2024-12-18"),
        "HomeTeam": "Monaco",
        "AwayTeam": "Paris SG",
        "tipo_temporada": "EUROPA",
        "ano_temporada": 2024,
    }
    existe_jogo_adicionado = (
        partidas["Division"].eq(jogo_adicionado["Division"])
        & partidas["MatchDate"].eq(jogo_adicionado["MatchDate"])
        & partidas["HomeTeam"].eq(jogo_adicionado["HomeTeam"])
        & partidas["AwayTeam"].eq(jogo_adicionado["AwayTeam"])
    ).any()
    if not existe_jogo_adicionado:
        partidas = pd.concat([partidas, pd.DataFrame([jogo_adicionado])], ignore_index=True)
    return partidas


class UnionFind:
    def __init__(self, valores):
        self.pai = {valor: valor for valor in valores}

    def encontrar(self, valor):
        pai = self.pai[valor]
        if pai != valor:
            self.pai[valor] = self.encontrar(pai)
        return self.pai[valor]

    def unir(self, a, b):
        raiz_a, raiz_b = self.encontrar(a), self.encontrar(b)
        if raiz_a != raiz_b:
            # raiz determinística para resultados reproduzíveis
            menor, maior = sorted((raiz_a, raiz_b), key=normalizar_nome)
            self.pai[maior] = menor


def montar_aliases(times: list[str], clubes: pd.DataFrame):
    """Resolve nomes conservadores e devolve chaves de clube e relatório."""
    aliases_por_time: dict[str, set[str]] = {}
    aliases_norm: dict[str, set[str]] = defaultdict(set)

    # O dicionário contém equivalências revisadas para diferenças conhecidas
    # entre o feed de partidas e o nome do Transfermarkt.
    for time in times:
        nomes = {time}
        nomes.update(ALIASES_TIME_PARTIDAS.get(time, []))
        aliases_por_time[time] = nomes
        for nome in nomes:
            chave = normalizar_nome(nome)
            if chave:
                aliases_norm[chave].add(time)

    uniao = UnionFind(times)
    for candidatos in aliases_norm.values():
        if len(candidatos) > 1:
            candidatos = sorted(candidatos)
            for time in candidatos[1:]:
                uniao.unir(candidatos[0], time)

    chave_time = {
        time: "time:" + normalizar_nome(uniao.encontrar(time)).replace(" ", "_")
        for time in times
    }
    nomes_por_chave: dict[str, set[str]] = defaultdict(set)
    for time, nomes in aliases_por_time.items():
        nomes_por_chave[chave_time[time]].update(nomes)

    exatos: dict[str, set[str]] = defaultdict(set)
    nucleos: dict[str, set[str]] = defaultdict(set)

    def adicionar_alias(nome: str, key: str):
        exato = normalizar_nome(nome)
        nucleo = chave_nucleo(nome)
        if exato:
            exatos[exato].add(key)
        if nucleo:
            nucleos[nucleo].add(key)

    for key, nomes in nomes_por_chave.items():
        for nome in nomes:
            adicionar_alias(nome, key)

    def resolver(nome: str):
        exato = normalizar_nome(nome)
        encontrados = exatos.get(exato, set()) if exato else set()
        if len(encontrados) == 1:
            return next(iter(encontrados)), "nome_exato"
        if len(encontrados) > 1:
            return None, "nome_exato_ambiguo"

        nucleo = chave_nucleo(nome)
        encontrados = nucleos.get(nucleo, set()) if nucleo else set()
        if len(encontrados) == 1:
            return next(iter(encontrados)), "nucleo_unico"
        if len(encontrados) > 1:
            return None, "nucleo_ambiguo"
        return None, "sem_correspondencia"

    ids_por_time: dict[str, set[str]] = defaultdict(set)
    catalogo_por_time: dict[str, set[str]] = defaultdict(set)
    nomes_catalogo_sem_correspondencia = []
    for linha in clubes[["club_id", "name"]].itertuples(index=False):
        club_id = str(linha.club_id)
        nome = str(linha.name)
        key, metodo = resolver(nome)
        if key:
            ids_por_time[key].add(club_id)
            catalogo_por_time[key].add(nome)
            # O nome atual do catálogo também poderá ser o nome histórico na
            # tabela de avaliações. Só entra no mapa se identificar um time só.
            adicionar_alias(nome, key)
        else:
            nomes_catalogo_sem_correspondencia.append((nome, club_id, metodo))

    # Depois de enriquecer os aliases com o catálogo, calcula o estado de cada
    # time. IDs múltiplos nunca são escolhidos arbitrariamente.
    id_unico_por_time = {}
    status_time = {}
    for key in set(chave_time.values()):
        ids = ids_por_time.get(key, set())
        if len(ids) == 1:
            id_unico_por_time[key] = next(iter(ids))
            status_time[key] = "id_catalogo_unico"
        elif len(ids) > 1:
            id_unico_por_time[key] = pd.NA
            status_time[key] = "ids_catalogo_ambiguos"
        else:
            id_unico_por_time[key] = pd.NA
            status_time[key] = "sem_id_catalogo"

    # Chaves de nome são reconstruídas depois de incluir os nomes do catálogo.
    def resolver_final(nome: str):
        exato = normalizar_nome(nome)
        encontrados = exatos.get(exato, set()) if exato else set()
        if len(encontrados) == 1:
            return next(iter(encontrados)), "nome_exato"
        if len(encontrados) > 1:
            return None, "nome_exato_ambiguo"
        nucleo = chave_nucleo(nome)
        encontrados = nucleos.get(nucleo, set()) if nucleo else set()
        if len(encontrados) == 1:
            return next(iter(encontrados)), "nucleo_unico"
        if len(encontrados) > 1:
            return None, "nucleo_ambiguo"
        return None, "sem_correspondencia"

    catalogo = clubes[["club_id", "name"]].copy()
    catalogo["club_id"] = catalogo["club_id"].astype("string")
    catalogo["chave_time"] = catalogo["name"].map(lambda n: resolver_final(str(n))[0])

    auditoria = []
    for time in times:
        key = chave_time[time]
        nomes_match = sorted(nomes_por_chave[key])
        clubes_match = sorted(catalogo_por_time.get(key, set()))
        if status_time[key] == "id_catalogo_unico":
            status = "mapeado_com_id_unico"
        elif status_time[key] == "ids_catalogo_ambiguos":
            status = "mais_de_um_id_no_catalogo"
        else:
            status = "sem_id_no_catalogo"
        auditoria.append(
            {
                "time_partidas": time,
                "chave_clube": key,
                "aliases_configurados": " | ".join(nomes_match),
                "nomes_catalogo_correlacionados": " | ".join(clubes_match),
                "club_id_correlacionado": id_unico_por_time[key],
                "status_correlacao_catalogo": status,
            }
        )

    return chave_time, id_unico_por_time, catalogo, resolver_final, pd.DataFrame(auditoria)


def melhores_sugestoes(nome: str, nomes_catalogo: list[str], limite: int = 3) -> str:
    alvo = chave_nucleo(nome) or normalizar_nome(nome)
    if not alvo:
        return ""
    pontuados = []
    for candidato in nomes_catalogo:
        chave = chave_nucleo(candidato) or normalizar_nome(candidato)
        if chave:
            pontuados.append((SequenceMatcher(None, alvo, chave).ratio(), candidato))
    pontuados.sort(reverse=True)
    return json.dumps(
        [{"nome": nome, "similaridade": round(score, 3)} for score, nome in pontuados[:limite]],
        ensure_ascii=False,
    )


def construir_cruzamento(partidas, chave_time, id_unico_por_time):
    aparicoes = pd.concat(
        [
            partidas[["Division", "MatchDate", "tipo_temporada", "ano_temporada", "HomeTeam"]]
            .rename(columns={"HomeTeam": "time_partidas"}),
            partidas[["Division", "MatchDate", "tipo_temporada", "ano_temporada", "AwayTeam"]]
            .rename(columns={"AwayTeam": "time_partidas"}),
        ],
        ignore_index=True,
    )
    aparicoes["time_partidas"] = aparicoes["time_partidas"].astype("string").str.strip()
    aparicoes = aparicoes[aparicoes["time_partidas"].notna() & aparicoes["time_partidas"].ne("")].copy()
    aparicoes["chave_clube"] = aparicoes["time_partidas"].map(chave_time)
    aparicoes["competicao_id_partidas"] = aparicoes["Division"].map(COMPETICAO_POR_DIVISAO)

    chaves = ["chave_clube", "tipo_temporada", "ano_temporada"]
    resumo = (
        aparicoes.groupby(chaves, dropna=False)
        .agg(
            divisoes=("Division", lambda s: sorted(set(s.dropna().astype(str)))),
            times_partidas=("time_partidas", lambda s: sorted(set(s.dropna().astype(str)))),
            quantidade_partidas=("MatchDate", "size"),
        )
        .reset_index()
    )
    resumo["quantidade_divisoes"] = resumo["divisoes"].map(len)
    resumo["Division"] = resumo["divisoes"].map(lambda x: x[0] if len(x) == 1 else pd.NA)
    resumo["competicao_id_corrigida"] = resumo["Division"].map(COMPETICAO_POR_DIVISAO)
    resumo["status_temporada"] = resumo["quantidade_divisoes"].map(
        lambda n: "mapeado" if n == 1 else "mais_de_uma_divisao"
    )
    resumo["club_id"] = resumo["chave_clube"].map(id_unico_por_time)
    resumo["temporada"] = resumo.apply(
        lambda r: f"{int(r.ano_temporada)}/{str(int(r.ano_temporada) + 1)[-2:]}"
        if r.tipo_temporada == "EUROPA"
        else str(int(r.ano_temporada)),
        axis=1,
    )
    resumo["divisoes"] = resumo["divisoes"].map(lambda x: " | ".join(x))
    resumo["times_partidas"] = resumo["times_partidas"].map(lambda x: " | ".join(x))
    return resumo, aparicoes


def temporadas_avaliacoes(avaliacoes: pd.DataFrame) -> pd.DataFrame:
    linhas = avaliacoes.copy()
    linhas["_linha_id"] = range(len(linhas))
    linhas["_data"] = pd.to_datetime(linhas["date"], errors="coerce")
    linhas["_ano_europa"] = linhas["_data"].dt.year
    linhas.loc[linhas["_data"].dt.month.lt(7), "_ano_europa"] -= 1
    linhas["_ano_brasil"] = linhas["_data"].dt.year

    # Preserva as janelas usadas na seleção prata que já existe no projeto:
    # 25/jul a 15/jun para Europa e o ano civil para o Brasileirão.
    data = linhas["_data"]
    inicio_ano = linhas["_ano_europa"]
    inicio_europa = pd.to_datetime(inicio_ano.astype("Int64").astype("string") + "-07-25", errors="coerce")
    fim_europa = pd.to_datetime((inicio_ano + 1).astype("Int64").astype("string") + "-06-15", errors="coerce")
    dentro_janela_europa = (data.ge(inicio_europa) & data.le(fim_europa))

    europeias = linhas[
        dentro_janela_europa & linhas["_ano_europa"].isin(ANOS_EUROPA)
    ][["_linha_id", "_data", "_ano_europa"]].copy()
    europeias["tipo_temporada"] = "EUROPA"
    europeias["ano_temporada"] = europeias["_ano_europa"]

    brasileiras = linhas[
        data.notna() & linhas["_ano_brasil"].isin(ANOS_BRASIL)
    ][["_linha_id", "_data", "_ano_brasil"]].copy()
    brasileiras["tipo_temporada"] = "BRA"
    brasileiras["ano_temporada"] = brasileiras["_ano_brasil"]

    elegiveis = pd.concat(
        [
            europeias[["_linha_id", "_data", "tipo_temporada", "ano_temporada"]],
            brasileiras[["_linha_id", "_data", "tipo_temporada", "ano_temporada"]],
        ],
        ignore_index=True,
    )
    return linhas.merge(elegiveis, on="_linha_id", how="inner")


def salvar_tabela(df: pd.DataFrame, nome_sem_extensao: str) -> Path:
    """Prefere Parquet; usa CSV UTF-8 quando o ambiente não tem engine Parquet."""
    destino_parquet = PRATA / f"{nome_sem_extensao}.parquet"
    try:
        df.to_parquet(destino_parquet, index=False)
        return destino_parquet
    except (ImportError, ValueError) as erro:
        destino_csv = PRATA / f"{nome_sem_extensao}.csv"
        df.to_csv(destino_csv, index=False, encoding="utf-8-sig")
        print(f"Parquet indisponível ({erro}); salvo como CSV: {destino_csv.name}")
        return destino_csv







def main():
    PRATA.mkdir(parents=True, exist_ok=True)
    caminho_clubes = localizar_arquivo("clubs_*.csv")
    caminho_avaliacoes = localizar_arquivo("player_valuations_*.csv")
    clubes = carregar_csv(caminho_clubes, dtype={"club_id": "string"})
    avaliacoes = carregar_csv(
        caminho_avaliacoes,
        dtype={"player_id": "string", "current_club_id": "string"},
    )
    partidas_originais, origem_partidas = ler_partidas()
    partidas = temporada_partida(partidas_originais)

    nomes_times = sorted(
        set(partidas["HomeTeam"].dropna().astype(str).str.strip())
        | set(partidas["AwayTeam"].dropna().astype(str).str.strip())
    )
    chave_time, id_unico_por_time, catalogo, resolver_nome, auditoria_times = montar_aliases(
        nomes_times, clubes
    )
    cruzamento, aparicoes = construir_cruzamento(partidas, chave_time, id_unico_por_time)

    # Inclui sugestões apenas para revisão; elas nunca preenchem uma competição.
    nomes_catalogo = catalogo["name"].dropna().astype(str).drop_duplicates().tolist()
    auditoria_times["sugestoes_catalogo"] = auditoria_times.apply(
        lambda r: melhores_sugestoes(r["time_partidas"], nomes_catalogo)
        if r["status_correlacao_catalogo"] != "mapeado_com_id_unico"
        else "",
        axis=1,
    )
    temporadas_por_time = (
        cruzamento.groupby("chave_clube")["temporada"]
        .agg(lambda s: " | ".join(sorted(set(s.astype(str)))))
        .to_dict()
    )
    competicoes_por_time = (
        cruzamento.groupby("chave_clube")["competicao_id_corrigida"]
        .agg(lambda s: " | ".join(sorted(set(s.dropna().astype(str)))))
        .to_dict()
    )
    auditoria_times["temporadas_observadas"] = auditoria_times["chave_clube"].map(temporadas_por_time)
    auditoria_times["competicoes_observadas"] = auditoria_times["chave_clube"].map(competicoes_por_time)

    elegiveis = temporadas_avaliacoes(avaliacoes)
    nomes_unicos = elegiveis["current_club_name"].drop_duplicates().tolist()
    mapa_nomes = {}
    for nome in nomes_unicos:
        if pd.isna(nome) or normalizar_nome(nome) in {"", "unknown", "without club"}:
            mapa_nomes[str(nome)] = (None, "sem_nome_de_clube")
        else:
            mapa_nomes[str(nome)] = resolver_nome(str(nome))
    resolvidos = elegiveis["current_club_name"].astype(str).map(mapa_nomes)
    elegiveis["chave_clube"] = resolvidos.map(lambda item: item[0])
    elegiveis["metodo_correlacao_nome"] = resolvidos.map(lambda item: item[1])

    chaves_crosswalk = cruzamento[
        [
            "chave_clube", "tipo_temporada", "ano_temporada", "Division",
            "competicao_id_corrigida", "status_temporada", "temporada",
            "club_id", "times_partidas", "quantidade_partidas",
        ]
    ].copy()
    candidatas = elegiveis.merge(
        chaves_crosswalk,
        on=["chave_clube", "tipo_temporada", "ano_temporada"],
        how="left",
        suffixes=("", "_crosswalk"),
    )

    # Resolve a linha apenas quando o nome identifica um clube único e esse
    # clube tem uma única divisão na temporada consultada.
    mapped_candidatas = candidatas[
        candidatas["chave_clube"].notna()
        & candidatas["competicao_id_corrigida"].notna()
        & candidatas["status_temporada"].eq("mapeado")
    ].copy()
    mapped_candidatas["_chave_candidata"] = (
        mapped_candidatas["Division"].astype(str)
        + "|" + mapped_candidatas["tipo_temporada"].astype(str)
        + "|" + mapped_candidatas["ano_temporada"].astype(str)
    )
    quantidade_candidatas_validas = mapped_candidatas.groupby("_linha_id")["_chave_candidata"].nunique()
    ids_linha_mapeados = quantidade_candidatas_validas[quantidade_candidatas_validas.eq(1)].index
    ids_linha_competicao_ambigua = quantidade_candidatas_validas[quantidade_candidatas_validas.gt(1)].index
    mapped = (
        mapped_candidatas[mapped_candidatas["_linha_id"].isin(ids_linha_mapeados)]
        .drop_duplicates("_linha_id", keep="first")
        .copy()
    )

    todas = avaliacoes.copy()
    todas["current_club_id_original"] = todas["current_club_id"]
    todas["player_club_domestic_competition_id_original"] = (
        todas["player_club_domestic_competition_id"]
    )
    todas["current_club_id_corrigido"] = pd.Series(pd.NA, index=todas.index, dtype="string")
    todas["player_club_domestic_competition_id_corrigido"] = pd.Series(
        pd.NA, index=todas.index, dtype="string"
    )
    todas["Division_corrigida"] = pd.Series(pd.NA, index=todas.index, dtype="string")
    todas["temporada_corrigida"] = pd.Series(pd.NA, index=todas.index, dtype="string")
    todas["tipo_temporada_corrigida"] = pd.Series(pd.NA, index=todas.index, dtype="string")
    todas["time_partidas_correlacionado"] = pd.Series(pd.NA, index=todas.index, dtype="string")
    todas["metodo_correlacao_nome"] = pd.Series(pd.NA, index=todas.index, dtype="string")
    todas["partidas_clube_temporada"] = pd.Series(pd.NA, index=todas.index, dtype="Int64")
    todas["status_correcao_competicao"] = "fora_das_temporadas_selecionadas"

    ids_por_chave = pd.Series(id_unico_por_time, dtype="string")
    indices_mapeados = mapped["_linha_id"].astype("int64").to_numpy()
    mapped = mapped.set_index("_linha_id")
    todas.loc[indices_mapeados, "current_club_id_corrigido"] = (
        mapped["chave_clube"].map(ids_por_chave).to_numpy()
    )
    todas.loc[indices_mapeados, "player_club_domestic_competition_id_corrigido"] = (
        mapped["competicao_id_corrigida"].to_numpy()
    )
    todas.loc[indices_mapeados, "Division_corrigida"] = mapped["Division"].to_numpy()
    todas.loc[indices_mapeados, "temporada_corrigida"] = mapped["temporada"].to_numpy()
    todas.loc[indices_mapeados, "tipo_temporada_corrigida"] = mapped["tipo_temporada"].to_numpy()
    todas.loc[indices_mapeados, "time_partidas_correlacionado"] = mapped["times_partidas"].to_numpy()
    todas.loc[indices_mapeados, "metodo_correlacao_nome"] = mapped["metodo_correlacao_nome"].to_numpy()
    todas.loc[indices_mapeados, "partidas_clube_temporada"] = mapped["quantidade_partidas"].to_numpy()
    todas.loc[indices_mapeados, "status_correcao_competicao"] = "corrigido_por_partidas"

    # Monta o relatório de linhas elegíveis sem atribuição, com motivo explícito.
    flags = candidatas.assign(
        _tem_chave=candidatas["chave_clube"].notna().astype("int8"),
        _nome_ambiguo=candidatas["metodo_correlacao_nome"].astype(str).str.contains("ambiguo").astype("int8"),
        _sem_nome=candidatas["metodo_correlacao_nome"].eq("sem_nome_de_clube").astype("int8"),
        _tem_temporada=candidatas["status_temporada"].notna().astype("int8"),
        _temporada_ambigua=candidatas["status_temporada"].eq("mais_de_uma_divisao").astype("int8"),
    )
    status_por_linha = flags.groupby("_linha_id").agg(
        tem_chave=("_tem_chave", "max"),
        nome_ambiguo=("_nome_ambiguo", "max"),
        sem_nome=("_sem_nome", "max"),
        tem_temporada=("_tem_temporada", "max"),
        temporada_ambigua=("_temporada_ambigua", "max"),
    )
    status_por_linha["motivo"] = "clube_fora_das_competicoes_selecionadas_na_temporada"
    status_por_linha.loc[status_por_linha["tem_chave"].eq(0), "motivo"] = "nome_sem_correspondencia"
    status_por_linha.loc[status_por_linha["sem_nome"].eq(1), "motivo"] = "sem_nome_de_clube"
    status_por_linha.loc[status_por_linha["nome_ambiguo"].eq(1), "motivo"] = "nome_ambiguo"
    status_por_linha.loc[status_por_linha["temporada_ambigua"].eq(1), "motivo"] = "clube_em_mais_de_uma_divisao_na_temporada"
    status_por_linha.loc[
        status_por_linha.index.isin(ids_linha_competicao_ambigua), "motivo"
    ] = "nome_correspondente_a_mais_de_uma_competicao"
    sem_competicao_unica = (
        status_por_linha["tem_temporada"].eq(1)
        & status_por_linha["temporada_ambigua"].eq(0)
        & ~status_por_linha.index.isin(ids_linha_mapeados)
        & ~status_por_linha.index.isin(ids_linha_competicao_ambigua)
    )
    status_por_linha.loc[sem_competicao_unica, "motivo"] = "sem_competicao_mapeada_na_temporada"
    todas.loc[status_por_linha.index, "status_correcao_competicao"] = status_por_linha["motivo"].to_numpy()
    todas.loc[indices_mapeados, "status_correcao_competicao"] = "corrigido_por_partidas"

    ids_mapeados_set = set(indices_mapeados.tolist())
    elegiveis_unicos = elegiveis.drop_duplicates("_linha_id").copy()
    elegiveis_unicos = elegiveis_unicos[
        ~elegiveis_unicos["_linha_id"].isin(ids_mapeados_set)
    ].copy()
    elegiveis_unicos = elegiveis_unicos.merge(
        status_por_linha[["motivo"]], left_on="_linha_id", right_index=True, how="left"
    )
    elegiveis_unicos["ano_avaliacao"] = pd.to_datetime(
        elegiveis_unicos["date"], errors="coerce"
    ).dt.year
    nao_mapeadas = (
        elegiveis_unicos.groupby(
            ["current_club_name", "ano_avaliacao", "player_club_domestic_competition_id", "motivo"],
            dropna=False,
        )
        .size()
        .rename("quantidade_avaliacoes")
        .reset_index()
    )

    # Filtra por pares competição/temporada realmente presentes no cruzamento
    # selecionado e mantém apenas linhas com club_id corrigido pelo catálogo.
    pares_competicao_temporada_usados = set(
        cruzamento.loc[
            cruzamento["status_temporada"].eq("mapeado")
            & cruzamento["competicao_id_corrigida"].notna()
            & cruzamento["temporada"].notna(),
            ["competicao_id_corrigida", "temporada"],
        ].itertuples(index=False, name=None)
    )
    par_linha_pertence_ao_cruzamento = pd.Series(
        [
            pd.notna(competicao)
            and pd.notna(temporada)
            and (competicao, temporada) in pares_competicao_temporada_usados
            for competicao, temporada in zip(
                todas["player_club_domestic_competition_id_corrigido"],
                todas["temporada_corrigida"],
            )
        ],
        index=todas.index,
    )
    selecionadas = todas[
        par_linha_pertence_ao_cruzamento
        & todas["player_club_domestic_competition_id_corrigido"].isin(
            set(COMPETICAO_POR_DIVISAO.values())
        )
        & todas["current_club_id_corrigido"].notna()
    ].copy()

    # Arquivo auditável completo: todas as linhas de origem, com original,
    # valor corrigido, temporada, time encontrado e evidência em partidas.
    caminho_auditoria = PRATA / "avaliacoes_jogadores_corrigidas.csv"
    todas.to_csv(caminho_auditoria, index=False, encoding="utf-8-sig")

    # Entrega no esquema original, já filtrado por competição/temporada e com
    # ambos os IDs substituídos pelos valores confirmados pelo cruzamento.
    final_mesmo_esquema = avaliacoes.loc[selecionadas.index].copy()
    final_mesmo_esquema["current_club_id"] = (
        selecionadas["current_club_id_corrigido"].astype("string").to_numpy()
    )
    final_mesmo_esquema["player_club_domestic_competition_id"] = (
        selecionadas["player_club_domestic_competition_id_corrigido"].astype("string").to_numpy()
    )
    caminho_final = PRATA / "player_valuations_corrigido.csv"
    final_mesmo_esquema.to_csv(caminho_final, index=False, encoding="utf-8-sig")
    salvar_tabela(final_mesmo_esquema, "player_valuations_corrigido")

    caminho_cruzamento = PRATA / "clubes_competicoes_por_temporada.csv"
    cruzamento.to_csv(caminho_cruzamento, index=False, encoding="utf-8-sig")
    caminho_revisao = PRATA / "revisao_correlacao_clubes.csv"
    auditoria_times.to_csv(caminho_revisao, index=False, encoding="utf-8-sig")
    caminho_sem_comp = PRATA / "avaliacoes_sem_competicao.csv"
    nao_mapeadas.to_csv(caminho_sem_comp, index=False, encoding="utf-8-sig")

    # Resumo que permite conferir por competição/temporada quantos clubes e
    # jogos sustentam o mapa eF quantas avaliações foram corrigidas.
    resumo_crosswalk = (
        cruzamento.groupby(["Division", "competicao_id_corrigida", "temporada"], dropna=False)
        .agg(
            clubes_com_jogos=("chave_clube", "nunique"),
            clubes_sem_id_catalogo=("club_id", lambda s: s.isna().sum()),
            aparicoes_clube_partida=("quantidade_partidas", "sum"),
            clubes_com_conflito=("status_temporada", lambda s: s.ne("mapeado").sum()),
        )
        .reset_index()
    )
    mapeadas_para_resumo = mapped.reset_index().copy()
    mapeadas_para_resumo["divergencia_competicao_original"] = (
        mapeadas_para_resumo["player_club_domestic_competition_id"].fillna("").astype(str)
        .ne(mapeadas_para_resumo["competicao_id_corrigida"].fillna("").astype(str))
    )
    resumo_avaliacoes = (
        mapeadas_para_resumo.groupby(
            ["Division", "competicao_id_corrigida", "temporada"], dropna=False
        )
        .agg(
            avaliacoes_corrigidas=("_linha_id", "nunique"),
            divergencias_competicao_original=("divergencia_competicao_original", "sum"),
        )
        .reset_index()
    )
    validacao = resumo_crosswalk.merge(
        resumo_avaliacoes,
        on=["Division", "competicao_id_corrigida", "temporada"],
        how="left",
    )
    validacao[["avaliacoes_corrigidas", "divergencias_competicao_original"]] = validacao[
        ["avaliacoes_corrigidas", "divergencias_competicao_original"]
    ].fillna(0).astype("int64")
    caminho_validacao = PRATA / "validacao_competicoes_por_temporada.csv"
    validacao.to_csv(caminho_validacao, index=False, encoding="utf-8-sig")

    print(f"Partidas usadas: {origem_partidas} ({len(partidas):,} partidas selecionadas)")
    print(f"Clubes/temporadas no cruzamento: {len(cruzamento):,}")
    print(f"Avaliações lidas: {len(avaliacoes):,}")
    print(f"Avaliações com IDs corrigidos e competição/temporada selecionadas: {len(selecionadas):,}")
    sem_id_catalogo = int(
        (
            todas["player_club_domestic_competition_id_corrigido"].notna()
            & todas["current_club_id_corrigido"].isna()
        ).sum()
    )
    print(f"Avaliações excluídas por falta de club_id único no catálogo: {sem_id_catalogo:,}")
    divergentes = selecionadas[
        selecionadas["player_club_domestic_competition_id_original"].fillna("").astype(str)
        .ne(selecionadas["player_club_domestic_competition_id_corrigido"].fillna("").astype(str))
    ]
    print(f"Competição corrigida diferente da original (inclui original vazia): {len(divergentes):,}")
    print("Avaliações confirmadas por competição:")
    print(selecionadas["player_club_domestic_competition_id_corrigido"].value_counts().to_string())
    print("Avaliações confirmadas por competição e temporada:")
    print(
        selecionadas.groupby(
            ["player_club_domestic_competition_id_corrigido", "temporada_corrigida"]
        ).size().to_string()
    )
    print(f"Arquivo final mesmo esquema: {caminho_final.name} ({len(final_mesmo_esquema):,} linhas)")
    print(f"Arquivo completo com auditoria: {caminho_auditoria.name} ({len(todas):,} linhas)")
    print(f"Arquivos de validação: {caminho_cruzamento.name}, {caminho_validacao.name}, {caminho_revisao.name}, {caminho_sem_comp.name}")

    
if __name__ == "__main__":
    main()
