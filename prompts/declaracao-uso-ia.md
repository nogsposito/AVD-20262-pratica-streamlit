# Declaração de Uso de IA

**Nome:** Vinicius Sposito
**Data:** 27/10/2026 a 03/11/2026

## Ferramenta

Claude Code (app desktop), modelo Claude Opus 5.5.

## Prompt usado

Prompt inicial, com os PDFs das Aulas 21 e 22 e a mensagem da professora anexados:

"veja essa atividade que terei que fazer. veja que em minha pasta de avd em cesar school ja tenho 'avd-20262-pratica-streamlit', onde deixei meu notebook prévio de eda onde explorei dados relacionados a músicas do spotify. baseado nisso, quero que você vá me ajudando a fazer essa atividade, me ensinando e ajudando a implementar as coisas. não quero que vc efetivamente mexa em nada, quero que pegue o contexto do que estamos fazendo e primeiro me ajude a planejar no chat quais passos vamos tomar (me perguntando o que for em aberto também) e depois ao meu comando ir mandando sugestões dos códigos pelo chat pra que eu possa ir implementando aprendendo como funciona e como devo fazer essa atv."

Pedidos seguintes que mudaram o resultado:

- "mas realmente faz sentido essas visualizações no dashboard? o que vai ser de fato mais útil e fazer mais sentido"
- "me mande uma visualização de como você deixaria como algo final, algo que teria realmente algo interessante pra mostrar e que textos você colocaria pra ficar bem claro"
- "deixe os dois gráficos um pouco separados um do outro (...) mude esses tons vermelhos. tons vermelhos passam a sensação de que tem algo errado"
- Envio dos meus rascunhos (`entregas/rascunho-dashboard1.png` e `entregas/rascunho-dashboard2.png`) para a IA montar o código a partir deles
- PDF da Aula 23, para incluir as exigências finais no plano
- - vamos precisar mudar a parte de correlação e distribuição: a parte de histogramas não deve ser um, devem haver vários histogramas, um pra cada variável (...) além disso, precisaremos mudar o gráfico de barra por heatmap, pra mostrar todas as correlações entre variáveis

## O que foi aceito, modificado ou rejeitado e por quê

- **Aceito:** o plano em etapas; a configuração do fork; a exportação de `data/clean/dataset.csv` com as 16 colunas que o app usa; parte do código dos dois dashboards, enviado pelo chat e implementado por mim, depois de rodar e conferir cada parte, predindo os ajustes necessários; a identidade visual (violeta e fonte Inter); as quatro métricas do Dashboard 2, depois de conferir os cálculos em `notebooks/metricas-dashboard2.ipynb`.
- **Modificado:** tirei emojis, citações e negritos das células sugeridas para o notebook e encurtei os comentários; escolhi o nome SpotiStats e desenhei os dois rascunhos; o Dashboard 2 seguiu o meu rascunho (filtros no topo e três gráficos lado a lado), e não o layout sugerido pela IA (filtros na sidebar); pedi mais espaço entre os gráficos e a troca das cores; reescrevi partes da justificativa das métricas com as minhas palavras. No Dashboard 1, depois de usar por um tempo o ranking de correlação com a popularidade e um histograma por vez, voltei para o heatmap com todas as correlações e um histograma para cada variável, para que todos os pares e todas as distribuições fiquem visíveis ao mesmo tempo.
- **Rejeitado:** o gráfico de streams medianos por ano, porque a mediana dá 2 mil em todos os anos; o vermelho do tema-modelo, porque passava a sensação de erro; e a primeira divisão das faixas dos histogramas, que criava "dentes" que não existiam nos dados.