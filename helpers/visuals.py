from IPython.display import HTML, display
import pathlib


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
