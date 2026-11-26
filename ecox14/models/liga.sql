SELECT DISTINCT
    liga_id,
    CASE liga_id
        WHEN 'BRA' THEN 'Brasileirão Série A'
        WHEN 'D1'  THEN 'Bundesliga'
        WHEN 'E0'  THEN 'Premier League'
        WHEN 'F1'  THEN 'Ligue 1'
        WHEN 'I1'  THEN 'Serie A'
        WHEN 'SP1' THEN 'La Liga'
    END AS nome_liga,
    CASE liga_id
        WHEN 'BRA' THEN 'Brasil'
        WHEN 'D1'  THEN 'Alemanha'
        WHEN 'E0'  THEN 'Inglaterra'
        WHEN 'F1'  THEN 'França'
        WHEN 'I1'  THEN 'Itália'
        WHEN 'SP1' THEN 'Espanha'
    END AS pais
FROM {{ ref('partidas') }}