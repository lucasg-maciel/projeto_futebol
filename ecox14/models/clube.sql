WITH clubes AS (
    SELECT DISTINCT clube_home AS clube_nome, liga_id FROM {{ ref('partidas') }}
    UNION
    SELECT DISTINCT clube_away AS clube_nome, liga_id FROM {{ ref('partidas') }}
)
SELECT
    md5(clube_nome) AS clube_sk,
    clube_nome,
    liga_id
FROM clubes