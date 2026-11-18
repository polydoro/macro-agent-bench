"""Copied from PR #1 visual-rubric-v1/code_check.py (S tasks) and extended for C01, C02, C03, C05.

Numeric correctness checked in code against the answer key (the author, 2026-11-17: split the 40 points).

For each delivery, read the tables the agent wrote (CSV/XLSX under work/, raw downloads excluded).
A question is correct when some saved cell
  - is labelled as the question's series (role keywords, after removing "ex-..." phrases),
  - is labelled with the question's transformation (YoY, 3m SAAR, q/q; none for native units),
  - sits on a row (or under a header) for the reference period, when the table states periods,
  - and equals an admitted variant within its tolerance.
Labels come from the cell's column header and the non-numeric cells of its row, which covers
wide time series, long tables and summary tables. Every match is recorded as evidence.
"""
import csv
import glob
import re
from pathlib import Path

csv.field_size_limit(10 ** 9)
REPO = Path(__file__).parent.parent.parent
RAW = re.compile(r'(^|/)(raw|bruto|brutos|downloads?|cache)(/|_|\.|$)|_bruto|_raw\b|raw_', re.I)

MONTHS = {}
for i, names in enumerate([
        'jan janeiro january janvier januar enero gennaio', 'feb fev fevereiro february fevrier février februar febrero febbraio',
        'mar marco março march mars marz märz marzo', 'apr abr abril april avril aprile', 'may mai maio mayo maggio',
        'jun junho june juin juni junio giugno', 'jul julho july juillet juli julio luglio',
        'aug ago agosto august aout août', 'sep set setembro september septembre septiembre settembre',
        'oct out outubro october octobre oktober octubre ottobre okt', 'nov novembro november novembre noviembre',
        'dec dez dezembro december decembre décembre dezember diciembre dicembre'], 1):
    for n in names.split():
        MONTHS[n] = i


def periods(text):
    """Normalised period tokens in a string: 'YYYY-MM' and 'YYYYQn'."""
    s = text.lower()
    out = set()
    for y, m in re.findall(r'((?:19|20)\d\d)[-/.m]?(0[1-9]|1[0-2])(?![\d])', s):
        out.add(f'{y}-{m}')
    for m, y in re.findall(r'\b(0?[1-9]|1[0-2])[/.-]((?:19|20)\d\d)\b', s):
        out.add(f'{y}-{int(m):02d}')
    for name, y in re.findall(r'([a-zçéû]{3,10})\.?[\s/_-]*((?:19|20)\d\d)', s):
        if name in MONTHS:
            out.add(f'{y}-{MONTHS[name]:02d}')
    for y, name in re.findall(r'((?:19|20)\d\d)[\s/_-]+([a-zçéû]{3,10})\b', s):  # '1998 AUG' (ONS)
        if name in MONTHS:
            out.add(f'{y}-{MONTHS[name]:02d}')
    for y, q in re.findall(r'((?:19|20)\d\d)[\s_-]*[qt]([1-4])\b', s):
        out.add(f'{y}Q{q}')
    for q, y in re.findall(r'\b[qt]([1-4])[\s/_-]*((?:19|20)\d\d)', s) + re.findall(r'\b([1-4])\s*[qt]\s*((?:19|20)\d\d)', s):
        out.add(f'{y}Q{q}')
    return out


def period_ok(tokens, ref_periods, quarterly):
    if quarterly:
        tokens = {t if 'Q' in t else f'{t[:4]}Q{(int(t[5:7]) - 1) // 3 + 1}' for t in tokens}
    else:
        if tokens and all('Q' in t for t in tokens):
            return False  # a quarterly row cannot carry a monthly reference
        tokens = {t for t in tokens if 'Q' not in t}
    return None if not tokens else bool(tokens & ref_periods)


