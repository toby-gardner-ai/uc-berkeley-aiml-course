import re
import shutil
import subprocess
from pathlib import Path

MERMAID_FILE = Path("/Users/tobygardner/Projects/uc-berkeley-aiml-course/images/mermaid_diagrams.md")
OUT_DIR = Path("/Users/tobygardner/Projects/uc-berkeley-aiml-course/images/cache")
FINAL_DIR = Path("/Users/tobygardner/Projects/uc-berkeley-aiml-course/images")

# Ensure dirs exist
OUT_DIR.mkdir(exist_ok=True, parents=True)
FINAL_DIR.mkdir(exist_ok=True, parents=True)

# regex: fenced block with name
BLOCK_RE = re.compile(
    r"```mermaid\s+name=(\S+)\s+(.*?)```",
    re.DOTALL
)

def export_mermaid():
    text = MERMAID_FILE.read_text()
    matches = BLOCK_RE.findall(text)
    print(f"Found {len(matches)} diagrams")

    for name, code in matches:
        print(f"Exporting: {name}...")
        
        src = OUT_DIR / f"{name}.mmd"
        img = OUT_DIR / f"{name}.png"

        # Write intermediate mermaid file
        src.write_text(code)

        # Render via mermaid-cli
        try:
            subprocess.run(
                ["mmdc", "-i", str(src), "-o", str(img)],
                check=True
            )
        except subprocess.CalledProcessError:
            print(f"❌ Error generating diagram: {name}")
            continue

        # Copy PNG to images/ root
        shutil.copy2(img, FINAL_DIR / f"{name}.png")

    print("✅ Export complete!")

if __name__ == "__main__":
    export_mermaid()