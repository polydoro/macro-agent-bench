"""Jev (TypeSafe System One) adapter. Every raw response is stored and never re-fetched.

The stored response is the unit of record: a score is reproduced by reading it back,
not by calling the model again. The storage key is the SHA-256 of everything the model
sees (model id, state, questions, image bytes as sent) plus a repeat index that the
model does not see.

API shape taken from docs.typesafe.ai on 2026-11-16: POST /v1/systemone with
{model, state, questions, assets}; choice questions carry `instructions` and
`criteria` {option: description}; answers carry `choice`, `confidence`, `probabilities`.
Image input is experimental at TypeSafe and needs an opt-in header.
"""
import base64
import hashlib
import io
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

import rubric
from references import blind as blind_reference, blind_text

URL = 'https://api.typesafe.ai/v1/systemone'
MODEL = 'jev-1.14.0'  # pinned; aliases such as jev-latest move between releases
MIN_SIDE, MAX_SIDE, MAX_PIXELS = 280, 1568, 2_458_624  # TypeSafe image limits; out-of-range images are rejected


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def fit_image(data):
    """PNG bytes within the API limits. Unchanged if already inside them, else resized with a fixed filter."""
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


def build_request(task, image_paths, references=None, kinds=None):
    """(request body, manifest). Questions that need a reference are left out unless one is supplied.
    kinds limits the request to those question kinds (the numeric pass asks only 'numeric')."""
    references = references or {}
    assets, placeholders, images = {}, [], []
    for path in sorted(Path(p) for p in image_paths):
        original = path.read_bytes()
        sent = fit_image(original)
        key = 'IMG_' + sha256(sent)[:16]
        assets[key] = {'type': 'image', 'format': 'png', 'data_base64': base64.b64encode(sent).decode()}
        placeholders.append(key)
        images.append({'file': path.name, 'original_sha256': sha256(original), 'sent_sha256': sha256(sent),
                       'resized': sent != original})
    questions = {}
    for qid, spec in rubric.questions(task).items():
        text = spec['text']
        if kinds and spec['kind'] not in kinds:
            continue
        if spec['needs_reference']:
            if qid not in references:
                continue
            ref = references[qid]
            if 'variants' in ref:  # blind reading: the reference is never shown to the model
                criteria, _ = blind_reference(ref)
                questions[qid] = {'type': 'choice', 'instructions': text + blind_text(ref), 'criteria': criteria}
                continue
            else:
                text += f" Referência: {ref['value']} {ref['unit']}, período {ref['period']}, tolerância ±{ref['tolerance']}."
        questions[qid] = {'type': 'choice', 'instructions': text, 'criteria': rubric.OPTIONS[spec['kind']]}
    body = {'model': MODEL, 'state': rubric.state_text(task, placeholders), 'questions': questions, 'assets': assets}
    manifest = {'task': task, 'model_requested': MODEL, 'rubric_version': rubric.VERSION,
                'rubric_sha256': rubric.rubric_hash(task), 'images': images, 'questions_asked': sorted(questions)}
    return body, manifest


def request_key(body, long_context=False):
    canonical = json.dumps({'body': body, 'long_context': long_context}, sort_keys=True, ensure_ascii=False)
    return sha256(canonical.encode())


def post(body, long_context=False, timeout=300):
    """One live call. The key comes from JEV_API_KEY; without it the request relies on the
    environment's network secret for api.typesafe.ai to add the Authorization header."""
    headers = {'Content-Type': 'application/json', 'TypeSafe-Danger-Zone-Images': 'true'}
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


def judge(task, image_paths, store, repeat=0, references=None, long_context=False, call=post, kinds=None):
    """Stored record for (request, repeat); calls the model only if that record does not exist."""
    body, manifest = build_request(task, image_paths, references, kinds)
    key = request_key(body, long_context)
    path = Path(store) / key / f'r{repeat}.json'
    if path.exists():
        return json.loads(path.read_text())
    response = call(body, long_context)
    record = {'request_sha256': key, 'repeat': repeat, **manifest, 'long_context': long_context, 'response': response}
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('x') as handle:  # never overwrite a stored response
            json.dump(record, handle, ensure_ascii=False, indent=1, sort_keys=True)
    except FileExistsError:  # an identical request finished first in another worker: keep the stored one
        return json.loads(path.read_text())
    return record


def answers(record):
    """{question id: {option: probability}} from a stored record."""
    return {qid: a['probabilities'] for qid, a in record['response']['answers'].items()}
