"""C04 answer key: revisions to German real GDP growth from the Bundesbank real-time database (BBKRT).

Source: series BBKRT Q.DE.Y.A.AG1.CA010.A.I (price-adjusted GDP, seasonally and calendar adjusted,
index), one column per release ("vintage"), as saved by agents during their runs. Every saved
copy listed in SOURCES must agree cell by cell on the vintages they share, or the build stops.

For each cell the key uses only vintages published before the cell's submitted_at_utc
(receipt.json), so a run never gets credit or blame for a release it could not see.

Definitions (computed here, not taken from any agent):
- growth, two measures: q/q % change of the index within one vintage, 100*(x_t/x_t-1 - 1), and
  YoY % change, 100*(x_t/x_t-4 - 1) (Destatis publishes its own revision statistics on YoY rates).
- first estimate: the first vintage that contains the quarter, if published within 120 days of
  the quarter's end. Quarters before 2005-Q1 have no genuine first estimate in BBKRT (the
  database starts on 2005-05-12) and are excluded.
- revision at horizon h: growth in the later vintage minus growth in the first, in pp.
  Horizons by release count (next release, 4, 8 and 12 releases later) and by elapsed time
  (latest vintage within 92, 365, 730 and 1095 days), plus the latest vintage available.
- samples: 2005-2019, 2005-latest without 2020-21, 2005-latest.

Usage: python build_c04.py  (writes C04-key.csv and C04-cells.csv next to this file)
"""
import csv
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
REPO = HERE.parent.parent
C04 = REPO / 'execucoes'
SOURCES = [  # BBKRT Q.DE.Y.A.AG1.CA010.A.I saved by agents, one per arm plus cross-checks
    'pilot-one-c04-low-normal-20261028-v21/attempts/one-c04-claude-opus-primary/work/dados/bbkrt_pib_sa_vintages.csv',
    'pilot-one-c04-low-normal-20261028-v21/attempts/one-c04-claude-opus-primary/work/entrega/dados_bbkrt_vintages_pib.csv',
    'pilot-a2-c04-high-normal-20261101-v1/attempts/a2-c04-claude-opus-high-normal-primary/work/data/vintages_gdp_Y_A_I.csv',
    'pilot-a3-c04-low-normal-20261105-v1/attempts/a3-c04-claude-sonnet-low-normal-primary/work/dados/bbkrt_Y_A_I.csv',
]
HORIZONS = {  # name: (kind, amount)
    'next_release': ('releases', 1), 'r4_releases': ('releases', 4), 'r8_releases': ('releases', 8),
    'r12_releases': ('releases', 12), 'd92': ('days', 92), 'd365': ('days', 365), 'd730': ('days', 730),
    'd1095': ('days', 1095), 'latest': ('latest', None),
}
HORIZON_GROUP = {'next_release': 'short', 'd92': 'short', 'r4_releases': 'one_year', 'd365': 'one_year',
                 'r8_releases': 'two_years', 'd730': 'two_years', 'r12_releases': 'three_years', 'd1095': 'three_years',
                 'latest': 'latest'}
MEASURES = {'qoq': 1, 'yoy': 4}  # lag in quarters
SAMPLES = {'2005-2019': lambda y: 2005 <= y <= 2019, '2005-latest ex 2020-21': lambda y: y >= 2005 and y not in (2020, 2021),
           '2005-latest': lambda y: y >= 2005}


def read_vintages(path):
    """Quarter x vintage-date matrix of index levels from a BBKRT CSV in any of the saved layouts."""
    text = path.read_text(encoding='utf-8-sig')
    sep = ';' if text.split('\n', 1)[0].count(';') > text.split('\n', 1)[0].count(',') else ','
    raw = pd.read_csv(path, sep=sep, index_col=0, dtype=str, encoding='utf-8-sig')
    raw = raw[raw.index.astype(str).str.fullmatch(r'\d{4}-Q[1-4]')]
    dates = pd.to_datetime(raw.columns, format='%d.%m.%Y' if '.' in raw.columns[0] else '%Y-%m-%d')
    values = raw.apply(lambda c: pd.to_numeric(c.str.replace(',', '.', regex=False), errors='coerce'))
    values.columns = dates
    return values