# official files saved as downloaded: they show what the source published, not what the agent reported
OFFICIAL = re.compile(r'^(mgdp\.(csv|xlsx)|monthlygdptables.*|260_ir_camme.*|icm\d{4}.*\.xlsx|ine_icm\d+.*\.xlsx|t60\d{3}\.csv|serie\d\d_\d{4}\.xlsx|qna_.*\.xlsx|ons_mgdp_.*\.xlsx|.*_anexo\.xlsx|tabla\d.*\.csv)$', re.I)
EXCL = re.compile(r'\b(ex|excl\w*|exceto|excluding|sem|sin|senza|ohne|hors|without)[-.\s]+(\w+)([\s,]+(e|y|and|und|et|,)\s+\w+)*', re.I)
TR = {
    'yoy': r'yoy|y/y|a/a|\b12\s?m|12.?meses|12.?month|interanual|tendenzial|vorjahr|\bvj|year|\bano\b|ano.?anterior|var.?12|pct.?12|_12\b|g12|annual.?rate|taxa.?anual(?!iz)|glissement',
    'saar': r'saar|3m|3\s?m[eê]s|anualiz|annuali[sz]|annualis',
    'qoq': r'qoq|q/q|t/t|(?<![a-z])t_t(?![a-z])|var.?trim|\bqq\b|trimestr|quarter|vorquartal|\btri\b|qoq_ann|qtr',
}
ANYTR = re.compile('|'.join(TR.values()) + r'|m/m|mom\b|var|diff|change|delta|Δ|cresc|growth', re.I)

ROLES = {
    'S01': [('consumo_nao_duraveis', r'n[aã]o.?dur|non.?dur|ndcog|a2p340000'), ('consumo_duraveis', r'dur[aá]v|durable|\bdcog|a2p330000'),
            ('total', r'^ind\b|\btotal\b|\bb ?[-–] ?d\b|\bb ?[-–] ?f\b|a2p000000|a2p100000|a2p300000|produzierend|\bb c\b|ind[uú]stria \(?ex|ind[uú]stria total|industri\w* (sem|ex|ohne|excl)'),
            ('skip', r'intensiv|energointens|ramos'),
            ('intermediarios', r'intermed|mig.ing|vorleist|a2p310000'), ('capital', r'capital|mig.cag|investitionsg|a2p320000'),
            ('consumo', r'consum|mig.cog|konsum|a2p330000|a2p340000'), ('energia', r'energ|mig.nrg|\bnace d\b|a2p500000'), ('construcao', r'constru|bauge|\bbau\b|n2f000000'),
            ('energia', r'^\W*d\W*$|\(d\)'), ('construcao', r'^\W*f\W*$|\(f\)'),
            ('total', r'produ[cç][aã]o industrial|industrial production|\bip\b|b.?-?d')],
    'S02': [('domestico', r'dom[eé]st|inland|intern|aeb1'), ('externo', r'extern|ausland|exterior|foreign|aeb5'),
            ('total', r'total|gesamt|aea1|encomendas|orders|auftrag')],
    'S03': [('resto', r'resto|no.?aliment|n[aã]o.?aliment|non.?food'), ('alimentacion', r'aliment|food'),
            ('equipo_personal', r'personal|pessoal'), ('equipo_hogar', r'hogar|\blar\b|household'),
            ('grandes_superficies', r'superf'), ('pequenas_cadenas', r'peque|small.?chain'), ('grandes_cadenas', r'grandes.?(cad|rede)|large.?chain'),
            ('unilocalizadas', r'unilocal|loja.?[uú]nica|single.?(retail|store)'), ('skip', r'eess|estaci|servi[cç]e?o?s? station'), ('total', r'general|geral|total|[ií]ndice|retail|varejo')],
    'S04': [('situacao_financeira_passada', r'(situa|finan[cç]).*(pass|past)'), ('situacao_financeira_futura', r'(situa|finan[cç]).*(futur|perspect)'),
            ('nivel_vida_futuro', r'niveau de vie|n[ií]vel( de)? vida|padr[aã]o de vida|standard of living'), ('compras_importantes', r'achat|compra|purchase'),
            ('capacidade_poupanca', r'[ée]pargne|poupan|poupar|saving'), ('desemprego_esperado', r'ch[oô]mage|desempreg|unemploy'),
            ('precos', r'prix|pre[cç]o|price|infla'), ('total', r'synth|\bisc\b|confian|indicateur|indicador|confidence|total')],
    'S07': [('skip', r'manufact|ecy6|manufat'), ('servicos', r'serv|ecyc'), ('construcao', r'constru|ecy9'),
            ('producao', r'produ[cç]|production|ecy4|industri'), ('total', r'gdp|pib|ecy2|total|gva|vab')],
    'S08': [('consumo_familias', r'privad|fam[ií]l|household|private|p31|konsum|cons.priv'), ('consumo_governo', r'govern|p3.s13|[ée]tat|staat|p3s13'),
            ('investimento', r'invest|\binv\b|fbcf|gfcf|p51|anlage'), ('exportacoes', r'export|\bp6'), ('importacoes', r'import|\bp7'),
            ('industria', r'ind[uú]str|manufat|manufact|\bmanu\b|transforma|noga 10|qu[ií]mic|chem'), ('servicos', r'servi|noga [4-9]|com[eé]rcio|financ|sa[uú]de|hotel|transport'),
            ('total', r'pib|gdp|b1gq|\bbip\b|total')],
    'S09': [('alimentos', r'aliment|food|47\.[12]|dagligvare|n[æae]rings'), ('combustivel', r'combust|fuel|drivstoff|47\.3'),
            ('equipamentos_domesticos', r'dom[eé]stic|household|47\.[45]|equip|elektr|\bikt\b|tecnolog'), ('cultura_lazer', r'cultur|lazer|leisure|47\.6|kultur|fritid'),
            ('outros_bens', r'outros|other|47\.7|vestu|farm|apotek|cosm'), ('internet', r'internet|online|47\.9(?!\d)|correspond|netthandel|e-?commerce|fora de lojas|utenfor butikk|non.?store'),
            ('total', r'total|varejo|retail|47(?![.\d])|detaljhandel|varehandel|vendas')],
    'S10': [('skip', r'registr|arbetsf[oö]rmed'), ('total', r'desemp|unemploy|arbetsl|taxa|rate|\baku\b|\blfs\b|ledighet')],
    'S05': [('nucleo', r'n[uú]cleo|core|xef|tot.x.nrg.food|nucleo|esclus'), ('bens_nao_energeticos', r'n[aã]o.?energ|non.?energ|neig|igd.nnrg|igxe|bens.?ind|beni.?ind'),
            ('servicos', r'servi|serv\b|serv_|serv00'), ('alimentos', r'aliment|food|alim'), ('energia', r'energ|nrg'),
            ('total', r'total|cheio|headline|hicp|ipca|\bnic\b|generale|all.?items|000000|cp00|geral')],
}
ROLES['S06'] = ROLES['S05']
# C tasks (2026-11-17, gold standard). Question ids map to (role, transform) in C_TARGETS below.
ROLES['C01'] = [('skip', r'exterior|extern|ausland|inland|dom[eé]st|interno|\(\d\d\)|equip|grandes|large'),
                ('ord', r'encomend|pedido|order|auftr|a2p300000|aea1|neworder'),
                ('skip', r'energ|constru|bau|intermed|capital|consum|mig|vorleist|investitionsg|ramo|setor|sector|\bc\d\d|nace c\d|auto|qu[ií]m|chem|metal|m[aá]quin'),
                ('prod', r'produ|output|\bip\b|b.?-?d|b_c|manufat|manufact|industri|a2p100000|a2p000000|verarbeit')]
