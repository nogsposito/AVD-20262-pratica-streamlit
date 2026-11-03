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

# Variáveis quantitativas do Dashboard 1 (streams em log, por causa da assimetria)
VARIAVEIS = {
    "popularity": "Popularidade",
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
COR_BAIXA = "#3AA59D"
NOMES_FAIXA = {"Low": "Baixa (0 a 32)", "Medium": "Média (33 a 65)", "High": "Alta (66 a 100)"}
NOMES_CURTOS = {"Low": "baixa", "Medium": "média", "High": "alta"}
EIXO_PCT = "replace(datum.label, '.', ',') + '%'"
CORES_FAIXA = alt.Scale(domain=list(NOMES_FAIXA.values()), range=[COR_BAIXA, COR_NEUTRA, COR_DESTAQUE])

# Uma legenda só para a grade de histogramas, no lugar de uma em cada gráfico
LEGENDA_FAIXAS = "  ".join(
    f':color[■]{{foreground="{cor}"}} {nome}'
    for nome, cor in zip(NOMES_FAIXA.values(), [COR_BAIXA, COR_NEUTRA, COR_DESTAQUE])
)

# Taxa de hits do catálogo inteiro, a referência dos indicadores do Dashboard 2
TAXA_CATALOGO = 100 * (df["popularity_category"] == "High").mean()

def formata_streams(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f} mi".replace(".0 ", " ").replace(".", ",")
    return f"{n / 1_000:.0f} mil"

def formata_numero(x):
    return f"{x:.2f}".replace(".", ",")

def formata_valor(v, eh_streams):
    return formata_streams(10 ** v) if eh_streams else formata_numero(v)

def formata_pct(x):
    return f"{x:.1f}%".replace(".", ",")

def valores_do_grafico(dados, var):
    # Streams em log10 (log natural / ln 10): cada unidade a mais no eixo é 10 vezes mais streams
    return dados["log_stream_count"] / np.log(10) if var == "log_stream_count" else dados[var]

def histograma(dados, var, separar_por_faixa):
    eh_streams = var == "log_stream_count"
    valores = valores_do_grafico(dados, var)

    # Faixas com largura múltipla da precisão dos dados (0,01 na dançabilidade). Senão umas faixas
    # pegam 5 valores possíveis e outras 4, e o gráfico ganha "dentes" que não existem nos dados
    precisao = np.diff(np.unique(valores)).min() if valores.nunique() > 1 else 1.0
    largura = max(precisao, np.ceil((valores.max() - valores.min()) / 20 / precisao) * precisao)
    bordas = np.arange(valores.min() - precisao / 2, valores.max() + largura, largura)

    # Um grupo por faixa de popularidade, ou um grupo só com todas as músicas
    if separar_por_faixa:
        grupos = {f: valores[dados["popularity_category"] == f] for f in NOMES_FAIXA}
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
                f"{formata_valor(a + precisao / 2, eh_streams)} a {formata_valor(b - precisao / 2, eh_streams)}"
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
        eixo_x = alt.Axis(title=VARIAVEIS[var], labelExpr="replace(datum.label, '.', ',')")
    dicas = [
        alt.Tooltip("intervalo:N", title="Intervalo"),
        alt.Tooltip("pct:Q", title="% das músicas", format=".1f"),
    ]

    if separar_por_faixa:
        grafico = alt.Chart(dist).mark_line(strokeWidth=2).encode(
            x=alt.X("meio:Q", scale=escala_x, axis=eixo_x),
            y=alt.Y("pct:Q", title="% da faixa", axis=alt.Axis(labelExpr=EIXO_PCT)),
            color=alt.Color("faixa:N", scale=CORES_FAIXA, legend=None),
            tooltip=[alt.Tooltip("faixa:N", title="Faixa"), *dicas],
        )
    else:
        grafico = alt.Chart(dist).mark_bar(color=COR_DESTAQUE).encode(
            x=alt.X("inicio:Q", bin="binned", scale=escala_x, axis=eixo_x),
            x2="fim:Q",
            y=alt.Y("pct:Q", title="% das músicas", axis=alt.Axis(labelExpr=EIXO_PCT)),
            tooltip=dicas,
        )
    return grafico.properties(height=200)

def resumo_distribuicoes(dados, variaveis, separar_por_faixa):
    if not separar_por_faixa:
        # Assimetria acima de 1 (para mais ou para menos): as músicas se concentram num dos lados
        frases = []
        for var in variaveis:
            assimetria = float(valores_do_grafico(dados, var).skew())
            if abs(assimetria) > 1:
                lado = "baixos" if assimetria > 0 else "altos"
                frases.append(f"{VARIAVEIS[var]} concentra as músicas nos valores mais {lado}")
        if not frases:
            return "Nenhuma variável é muito assimétrica: as músicas não se concentram num dos extremos."
        texto = "; ".join(frases) + "."
        if len(frases) < len(variaveis):
            texto += " As demais variáveis não têm esse desequilíbrio."
        return texto

    # As faixas vêm da própria popularidade, então ela fica fora da comparação
    comparaveis = [v for v in variaveis if v != "popularity"]
    if not comparaveis:
        return "As faixas são definidas pela própria popularidade. Escolha outras variáveis para comparar."

    diferentes = []
    for var in comparaveis:
        valores = valores_do_grafico(dados, var)
        medianas = {
            f: valores[dados["popularity_category"] == f].median()
            for f in NOMES_FAIXA
            if (dados["popularity_category"] == f).any()
        }
        q1, q3 = valores.quantile([0.25, 0.75])
        # Diferença entre medianas menor que 10% da faixa central dos dados: na prática, iguais
        if len(medianas) >= 2 and max(medianas.values()) - min(medianas.values()) > 0.1 * (q3 - q1):
            eh_streams = var == "log_stream_count"
            detalhe = ", ".join(
                f"{formata_valor(m, eh_streams)} na faixa {NOMES_CURTOS[f]}" for f, m in medianas.items()
            )
            diferentes.append(f"{VARIAVEIS[var]} (mediana de {detalhe})")

    if not diferentes:
        return "Em nenhuma variável as faixas se diferenciam: as linhas ficam sobrepostas."
    texto = "As faixas se diferenciam em " + "; ".join(diferentes) + "."
    if len(diferentes) < len(comparaveis):
        texto += " Nas demais variáveis, praticamente não se diferenciam."
    return texto

# Com on_change="rerun" só a aba aberta roda, e cada aba mostra os próprios filtros
aba_d1, aba_d2 = st.tabs(["Correlação e distribuição", "Indicadores"], key="aba", on_change="rerun")

if aba_d1.open:
    # Sidebar (persist_state guarda as escolhas enquanto a outra aba está aberta)
    with st.sidebar:
        st.header("Filtros")

        variaveis = st.multiselect(
            "Variáveis quantitativas",
            options=list(VARIAVEIS),
            default=list(VARIAVEIS),
            format_func=lambda v: VARIAVEIS[v],
            help="Quais variáveis entram no heatmap e nos histogramas.",
            key="variaveis",
            persist_state="page",
        )

        metodo = st.radio(
            "Método de correlação",
            options=METODOS,
            format_func=str.capitalize,
            horizontal=True,
            help="Pearson mede relação linear; Spearman compara a ordem dos valores.",
            key="metodo",
            persist_state="page",
        )

        separar_por_faixa = st.toggle(
            "Separar por faixa de popularidade",
            help="Nos histogramas, compara as faixas baixa (0 a 32), média (33 a 65) e alta (66 a 100).",
            key="separar_por_faixa",
            persist_state="page",
        )

        # Um slider de intervalo para cada variável escolhida
        st.subheader("Intervalos")
        intervalos: dict[str, tuple[float, float]] = {}
        for var in variaveis:
            if var == "log_stream_count":
                # Filtra pelos streams reais, mais fáceis de ler que o log
                intervalos["stream_count"] = st.select_slider(
                    "Streams",
                    options=OPCOES_STREAMS,
                    value=(OPCOES_STREAMS[0], OPCOES_STREAMS[-1]),
                    format_func=formata_streams,
                    key="intervalo_streams",
                    persist_state="page",
                )
            elif pd.api.types.is_integer_dtype(df[var]):
                minimo_int, maximo_int = int(df[var].min()), int(df[var].max())
                intervalos[var] = st.slider(
                    VARIAVEIS[var],
                    minimo_int,
                    maximo_int,
                    (minimo_int, maximo_int),
                    key=f"intervalo_{var}",
                    persist_state="page",
                )
            else:
                minimo, maximo = float(df[var].min()), float(df[var].max())
                intervalos[var] = st.slider(
                    VARIAVEIS[var],
                    min_value=minimo,
                    max_value=maximo,
                    value=(minimo, maximo),
                    step=0.01,
                    key=f"intervalo_{var}",
                    persist_state="page",
                )

    # Filtros e abas
    df_filtrado = df

    for coluna, (inicio, fim) in intervalos.items():
        df_filtrado = df_filtrado[df_filtrado[coluna].between(inicio, fim)]

    with aba_d1:
        st.caption(f"{len(df_filtrado)} de {len(df)} músicas dentro dos filtros.")

        col_correlacao, col_distribuicao = st.columns([1, 1.5], gap="large", border=True)

        with col_correlacao:
            st.subheader("Como as variáveis se relacionam")
            st.caption(
                f"Correlação de {metodo.capitalize()} entre cada par de variáveis, de -1 a 1. Roxo: sobem juntas. "
                "Verde: quando uma sobe, a outra desce. Cinza: não andam juntas."
            )

            # Variável que não varia dentro dos filtros não tem correlação
            validas = [v for v in variaveis if df_filtrado[v].nunique() > 1]
            if len(variaveis) < 2:
                st.warning("Selecione pelo menos 2 variáveis para calcular a correlação.")
            elif len(df_filtrado) < 30:
                st.warning("Poucas músicas dentro dos filtros para calcular a correlação.")
            elif len(validas) < 2:
                st.warning("Com esses intervalos, menos de 2 variáveis variam. Abra algum intervalo.")
            else:
                # Correlação não tem unidade, então os nomes vão sem o "(min)", "(dB)" etc.
                nomes = {v: VARIAVEIS[v].split(" (")[0] for v in validas}
                ordem = list(nomes.values())

                # Matriz de correlação em formato longo: uma linha por par de variáveis
                corr = (
                    df_filtrado[validas]
                    .corr(method=metodo)
                    .rename(index=nomes, columns=nomes)
                    .rename_axis("var_y")
                    .reset_index()
                    .melt(id_vars="var_y", var_name="var_x", value_name="correlacao")
                )
                # Só o triângulo de baixo, sem a diagonal: a matriz é espelhada e a diagonal é sempre 1
                posicao = {nome: i for i, nome in enumerate(ordem)}
                corr = corr[corr["var_y"].map(posicao) > corr["var_x"].map(posicao)]
                # Abaixo de 0,05 o valor não quer dizer nada, então mostra "≈ 0"
                corr = corr.assign(
                    rotulo=corr["correlacao"].map(lambda r: "≈ 0" if abs(r) < 0.05 else formata_numero(r)),
                    forca=corr["correlacao"].abs(),
                )

                base = alt.Chart(corr).encode(
                    x=alt.X("var_x:N", sort=ordem[:-1], title=None, axis=alt.Axis(labelAngle=-45, labelOverlap=False)),
                    y=alt.Y("var_y:N", sort=ordem[1:], title=None),
                )
                celulas = base.mark_rect().encode(
                    color=alt.Color(
                        "correlacao:Q",
                        title=None,
                        # interpolate="rgb" vai do cinza ao roxo em linha reta, sem passar por tons de vermelho
                        scale=alt.Scale(
                            domain=[-1, 0, 1], range=[COR_BAIXA, COR_NEUTRA, COR_DESTAQUE], interpolate="rgb"
                        ),
                        legend=alt.Legend(orient="bottom", labelExpr="replace(datum.label, '.', ',')"),
                    ),
                    tooltip=[
                        alt.Tooltip("var_y:N", title="Variável"),
                        alt.Tooltip("var_x:N", title="Com"),
                        alt.Tooltip("correlacao:Q", title="Correlação", format=".2f"),
                    ],
                )
                textos = base.mark_text(color="white", fontSize=13).encode(text="rotulo:N")

                st.altair_chart(
                    (celulas + textos).properties(
                        width="container", height=60 * (len(ordem) - 1) + 40, padding={"left": 20}
                    ),
                    width="stretch",
                )
                fora = [VARIAVEIS[v] for v in variaveis if v not in validas]
                if fora:
                    st.caption(f"Fora do heatmap por não variar dentro dos filtros: {', '.join(fora)}.")

                pares = corr.sort_values("forca", ascending=False)
                principal = pares.iloc[0]
                if principal["forca"] < 0.1:
                    st.info("Nenhum par de variáveis anda junto: todas as correlações ficam perto de zero.")
                else:
                    texto = (
                        f"O par que mais anda junto é {principal['var_y']} e {principal['var_x']} "
                        f"({formata_numero(principal['correlacao'])})."
                    )
                    resto = pares.iloc[1:]
                    if not resto.empty and resto["forca"].max() < 0.05:
                        texto += " Os demais pares ficam perto de zero."
                    elif not resto.empty:
                        segundo = resto.iloc[0]
                        texto += f" Em seguida vem {segundo['var_y']} e {segundo['var_x']} ({segundo['rotulo']})."
                    st.info(texto)

    # Distribuiçao e sobre os dados
    with col_distribuicao:
        st.subheader("Como cada variável se distribui")

        if not variaveis:
            st.warning("Selecione pelo menos 1 variável.")
        elif df_filtrado.empty:
            st.warning("Nenhuma música dentro dos filtros.")
        else:
            if separar_por_faixa:
                st.caption(
                    "Um gráfico por variável. Cada linha é uma faixa de popularidade, e a altura mostra "
                    "quantos % das músicas da faixa caem em cada intervalo."
                )
                st.markdown(LEGENDA_FAIXAS)
            else:
                st.caption(
                    "Um gráfico por variável. A altura de cada barra mostra quantos % das músicas caem "
                    "naquele intervalo."
                )

            # Grade de 2 colunas, um histograma por variável escolhida
            for i in range(0, len(variaveis), 2):
                colunas_grade = st.columns(2)
                for col, var in zip(colunas_grade, variaveis[i:i + 2]):
                    col.altair_chart(histograma(df_filtrado, var, separar_por_faixa), width="stretch")

            st.info(resumo_distribuicoes(df_filtrado, variaveis, separar_por_faixa))


if aba_d2.open:
    with aba_d2:
        st.subheader("Onde estão os streams?")

        # Filtros do Dashboard 2 no topo da aba, como no rascunho
        col_genero, col_pais, col_ano = st.columns([1, 1, 1.2])
        generos = col_genero.multiselect(
            "Gêneros", options=sorted(df["genre"].unique()), placeholder="Todos", key="generos", persist_state="page"
        )
        paises = col_pais.multiselect(
            "Países", options=sorted(df["country"].unique()), placeholder="Todos", key="paises", persist_state="page"
        )
        anos = col_ano.slider(
            "Ano de lançamento", 2015, 2025, (2015, 2025), key="anos", persist_state="page"
        )

        df_d2 = df[df["release_year"].between(anos[0], anos[1])]
        if generos:
            df_d2 = df_d2[df_d2["genre"].isin(generos)]
        if paises:
            df_d2 = df_d2[df_d2["country"].isin(paises)]

        if df_d2.empty:
            st.warning("Nenhuma música com esses filtros.")
        else:
            # Os indicadores ficam em cima, mas só são preenchidos depois do clique no gráfico de gêneros
            area_indicadores = st.container()
            col_generos, col_popularidade, col_peso = st.columns(3, gap="large", border=True)

            with col_generos:
                st.subheader("Algum gênero emplaca mais hits?")
                hits = df_d2["popularity_category"] == "High"
                taxa_genero = (100 * hits.groupby(df_d2["genre"]).mean()).rename("taxa").reset_index()

                clique = alt.selection_point(name="genero", fields=["genre"])
                barras_genero = alt.Chart(taxa_genero).mark_bar(color=COR_DESTAQUE).encode(
                    x=alt.X(
                        "taxa:Q",
                        title="% das músicas com popularidade 66+",
                        scale=alt.Scale(domain=[0, max(15, taxa_genero["taxa"].max())]),
                    ),
                    y=alt.Y("genre:N", sort="-x", title=None),
                    opacity=alt.condition(clique, alt.value(1), alt.value(0.3)),
                    tooltip=[
                        alt.Tooltip("genre:N", title="Gênero"),
                        alt.Tooltip("taxa:Q", title="% de hits", format=".1f"),
                    ],
                ).add_params(clique)
                media_genero = alt.Chart(pd.DataFrame({"x": [100 * hits.mean()]})).mark_rule(
                    color=COR_NEUTRA, strokeDash=[4, 4]
                ).encode(x="x:Q")

                evento = st.altair_chart(
                    (barras_genero + media_genero).properties(height=360),
                    on_select="rerun",
                    key="grafico_generos",
                    width="stretch",
                )
                clicados = [item["genre"] for item in evento.selection.get("genero", [])]

                menor, maior = taxa_genero["taxa"].min(), taxa_genero["taxa"].max()
                if len(taxa_genero) == 1:
                    st.info(f"{taxa_genero['genre'].iloc[0]}: {formata_pct(maior)} das músicas viram hit.")
                elif maior - menor < 2:
                    st.info(f"Nenhum gênero se destaca: todos ficam entre {formata_pct(menor)} e {formata_pct(maior)}.")
                else:
                    lider = taxa_genero.set_index("genre")["taxa"].idxmax()
                    st.info(f"{lider} lidera com {formata_pct(maior)}. O menor fica em {formata_pct(menor)}.")

            # O clique num gênero filtra os indicadores e os outros dois gráficos
            df_sel = df_d2[df_d2["genre"].isin(clicados)] if clicados else df_d2

            with area_indicadores:
                if clicados:
                    st.caption(f"Filtrando por {', '.join(clicados)}. Clique numa área vazia do gráfico para limpar.")
                else:
                    st.caption("Clique num gênero do gráfico para filtrar os indicadores.")

                streams = df_sel["stream_count"].sort_values(ascending=False)
                top1 = max(1, int(len(streams) * 0.01))
                taxa = 100 * (df_sel["popularity_category"] == "High").mean()
                diferenca = f"{taxa - TAXA_CATALOGO:+.1f}".replace(".", ",")

                ind1, ind2, ind3, ind4 = st.columns(4)
                ind1.metric("Músicas no recorte", f"{len(df_sel):,}".replace(",", "."), border=True)
                ind2.metric(
                    "Taxa de hits",
                    formata_pct(taxa),
                    delta=f"{diferenca} p.p. vs. catálogo" if diferenca not in ("+0,0", "-0,0") else None,
                    delta_color="off",
                    help="% das músicas com popularidade de 66 a 100.",
                    border=True,
                )
                ind3.metric(
                    "Música típica",
                    f"{formata_streams(streams.median())} streams",
                    help=f"Mediana: metade das músicas tem até esse valor. A média é {formata_streams(streams.mean())}, "
                    "puxada por poucos sucessos.",
                    border=True,
                )
                ind4.metric(
                    "Concentração",
                    formata_pct(100 * streams.iloc[:top1].sum() / streams.sum()),
                    help="% dos streams que vão para o 1% das músicas mais ouvidas do recorte.",
                    border=True,
                )

            with col_popularidade:
                st.subheader("Quanto tende a subir na popularidade")

                # Arredonda a popularidade para baixo de 5 em 5 (100 entra na faixa de 95)
                faixa_pop = (df_sel["popularity"] // 5 * 5).clip(upper=95)
                por_pop = df_sel.groupby(faixa_pop)["stream_count"].median().rename("mediana").reset_index()
                por_pop["faixa"] = por_pop["popularity"].map(lambda p: f"{p} a {p + 4 if p < 95 else 100}")

                linha = alt.Chart(por_pop).mark_line(point=True, color=COR_DESTAQUE).encode(
                    x=alt.X("popularity:Q", title="Popularidade", scale=alt.Scale(domain=[0, 100])),
                    y=alt.Y(
                        "mediana:Q",
                        title="Streams medianos (escala log)",
                        scale=alt.Scale(type="log"),
                        axis=alt.Axis(
                            values=[1e3, 1e4, 1e5, 1e6, 1e7],
                            labelExpr="datum.value >= 1e6 ? datum.value / 1e6 + ' mi' : datum.value / 1e3 + ' mil'",
                        ),
                    ),
                    tooltip=[
                        alt.Tooltip("faixa:N", title="Popularidade"),
                        alt.Tooltip("mediana:Q", title="Streams medianos", format=",.0f"),
                    ],
                )
                corte = alt.Chart(pd.DataFrame({"x": [66]})).mark_rule(
                    color=COR_NEUTRA, strokeDash=[4, 4]
                ).encode(x="x:Q")
                st.altair_chart((linha + corte).properties(height=360), width="stretch")
                st.caption("A linha tracejada marca o início da faixa alta (66).")

                inicio_pop, fim_pop = por_pop.iloc[0], por_pop.iloc[-1]
                if len(por_pop) >= 2:
                    st.info(
                        f"Com popularidade de {inicio_pop['faixa']}, a música típica tem "
                        f"{formata_streams(inicio_pop['mediana'])} streams. De {fim_pop['faixa']}, "
                        f"tem {formata_streams(fim_pop['mediana'])}."
                    )

            with col_peso:
                st.subheader("Proporção de quantidade de músicas e streams por faixa de popularidade")

                peso = df_sel.groupby("popularity_category").agg(
                    musicas=("stream_count", "size"), streams=("stream_count", "sum")
                )
                peso = (100 * peso / peso.sum()).reindex([f for f in NOMES_FAIXA if f in peso.index])
                peso = (
                    peso.rename(index=NOMES_FAIXA, columns={"musicas": "Músicas", "streams": "Streams"})
                    .rename_axis("faixa")
                    .reset_index()
                    .melt(id_vars="faixa", var_name="medida", value_name="pct")
                )
                # Início e fim de cada pedaço da barra, para empilhar na ordem baixa, média, alta
                peso["fim"] = peso.groupby("medida")["pct"].cumsum()
                peso["inicio"] = peso["fim"] - peso["pct"]
                peso["meio"] = (peso["inicio"] + peso["fim"]) / 2
                peso["rotulo"] = peso["pct"].map(lambda p: f"{p:.0f}%" if p >= 5 else "")

                base_peso = alt.Chart(peso).encode(y=alt.Y("medida:N", title=None, sort=["Músicas", "Streams"]))
                pedacos = base_peso.mark_bar().encode(
                    x=alt.X(
                        "inicio:Q",
                        title=None,
                        scale=alt.Scale(domain=[0, 100]),
                        axis=alt.Axis(values=[0, 25, 50, 75, 100], labelExpr="datum.value + '%'"),
                    ),
                    x2="fim:Q",
                    color=alt.Color(
                        "faixa:N", title=None, scale=CORES_FAIXA, legend=alt.Legend(orient="bottom", columns=1)
                    ),
                    tooltip=[
                        alt.Tooltip("faixa:N", title="Faixa"),
                        alt.Tooltip("medida:N", title="Parte das"),
                        alt.Tooltip("pct:Q", title="%", format=".1f"),
                    ],
                )
                textos_peso = base_peso.mark_text(color="white", fontSize=13).encode(x="meio:Q", text="rotulo:N")
                st.altair_chart((pedacos + textos_peso).properties(height=200), width="stretch")

                alta = peso[peso["faixa"] == NOMES_FAIXA["High"]].set_index("medida")["pct"]
                if alta.empty:
                    st.info("Nenhuma música de popularidade alta neste recorte.")
                else:
                    st.info(
                        f"As músicas de popularidade alta são {alta['Músicas']:.0f}% do recorte "
                        f"e ficam com {alta['Streams']:.0f}% dos streams."
                    )

with st.expander("Sobre os dados"):
    st.markdown(
        "Fonte: [Spotify Artist Streaming Analytics (2015-2025)]"
        "(https://www.kaggle.com/datasets/yogeshm01/spotify-artist-streaming-analytics-20152025), no Kaggle.\n\n"
        "As características de áudio têm distribuição quase uniforme e praticamente nenhuma correlação "
        "entre si, sinal de que o dataset é sintético. As conclusões valem para esta base, não para o "
        "Spotify real. E correlação não indica causa."
    )