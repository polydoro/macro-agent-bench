# Tasks

Sixteen tasks from the day-to-day work of a euro-area macro economist. Each request is one sentence in Portuguese, identical for every model and method, sent after a fixed common context (below). Agents ran between 26 October and 7 November 2026 on a clean working directory, with internet access, and had to find, download and process the data themselves.

## Simple tasks: data-release write-ups (15-minute limit)

| ID | Request (as sent) | English | What the answer key checks |
|---|---|---|---|
| S01 | Faça a divulgação da produção industrial da Alemanha. | Write up the German industrial production release. | Total (B-D, B-D_F or Destatis "Industrie") YoY and 3m SAAR; main industrial groupings YoY |
| S02 | Faça a divulgação das encomendas à indústria da Alemanha. | German factory orders | Total, domestic and foreign orders YoY; total 3m SAAR |
| S03 | Faça a divulgação das vendas no varejo da Espanha. | Spanish retail sales | Total and breakdowns by product group and store type, YoY and 3m SAAR |
| S04 | Faça a divulgação da confiança do consumidor da França. | French consumer confidence | Headline balance and components, in balance points |
| S05 | Faça a divulgação da inflação da Itália. | Italian inflation | HICP or NIC headline, core and components; YoY and 3m SAAR (seasonal-adjustment rule below) |
| S06 | Faça a divulgação da inflação da zona do euro. | Euro-area inflation | HICP headline, core, energy, food, goods, services; YoY and 3m SAAR |
| S07 | Faça a divulgação do PIB mensal do Reino Unido. | UK monthly GDP | GDP, services, production, manufacturing and construction: YoY and 3m/3m |
| S08 | Faça a divulgação do PIB da Suíça. | Swiss GDP | GDP and expenditure and industry components: q/q, annualised q/q and YoY (with or without the sport-events adjustment) |
| S09 | Faça a divulgação das vendas no varejo da Noruega. | Norwegian retail sales | Total volume and components, YoY and 3m SAAR |
| S10 | Faça a divulgação do desemprego da Suécia. | Swedish unemployment | Unemployment rate (SA, unadjusted or trend) and its 1- and 12-month changes in pp |
| S11 | Faça a divulgação da pesquisa de crédito bancário da zona do euro. | Euro-area Bank Lending Survey | Net percentages for credit standards and demand (firms, house purchase, consumer credit), realised and expected |

## Complex tasks: analytical questions (60-minute limit)

| ID | Request (as sent) | English | Gold-standard answer |
|---|---|---|---|
| C01 | A indústria alemã está se recuperando? Faça um diagnóstico. | Is German industry recovering? Give a diagnosis. | Mixed signals |
| C02 | Como está o consumo das famílias na zona do euro? | How is euro-area household consumption doing? | Moderate (also "weak or losing momentum" for runs that saw September retail data) |
| C03 | Faça um nowcast do PIB da zona do euro. | Nowcast euro-area GDP. | Scored on accuracy against Eurostat's Q3 2026 flash (+0.4% q/q) for runs that nowcast Q3; runs that nowcast Q4 await the Q4 flash |
| C04 | As primeiras estimativas do PIB da Alemanha costumam ser revisadas para cima? | Are first estimates of German GDP usually revised up? | Yes, small upward revisions (positive and significant at horizons of a year or more; computed from Bundesbank real-time vintages) |
| C05 | Como a energia tem afetado o núcleo da inflação da zona do euro? | How has energy affected euro-area core inflation? | Small but positive indirect effect, already visible (distributed-lag estimate: long-run pass-through 0.08, about +0.4 pp on core YoY by autumn 2026) |

The gold answers were set before the verdict pass and are documented with their evidence in [`scoring/c-rubric-v1/gold/NOTES.md`](../scoring/c-rubric-v1/gold/NOTES.md).

## Common context (sent before every request)

Original, in Portuguese, as sent:

> Você trabalha com pesquisa macroeconômica. Use dados públicos, com preferência por fontes oficiais, e entregue em português. Use sempre o último dado disponível; registre a data/hora da coleta e o período da última observação. Busque as séries necessárias e entregue gráficos e tabelas úteis dos principais indicadores, com fontes, dados utilizados e código reproduzível. Para divulgações de inflação, apresente YoY e 3msaar. Para divulgações de atividade, apresente nível dessazonalizado (SA), YoY e 3msaar. Para inflação, 3msaar é a variação do índice SA em três meses anualizada. Para atividade mensal, use a variação entre a média dos últimos três meses e a média dos três meses anteriores, anualizada, conforme a convenção das divulgações do projeto. O 3msaar deve usar série SA; identifique qualquer ajuste sazonal próprio e suas limitações. Para séries trimestrais, identifique a variação trimestral anualizada correspondente; não a apresente como uma série mensal. Não aplique taxas de crescimento sem sentido a saldos, taxas de desemprego ou índices de confiança: preserve suas unidades e explique a adaptação. Identifique períodos, unidades, ajustes e limites da evidência. Não é exigida uma quantidade fixa de gráficos nem uma conclusão predeterminada. Grave a entrega em arquivos na pasta entrega/; dados e código podem ficar em outras pastas deste diretório de trabalho. Não peça intervenção durante a tarefa. Quando não conseguir concluir, entregue a parte verificável e explique o bloqueio. Não leia credenciais nem arquivos de autenticação, não use serviços ou dados pagos e não altere contas, permissões ou configurações externas. Faça a tarefa com o modelo selecionado, em um único agente. Não invoque outros modelos ou CLIs para obter respostas.
>
> Organização visual comum, conforme calibração do usuário em 26/10/2026: em divulgações de atividade, quando pertinente, mostre primeiro o nível total SA, depois as aberturas e por fim as taxas. Prefira um único YoY corretamente identificado, em especial ajustado pelo calendário quando disponível, junto do 3msaar no mesmo gráfico para comparação. Para inflação, combine YoY e 3msaar por abertura; se mostrar os componentes do núcleo (bens industriais não energéticos e serviços), organize-os separadamente de energia e alimentos. Comparações adicionais de YoY entre categorias e de inflação total versus núcleo podem complementar. Não há quantidade fixa de gráficos. Identifique diferenças de ajuste e cobertura sem misturá-las silenciosamente.
>
> Para nowcast, identifique o trimestre corrente na data da execução e diferencie uma estimativa para o trimestre anterior ainda não divulgado. Não apresente estimativa de um trimestre como se fosse de outro. Em análises de revisão, explicite o significado de primeira estimativa e o horizonte posterior; série atual truncada não é um arquivo de vintages históricos. Use sempre a última informação pública disponível e registre a coleta.
>
> PEDIDO: *(the one-sentence request)*

English translation:

> You work in macroeconomic research. Use public data, preferring official sources, and deliver in Portuguese. Always use the latest available data; record the date and time of collection and the period of the last observation. Fetch the series you need and deliver useful charts and tables of the main indicators, with sources, the data used and reproducible code. For inflation releases, present YoY and 3m SAAR. For activity releases, present the seasonally adjusted (SA) level, YoY and 3m SAAR. For inflation, 3m SAAR is the three-month change in the SA index, annualised. For monthly activity, use the change between the average of the last three months and the average of the three months before, annualised. The 3m SAAR must use an SA series; identify any seasonal adjustment of your own and its limits. For quarterly series, give the corresponding annualised quarterly change; do not present it as a monthly series. Do not apply meaningless growth rates to balances, unemployment rates or confidence indices: keep their units and explain the adaptation. Identify periods, units, adjustments and the limits of the evidence. No fixed number of charts and no predetermined conclusion is required. Save the delivery as files in the entrega/ folder; data and code may sit in other folders of this working directory. Do not ask for intervention during the task. If you cannot finish, deliver the verifiable part and explain what blocked you. Do not read credentials or authentication files, do not use paid services or data, and do not change accounts, permissions or external settings. Do the task with the selected model, as a single agent. Do not call other models or CLIs for answers.
>
> Common visual layout: in activity releases, where relevant, show the total SA level first, then the breakdowns, then the rates. Prefer a single, clearly identified YoY, calendar-adjusted where available, next to the 3m SAAR in the same chart. For inflation, combine YoY and 3m SAAR by component; if you show the core components (non-energy industrial goods and services), keep them separate from energy and food. Extra YoY comparisons across categories and of headline against core may complement. No fixed number of charts. Identify differences in adjustment and coverage without silently mixing them.
>
> For a nowcast, identify the current quarter at the run date and distinguish an estimate for the previous quarter not yet released. Do not present an estimate for one quarter as if it were for another. In revision analyses, state what "first estimate" and the later horizon mean; a truncated current series is not an archive of historical vintages. Always use the latest public information and record the collection.