ROLES['C02'] = [('skip', r'aliment|food|combust|fuel|g47\d|g4[5-6]|vestu|cloth|online|internet|n[aã]o.?aliment|non.?food'),
                ('sav', r'poupan|saving|sparquote|srg'), ('conf', r'confian|confidence|sentiment|bs.?csmci|consumer conf'),
                ('ret', r'varej|retail|vendas|g47|trtu|einzelhandel|com[eé]rcio'),
                ('cons', r'consumo|consumption|p31|despesa|household|fam[ií]lia')]
ROLES['C03'] = [('skip', r'cen[aá]rio|scenario|choque|shock|nowcast|estimat|previs|proje|forecast|ponte|bridge|fitted'),
                ('last', r'pib|gdp|b1gq|bip|produto')]
ROLES['C05'] = ROLES['S06']
C_TARGETS = {'N_prod_yoy': ('prod', 'yoy'), 'N_prod_3m': ('prod', '3m'), 'N_ord_yoy': ('ord', 'yoy'), 'N_ord_3m': ('ord', '3m'),
             'N_cons_qoq': ('cons', 'qoq'), 'N_cons_yoy': ('cons', 'yoy'), 'N_ret_yoy': ('ret', 'yoy'), 'N_ret_3m': ('ret', '3m'),
             'N_conf': ('conf', 'native'), 'N_sav': ('sav', 'native'), 'N_last_qoq': ('last', 'qoq'), 'N_last_yoy': ('last', 'yoy'),
             'N_energy_yoy': ('energia', 'yoy'), 'N_core_yoy': ('nucleo', 'yoy'), 'N_energy_3m': ('energia', '3m'), 'N_core_3m': ('nucleo', '3me')}


