"""Read Eurostat JSON-stat 2.0 files into rows. No network: inputs are the agents' saved downloads."""
import json
from itertools import product


def rows(path):
    """[(dims dict, value)] for every non-missing cell, plus the dataset's 'updated' stamp."""
    d = json.load(open(path))
    ids, sizes = d['id'], d['size']
    cats = []
    for dim in ids:
        index = d['dimension'][dim]['category']['index']
        order = sorted(index, key=index.get) if isinstance(index, dict) else list(index)
        cats.append(order)
    values = d['value']
    get = values.get if isinstance(values, dict) else (lambda k: values[int(k)] if int(k) < len(values) else None)
    out = []
    for flat, combo in enumerate(product(*cats)):
        v = get(str(flat)) if isinstance(values, dict) else get(flat)
        if v is not None:
            out.append((dict(zip(ids, combo)), float(v)))
    return d.get('updated'), out


def is_jsonstat(path, required_dim):
    try:
        d = json.load(open(path))
    except Exception:
        return False
    return isinstance(d, dict) and 'value' in d and required_dim in d.get('dimension', {})
