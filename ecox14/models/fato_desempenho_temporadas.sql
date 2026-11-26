WITH jogos_por_clube AS (
    SELECT
        liga_id,
        temporada,
        clube_home AS clube_nome,
        pontos_home AS pontos,
        gols_home AS gols_pro,
        gols_away AS gols_contra,
        CASE WHEN resultado = 'H' THEN 1 ELSE 0 END AS vitoria,
        CASE WHEN resultado = 'D' THEN 1 ELSE 0 END AS empate,
        CASE WHEN resultado = 'A' THEN 1 ELSE 0 END AS derrota,
        valor_elenco_home AS valor_elenco
    FROM {{ ref('partidas') }}

    UNION ALL

    SELECT
        liga_id,
        temporada,
        clube_away AS clube_nome,
        pontos_away AS pontos,
        gols_away AS gols_pro,
        gols_home AS gols_contra,
        CASE WHEN resultado = 'A' THEN 1 ELSE 0 END AS vitoria,
        CASE WHEN resultado = 'D' THEN 1 ELSE 0 END AS empate,
        CASE WHEN resultado = 'H' THEN 1 ELSE 0 END AS derrota,
        valor_elenco_away AS valor_elenco
    FROM {{ ref('partidas') }}
),
agregado AS (
    SELECT
        liga_id,
        temporada,
        md5(clube_nome) AS clube_sk,
        clube_nome,
        COUNT(*) AS jogos,
        SUM(pontos) AS pontos_totais,
        SUM(vitoria) AS vitorias,
        SUM(empate) AS empates,
        SUM(derrota) AS derrotas,
        SUM(gols_pro) AS gols_pro,
        SUM(gols_contra) AS gols_contra,
        SUM(gols_pro) - SUM(gols_contra) AS saldo_gols,
        MAX(valor_elenco) AS valor_total_elenco
    FROM jogos_por_clube
    GROUP BY liga_id, temporada, clube_nome
)
SELECT
    *,
    ROW_NUMBER() OVER (
        PARTITION BY liga_id, temporada
        ORDER BY pontos_totais DESC, vitorias DESC, saldo_gols DESC, gols_pro DESC
    ) AS posicao_tabela,
    ROUND(valor_total_elenco / NULLIF(pontos_totais, 0), 2) AS custo_por_ponto
FROM agregado