def role_of(task, text):
    text = text.replace('_', ' ')
    s = EXCL.sub(' ', text.lower()) if task not in ('S05', 'S06', 'C05') else re.sub(r'\b(ex|excl\w*|exceto|sem|senza)[-.\s]+(energ\w*|aliment\w*|food)([\s,]+(e|and|,)\s+\w+)*', ' core ', text.lower())
    if task == 'S11':
        if re.search(r'esper|expect|\bf3\b|\.f3\.|futur|previs|next', s):
            return None
        # factor rows, single countries, firm-size or maturity splits and ad hoc questions are not the aggregate
        if re.search(r'fator|factor|posi[cç][aã]o de capital|liquidez|liquidity|concorr|competi|risco|\brisk|custo|\bcost|situa[cç][aã]o econ|perspectiv|outlook|'
                     r'capacidade|juros|interest|confian|confidence|solv[eê]n|toler|\b(cp|lp|mf|gea|ifo|rto|hmp|cwb|gli|ccf)\b|alemanha|germany|espanha|spain|'
                     r'fran[cç]a|france|it[aá]lia|italy|holanda|netherlands|\bpmes?\b|\bsmes?\b|grandes|large|curto prazo|longo prazo|short.?term|long.?term|ad.?hoc', s):
            return None
        seg = 'emp' if re.search(r'empres|firm|enterpr|\bnfc|\bsnf|corpor|o\.e\.z|companies|business', s) else \
              'hab' if re.search(r'habita|housing|hous|mortgage|imobili|h\.h\.|casa', s) else \
              'con' if re.search(r'consum|consumer|h\.c\.|\bcc\b', s) else None
        con = 'pad' if re.search(r'padr|standard|crit[eé]r|st\.s|aperto|tighten', s) else 'dem' if re.search(r'demand|procura|zz\.d', s) else None
        return {('emp', 'pad'): 'total', ('emp', 'dem'): 'demanda_empresas', ('hab', 'pad'): 'padroes_habitacao', ('hab', 'dem'): 'demanda_habitacao',
                ('con', 'pad'): 'padroes_consumo', ('con', 'dem'): 'demanda_consumo'}.get((seg, con))
    for role, rx in ROLES[task]:
        if re.search(rx, s):
            return None if role == 'skip' else role
    return None


def transform_ok(qtr, text):
    s = text.lower()
    if qtr == 'native':
        return not ANYTR.search(s) or bool(re.search(r'n[ií]vel|level|saldo|balance|net|l[ií]quido|taxa de desemp|rate', s)) and not re.search(TR['yoy'] + '|' + TR['saar'], s)
    if qtr in ('3m', '3me'):
        return bool(re.search(TR['saar'], s)) and not re.search(r'6m|nsa(?![a-z])|sem ajuste|unadjust|n[aã]o.?ajust', s) if qtr == '3me' else bool(re.search(TR['saar'], s))
    if qtr == 'growth':
        return bool(re.search(TR['yoy'] + '|' + TR['qoq'], s))
    if qtr == 'qoq':
        return bool(re.search(TR['qoq'], s)) and not re.search(TR['yoy'], s)
    return bool(re.search(TR['yoy'], s)) and not re.search(r'saar|3m', s)


