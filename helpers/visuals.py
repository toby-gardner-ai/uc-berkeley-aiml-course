from IPython.display import HTML, display
import pathlib
# Visualization libraries
import matplotlib.pyplot as plt
import seaborn as sns
import missingno as msno

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
