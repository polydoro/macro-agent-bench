You are checking economic charts for one narrow fact: is a specific number PRINTED on the chart?

For each delivery folder listed below:
1. Read `questions.json`. Each question names a series (in Portuguese), a period (e.g. 2026-08 = August 2026; 2026-Q3 = third quarter) and a unit.
2. Open every image `imgN.png` in the folder with the Read tool. Look at all of them.
3. For each question decide whether the chart PRINTS, as digits, the value of that series at exactly that period. It counts as printed ONLY if the number appears as text: a data label on/next to a bar or line end, a cell in a table, an annotation, or a title/subtitle/caption sentence. It does NOT count if you would have to estimate it from the axis, gridlines, bar length or line position, however clearly. A number for another period, another series, or another transformation (e.g. level instead of YoY, m/m instead of YoY, 3m moving average instead of 3m/3m SAAR) does not count. Any one of the admitted series listed counts as the right series.
4. Write `result.json` in that folder: a JSON list, one object per question:
   {"id": "<question id>", "printed": "yes" | "no" | "unclear", "value": <the printed number as a float, or null>, "values": [<every printed number that matches an admitted series at that period, as floats>], "where": "<imgN and where on it, or why not>"}
   Use "unclear" only if digits are printed but you cannot read them reliably (tiny, overlapping, cut off).

Be literal and strict. Do not guess values. Do not use any knowledge of economic data. Work folder by folder; write each result.json before moving on. When done, reply with one line per folder: code and counts of yes/no/unclear.
