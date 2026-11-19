# Worked example: Spanish industrial turnover

One of the 16 worked examples used in the "with examples" method, published exactly as the agents received it. The four files are byte-identical to the originals (SHA-256 below). The other 15 are not published.

**Where it was used.** In six of the eleven simple tasks (S01 German industrial production, S02 German factory orders, S03 Spanish retail sales, S07 UK monthly GDP, S08 Swiss GDP, S09 Norwegian retail sales), together with a second example on Swedish household consumption. The agent found both in `/work/EXEMPLOS/` with the note that the request is a different task (see [docs/methods.md](../../docs/methods.md)).

**Origin.** A chart from my own day-to-day work, made with an earlier AI model and refined over time. Data: INE (Spain), industrial turnover index, seasonally and calendar adjusted, latest observation August 2026. INE data are reused with attribution.

## The files

| File | What it is |
|---|---|
| `pedido.txt` | The one-line request the example answers |
| `figura.png` | The finished chart: level of manufacturing and mining turnover, then manufacturing YoY and 3m SAAR in one panel |
| `solucao.txt` | The note on how to build and read it |
| `dados_e_calculos.csv` | Not a data table: an inventory of the two source charts the figure was made from (file names and hashes). No example in the library carried its numbers |

## English translation

**pedido.txt**: Short example: Spanish industrial turnover. Show the charts and explain the reading, the units, the frequency and the relevant limits.

**solucao.txt**:

> Spanish industrial turnover
>
> Show the level first, then YoY and 3m SAAR in the same manufacturing panel. Industrial turnover can reflect prices; do not call it production volume or retail sales. Sources, scope and date must go with the product.
>
> Source and period: INE Spain; industrial turnover index, seasonally and calendar adjusted series, base shown on the chart. Historical snapshot from the repository.
>
> Limits: a comparison of form and interpretation; it is not the held-out release of German orders or Spanish retail.
>
> Historical presentation example. Do not copy its values or conclusions into the new task. No claim of a top score, scientific review or untouched holdout.

## Integrity

| File | Bytes | SHA-256 |
|---|---:|---|
| `pedido.txt` | 144 | `d18d723229cd6d385cf6a71173d2cc81892b1c20329b37821ee8fc5bd39e8e5a` |
| `solucao.txt` | 738 | `cd7e86a53d447c7a344f872f6e25afe1b415e9b3d2eed2ecb98e658944152057` |
| `dados_e_calculos.csv` | 384 | `614ca29e8ffed1aa08c67c3995f9258f6f8eb2a7fd16c417458bb146c2de3ad8` |
| `figura.png` | 414,904 | `9f2e610118bb3ab2b4a6a745b2383ffa33e601e89b56879e147fe1a726bee525` |
