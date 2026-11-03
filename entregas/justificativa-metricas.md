# Justificativa das métricas — Dashboard 2

## Métrica 1: Músicas no recorte
- **Variável:** contagem de músicas depois dos filtros de gênero, país e ano de lançamento
- **O que mede:** quantas músicas do catálogo entram no recorte escolhido
- **Por que foi escolhida:** é a base das outras métricas. É muito importante que esse tipo e informação seja filtrada para que seja possível fazer análises de comportamento de consumidores mais verídicas.
- **Público-alvo:** equipe de marketing de uma gravadora, que decide em quais músicas e gêneros investir divulgação.
- **Qual decisão pode ser apoiada por essa métrica?** Se o recorte tem músicas suficientes para tirar conclusão ou se seria preciso abrir os filtros
- **O que comunica ao público-alvo:** O tamanho do grupo que está sendo analisado.

## Métrica 2: Taxa de hits
- **Variável:** `popularity_category` (faixa alta = popularidade de 66 a 100)
- **O que mede:** a porcentagem das músicas do recorte que chegaram à faixa alta de popularidade, comparada com a do catálogo inteiro
- **Por que foi escolhida:** responde à pergunta de quem investe, "qual a chance de uma música virar sucesso?". Por ser proporção, permite comparar recortes de tamanhos diferentes.
- **Público-alvo:** equipe de marketing da gravadora.
- **Qual decisão pode ser apoiada por essa métrica?** em quais gêneros, países ou períodos concentrar o investimento. Nesta base a taxa fica entre 11,2% e 12,5% em todos os gêneros, então ela mostra que escolher gênero pela chance de sucesso não traz vantagem.
- **O que comunica ao público-alvo:** "de cada 100 músicas deste recorte, cerca de 12 viram hit", ou que "Historicamente, existe uma chance de 12% dessa música se tornar um hit."

## Métrica 3: Música típica
- **Variável:** `stream_count`
- **O que mede:** a mediana de streams do recorte: metade das músicas tem até esse número
- **Por que foi escolhida:** a média (214 mil) é puxada por poucos sucessos com até 20 milhões de streams. A mediana (2 mil) mostra o que acontece com a maioria. A EDA já tinha mostrado a forte assimetria dos streams.
- **Público-alvo:** equipe de marketing da gravadora.
- **Qual decisão pode ser apoiada por essa métrica?** calibrar a expectativa de retorno de um lançamento comum, sem se guiar pelos sucessos e entendendo o quanto uma música foi bem sucedida em uma escala.
- **O que comunica ao público-alvo:** "uma música comum deste recorte tem cerca de 2 mil streams"

## Métrica 4: Concentração de streams
- **Variável:** `stream_count`
- **O que mede:** a porcentagem do total de streams do recorte que vai para o 1% das músicas mais ouvidas
- **Por que foi escolhida:** mostra o quanto o resultado depende de poucos sucessos. No catálogo inteiro, 1% das músicas tem 73,5% dos streams.
- **Público-alvo:** equipe de marketing da gravadora.
- **Qual decisão pode ser apoiada por essa métrica?** se vale espalhar o orçamento por muitas músicas ou concentrar nas que já começam a despontar
- **O que comunica ao público-alvo:** "quase todo o resultado vem de poucas músicas"