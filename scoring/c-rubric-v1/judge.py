"""Jev adapter for the C rubric. Every raw response is stored and never re-fetched.

Same API, model pin, image fitting and storage rule as visual-rubric-v1/judge.py (PR #1):
the storage key is the SHA-256 of everything the model sees plus a repeat index it does not see.
Three requests per delivery: 'images' (blocks A-C), 'text' (block E), 'numeric' (block D).
"""
import base64
import hashlib
import html
import io
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

import references as R
import rubric

URL = 'https://api.typesafe.ai/v1/systemone'
MODEL = 'jev-1.14.0'
MIN_SIDE, MAX_SIDE, MAX_PIXELS = 280, 1568, 2_458_624
MAX_REPORT_CHARS = 120_000


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def fit_image(data):
    image = Image.open(io.BytesIO(data))
    width, height = image.size
    scale = min(1.0, MAX_SIDE / max(width, height), (MAX_PIXELS / (width * height)) ** 0.5)
    scale = max(scale, MIN_SIDE / min(width, height)) if min(width, height) < MIN_SIDE else scale
    if scale == 1.0 and image.format == 'PNG':
        return data
    size = (max(MIN_SIDE, int(width * scale)), max(MIN_SIDE, int(height * scale)))
    if max(size) > MAX_SIDE or size[0] * size[1] > MAX_PIXELS:
        raise ValueError(f'Image {width}x{height} cannot be fitted to the API limits')
    out = io.BytesIO()
    image.convert('RGB').resize(size, Image.LANCZOS).save(out, format='PNG', optimize=False)
    return out.getvalue()


def html_text(raw):
    raw = re.sub(r'(?is)<(script|style)\b.*?</\1>', ' ', raw)
    raw = re.sub(r'(?is)<img\b[^>]*>', ' ', raw)
    raw = re.sub(r'(?i)<(br|/p|/div|/h\d|/li|/tr)\b[^>]*>', '\n', raw)
    raw = re.sub(r'(?i)</t[dh]>', ' | ', raw)
    text = html.unescape(re.sub(r'<[^>]+>', ' ', raw))
    return re.sub(r'[ \t]+', ' ', re.sub(r'\n\s*\n+', '\n\n', text)).strip()


def report_files(entrega):
    """Text files of the report: .md, .txt and .html anywhere under entrega/; PDFs only if none exist."""
    files = sorted(p for p in Path(entrega).rglob('*') if p.suffix.lower() in ('.md', '.txt', '.html', '.htm'))
    return files or sorted(Path(entrega).rglob('*.pdf'))


def report_text(entrega):
    parts = []
    for path in report_files(entrega):
        if path.suffix.lower() == '.pdf':
            body = subprocess.run(['pdftotext', '-layout', str(path), '-'], capture_output=True, text=True).stdout
        elif path.suffix.lower() in ('.html', '.htm'):
            body = html_text(path.read_text(errors='replace'))
        else:
            body = path.read_text(errors='replace')
        parts.append(f'### Arquivo: {path.relative_to(entrega)}\n{body.strip()}')
    text = '\n\n'.join(parts)
    return text[:MAX_REPORT_CHARS] + ('\n[... relatório truncado ...]' if len(text) > MAX_REPORT_CHARS else '')


def _assets(image_paths):
    assets, placeholders, images = {}, [], []
    for path in sorted(Path(p) for p in image_paths):
        original = path.read_bytes()
        sent = fit_image(original)
        key = 'IMG_' + sha256(sent)[:16]
        assets[key] = {'type': 'image', 'format': 'png', 'data_base64': base64.b64encode(sent).decode()}
        placeholders.append(key)
        images.append({'file': str(path), 'original_sha256': sha256(original), 'sent_sha256': sha256(sent), 'resized': sent != original})
    return assets, placeholders, images


def build_request(task, request, image_paths=(), report='', refs=None):
    """(body, manifest) for one of the three requests."""
    specs = {q: s for q, s in rubric.questions(task).items() if s['request'] == request}
    assets, placeholders, images = _assets(image_paths) if request in ('images', 'numeric') else ({}, [], [])
    questions = {}
    for qid, spec in specs.items():
        if spec['needs_reference']:
            criteria, _ = R.blind(refs[qid])
            questions[qid] = {'type': 'choice', 'instructions': spec['text'] + R.blind_text(refs[qid]), 'criteria': criteria}
        else:
            questions[qid] = {'type': 'choice', 'instructions': spec['text'], 'criteria': rubric.OPTIONS[spec['kind']]}
    body = {'model': MODEL, 'state': rubric.state_text(task, request, placeholders, report), 'questions': questions}
    if assets:
        body['assets'] = assets
    manifest = {'task': task, 'request': request, 'model_requested': MODEL, 'rubric_version': rubric.VERSION,
                'rubric_sha256': rubric.rubric_hash(task), 'images': images, 'report_sha256': sha256(report.encode()),
                'report_chars': len(report), 'questions_asked': sorted(questions)}
    return body, manifest


def request_key(body, long_context=True):
    canonical = json.dumps({'body': body, 'long_context': long_context}, sort_keys=True, ensure_ascii=False)
    return sha256(canonical.encode())


def post(body, long_context=True, timeout=300):
    headers = {'Content-Type': 'application/json'}
    if 'assets' in body:
        headers['TypeSafe-Danger-Zone-Images'] = 'true'
    if long_context:
        headers['TypeSafe-Danger-Zone-Long-Context'] = 'true'
    if os.environ.get('JEV_API_KEY'):
        headers['Authorization'] = 'Bearer ' + os.environ['JEV_API_KEY']
    request = urllib.request.Request(URL, data=json.dumps(body).encode(), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        raise RuntimeError(f'Jev HTTP {error.code}: {error.read().decode(errors="replace")[:500]}') from None


def judge(body, manifest, store, repeat=0, long_context=True, call=post):
    """Stored record for (request, repeat); calls the model only if that record does not exist."""
    key = request_key(body, long_context)
    path = Path(store) / key / f'r{repeat}.json'
    if path.exists():
        return json.loads(path.read_text())
    response = call(body, long_context)
    record = {'request_sha256': key, 'repeat': repeat, **manifest, 'long_context': long_context, 'response': response}
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('x') as handle:
            json.dump(record, handle, ensure_ascii=False, indent=1, sort_keys=True)
    except FileExistsError:  # an identical request from another cell (e.g. two no-op A4 snapshots) stored it first
        return json.loads(path.read_text())
    return record


def answers(record):
    return {qid: a['probabilities'] for qid, a in record['response']['answers'].items()}