def merged_matrix():
    frames = [(s, read_vintages(C04 / s)) for s in SOURCES]
    merged = frames[0][1]
    for source, frame in frames[1:]:
        common_cols = merged.columns.intersection(frame.columns)
        common_rows = merged.index.intersection(frame.index)
        a, b = merged.loc[common_rows, common_cols], frame.loc[common_rows, common_cols]
        bad = ((a - b).abs() > 1e-9) & a.notna() & b.notna() | (a.isna() != b.isna())
        if bad.values.any():
            raise SystemExit(f'{source}: {int(bad.values.sum())} cells disagree with earlier copies')
        merged = merged.combine_first(frame)
    return merged.sort_index(axis=1), frames


def revisions(levels, lag=1):
    """One row per quarter with a genuine first estimate: first growth and revision at each horizon."""
    growth = levels.pct_change(lag, axis=0, fill_method=None) * 100
    rows = []
    for quarter in growth.index:
        series = growth.loc[quarter].dropna()
        if series.empty:
            continue
        first_date = series.index[0]
        quarter_end = pd.Period(quarter.replace('-', ''), 'Q').end_time
        if (first_date - quarter_end).days > 120:
            continue
        row = {'quarter': quarter, 'year': int(quarter[:4]), 'first_vintage': first_date.date().isoformat(),
               'first': series.iloc[0]}
        for name, (kind, amount) in HORIZONS.items():
            later = None
            if kind == 'releases' and len(series) > amount:
                later = series.iloc[amount]
            elif kind == 'days' and series.index[-1] >= first_date + pd.Timedelta(days=amount):
                later = series[series.index <= first_date + pd.Timedelta(days=amount)].iloc[-1]
            elif kind == 'latest' and len(series) > 1:
                later = series.iloc[-1]
            row[name] = None if later is None else later - series.iloc[0]
        rows.append(row)
    return pd.DataFrame(rows)


def stats(rev, sample, horizon):
    mask = rev['year'].map(SAMPLES[sample])
    values = rev.loc[mask, horizon].dropna().astype(float).round(2)
    n = len(values)
    if n == 0:
        return None
    return {'n': n, 'mean': round(values.mean(), 4), 'median': round(values.median(), 4),
            'share_up': round((values > 0).mean() * 100, 1), 'share_zero': round((values == 0).mean() * 100, 1),
            'share_down': round((values < 0).mean() * 100, 1)}


def cell_cutoffs():
    out = []
    for receipt in sorted(C04.glob('pilot-*-c04-*/attempts/*/receipt.json')):
        data = json.loads(receipt.read_text())
        out.append({'attempt': receipt.parent.name, 'campaign': receipt.parent.parent.parent.name,
                    'submitted_at_utc': data['submitted_at_utc']})
    return out


def main():
    levels, frames = merged_matrix()
    cutoffs = sorted({pd.Timestamp(c['submitted_at_utc']).tz_convert(None).normalize() for c in cell_cutoffs()})
    keys, last_by_cutoff = [], {}
    for cutoff in cutoffs:
        visible = levels.loc[:, levels.columns < cutoff].dropna(axis=1, how='all')
        last = visible.columns[-1].date().isoformat()
        if last in last_by_cutoff.values():
            last_by_cutoff[cutoff] = last
            continue
        last_by_cutoff[cutoff] = last
        for measure, lag in MEASURES.items():
            rev = revisions(visible, lag)
            for sample in SAMPLES:
                for horizon in HORIZONS:
                    s = stats(rev, sample, horizon)
                    if s:
                        keys.append({'last_vintage': last, 'measure': measure, 'sample': sample, 'horizon': horizon,
                                     'horizon_group': HORIZON_GROUP[horizon], **s})
    with (HERE / 'C04-key.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(keys[0]))
        writer.writeheader()
        writer.writerows(keys)
    with (HERE / 'C04-cells.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['campaign', 'attempt', 'submitted_at_utc', 'last_vintage'])
        writer.writeheader()
        for c in cell_cutoffs():
            day = pd.Timestamp(c['submitted_at_utc']).tz_convert(None).normalize()
            writer.writerow({**c, 'last_vintage': last_by_cutoff[day]})
    print('sources:', ', '.join(f'{s.split("/attempts/")[1].split("/")[0]} ({f.shape[1]} vintages)' for s, f in frames))
    print('vintages merged:', levels.shape[1], levels.columns[0].date(), '->', levels.columns[-1].date())
    print('last vintage by cutoff:', {k.date().isoformat(): v for k, v in last_by_cutoff.items()})


if __name__ == '__main__':
    main()
