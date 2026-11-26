import streamlit as st
import consultas
import altair as alt

st.set_page_config(page_title="Elenco vs. Desempenho", layout="wide")

st.title("Valor de Mercado do Elenco vs. Desempenho nas Ligas")

df_ligas = consultas.ligas()
mapa_ligas = dict(zip(df_ligas["nome_liga"], df_ligas["liga_id"]))
nome_liga = st.sidebar.selectbox("Liga", list(mapa_ligas.keys()))
liga_id = mapa_ligas[nome_liga]

df_temporadas = consultas.temporadas(liga_id)
temporada = st.sidebar.selectbox("Temporada", df_temporadas["temporada"])

dados = consultas.desempenho_por_temporada(liga_id, temporada)

# 2. Gráfico usando toda a largura disponível
min_valor = dados["valor_total_elenco"].min() * (-5)
max_valor = dados["valor_total_elenco"].max() * 1.5
min_pontos = max(0, dados["pontos_totais"].min() - 30)
max_pontos = dados["pontos_totais"].max() + 30

grafico = (
    alt.Chart(dados)
    .mark_circle(size=90)
    .encode(
        x=alt.X(
            "valor_total_elenco:Q",
            title="Valor do Elenco (€)",
            scale=alt.Scale(domain=[min_valor, max_valor]),
        ),
        y=alt.Y(
            "pontos_totais:Q",
            title="Pontos Totais",
            scale=alt.Scale(domain=[min_pontos, max_pontos]),
        ),
        tooltip=["clube_nome", "pontos_totais", "valor_total_elenco"],
    )
    .properties(height=500)
    .interactive()
)

st.altair_chart(grafico, width="stretch")

# 3. Tabela usando toda a largura disponível
st.subheader("Classificação e valor de elenco")
st.dataframe(
    dados,
    hide_index=True,
    width="stretch",
    height=740,
    column_config={
        "clube_nome": "Clube",
        "jogos": "J",
        "pontos_totais": "Pts",
        "vitorias": "V",
        "empates": "E",
        "derrotas": "D",
        "saldo_gols": "SG",
        "valor_total_elenco": st.column_config.NumberColumn(
            "Elenco (€)", format="€ %d"
        ),
    },
)