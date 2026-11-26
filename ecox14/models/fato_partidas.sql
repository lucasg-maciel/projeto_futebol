SELECT
    md5(CONCAT(data_partida, '|', clube_home, '|', clube_away)) AS partida_sk,
    data_partida,
    temporada,
    liga_id,
    md5(clube_home) AS clube_home_sk,
    md5(clube_away) AS clube_away_sk,
    clube_home,
    clube_away,
    gols_home,
    gols_away,
    resultado,
    pontos_home,
    pontos_away,
    valor_elenco_home,
    valor_elenco_away
FROM {{ ref('partidas') }}