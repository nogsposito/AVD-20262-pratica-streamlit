from typing import Literal
import pandas as pd
import streamlit as st

from src.data_loader import load_data

st.set_page_config(page_title="SpotiStats", layout="wide")

df = load_data()

st.title("SpotiStats")
st.markdown(
    f":gray[O que anda junto com a popularidade das músicas? "
    f"{len(df) // 1000} mil músicas lançadas entre {df['release_year'].min()} e {df['release_year'].max()}.]"
)

METODOS: list[Literal["spearman", "pearson"]] = ["spearman", "pearson"]

# Características comparadas com a popularidade (streams em log, por causa da assimetria)
CARACTERISTICAS = {
    "log_stream_count": "Streams",
    "duration_minutes": "Duração (min)",
    "danceability": "Dançabilidade",
    "energy": "Energia",
    "loudness": "Volume (dB)",
    "tempo": "Andamento (BPM)",
}

OPCOES_STREAMS = [
    1_000, 2_000, 5_000, 10_000, 20_000, 50_000, 100_000, 200_000, 500_000,
    1_000_000, 2_000_000, 5_000_000, 10_000_000, 20_000_000,
]

def formata_streams(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:g} mi"
    return f"{n / 1_000:g} mil"

# Sidebar
with st.sidebar:
    st.header("Filtros")

    caracteristicas = st.multiselect(
        "Características comparadas",
        options=list(CARACTERISTICAS),
        default=list(CARACTERISTICAS),
        format_func=lambda c: CARACTERISTICAS[c],
        help="Quais características entram na comparação com a popularidade.",
    )

    metodo = st.radio(
        "Método de correlação",
        options=METODOS,
        format_func=str.capitalize,
        horizontal=True,
        help="Pearson mede relação linear; Spearman compara a ordem dos valores.",
    )

    separar_por_faixa = st.toggle(
        "Separar por faixa de popularidade",
        help="Compara as faixas baixa (0 a 32), média (33 a 65) e alta (66 a 100).",
    )

    st.subheader("Intervalos")
    intervalos: dict[str, tuple[float, float]] = {"popularity": st.slider("Popularidade", 0, 100, (0, 100))}
    for var in caracteristicas:
        if var == "log_stream_count":
            # Filtra pelos streams reais, mais fáceis de ler que o log
            intervalos["stream_count"] = st.select_slider(
                "Streams",
                options=OPCOES_STREAMS,
                value=(OPCOES_STREAMS[0], OPCOES_STREAMS[-1]),
                format_func=formata_streams,
            )
        else:
            minimo, maximo = float(df[var].min()), float(df[var].max())
            intervalos[var] = st.slider(
                CARACTERISTICAS[var],
                min_value=minimo,
                max_value=maximo,
                value=(minimo, maximo),
                step=0.01,
                key=f"intervalo_{var}",
            )

# Filtros e abas
df_filtrado = df

for coluna, (inicio, fim) in intervalos.items():
    df_filtrado = df_filtrado[df_filtrado[coluna].between(inicio, fim)]

aba_d1, aba_d2 = st.tabs(["Correlação e distribuição", "Indicadores"])

with aba_d1:
    st.caption(f"{len(df_filtrado)} de {len(df)} músicas dentro dos filtros.")

    col_correlacao, col_distribuicao = st.columns([1, 1.5])

    with col_correlacao:
        st.subheader("O que acompanha a popularidade")
        st.caption(
            f"Correlação de {metodo.capitalize()} de cada característica com a popularidade, "
            "de -1 a 1. Perto de 0: não andam juntas."
        )

        if not caracteristicas:
            st.warning("Selecione pelo menos 1 característica.")
        elif len(df_filtrado) < 30:
            st.warning("Poucas músicas dentro dos filtros para calcular a correlação.")
        elif df_filtrado["popularity"].nunique() < 2:
            st.warning("Com um único valor de popularidade não dá para calcular correlação. Abra o intervalo.")
        else:
            # Provisório: tabela no lugar do gráfico de barras
            corr = df_filtrado[caracteristicas].corrwith(df_filtrado["popularity"], method=metodo)
            corr = corr.sort_values(key=abs, ascending=False).rename(index=CARACTERISTICAS)
            st.dataframe(corr.round(2).rename("correlação"))

# Distribuiçao e sobre os dados
with col_distribuicao:
    st.subheader("Como as músicas se distribuem")

    if not caracteristicas:
        st.warning("Selecione pelo menos 1 característica.")
    elif df_filtrado.empty:
        st.warning("Nenhuma música dentro dos filtros.")
    else:
        var = st.selectbox("Variável", options=caracteristicas, format_func=lambda c: CARACTERISTICAS[c])

        # Provisório: resumo numérico no lugar do histograma
        if separar_por_faixa:
            resumo = df_filtrado.groupby("popularity_category")[var].describe()
        else:
            resumo = df_filtrado[var].describe().to_frame().T
        st.dataframe(resumo.round(2))

with st.expander("Sobre os dados"):
    st.markdown(
        "Fonte: [Spotify Artist Streaming Analytics (2015-2025)]"
        "(https://www.kaggle.com/datasets/yogeshm01/spotify-artist-streaming-analytics-20152025), no Kaggle.\n\n"
        "As características de áudio têm distribuição quase uniforme e praticamente nenhuma correlação "
        "entre si, sinal de que o dataset é sintético. As conclusões valem para esta base, não para o "
        "Spotify real. E correlação não indica causa."
    )

with aba_d2:
    st.info("Os indicadores entram nas próximas etapas.")