"""Offline tests: no network, a fake judge call."""
import pytest

import aggregate
import judge
import references as R
import rubric

ATTEMPT = 'one-c04-claude-opus-primary'


def test_full_marks_are_100():
    qs = rubric.questions('C04')
    result = aggregate.score(qs, rubric.groups('C04'), {q: {'ATENDE': 1.0} for q in qs})
    assert result['L'] == pytest.approx(100)


def test_block_weights():
    qs = rubric.questions('C04')
    by = {}
    for spec in qs.values():
        by[spec['kind']] = by.get(spec['kind'], 0) + spec['weight']
    assert by['identity'] + by['conventions'] == 20 and by['coverage'] == pytest.approx(20)
    assert by['legibility'] + by['identification'] == 20
    assert by['answer'] + by['support'] + by['method'] + by['limits'] == 20 and by['method'] == 12 and by['support'] == 0
    assert by['numeric'] / len([q for q in qs if q.startswith('N_')]) * rubric.groups('C04')['N'] == 20


def test_reference_never_in_request():
    refs = R.references('C04', ATTEMPT)
    body, _ = judge.build_request('C04', 'numeric', [], 'texto', refs)
    dumped = str(body)
    for ref in refs.values():
        for label, value, _ in ref['variants']:
            assert label not in dumped
    assert all('FAIXA_' in ''.join(q['criteria']) for q in body['questions'].values())


def test_key_admits_known_value_and_rejects_pre2005_trap():
    refs = R.references('C04', ATTEMPT)
    one_year = [v for _, v, t in refs['N_qoq_one_year']['variants'] if t == R.C04_TOL]
    assert any(abs(v - 0.048) < 1e-6 for v in one_year)  # 2005-2019, 365 days
    latest = [v for _, v, t in refs['N_qoq_latest']['variants'] if t == R.C04_TOL]
    # 1991-2019 with the May-2005 vintage taken as "first": +0.044 to the latest vintage. At one year
    # the trap (+0.024) sits inside the 0.03 tolerance, so only the latest horizon separates it.
    assert all(abs(v - 0.044) > R.C04_TOL for v in latest)


def test_blind_maps_choices():
    ref = {'variants': [('a', 1.0, 0.1)]}
    criteria, admitted = R.blind(ref)
    assert len(admitted) == 1 and 'OUTRO_VALOR' in criteria
    assert R.to_options({admitted[0]: 1.0}, admitted)['ATENDE'] == 1.0
    assert R.to_options({'OUTRO_VALOR': 1.0}, admitted)['NAO_ATENDE'] == 1.0


def test_requests_split_questions():
    refs = R.references('C04', ATTEMPT)
    asked = set()
    for request in ('images', 'text', 'numeric'):
        body, _ = judge.build_request('C04', request, [], 'texto', refs)
        assert not asked & set(body['questions'])
        asked |= set(body['questions'])
    assert asked == set(rubric.questions('C04'))


def test_html_text():
    assert judge.html_text('<p>Sim, <b>modesto</b></p><table><tr><td>1</td><td>2</td></tr></table>').startswith('Sim, modesto')


def test_c01_weights_period_and_blindness():
    import rubric
    qs = rubric.questions('C01')
    assert sum(q['weight'] for q in qs.values() if q['group'] != 'N') + 20 == 100
    assert rubric.groups('C01') == {'N': 2}
    refs = R.references('C01', 'a3-c01-claude-opus-primary')
    assert refs['N_ord_yoy']['period'] == '2026-09' and refs['N_prod_yoy']['period'] == '2026-08'
    body, _ = judge.build_request('C01', 'numeric', [], 'texto', refs)
    dumped = str(body)
    assert '2026-09' in dumped
    assert '0.74' not in dumped and '3.32' not in dumped and 'B-D_F, YoY' not in dumped
