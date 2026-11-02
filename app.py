from typing import Literal
import pandas as pd
import streamlit as st
import altair as alt
import numpy as np

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

COR_DESTAQUE = "#7F77DD"
COR_NEUTRA = "#888780"
NOMES_FAIXA = {"Low": "Baixa (0 a 32)", "Medium": "Média (33 a 65)", "High": "Alta (66 a 100)"}
CORES_FAIXA = alt.Scale(domain=list(NOMES_FAIXA.values()), range=["#3AA59D", COR_NEUTRA, COR_DESTAQUE])

def formata_streams(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f} mi".replace(".0 ", " ").replace(".", ",")
    return f"{n / 1_000:.0f} mil"

def formata_numero(x):
    return f"{x:.2f}".replace(".", ",")

def formata_valor(v, eh_streams):
    return formata_streams(10 ** v) if eh_streams else formata_numero(v)

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

    col_correlacao, col_distribuicao = st.columns([1, 1.5], gap="large", border=True)

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
            # Uma linha por característica, da correlação mais forte para a mais fraca
            corr = (
                df_filtrado[caracteristicas]
                .corrwith(df_filtrado["popularity"], method=metodo)
                .dropna()
                .sort_values(key=abs, ascending=False)
                # Correlação não tem unidade, então o nome vai sem o "(min)", "(dB)" etc.
                .rename(index=lambda c: CARACTERISTICAS[c].split(" (")[0])
                .rename_axis("caracteristica")
                .reset_index(name="correlacao")
            )
            # Abaixo de 0,05 o valor não quer dizer nada, então mostra "≈ 0"
            corr["rotulo"] = corr["correlacao"].map(lambda r: "≈ 0" if abs(r) < 0.05 else formata_numero(r))
            corr["posicao_rotulo"] = corr["correlacao"].clip(lower=0)

            base = alt.Chart(corr).encode(
                y=alt.Y("caracteristica:N", sort=corr["caracteristica"].tolist(), title=None),
            )

            # Destaca só correlações de 0,1 para cima; o resto fica cinza
            cor = alt.condition("abs(datum.correlacao) >= 0.1", alt.value(COR_DESTAQUE), alt.value(COR_NEUTRA))
            barras = base.mark_bar().encode(
                x=alt.X(
                    "correlacao:Q",
                    scale=alt.Scale(domain=[-1, 1]),
                    title=None,
                    axis=alt.Axis(values=[-1, -0.5, 0, 0.5, 1], labelExpr="replace(datum.label, '.', ',')"),
                ),
                color=cor,
                tooltip=[
                    alt.Tooltip("caracteristica:N", title="Característica"),
                    alt.Tooltip("correlacao:Q", title="Correlação", format=".2f"),
                ],
            )
            rotulos = base.mark_text(align="left", dx=4, fontSize=13).encode(
                x="posicao_rotulo:Q", text="rotulo:N", color=cor
            )
            linha_zero = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color=COR_NEUTRA).encode(x="x:Q")

            st.altair_chart(
                (barras + rotulos + linha_zero).properties(height=45 * len(corr) + 30, padding={"left": 20}),
                width="stretch",
            )

            principal = corr.iloc[0]
            if abs(principal["correlacao"]) < 0.1:
                st.info("Nenhuma característica acompanha a popularidade nestes filtros: todas ficam perto de zero.")
            else:
                texto = (
                    f"{principal['caracteristica']} é o que mais acompanha a popularidade "
                    f"({formata_numero(principal['correlacao'])})."
                )
                resto = corr.iloc[1:]
                if not resto.empty and resto["correlacao"].abs().max() < 0.05:
                    texto += " As demais características ficam perto de zero."
                elif not resto.empty:
                    texto += f" Em seguida vem {resto.iloc[0]['caracteristica']} ({resto.iloc[0]['rotulo']})."
                st.info(texto)

