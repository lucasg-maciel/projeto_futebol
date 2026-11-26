from pathlib import Path
import duckdb
RAIZ = Path(__file__).resolve().parent.parent
BANCO = RAIZ / "dados" / "ouro" / "projeto.duckdb"
def _consultar(sql, parametros=None):
    con = duckdb.connect(str(BANCO), read_only=True)
    try:
        return con.execute(sql, parametros or []).df()
    finally:
        con.close()

def ligas():
    """Lista as ligas disponíveis para o filtro do painel."""
    return _consultar(
        """
        SELECT DISTINCT
            liga_id,
            nome_liga
        FROM ouro.liga
        ORDER BY nome_liga
        """
    )


def temporadas(liga_id):
    """Lista as temporadas disponíveis para a liga selecionada."""
    return _consultar(
        """
        SELECT DISTINCT
            temporada
        FROM ouro.fato_desempenho_temporadas
        WHERE liga_id = ?
        ORDER BY temporada DESC
        """,
        [liga_id],
    )


def desempenho_por_temporada(liga_id, temporada):
    """Classificação da temporada cruzando pontos e valor de mercado do elenco."""
    return _consultar(
        """
        SELECT
            clube_nome,
            jogos,
            pontos_totais,
            vitorias,
            empates,
            derrotas,
            saldo_gols,
            valor_total_elenco
        FROM ouro.fato_desempenho_temporadas
        WHERE liga_id = ?
          AND temporada = ?
        ORDER BY pontos_totais DESC, vitorias DESC, saldo_gols DESC
        """,
        [liga_id, temporada],
    )


def historico_clube(clube_nome):
    """Evolução de pontos e valor de elenco de um clube ao longo das temporadas."""
    return _consultar(
        """
        SELECT
            f.temporada,
            l.nome_liga,
            f.pontos_totais,
            f.vitorias,
            f.valor_total_elenco
        FROM ouro.fato_desempenho_temporadas f
        JOIN ouro.liga l ON f.liga_id = l.liga_id
        WHERE f.clube_nome = ?
        ORDER BY f.temporada
        """,
        [clube_nome],
    )