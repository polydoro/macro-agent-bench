"""Offline tests: no network, a fake judge call."""
import io
import json

import pytest
from PIL import Image

import aggregate
import judge
import rubric


def png(width, height):
    out = io.BytesIO()
    Image.new('RGB', (width, height), 'white').save(out, format='PNG')
    return out.getvalue()


def all_answers(task, option='ATENDE', skip_reference=False):
    return {qid: {option: 1.0} for qid, spec in rubric.questions(task).items()
            if not (skip_reference and spec['needs_reference'])}


@pytest.mark.parametrize('task', sorted(rubric.TASKS))
def test_full_marks_are_100_and_weights_are_fixed(task):
    result = aggregate.score(rubric.questions(task), rubric.groups(task), all_answers(task))
    assert result['L'] == pytest.approx(100) and result['U'] == pytest.approx(100)
    assert result['pending_points'] == 0


@pytest.mark.parametrize('task', sorted(rubric.TASKS))
def test_without_references_60_points_are_asked_and_40_pending(task):
    result = aggregate.score(rubric.questions(task), rubric.groups(task), all_answers(task, skip_reference=True))
    assert result['L'] == pytest.approx(60) and result['asked_points'] == pytest.approx(60)
    assert result['pending_points'] == pytest.approx(40)


def test_unverifiable_opens_a_band_and_omission_scores_zero():
    questions, groups = rubric.questions('S02'), rubric.groups('S02')
    answers = all_answers('S02')
    answers['P1'] = {'ATENDE': 0.5, 'NAO_VERIFICAVEL': 0.5}
    answers['N_total_yoy'] = {'NAO_MOSTRADO': 1.0}
    result = aggregate.score(questions, groups, answers)
    assert result['L'] == pytest.approx(100 - 5 - 10)
    assert result['U'] == pytest.approx(100 - 10)


def test_best_k_counts_only_the_k_best_components():
    questions, groups = rubric.questions('S01'), rubric.groups('S01')
    answers = all_answers('S01')
    answers['C_construcao_yoy'] = {'NAO_ATENDE': 1.0}  # five admissible, four count
    assert aggregate.score(questions, groups, answers)['L'] == pytest.approx(100)
    answers['C_energia_yoy'] = {'NAO_ATENDE': 1.0}
    assert aggregate.score(questions, groups, answers)['L'] == pytest.approx(97.5)


def test_partial_is_half_and_bad_input_is_rejected():
    questions, groups = rubric.questions('S02'), rubric.groups('S02')
    answers = all_answers('S02')
    answers['I1'] = {'PARCIAL': 1.0}
    assert aggregate.score(questions, groups, answers)['L'] == pytest.approx(95)
    with pytest.raises(ValueError):
        aggregate.score(questions, groups, {**answers, 'I1': {'TALVEZ': 1.0}})
    with pytest.raises(ValueError):
        aggregate.score(questions, groups, {**answers, 'I1': {'ATENDE': 0.4}})


def test_images_are_fitted_to_api_limits_deterministically():
    small = png(1000, 600)
    assert judge.fit_image(small) == small
    big = judge.fit_image(png(1679, 823))
    assert big == judge.fit_image(png(1679, 823))
    width, height = Image.open(io.BytesIO(big)).size
    assert max(width, height) <= judge.MAX_SIDE and width * height <= judge.MAX_PIXELS


def test_stored_response_is_reused_and_repeats_are_separate(tmp_path):
    image = tmp_path / 'a.png'
    image.write_bytes(png(800, 500))
    calls = []

    def fake(body, long_context):
        calls.append(body)
        return {'model': 'jev-1.14.0', 'usage': {'input_tokens': 1, 'output_tokens': 1},
                'answers': {q: {'type': 'choice', 'choice': 'ATENDE', 'confidence': 1.0, 'probabilities': {'ATENDE': 1.0}}
                            for q in body['questions']}}

    store = tmp_path / 'store'
    first = judge.judge('S02', [image], store, 0, call=fake)
    again = judge.judge('S02', [image], store, 0, call=fake)
    judge.judge('S02', [image], store, 1, call=fake)
    assert first == again and len(calls) == 2
    body = calls[0]
    assert all(not q.startswith('N_') for q in body['questions'])  # no reference, numeric not asked
    assert all(key in body['state'] for key in body['assets'])  # every image is referenced
    result = aggregate.score(rubric.questions('S02'), rubric.groups('S02'), judge.answers(first))
    assert result['L'] == pytest.approx(60)


def test_request_key_changes_with_image_bytes(tmp_path):
    a, b = tmp_path / 'a.png', tmp_path / 'b.png'
    a.write_bytes(png(800, 500))
    b.write_bytes(png(801, 500))
    key = lambda p: judge.request_key(judge.build_request('S02', [p])[0])
    assert key(a) != key(b) and key(a) == key(a)
    json.dumps(judge.build_request('S02', [a])[0])  # body is JSON-serialisable


def test_task_without_components_puts_all_points_on_the_total():
    questions = rubric.questions('S10')
    assert rubric.groups('S10') == {}
    assert questions['N_total_native']['weight'] == pytest.approx(40)
    assert questions['C_total_native']['weight'] == pytest.approx(20)


def test_inflation_components_count_best_k_per_transformation():
    questions, groups = rubric.questions('S05'), rubric.groups('S05')
    assert groups == {'N_components_yoy': 5, 'N_components_3me': 5, 'C_components_yoy': 5, 'C_components_3me': 5}
    answers = all_answers('S05')
    answers['C_energia_3me'] = {'NAO_ATENDE': 1.0}  # all five are required, so one miss costs its weight
    assert aggregate.score(questions, groups, answers)['L'] == pytest.approx(100 - 1)
