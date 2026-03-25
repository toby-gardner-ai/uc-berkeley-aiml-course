from IPython.display import HTML, display
from types import SimpleNamespace
import pathlib
# Visualization libraries
import matplotlib.pyplot as plt
import seaborn as sns
import missingno as msno

PALETTE = [
    "#2563EB", "#E11D48", "#16A34A", "#F59E0B",
    "#8B5CF6", "#06B6D4", "#EC4899", "#84CC16",
]


def configure_style():
    """Configure matplotlib/seaborn style and return standard figure sizes.

    Returns a SimpleNamespace with attributes like FIG.SINGLE, FIG.DOUBLE, etc.
    """
    sns.set_theme(style='whitegrid', palette=PALETTE, font_scale=1.1)

    plt.rcParams.update({
        # Figure
        'figure.figsize': (10, 6),
        'figure.dpi': 100,
        'figure.facecolor': 'white',
        'figure.titlesize': 16,
        'figure.titleweight': 'bold',
        # Axes
        'axes.titlesize': 14,
        'axes.titleweight': 'bold',
        'axes.labelsize': 12,
        'axes.labelweight': 'medium',
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': True,
        'axes.prop_cycle': plt.cycler('color', PALETTE),
        # Grid
        'grid.alpha': 0.3,
        'grid.linestyle': '--',
        # Ticks
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        # Legend
        'legend.fontsize': 10,
        'legend.framealpha': 0.9,
        'legend.edgecolor': '0.8',
        # Font
        'font.family': 'sans-serif',
    })

    print('\u2714 Visualization style configured')
    return SimpleNamespace(
        SINGLE   = (10, 6),
        DOUBLE   = (14, 5),
        TRIPLE   = (16, 5),
        GRID_2x2 = (12, 10),
        GRID_3x2 = (14, 14),
        TALL     = (10, 8),
    )

def show_mermaid_diagram(name, center=True, width=None):
    path = (
        pathlib.Path("/Users/tobygardner/Projects/uc-berkeley-aiml-course/images")
        / f"{name}.png"
    )
    if not path.exists():
        raise FileNotFoundError(f"No diagram found named {name}")

    img_tag = f'<img src="{path}"'
    if width:
        img_tag += f' style="width:{width};"'
    img_tag += ">"

    if center:
        display(HTML(f"<div style='text-align:center;'>{img_tag}</div>"))
    else:
        display(HTML(img_tag))


def visualize_missing_data(df, figsize, title_fontsize, label_fontsize):
    df = df.copy()

    ax = msno.matrix(df, figsize=figsize, sparkline=True)
    
    plt.suptitle("Missing Data Matrix", fontsize=title_fontsize, y=1.02)

    ax.xaxis.tick_bottom()
    plt.xticks(rotation=45, fontsize=label_fontsize)

    ax.set_yticklabels([])
    plt.show()
