"""Frontier figure: score vs median minutes per task, one line per method, overall frontier in grey,
model names on the overall frontier points. Writes results/frontier-en.png and results/frontier-pt.png.

    python analysis/figure.py      # needs matplotlib
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from frontier import METHODS, all_tasks, frontier, points

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results')
COL = {'low_effort': '#2a78d6', 'high_effort': '#eb6834', 'examples': '#1baf7a', 'self_review': '#eda100', 'external_review': '#e87ba4'}
MARK = {'low_effort': 'o', 'high_effort': 'o', 'examples': 'o', 'self_review': '^', 'external_review': 's'}
INK, INK2, MUTED, SURF, GRID, REF = '#1f1e1b', '#4a4944', '#6b6a64', '#fcfcfb', '#e4e3df', '#8f8e88'
TEXT = {
    'en': {'low_effort': 'Low effort', 'high_effort': 'High effort', 'examples': 'With examples',
           'self_review': 'Self-review', 'external_review': 'External review', 'frontier': 'Efficient frontier',
           'title': 'Worked examples: top scores in less time',
           'sub': 'Higher is better, left is faster. Each line joins the best runs of one method. 9 AI models, 16 macroeconomics tasks.',
           'x': 'Median minutes per task', 'y': 'Score (out of 100)',
           'note': "One point per model and method; only each method's best runs are shown. Score: mean over the 16 tasks, "
                   'a run with no delivery counts as 0. Personal project, Nov 2026.'},
    'pt': {'low_effort': 'Esforço baixo', 'high_effort': 'Esforço alto', 'examples': 'Com exemplos',
           'self_review': 'Autorrevisão', 'external_review': 'Revisão externa', 'frontier': 'Fronteira eficiente',
           'title': 'Exemplos resolvidos: notas de topo em menos tempo',
           'sub': 'Mais alto é melhor, à esquerda é mais rápido. Cada linha liga as melhores execuções de um método. '
                  '9 modelos de IA, 16 tarefas de macroeconomia.',
           'x': 'Minutos por tarefa (mediana)', 'y': 'Nota (de 100)',
           'note': 'Um ponto por modelo e método; só as melhores execuções de cada método aparecem. Nota: média nas 16 '
                   'tarefas, execução sem entrega conta como 0. Projeto pessoal, nov. 2026.'},
}
# label placement for the six overall-frontier points: (dx, dy, ha, va)
PLACE = {('GPT-6 Luna', 'low_effort'): (-0.16, 0, 'right', 'center'), ('Sonnet 5.5', 'examples'): (-0.16, 0, 'right', 'center'),
         ('Opus 5.5', 'examples'): (-0.05, 1.0, 'center', 'bottom')}


def step(pts):
    xs, ys = [], []
    for i, (t, s, *_) in enumerate(pts):
        xs.append(t); ys.append(s)
        if i + 1 < len(pts):
            xs.append(pts[i + 1][0]); ys.append(s)
    return xs, ys


def draw(lang):
    L = TEXT[lang]
    pts = points(all_tasks())
    overall = frontier(pts)
    fig = plt.figure(figsize=(12, 6.3), dpi=200)
    fig.patch.set_facecolor(SURF)
    ax = fig.add_axes([0.045, 0.215, 0.935, 0.555])
    ax.set_facecolor(SURF)
    ax.plot(*step(overall), color=REF, lw=4.2, alpha=0.45, solid_joinstyle='round', solid_capstyle='round', zorder=1)
    handles = []
    for a in METHODS:
        fa = frontier([p for p in pts if p[3] == a])
        ax.plot(*step(fa), color=COL[a], lw=1.4, alpha=0.85, zorder=2)
        ax.scatter([p[0] for p in fa], [p[1] for p in fa], marker=MARK[a], s=62, color=COL[a], edgecolor=SURF, linewidth=1.6, zorder=4)
        handles.append(Line2D([], [], color=COL[a], lw=0, marker=MARK[a], markersize=8.5, markeredgecolor=SURF,
                              markeredgewidth=1.2, label=L[a]))
    handles.append(Line2D([], [], color=REF, lw=4.2, alpha=0.45, label=L['frontier']))
    for t, s, m, a in overall:
        dx, dy, ha, va = PLACE.get((m, a), (0, 1.0, 'center', 'bottom'))
        ax.text(t + dx, s + dy, m, fontsize=10, color=INK2, ha=ha, va=va, zorder=6)
    ax.set_xlim(0, 16); ax.set_ylim(60, 100)
    ax.set_xticks(range(0, 17, 2)); ax.set_yticks(range(60, 101, 10))
    ax.grid(color=GRID, lw=0.8); ax.set_axisbelow(True)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0, colors=MUTED, labelsize=11, pad=6)
    ax.text(0, 1.035, L['y'], transform=ax.transAxes, fontsize=11, color=MUTED, ha='left', va='bottom')
    ax.text(1, -0.105, L['x'], transform=ax.transAxes, fontsize=11, color=MUTED, ha='right', va='top')
    fig.text(0.045, 0.925, L['title'], fontsize=20, fontweight='bold', color=INK, ha='left', va='bottom')
    fig.text(0.045, 0.868, L['sub'], fontsize=10.8, color=INK2, ha='left', va='bottom')
    fig.legend(handles=handles, loc='lower left', bbox_to_anchor=(0.035, 0.062), ncol=6, frameon=False, fontsize=11.5,
               handletextpad=0.35, columnspacing=1.7, labelcolor=INK2)
    fig.text(0.045, 0.028, L['note'], fontsize=8.6, color=MUTED, ha='left', va='bottom')
    path = os.path.join(OUT, f'frontier-{lang}.png')
    fig.savefig(path, facecolor=SURF)
    plt.close(fig)
    print(path)


if __name__ == '__main__':
    for lang in TEXT:
        draw(lang)
