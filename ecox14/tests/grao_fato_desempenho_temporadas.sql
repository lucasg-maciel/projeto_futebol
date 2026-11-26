-- passa quando devolve ZERO linhas
select liga_id, temporada, clube_nome, count(*)
from {{ ref('fato_desempenho_temporadas') }}
group by liga_id, temporada, clube_nome
having count(*) > 1