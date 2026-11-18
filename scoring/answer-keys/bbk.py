"""Read Bundesbank time-series downloads in the two formats agents saved: SDMX-CSV (';', one row
per observation) and the web 'time series' CSV (series key header, 'last update' line)."""
import csv, io, re

ORDER = ('BBK_STD_ADJUSTMENT', 'BBK_DOES_CONCEPT', 'BBK_DOES_CLASSIFICATION', 'BBK_PRICEUNIT', 'BBK_DO_SUFFIX')


def read(path):
    """[(series id 'ADJ.CONCEPT.CLASS.PRICE.SUFFIX', period, value, last_update or None)]"""
    txt = open(path, encoding='utf-8-sig', errors='ignore').read()
    out = []
    if txt.startswith('DATAFLOW;BBK_STD_FREQ'):
        for r in csv.DictReader(io.StringIO(txt), delimiter=';'):
            if r.get('BBK_STD_FREQ') != 'M' or not r.get('OBS_VALUE'):
                continue
            sid = '.'.join(r[c] for c in ORDER)
            out.append((sid, r['TIME_PERIOD'], float(r['OBS_VALUE']), None))
        return out
    first = txt.split('\n', 1)[0]
    keys = re.findall(r'BBDE1\.M\.DE\.([A-Z])\.(\w+)\.(\w+)\.\w\.(\w)\.I21\.(\w)(?!_FLAGS)', first)
    if not keys or '_FLAGS' in first and len(keys) == 0:
        return out
    cols = [c for c in next(csv.reader([first])) ]
    upd = re.search(r'last update,([0-9-]+ [0-9:]+)', txt)
    upd = upd.group(1) if upd else None
    for row in csv.reader(io.StringIO(txt)):
        if not row or not re.fullmatch(r'\d{4}-\d{2}', row[0]):
            continue
        for j, c in enumerate(cols):
            m = re.fullmatch(r'BBDE1\.M\.DE\.([A-Z])\.(\w+)\.(\w+)\.\w\.(\w)\.I21\.(\w)', c)
            if m and j < len(row) and row[j] not in ('', '.'):
                out.append(('.'.join(m.groups()), row[0], float(row[j]), upd))
    return out