# Distribuiçao e sobre os dados
with col_distribuicao:
    st.subheader("Como as músicas se distribuem")

    if not caracteristicas:
        st.warning("Selecione pelo menos 1 característica.")
    elif df_filtrado.empty:
        st.warning("Nenhuma música dentro dos filtros.")
    else:
        var = st.selectbox("Variável", options=caracteristicas, format_func=lambda c: CARACTERISTICAS[c])
        eh_streams = var == "log_stream_count"

        # Streams em log10 (log natural / ln 10): cada unidade a mais no eixo é 10 vezes mais streams
        valores = df_filtrado["log_stream_count"] / np.log(10) if eh_streams else df_filtrado[var]
        bordas = np.histogram_bin_edges(valores, bins=20)

        # Um grupo por faixa de popularidade, ou um grupo só com todas as músicas
        if separar_por_faixa:
            grupos = {f: valores[df_filtrado["popularity_category"] == f] for f in NOMES_FAIXA}
        else:
            grupos = {"Todas": valores}

        # % das músicas de cada grupo em cada intervalo (cada grupo soma 100%)
        partes = []
        for codigo, grupo in grupos.items():
            if grupo.empty:
                continue
            contagem, _ = np.histogram(grupo, bins=bordas)
            partes.append(pd.DataFrame({
                "faixa": NOMES_FAIXA.get(codigo, codigo),
                "inicio": bordas[:-1],
                "fim": bordas[1:],
                "meio": (bordas[:-1] + bordas[1:]) / 2,
                "pct": 100 * contagem / len(grupo),
                "intervalo": [
                    f"{formata_valor(a, eh_streams)} a {formata_valor(b, eh_streams)}"
                    for a, b in zip(bordas[:-1], bordas[1:])
                ],
            }))
        dist = pd.concat(partes)

        escala_x = alt.Scale(domain=[float(bordas[0]), float(bordas[-1])])
        if eh_streams:
            potencias = [p for p in range(3, 8) if bordas[0] <= p <= bordas[-1]]
            eixo_x = alt.Axis(
                title="Streams (escala log)",
                values=potencias,
                labelExpr="['1 mil', '10 mil', '100 mil', '1 mi', '10 mi'][datum.value - 3]",
            )
        else:
            eixo_x = alt.Axis(title=CARACTERISTICAS[var])
        dicas = [
            alt.Tooltip("intervalo:N", title="Intervalo"),
            alt.Tooltip("pct:Q", title="% das músicas", format=".1f"),
        ]

        if separar_por_faixa:
            st.caption("% das músicas de cada faixa de popularidade em cada intervalo. Cada linha soma 100%.")
            grafico = alt.Chart(dist).mark_line(strokeWidth=2.5).encode(
                x=alt.X("meio:Q", scale=escala_x, axis=eixo_x),
                y=alt.Y("pct:Q", title="% das músicas da faixa"),
                color=alt.Color("faixa:N", title=None, scale=CORES_FAIXA, legend=alt.Legend(orient="top")),
                tooltip=[alt.Tooltip("faixa:N", title="Faixa"), *dicas],
            )

            nomes_curtos = {"Low": "baixa", "Medium": "média", "High": "alta"}
            medianas = {f: grupo.median() for f, grupo in grupos.items() if not grupo.empty}
            texto = "Mediana: " + ", ".join(
                f"{formata_valor(m, eh_streams)} na faixa {nomes_curtos[f]}" for f, m in medianas.items()
            ) + "."
            if len(medianas) >= 2:
                q1, q3 = valores.quantile([0.25, 0.75])
                maior = max(medianas, key=lambda f: medianas[f])
                # Diferença entre medianas menor que 10% da faixa central dos dados: na prática, iguais
                if max(medianas.values()) - min(medianas.values()) <= 0.1 * (q3 - q1):
                    texto += " As faixas praticamente não se diferenciam."
                else:
                    texto += f" A faixa {nomes_curtos[maior]} concentra os valores mais altos."
        else:
            st.caption("% das músicas em cada intervalo.")
            grafico = alt.Chart(dist).mark_bar(color=COR_DESTAQUE).encode(
                x=alt.X("inicio:Q", bin="binned", scale=escala_x, axis=eixo_x),
                x2="fim:Q",
                y=alt.Y("pct:Q", title="% das músicas"),
                tooltip=dicas,
            )

            q1, mediana, q3 = valores.quantile([0.25, 0.5, 0.75])
            texto = (
                f"Mediana de {formata_valor(mediana, eh_streams)}. "
                f"Metade das músicas fica entre {formata_valor(q1, eh_streams)} e {formata_valor(q3, eh_streams)}."
            )

        st.altair_chart(grafico.properties(height=320), width="stretch")
        st.info(texto)

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