"""Pure aggregation of judge answers into a score. No model, no I/O. Copied unchanged from visual-rubric-v1/aggregate.py (PR #1).

Per question the judge returns probabilities over closed options. Values:
  ATENDE 1, PARCIAL 0.5, NAO_ATENDE 0, NAO_MOSTRADO 0 (candidate omission),
  NAO_VERIFICAVEL undetermined.

L = points supported by the answers. U = L plus the undetermined mass.
Questions that were not asked (no reference sheet yet) are evaluator-pending:
they are reported separately and never count for or against the candidate.
Points are never redistributed or renormalised.
"""

VALUE = {'ATENDE': 1.0, 'PARCIAL': 0.5, 'NAO_ATENDE': 0.0, 'NAO_MOSTRADO': 0.0}
UNDETERMINED = 'NAO_VERIFICAVEL'


def question_points(spec, probabilities):
    """(supported, undetermined) points for one answered question."""
    unknown = set(probabilities) - set(VALUE) - {UNDETERMINED}
    if unknown:
        raise ValueError(f'Unknown options: {sorted(unknown)}')
    total = sum(probabilities.values())
    if not 0.98 <= total <= 1.02:
        raise ValueError(f'Probabilities sum to {total}, expected 1')
    supported = sum(VALUE[o] * p for o, p in probabilities.items() if o in VALUE)
    return spec['weight'] * supported, spec['weight'] * probabilities.get(UNDETERMINED, 0.0)


def score(questions, groups, answers):
    """questions: {id: spec}; groups: {group: K}; answers: {id: {option: probability}}.

    Returns L, U, pending points and the per-question detail. A best-K group
    counts its K best members, for L by supported points and for U by
    supported + undetermined points.
    """
    extra = set(answers) - set(questions)
    if extra:
        raise ValueError(f'Answers for unknown questions: {sorted(extra)}')
    detail, lower, upper, pending = {}, 0.0, 0.0, 0.0
    members = {g: [] for g in groups}
    for qid, spec in questions.items():
        group = spec.get('group')
        if qid not in answers:
            detail[qid] = {'state': 'evaluator_pending', 'weight': spec['weight'], 'group': group}
            if group is None:
                pending += spec['weight']
            continue
        supported, undetermined = question_points(spec, answers[qid])
        detail[qid] = {'state': 'answered', 'weight': spec['weight'], 'group': group,
                       'supported': supported, 'undetermined': undetermined}
        if group is None:
            lower += supported
            upper += supported + undetermined
        else:
            members[group].append((supported, undetermined))
    for group, k in groups.items():
        answered = members[group]
        weight = next(s['weight'] for s in questions.values() if s.get('group') == group)
        if not answered:
            pending += k * weight
            continue
        lower += sum(sorted((s for s, _ in answered), reverse=True)[:k])
        upper += sum(sorted((s + u for s, u in answered), reverse=True)[:k])
    asked = 100.0 - pending
    return {'L': lower, 'U': upper, 'asked_points': asked, 'pending_points': pending, 'questions': detail}
