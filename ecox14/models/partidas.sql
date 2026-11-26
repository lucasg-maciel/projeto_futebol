SELECT
    CAST(MatchDate AS DATE) AS data_partida,
    CAST(temporada AS VARCHAR) AS temporada,
    
    Division AS liga_id,
    home_padrao AS clube_home,
    away_padrao AS clube_away,
    FTResult AS resultado,
    CAST(FTHome AS INTEGER) AS gols_home,
    CAST(FTAway AS INTEGER) AS gols_away,
    CASE
        WHEN FTResult = 'H' THEN 3
        WHEN FTResult = 'D' THEN 1
        ELSE 0
    END AS pontos_home,
    CASE
        WHEN FTResult = 'A' THEN 3
        WHEN FTResult = 'D' THEN 1
        ELSE 0
    END AS pontos_away,
    CAST(valor_total_elenco_home AS DOUBLE) AS valor_elenco_home,
    CAST(valor_total_elenco_away AS DOUBLE) AS valor_elenco_away
FROM {{ source('prata', 'partidas_enriquecidas') }}