def num(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    t = str(x).strip().replace('%', '').replace('+', '').replace('−', '-').strip()
    if re.fullmatch(r'-?\d+,\d+', t):
        t = t.replace(',', '.')
    try:
        return float(t)
    except ValueError:
        return None


def grids(path):
    if path.endswith('.csv') or path.endswith('.tsv'):
        txt = open(path, encoding='utf-8-sig', errors='ignore').read(20_000_000)
        try:
            dialect = csv.Sniffer().sniff(txt[:5000], delimiters=',;\t|')
        except csv.Error:
            dialect = csv.excel
        yield list(csv.reader(txt.splitlines(), dialect))
    elif path.endswith('.xlsx'):
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        for ws in wb.worksheets:
            ws.reset_dimensions()
            yield [list(r) for r in ws.iter_rows(values_only=True, max_row=20000)]


def candidate_files(workdir):
    files = []
    for ext in ('csv', 'tsv', 'xlsx'):
        files += glob.glob(f'{workdir}/**/*.{ext}', recursive=True)
    out = []
    for p in sorted(files):
        rel = p[len(str(workdir)) + 1:]
        if RAW.search(rel) or OFFICIAL.search(rel.split('/')[-1]) or '/fontes/' in f'/{rel}':
            continue
        try:
            head = open(p, errors='ignore').read(3000) if not p.endswith('.xlsx') else ''
        except OSError:
            continue
        if 'OBS_VALUE' in head or 'DATAFLOW' in head or head.startswith('"Series ID'):
            continue  # official SDMX download
        out.append((p, rel))
    return out


def check(task, workdir, refs, ref_period):
    """{qid: evidence or None}. refs: {qid: reference with variants}. ref_period: one period or a set (A4: seed or newer)."""
    ref_period = {ref_period} if isinstance(ref_period, str) else set(ref_period)
    ref_period = {p.replace('-Q', 'Q') for p in ref_period}
    quarterly = any('Q' in p for p in ref_period)
    want = ref_period
    if task == 'S11':
        want = {'2026Q4', '2026Q3'}
    cands = {q: [] for q in refs}
    targets = {}
    for q in refs:
        if task.startswith('C'):
            targets[q] = C_TARGETS[q]
            continue
        parts = q[2:].rsplit('_', 1)  # N_<role>_<transform> or X_<role>_<transform>
        targets[q] = (parts[0], parts[1])
    for path, rel in candidate_files(workdir):
        try:
            gs = list(grids(path))
        except Exception:
            continue
        for g in gs:
            if not g:
                continue
            width = max(len(r) for r in g)
            # header: rows before the first row holding a number in a column other than the first
            hdr_rows = []
            for r in g[:4]:
                if any(num(c) is not None for c in r):
                    break
                hdr_rows.append(r)
            header = [' '.join(str(h[j]) for h in hdr_rows if j < len(h) and h[j] not in (None, '')) for j in range(width)]
            for r in g[len(hdr_rows):]:
                texts = [str(c) for c in r if c not in (None, '') and num(c) is None]
                if r and re.fullmatch(r'\d\d(\.\d{1,2})?', str(r[0]).strip()):  # leading NACE-style code (47.9) labels the row
                    texts.insert(0, f'nace {str(r[0]).strip()}')
                rowtxt = ' '.join(texts)
                ptoks = periods(rowtxt)
                for j, c in enumerate(r):
                    v = num(c)
                    if v is None:
                        continue
                    h = header[j] if j < len(header) else ''
                    pok = period_ok(ptoks, want, quarterly)
                    if pok is None:
                        pok = period_ok(periods(h), want, quarterly)
                    if pok is False:
                        continue
                    ctx = f'{h} | {rowtxt}'
                    if task in ('C01', 'C02', 'C03') and ROLES[task][0][0] == 'skip' and \
                            re.search(ROLES[task][0][1], (ctx + (' ' + Path(rel).stem if task == 'C03' and re.search(r'cen[aá]rio|scenario', rel.lower()) else '')).replace('_', ' ').lower()):
                        continue  # sub-series, scenario or nowcast rows are never the headline number
                    role = (role_of(task, h) or role_of(task, rowtxt) or role_of(task, Path(rel).stem)) if task != 'S11' else (role_of(task, ctx) or role_of(task, f'{ctx} {Path(rel).stem}'))
                    if role is None:
                        continue
                    for q, (qrole, qtr) in targets.items():
                        if qrole != role or not transform_ok(qtr, ctx):
                            continue
                        hit = next((label for label, ref, tol in refs[q]['variants'] if abs(v - ref) <= tol + 1e-9), None)
                        if not hit and len(cands[q]) >= 50:  # cap the misses only: a long table must not crowd out a hit
                            continue
                        cands[q].append({'file': rel, 'header': h[:100], 'row': rowtxt[:100], 'value': round(v, 4),
                                         'variant': hit, 'period_stated': pok is not None})
    out = {}
    for q, cs in cands.items():
        hits = [c for c in cs if c['variant']]
        misses = [c for c in cs if not c['variant']]
        status = 'none' if not cs else 'fail' if not hits else 'ambiguous' if misses else 'auto'
        out[q] = {'status': status, 'correct': bool(hits), 'evidence': hits[:3], 'conflicts': misses[:3]}
    if 'X_consumo_duraveis_yoy' in out and 'N_consumo_yoy' in out and not out['N_consumo_yoy']['correct']:
        a, b = out['X_consumo_duraveis_yoy'], out['X_consumo_nao_duraveis_yoy']
        if a['correct'] and b['correct']:
            out['N_consumo_yoy'] = {'status': 'auto', 'correct': True, 'evidence': a['evidence'][:1] + b['evidence'][:1], 'conflicts': [],
                                    'note': 'shown as durables and non-durables, both match'}
    return {q: v for q, v in out.items() if q.startswith('N_')}
