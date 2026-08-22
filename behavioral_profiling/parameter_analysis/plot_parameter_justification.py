"""Create transparent K/lambda justification plots from the historical sweep.

Font sizes are set explicitly (large) so the figure reads well when placed at
column width in a LaTeX two-column paper, roughly matching body-text scale.

Run: python3 plot_parameter_justification.py
Requires: historical_tuning_results.csv (produced by 01_historical_parameter_tuning.ipynb)
in the same directory.
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent
d = pd.read_csv(ROOT / 'historical_tuning_results.csv')
K0, L0 = 10, 2.0
colors = {'mirai': '#1769aa', 'gafgyt': '#d95f02'}

# ---- font sizes (large, for LaTeX column-width placement) ----
FS_SUPTITLE = 26
FS_TITLE = 25
FS_AXIS_LABEL = 25
FS_TICK = 25
FS_LEGEND = 25
FS_ANNOTATION = 25
FS_CAPTION = 14

plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(1, 2, figsize=(19, 8.5))

for fam in ['mirai', 'gafgyt']:
    x = d[d.family == fam].groupby('K', as_index=False).agg(final_mean=('final_mean', 'mean'))
    ax[0].plot(x.K, x.final_mean, 'o-', lw=3.2, ms=9, label=fam.capitalize(), color=colors[fam])
ax[0].axvline(K0, color='black', ls='--', lw=2)
ax[0].annotate('selected K=10\n(shared conservative elbow)', xy=(K0, 0.52), xycoords=('data', 'axes fraction'),
               xytext=(19, .26), textcoords=('data', 'axes fraction'),
               fontsize=FS_ANNOTATION, arrowprops=dict(arrowstyle='->', lw=2))
ax[0].set_xlabel('Neighbourhood breadth K', fontsize=FS_AXIS_LABEL)
ax[0].set_ylabel('Final detected C2s\n(mean across seed draws)', fontsize=FS_AXIS_LABEL)
ax[0].set_title('Historical validation: K elbow', fontsize=FS_TITLE, pad=14)
ax[0].tick_params(axis='both', labelsize=FS_TICK)
ax[0].legend(fontsize=FS_LEGEND)

for fam in ['mirai', 'gafgyt']:
    x = d[(d.family == fam) & (d.K == K0)].sort_values('lam')
    ax[1].plot(x.lam, x.auc_mean, 'o-', lw=3.2, ms=9, label=fam.capitalize(), color=colors[fam])
ax[1].axvline(L0, color='black', ls='--', lw=2)
ax[1].annotate('selected λ=2.0\n(shared elbow)', xy=(L0, 0.64), xycoords=('data', 'axes fraction'),
               xytext=(6.5, .35), textcoords=('data', 'axes fraction'),
               fontsize=FS_ANNOTATION, arrowprops=dict(arrowstyle='->', lw=2))
ax[1].set_xlabel('Decay parameter λ', fontsize=FS_AXIS_LABEL)
ax[1].set_ylabel('Log-budget AUC (mean)', fontsize=FS_AXIS_LABEL)
ax[1].set_title('Historical validation at K=10: λ elbow', fontsize=FS_TITLE, pad=14)
ax[1].tick_params(axis='both', labelsize=FS_TICK)
ax[1].legend(fontsize=FS_LEGEND)

fig.suptitle('Pre-specified diminishing-returns selection: K=10, λ=2.0', fontsize=FS_SUPTITLE, y=1.02)
fig.text(.5, -.045,
         'Selection rule: smallest shared elbow after marginal gain falls below 10% of the early slope; no test-set tuning.\n'
         'Candidate graph built offline (windowed synthesis around observed evidence) -- see REPORT.md for the approximation and its limits.',
         ha='center', fontsize=FS_CAPTION)
fig.tight_layout()
fig.savefig(ROOT / 'parameter_justification.png', dpi=220, bbox_inches='tight')
print(ROOT / 'parameter_justification.png')
