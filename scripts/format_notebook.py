#!/usr/bin/env python3
"""
Jupyter Notebook Formatter
Standardises headings, builds ToC, cleans imports, injects viz style,
generates a flow diagram, fixes spelling, and documents functions.

Usage:
    python scripts/format_notebook.py <notebook.ipynb> [options]

Options:
    --steps 1,2,3,4,5,6   Steps to run (default: all)
    --dry-run              Print report without saving
    --ai                   Use Anthropic API for Steps 5-6
"""

import json
import re
import os
import sys
import argparse
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

PALETTE = [
    "#2563EB", "#E11D48", "#16A34A", "#F59E0B",
    "#8B5CF6", "#06B6D4", "#EC4899", "#84CC16",
]

FILLER_WORDS = frozenset(
    "a an and are at be but by for from has have if in into is it its "
    "not of on or so that the this to was were will with".split()
)

ABBREVS = {
    "evaluation": "eval", "preparation": "prep", "visualization": "viz",
    "configuration": "config", "implementation": "impl",
    "introduction": "intro", "exogenous": "exo", "statistical": "stat",
    "benchmarking": "bench", "recommendation": "rec",
    "engineering": "eng", "collection": "coll", "application": "app",
    "interpretation": "interp", "determining": "det",
}

MISSPELLINGS = {
    "teh": "the", "adn": "and", "taht": "that",
    "modle": "model", "modle": "model",
    "accuray": "accuracy", "accurancy": "accuracy",
    "prediciton": "prediction", "predicitons": "predictions",
    "paramter": "parameter", "paramters": "parameters",
    "hyperparamter": "hyperparameter",
    "classifer": "classifier",
    "intepretation": "interpretation", "intepret": "interpret",
    "explaination": "explanation",
    "occurance": "occurrence", "occurances": "occurrences",
    "seperate": "separate",
    "dependancy": "dependency",
    "differecing": "differencing",
    "frequenct": "frequency",
    "seriees": "series",
    "algorythm": "algorithm",
    "initalize": "initialize",
    "retreive": "retrieve",
    "leanring": "learning",
    "nueral": "neural",
    "feauture": "feature", "feautures": "features",
    "regresion": "regression",
    "clasification": "classification",
    "dimentional": "dimensional",
    "matix": "matrix", "graident": "gradient",
}

TYPE_BY_NAME = {
    "df": "pd.DataFrame", "data": "pd.DataFrame",
    "X": "np.ndarray", "y": "np.ndarray",
    "ax": "plt.Axes", "fig": "plt.Figure",
    "path": "str", "filepath": "str", "filename": "str",
    "query": "str", "text": "str", "name": "str",
    "col": "str", "column": "str", "metric": "str",
    "url": "str", "label": "str", "title": "str",
    "matrix": "np.ndarray", "scores": "np.ndarray",
}

TYPE_BY_PREFIX = [
    ("n_", "int"), ("num_", "int"), ("max_", "int"), ("min_", "int"),
    ("k", "int"),
    ("is_", "bool"), ("has_", "bool"), ("use_", "bool"),
    ("df_", "pd.DataFrame"),
]



# ═══════════════════════════════════════════════════════════════════
# NOTEBOOK I/O HELPERS
# ═══════════════════════════════════════════════════════════════════

def src(cell):
    """Return cell source as a single string."""
    return "".join(cell["source"])


def set_src(cell, text):
    """Set cell source from a plain string."""
    if not text:
        cell["source"] = [""]
        return
    text = text.rstrip("\n")
    lines = text.split("\n")
    cell["source"] = [ln + "\n" for ln in lines[:-1]] + [lines[-1]]


def make_md(text):
    c = {"cell_type": "markdown", "metadata": {}, "source": []}
    set_src(c, text)
    return c


def make_code(text):
    c = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [],
    }
    set_src(c, text)
    return c


# ═══════════════════════════════════════════════════════════════════
# STEP 1 — HEADINGS & TABLE OF CONTENTS
# ═══════════════════════════════════════════════════════════════════

def _heading_match(line):
    """Return (level, raw_text) if line is a markdown heading, else None."""
    m = re.match(r"^(#{1,6})\s+(.+)", line.strip())
    return (len(m.group(1)), m.group(2).strip()) if m else None


def _strip_heading_decorations(text):
    """Remove existing numbering and anchor tags from heading text."""
    # Remove anchor tag
    anchor = None
    am = re.search(r"<a\s+id=['\"]([^'\"]+)['\"]", text)
    if am:
        anchor = am.group(1)
    text = re.sub(r"\s*<a\s+id=['\"][^'\"]+['\"]>\s*</a>\s*", "", text)
    # Remove numbering  (e.g.  "1." or "3.1" or "3.1.")
    text = re.sub(r"^\d+(\.\d+)*\.?\s+", "", text).strip()
    return text, anchor


def _generate_anchor(num, title):
    """Create a short hyphenated anchor id from section number + title."""
    words = re.sub(r"[^a-z0-9\s-]", "", title.lower()).split()
    words = [w for w in words if w not in FILLER_WORDS]
    words = [ABBREVS.get(w, w) for w in words]
    words = words[:3]
    words = [w[:7] if len(w) > 9 else w for w in words]
    slug = "-".join(words) if words else "section"
    num_part = num.replace(".", "-")
    return f"{num_part}-{slug}"


def analyze_headings(cells):
    """Scan cells and return a section plan.

    Returns list of (cell_idx, effective_level, number_str, title, anchor_id)
    and the index of the title cell (or None).
    """
    raw = []  # (cell_idx, level, title, existing_anchor)
    title_idx = None

    for i, cell in enumerate(cells):
        if cell["cell_type"] != "markdown":
            continue
        first_line = src(cell).lstrip("-\n \t").split("\n")[0]
        hm = _heading_match(first_line)
        if not hm:
            continue
        level, raw_text = hm
        title_text, existing_anchor = _strip_heading_decorations(raw_text)
        if not title_text:
            continue

        # First # heading = notebook title
        if level == 1 and title_idx is None:
            title_idx = i
            continue

        # Skip structural/meta headings
        if title_text in ("Table of Contents", "Notebook Workflow"):
            continue

        raw.append((i, level, title_text, existing_anchor))

    # Build section plan: promote headings as needed
    # Track first_h2_seen *during iteration* so ### before the first ##
    # get promoted to ##, while ### after the first ## stay as subsections.
    first_h2_seen = False
    plan = []
    sec = 0
    sub = 0

    for cell_idx, level, title, anchor in raw:
        if level == 2:
            eff = 2
            first_h2_seen = True
        elif level == 3 and not first_h2_seen:
            eff = 2  # ### before first ## → promote to section
        elif level >= 4 and not first_h2_seen:
            eff = 3  # #### before first ## → promote to subsection
        elif level >= 4:
            eff = 4  # #### → keep at ####
        else:
            eff = level  # ### after first ## stays ###

        if eff == 2:
            sec += 1
            sub = 0
            num = str(sec)
        else:
            sub += 1
            num = f"{sec}.{sub}"

        aid = anchor or _generate_anchor(num, title)
        plan.append((cell_idx, eff, num, title, aid))

    return plan, title_idx


def step1(cells, plan, title_idx, report):
    """Apply heading formatting and insert ToC."""
    report.append("\nStep 1 — Headings & ToC:")

    # Fix title cell: strip decorations, ensure single #
    if title_idx is not None:
        s = src(cells[title_idx])
        lines = s.split("\n")
        first = lines[0]
        hm = _heading_match(first)
        if hm:
            _, raw_text = hm
            clean, _ = _strip_heading_decorations(raw_text)
            lines[0] = f"# {clean}"
            set_src(cells[title_idx], "\n".join(lines))
            report.append(f"  Title cell: '# {clean}'")

    # Format each heading cell
    for cell_idx, eff, num, title, anchor in plan:
        s = src(cells[cell_idx])
        # Remove leading --- separators
        s = re.sub(r"^---\s*\n+", "", s)
        lines = s.split("\n")
        # Find the heading line
        hl = 0
        for j, ln in enumerate(lines):
            if _heading_match(ln):
                hl = j
                break
        rest = "\n".join(lines[hl + 1 :]).strip()

        hashes = "#" * eff
        heading_line = f"{hashes} {num}. {title} <a id='{anchor}'></a>"

        new = f"---\n\n{heading_line}" if eff == 2 else heading_line
        if rest:
            new += "\n\n" + rest
        set_src(cells[cell_idx], new)

    # Build ToC
    toc_lines = ["### Table of Contents\n"]
    for _, eff, num, title, anchor in plan:
        if eff == 2:
            toc_lines.append(f"{num}. [{title}](#{anchor})")
        else:
            toc_lines.append(f"   - {num} [{title}](#{anchor})")
    toc_text = "\n".join(toc_lines)

    # Find or replace existing ToC cell
    insert_pos = (title_idx or 0) + 1
    toc_exists = False
    for i in range(min(insert_pos + 2, len(cells))):
        if cells[i]["cell_type"] == "markdown" and "Table of Contents" in src(cells[i]):
            set_src(cells[i], toc_text)
            toc_exists = True
            report.append("  Replaced existing ToC cell")
            break

    if not toc_exists:
        cells.insert(insert_pos, make_md(toc_text))
        report.append(f"  Inserted ToC cell at position {insert_pos}")

    secs = sum(1 for _, e, *_ in plan if e == 2)
    subs = sum(1 for _, e, *_ in plan if e == 3)
    report.append(f"  {secs} sections, {subs} subsections")
    return cells


# ═══════════════════════════════════════════════════════════════════
# STEP 2 — IMPORT CLEANUP
# ═══════════════════════════════════════════════════════════════════

def _parse_imports(source):
    """Return dict of {local_name: (full_line, original_name)} from source."""
    names = {}
    # Join continuation lines
    joined = []
    lines = source.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if "import" in line and "(" in line and ")" not in line:
            while i < len(lines) - 1 and ")" not in lines[i]:
                i += 1
                line += " " + lines[i].strip()
        while line.rstrip().endswith("\\") and i < len(lines) - 1:
            line = line.rstrip()[:-1]
            i += 1
            line += " " + lines[i].strip()
        joined.append(line)
        i += 1

    for line in joined:
        s = line.strip()
        if s.startswith("#") or not s:
            continue
        # from X import *
        if re.match(r"from\s+\S+\s+import\s+\*", s):
            continue
        # from X import A, B as C
        m = re.match(r"from\s+\S+\s+import\s+\(?\s*(.+?)\s*\)?$", s)
        if m:
            for item in re.split(r"\s*,\s*", m.group(1)):
                item = item.strip().strip(")")
                if not item:
                    continue
                am = re.match(r"(\w+)\s+as\s+(\w+)", item)
                if am:
                    names[am.group(2)] = (s, am.group(1))
                elif re.match(r"\w+$", item):
                    names[item] = (s, item)
            continue
        # import X as Y
        m = re.match(r"import\s+(\S+)\s+as\s+(\w+)", s)
        if m:
            names[m.group(2)] = (s, m.group(1))
            continue
        # import X  or  import X.Y.Z
        m = re.match(r"import\s+([\w.]+)", s)
        if m:
            mod = m.group(1)
            names[mod.split(".")[0]] = (s, mod)
    return names


# ═══════════════════════════════════════════════════════════════════
# STEP 2 — IMPORT CLEANUP
# ═══════════════════════════════════════════════════════════════════

def _strip_inline_comment(line):
    """Remove inline comments, respecting strings."""
    in_str = None
    for i, ch in enumerate(line):
        if ch in ('"', "'") and (i == 0 or line[i-1] != '\\'):
            if in_str == ch:
                in_str = None
            elif in_str is None:
                in_str = ch
        elif ch == '#' and in_str is None:
            return line[:i].rstrip()
    return line


def _parse_imports(source):
    """
    Return dict of {local_name: (full_line, original_name, is_multi)}
    from source. is_multi indicates the import line brings in multiple names.
    """
    names = {}
    lines = source.split("\n")
    joined = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Handle parenthesized multi-line imports: from X import (A, B,
        #                                                         C, D)
        if "import" in line and "(" in line and ")" not in line:
            while i < len(lines) - 1:
                i += 1
                line += " " + lines[i].strip()
                if ")" in lines[i]:
                    break
        # Handle backslash continuation
        while line.rstrip().endswith("\\") and i < len(lines) - 1:
            line = line.rstrip()[:-1]
            i += 1
            line += " " + lines[i].strip()
        joined.append(line)
        i += 1

    for line in joined:
        s = _strip_inline_comment(line.strip())
        if s.startswith("#") or not s:
            continue
        # from X import *
        if re.match(r"from\s+\S+\s+import\s+\*", s):
            continue
        # from X import A, B as C
        m = re.match(r"from\s+\S+\s+import\s+\(?\s*(.+?)\s*\)?$", s)
        if m:
            items_str = m.group(1)
            item_list = [x.strip().strip(")") for x in re.split(r"\s*,\s*", items_str) if x.strip()]
            is_multi = len(item_list) > 1
            for item in item_list:
                if not item:
                    continue
                am = re.match(r"(\w+)\s+as\s+(\w+)", item)
                if am:
                    names[am.group(2)] = (s, am.group(1), is_multi)
                elif re.match(r"\w+$", item):
                    names[item] = (s, item, is_multi)
            continue
        # import X as Y
        m = re.match(r"import\s+(\S+)\s+as\s+(\w+)", s)
        if m:
            names[m.group(2)] = (s, m.group(1), False)
            continue
        # import X  or  import X.Y.Z
        m = re.match(r"import\s+([\w.]+)", s)
        if m:
            mod = m.group(1)
            names[mod.split(".")[0]] = (s, mod, False)
    return names


def _remove_name_from_import_line(source, import_line, name_to_remove):
    """
    Remove a single name from a multi-name import line in source.
    E.g., remove 'f1_score' from 'from sklearn.metrics import accuracy_score, f1_score, roc_auc_score'.
    Returns the modified source. If the line becomes empty after removal, removes it entirely.
    """
    # Build pattern to match the name (possibly with 'as alias')
    pattern = re.compile(
        r",?\s*\b" + re.escape(name_to_remove) + r"(?:\s+as\s+\w+)?\s*,?"
    )
    new_line = pattern.sub("", import_line, count=1).strip()
    # Clean up: fix leading/trailing commas and double commas
    new_line = re.sub(r"import\s+\(\s*,", "import (", new_line)
    new_line = re.sub(r",\s*\)", ")", new_line)
    new_line = re.sub(r"import\s+,", "import ", new_line)
    new_line = re.sub(r",\s*$", "", new_line)
    new_line = re.sub(r",\s*,", ",", new_line)

    # Check if all names were removed (only 'from X import' left with nothing after)
    if re.match(r"from\s+\S+\s+import\s*\(?\s*\)?\s*$", new_line):
        return _remove_whole_line(source, import_line)

    return source.replace(import_line, new_line, 1)


def _remove_whole_line(source, import_line):
    """Remove an entire import line from source, cleaning up blank lines."""
    new_s = source.replace(import_line + "\n", "", 1)
    if new_s == source:
        new_s = source.replace(import_line, "", 1)
    return re.sub(r"\n{3,}", "\n\n", new_s)


def step2(cells, report):
    """Remove unused and duplicate imports."""
    report.append("\nStep 2 — Import Cleanup:")
    removed = []

    # Collect all imported names across all code cells
    all_imports = {}  # name -> [(cell_idx, full_line, original_name, is_multi)]
    for i, cell in enumerate(cells):
        if cell["cell_type"] != "code":
            continue
        for name, (line, orig, is_multi) in _parse_imports(src(cell)).items():
            all_imports.setdefault(name, []).append((i, line, orig, is_multi))

    # Build full text of all cells for usage scanning
    full_text = "\n".join(src(cell) for cell in cells)

    for name, occurrences in all_imports.items():
        pattern = re.compile(r"\b" + re.escape(name) + r"\b")
        matches = pattern.findall(full_text)
        # Subtract occurrences in import lines themselves
        import_mentions = sum(
            len(pattern.findall(line)) for _, line, _, _ in occurrences
        )
        used = len(matches) - import_mentions > 0

        if not used:
            for cidx, line, orig, is_multi in occurrences:
                if is_multi:
                    # Remove just this name from the multi-import line
                    new_s = _remove_name_from_import_line(src(cells[cidx]), line, orig)
                    set_src(cells[cidx], new_s.strip())
                    removed.append(f"from ...: {orig}" + (f" (as {name})" if orig != name else ""))
                else:
                    new_s = _remove_whole_line(src(cells[cidx]), line)
                    set_src(cells[cidx], new_s.strip())
                    removed.append(f"{orig}" + (f" (as {name})" if orig != name else ""))

        elif len(occurrences) > 1:
            # Remove duplicates (keep first occurrence)
            for cidx, line, orig, is_multi in occurrences[1:]:
                new_s = _remove_whole_line(src(cells[cidx]), line)
                set_src(cells[cidx], new_s.strip())
                removed.append(f"{name} (duplicate, cell {cidx})")

    if removed:
        for r in removed:
            report.append(f"  - Removed: {r}")
    else:
        report.append("  All imports are in use — no changes needed.")
    return cells


# ═══════════════════════════════════════════════════════════════════
# STEP 3 — VISUALIZATION STYLE
# ═══════════════════════════════════════════════════════════════════

VIZ_STYLE_TEMPLATE = """# ── Visualization Style ──────────────────────────────────────────────
import pathlib, sys
sys.path.insert(0, str(pathlib.Path.cwd().parent))
from helpers.visuals import configure_style
FIG = configure_style()"""


def _detect_layout(cell_source):
    """Return (rows, cols) from subplots/figure call, or None.

    rows or cols may be None when the value is a runtime expression.
    """
    for line in cell_source.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue

        if "plt.figure(" in stripped:
            return (1, 1)

        # Find plt.subplots( and extract args with balanced parens
        idx = stripped.find("plt.subplots(")
        if idx == -1:
            idx = stripped.find(".subplots(")
        if idx == -1:
            continue
        # Advance to the opening paren of subplots(...)
        start = stripped.index("(", idx) + 1
        depth, pos = 1, start
        while pos < len(stripped) and depth > 0:
            if stripped[pos] == "(":
                depth += 1
            elif stripped[pos] == ")":
                depth -= 1
            pos += 1
        raw = stripped[start:pos - 1].strip()

        if not raw:
            return (1, 1)  # plt.subplots() with no args

        # Split on commas respecting parentheses depth
        parts, depth, cur = [], 0, []
        for ch in raw:
            if ch == "(":
                depth += 1
                cur.append(ch)
            elif ch == ")":
                depth -= 1
                cur.append(ch)
            elif ch == "," and depth == 0:
                parts.append("".join(cur).strip())
                cur = []
            else:
                cur.append(ch)
        if cur:
            parts.append("".join(cur).strip())

        # Extract positional (non-keyword) args; None for expressions
        positional = []
        for p in parts:
            p = p.strip()
            if "=" in p:
                continue  # keyword arg
            if not p:
                continue
            try:
                positional.append(int(p))
            except ValueError:
                positional.append(None)  # expression — can't evaluate

        if len(positional) >= 2:
            return (positional[0], positional[1])
        elif len(positional) == 1:
            return (positional[0], 1)
        return (1, 1)
    return None


def _fig_var_for(rows, cols, cell_source=""):
    """Return the closest standard FIG.* name based on total plot count."""
    eff_rows = rows if rows is not None else 2
    eff_cols = cols if cols is not None else 2
    total = eff_rows * eff_cols

    if total == 1 and re.search(r"heatmap|corr", cell_source, re.I):
        return "FIG.TALL"
    if total == 1:
        return "FIG.SINGLE"
    if total == 2:
        return "FIG.DOUBLE"
    if total == 3:
        return "FIG.TRIPLE"
    if total == 4:
        return "FIG.GRID_2x2"
    return "FIG.GRID_3x2"


def step3(cells, report):
    """Inject style block and update plot cells."""
    report.append("\nStep 3 — Visualization Style:")
    changes = []

    # Find the first code cell with imports (the "setup imports cell")
    setup_idx = None
    for i, cell in enumerate(cells):
        if cell["cell_type"] == "code" and re.search(r"^\s*(?:import |from )", src(cell), re.M):
            setup_idx = i
            break

    if setup_idx is None:
        report.append("  No import cell found — skipping style injection.")
        return cells

    # Ensure seaborn is imported
    s = src(cells[setup_idx])
    if "seaborn" not in s and "sns" not in s:
        # Add after matplotlib or at end of imports
        if "matplotlib" in s:
            s = re.sub(
                r"(import matplotlib\.pyplot as plt\n)",
                r"\1import seaborn as sns\n",
                s,
            )
        else:
            s = s.rstrip() + "\nimport seaborn as sns\n"
        set_src(cells[setup_idx], s)
        report.append("  Added: import seaborn as sns")

    # Scan plot cells for figsize replacements
    fig_replacements = []  # (cell_idx, old_figsize_text, new_var)

    for i, cell in enumerate(cells):
        if cell["cell_type"] != "code":
            continue
        cs = src(cell)
        _STD_NAMES = {"FIG.SINGLE", "FIG.DOUBLE", "FIG.TRIPLE",
                      "FIG.GRID_2x2", "FIG.GRID_3x2", "FIG.TALL"}
        for m in re.finditer(r"figsize\s*=\s*(\([^)]+\)|[\w.]+)", cs):
            val = m.group(1)
            if val in _STD_NAMES:
                continue  # Already using a valid standard size
            layout = _detect_layout(cs)
            if layout is None:
                continue
            rows, cols = layout
            var = _fig_var_for(rows, cols, cs)
            fig_replacements.append((i, val, var))

    # Build the style block
    style_block = VIZ_STYLE_TEMPLATE

    # Find or replace existing style cell
    style_inserted = False
    for i, cell in enumerate(cells):
        if cell["cell_type"] == "code" and "Visualization Style" in src(cell):
            set_src(cells[i], style_block)
            style_inserted = True
            report.append(f"  Replaced existing style block (cell {i})")
            break

    if not style_inserted:
        # Insert after the setup imports cell
        cells.insert(setup_idx + 1, make_code(style_block))
        report.append(f"  Injected style block at cell {setup_idx + 1}")
        # Adjust replacement indices for the insertion
        fig_replacements = [
            (idx + 1 if idx > setup_idx else idx, old, new)
            for idx, old, new in fig_replacements
        ]

    # Apply figsize replacements
    for cidx, old_val, new_var in fig_replacements:
        s = src(cells[cidx])
        old_pattern = f"figsize={old_val}"
        new_pattern = f"figsize={new_var}"
        if old_pattern in s:
            s = s.replace(old_pattern, new_pattern, 1)
            set_src(cells[cidx], s)
            changes.append(f"Cell {cidx}: figsize {old_val} -> {new_var}")

    # Migrate old FIG_* references to FIG.* (from previous format runs)
    _old_to_new = {
        "FIG_SINGLE": "FIG.SINGLE", "FIG_DOUBLE": "FIG.DOUBLE",
        "FIG_TRIPLE": "FIG.TRIPLE", "FIG_GRID_2x2": "FIG.GRID_2x2",
        "FIG_GRID_3x2": "FIG.GRID_3x2", "FIG_TALL": "FIG.TALL",
    }
    for i, cell in enumerate(cells):
        if cell["cell_type"] != "code":
            continue
        s = src(cell)
        if "Visualization Style" in s:
            continue  # Skip the style cell itself
        changed = False
        for old, new in _old_to_new.items():
            if old in s:
                s = s.replace(old, new)
                changed = True
        if changed:
            set_src(cells[i], s)
            changes.append(f"Cell {i}: migrated FIG_* -> FIG.*")

    # Strip redundant fontsize= overrides from calls covered by rcParams
    _FONT_FUNC_RE = re.compile(
        r'\.(?:suptitle|set_title|set_xlabel|set_ylabel)\s*\('
        r'|plt\.(?:suptitle|title|xlabel|ylabel)\s*\('
    )
    for i, cell in enumerate(cells):
        if cell["cell_type"] != "code":
            continue
        s = src(cell)
        if "Visualization Style" in s:
            continue
        new_lines = []
        cell_changed = False
        for line in s.split('\n'):
            if _FONT_FUNC_RE.search(line) and 'fontsize' in line:
                orig = line
                # ", fontsize=N" (middle or end position)
                line = re.sub(r',\s*fontsize\s*=\s*\d+\.?\d*', '', line)
                # "fontsize=N, " (leading kwarg position)
                line = re.sub(r'fontsize\s*=\s*\d+\.?\d*\s*,\s*', '', line)
                if line != orig:
                    cell_changed = True
            new_lines.append(line)
        if cell_changed:
            set_src(cells[i], '\n'.join(new_lines))
            changes.append(f"Cell {i}: removed redundant fontsize overrides")

    # Wrap plot_series() calls that lack ax= with a pre-created figure
    _PLOT_SERIES_RE = re.compile(r'plot_series\s*\(')
    _IDS_RE = re.compile(r'ids\s*=\s*\[([^\]]*)\]')
    _MAX_IDS_RE = re.compile(r'max_ids\s*=\s*(\d+)')
    for i, cell in enumerate(cells):
        if cell["cell_type"] != "code":
            continue
        s = src(cell)
        if not _PLOT_SERIES_RE.search(s):
            continue
        if re.search(r'\bax\s*=', s):
            continue  # Already has ax= parameter

        # Count series from ids=[...] or max_ids=N
        n_series = 1
        ids_m = _IDS_RE.search(s)
        if ids_m:
            items = [x.strip() for x in ids_m.group(1).split(",") if x.strip()]
            n_series = len(items)
        else:
            max_m = _MAX_IDS_RE.search(s)
            if max_m:
                n_series = int(max_m.group(1))

        fig_var = _fig_var_for(n_series, 1, s)
        ax_name = "ax" if n_series == 1 else "axes"
        prepend = f"fig, {ax_name} = plt.subplots({n_series}, 1, figsize={fig_var})\n"

        # Inject ax= before the closing ) of plot_series(...)
        # Find the closing paren by tracking depth from the opening
        ps_m = _PLOT_SERIES_RE.search(s)
        start = ps_m.end()  # position right after the opening (
        depth, pos = 1, start
        while pos < len(s) and depth > 0:
            if s[pos] == "(":
                depth += 1
            elif s[pos] == ")":
                depth -= 1
            pos += 1
        close_pos = pos - 1  # position of the closing )

        # Insert ,\n    ax=axes before the closing )
        s = s[:close_pos].rstrip() + f",\n    ax={ax_name}" + s[close_pos:]
        s = prepend + s
        set_src(cells[i], s)
        changes.append(f"Cell {i}: wrapped plot_series with figsize={fig_var}")

    # Add plt.tight_layout() where missing before plt.show()
    for i, cell in enumerate(cells):
        if cell["cell_type"] != "code":
            continue
        s = src(cell)
        if "plt.show()" in s and "tight_layout" not in s:
            s = s.replace("plt.show()", "plt.tight_layout()\nplt.show()")
            set_src(cells[i], s)
            changes.append(f"Cell {i}: added tight_layout()")

    if changes:
        report.append(f"  Updated {len(changes)} plot cells:")
        for c in changes:
            report.append(f"    - {c}")
    else:
        report.append("  No plot cells needed updates.")
    return cells


# ═══════════════════════════════════════════════════════════════════
# STEP 4 — MERMAID FLOW DIAGRAM
# ═══════════════════════════════════════════════════════════════════

def _darker_hex(h, factor=0.75):
    r, g, b = (int(h.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    return f"#{int(r*factor):02x}{int(g*factor):02x}{int(b*factor):02x}"


def _light_hex(h):
    """Return a very light tint for secondary nodes."""
    tints = {
        "#2563EB": "#dbeafe", "#E11D48": "#fce7f3", "#16A34A": "#dcfce7",
        "#F59E0B": "#fef9c3", "#8B5CF6": "#ede9fe", "#06B6D4": "#cffafe",
        "#EC4899": "#fce7f3", "#84CC16": "#ecfccb",
    }
    return tints.get(h, "#f3f4f6")


def step4(cells, plan, nb_path, report, title_idx=None):
    """Generate Mermaid flow diagram and matplotlib PNG code."""
    report.append("\nStep 4 — Mermaid Flow Diagram:")

    sections = []  # (num, title, color, [(sub_num, sub_title)])
    color_idx = 0
    for _, eff, num, title, _ in plan:
        if eff == 2:
            sections.append((num, title, PALETTE[color_idx % len(PALETTE)], []))
            color_idx += 1
        elif eff == 3 and sections:
            short = title[:25] + "..." if len(title) > 28 else title
            sections[-1][3].append((num, short))

    if not sections:
        report.append("  No sections found — skipping diagram.")
        return cells

    direction = "LR" if len(sections) <= 6 else "TD"

    # Build Mermaid code
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    mermaid_lines = [f"graph {direction}"]
    node_styles = []

    for i, (num, title, color, subs) in enumerate(sections):
        nid = letters[i % 26]
        short = title[:25] + "..." if len(title) > 28 else title
        mermaid_lines.append(f'    {nid}["{num}. {short}"]')
        node_styles.append(
            f"    style {nid} fill:{color},stroke:{_darker_hex(color)},color:#fff"
        )
        if i < len(sections) - 1:
            next_id = letters[(i + 1) % 26]
            # Connect through last sub if subs exist
            connector = nid
            if subs:
                last_sub = f"{nid}{len(subs)}"
                connector = last_sub
            mermaid_lines.append(f"    {connector} --> {next_id}")

        for j, (snum, stitle) in enumerate(subs):
            sid = f"{nid}{j + 1}"
            mermaid_lines.append(f'    {nid} --> {sid}["{snum} {stitle}"]')
            node_styles.append(
                f"    style {sid} fill:{_light_hex(color)},stroke:{color},color:#333"
            )

    mermaid_src = "\n".join(mermaid_lines + [""] + node_styles)

    # Determine image path relative to notebook
    nb_dir = Path(nb_path).resolve().parent
    repo_root = Path.cwd().resolve()
    img_dir = repo_root / "images"
    img_rel = os.path.relpath(img_dir, nb_dir)
    nb_stem = Path(nb_path).stem  # e.g. "mod20_ensemble_GenAI"
    img_name = f"{nb_stem}_flow.png"
    img_file = f"{img_rel}/{img_name}"

    # Generate PNG directly at format-time
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    img_dir.mkdir(parents=True, exist_ok=True)
    img_abs = img_dir / img_name

    def _hex_rgb(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16)/255 for i in (0, 2, 4))

    def _tint(h, mix=0.8):
        r, g, b = _hex_rgb(h)
        return (r+(1-r)*mix, g+(1-g)*mix, b+(1-b)*mix)

    def _dark(h, f=0.75):
        r, g, b = _hex_rgb(h)
        return (r*f, g*f, b*f)

    plot_sections = []
    for num, title, color, subs in sections:
        short = title[:25] + "..." if len(title) > 28 else title
        plot_sections.append((short, color, [(s[1],) for s in subs]))

    n = len(plot_sections)
    fig, ax = plt.subplots(figsize=(max(12, n*2.5), 6))
    ax.set_xlim(-1, n*2.2+0.5)
    max_subs = max((len(s[2]) for s in plot_sections), default=0)
    ax.set_ylim(-1.5 - max_subs*0.7, 2.5)
    ax.axis('off')

    bw, bh = 1.6, 0.55
    y0 = 1.0
    xs = [i*2.2 for i in range(n)]

    for i, (label, color, subs_list) in enumerate(plot_sections):
        x = xs[i]
        box = FancyBboxPatch((x-bw/2, y0-bh/2), bw, bh,
            boxstyle='round,pad=0.1', facecolor=color,
            edgecolor=_dark(color), linewidth=1.8)
        ax.add_patch(box)
        ax.text(x, y0, label, ha='center', va='center',
                fontsize=8, fontweight='bold', color='white')
        if i < n-1:
            ax.annotate('', xy=(xs[i+1]-bw/2-0.05, y0),
                xytext=(x+bw/2+0.05, y0),
                arrowprops=dict(arrowstyle='->', color='#555', lw=1.8))
        for j, (sub_label,) in enumerate(subs_list):
            sy = y0 - 1.0 - j*0.7
            sb = FancyBboxPatch((x-bw/2+0.1, sy-bh/2+0.05),
                bw-0.2, bh-0.1, boxstyle='round,pad=0.05',
                facecolor=_tint(color), edgecolor=color, linewidth=1.2)
            ax.add_patch(sb)
            ax.text(x, sy, sub_label, ha='center', va='center',
                    fontsize=7.5, color='#333')
            ax.annotate('', xy=(x, sy+bh/2-0.05), xytext=(x, y0-bh/2),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.0))

    ax.set_title('Notebook Workflow', fontsize=14, fontweight='bold', pad=12)
    plt.tight_layout()
    plt.savefig(str(img_abs), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    # Markdown cell
    md_cell_text = f"""#### Notebook Workflow

![Notebook Workflow]({img_file})"""

    # Find insertion point: directly after the Table of Contents cell
    insert_at = None
    for i, cell in enumerate(cells):
        if cell["cell_type"] == "markdown" and "Table of Contents" in src(cell):
            insert_at = i + 1
            break
    # Fallback: after title cell, or after first cell
    if insert_at is None:
        insert_at = (title_idx or 0) + 1

    # Remove existing diagram cells first
    to_remove = []
    for i, cell in enumerate(cells):
        s = src(cell)
        if "AUTO-GENERATED: Notebook flow diagram" in s:
            to_remove.append(i)
        elif cell["cell_type"] == "markdown" and "Notebook Workflow" in s and "mermaid" in s.lower():
            to_remove.append(i)
    for i in sorted(to_remove, reverse=True):
        cells.pop(i)
        if i < insert_at:
            insert_at -= 1

    cells.insert(insert_at, make_md(md_cell_text))

    n_secs = len(sections)
    n_subs = sum(len(s[3]) for s in sections)
    report.append(f"  Generated {direction} flowchart: {n_secs} sections, {n_subs} subsections")
    report.append(f"  Mermaid markdown cell inserted (PNG generated at {img_abs})")
    return cells


# ═══════════════════════════════════════════════════════════════════
# STEP 5 — SPELLING & POLISH
# ═══════════════════════════════════════════════════════════════════

def step5(cells, report, use_ai=False):
    """Fix common misspellings in markdown and code comments."""
    report.append("\nStep 5 — Spelling & Polish:")

    if use_ai:
        report.append("  --ai not yet implemented for Step 5. Using dictionary.")

    fixes = []
    for i, cell in enumerate(cells):
        s = src(cell)
        new_s = s
        for wrong, right in MISSPELLINGS.items():
            pattern = re.compile(r"\b" + re.escape(wrong) + r"\b", re.IGNORECASE)

            def _replacer(m, _right=right, _i=i, _cell=cell):
                original = m.group(0)
                if original[0].isupper():
                    repl = _right[0].upper() + _right[1:]
                else:
                    repl = _right
                ct = "markdown" if _cell["cell_type"] == "markdown" else "code"
                fixes.append(f'Cell {_i} ({ct}): "{original}" -> "{repl}"')
                return repl

            new_s = pattern.sub(_replacer, new_s)

        if new_s != s:
            set_src(cells[i], new_s)

    if fixes:
        for f in fixes:
            report.append(f"  - {f}")
        report.append(f"  Total: {len(fixes)} fixes")
    else:
        report.append("  All text is clean — no spelling changes needed.")
    return cells


# ═══════════════════════════════════════════════════════════════════
# STEP 6 — FUNCTION DOCUMENTATION
# ═══════════════════════════════════════════════════════════════════

def _infer_type(param_name, default=None):
    """Infer a type hint from parameter name and default value."""
    # From default value
    if default is not None:
        d = default.strip()
        if d in ("True", "False"):
            return "bool"
        if d == "None":
            return "Optional[Any]"
        if re.match(r"^-?\d+$", d):
            return "int"
        if re.match(r"^-?\d+\.\d+$", d):
            return "float"
        if d.startswith(("'", '"')):
            return "str"
        if d.startswith("["):
            return "list"
        if d.startswith("{"):
            return "dict"

    # From name
    if param_name in TYPE_BY_NAME:
        return TYPE_BY_NAME[param_name]

    # From prefix
    for prefix, typ in TYPE_BY_PREFIX:
        if param_name.startswith(prefix):
            return typ

    # Patterns
    if param_name.endswith(("_df", "_data")):
        return "pd.DataFrame"
    if param_name.endswith(("_path", "_file", "_dir")):
        return "str"
    if param_name.endswith(("_size", "_count", "_len", "_idx")):
        return "int"

    return None


def _infer_return_type(body):
    """Infer return type from function body."""
    returns = re.findall(r"^\s*return\s+(.+)", body, re.MULTILINE)
    if not returns:
        return "None"
    last = returns[-1].strip()
    if last.startswith("pd.DataFrame") or "DataFrame" in last:
        return "pd.DataFrame"
    if last.startswith("np."):
        return "np.ndarray"
    if last.startswith(("{",)):
        return "dict"
    if last.startswith(("[",)):
        return "list"
    if last.startswith(("True", "False")):
        return "bool"
    return None


def _make_docstring(func_name):
    """Generate a simple docstring from function name."""
    words = func_name.replace("_", " ").strip().split()
    if not words:
        return "Perform the operation."
    # Capitalise first word as verb
    words[0] = words[0].capitalize()
    return " ".join(words) + "."


def step6(cells, report, use_ai=False):
    """Add type hints and docstrings to functions."""
    report.append("\nStep 6 — Function Documentation:")

    if use_ai:
        report.append("  --ai not yet implemented for Step 6. Using heuristics.")

    documented = []
    typing_needed = set()

    for i, cell in enumerate(cells):
        if cell["cell_type"] != "code":
            continue
        s = src(cell)
        # Skip auto-generated cells (e.g. Mermaid diagram)
        if "AUTO-GENERATED" in s:
            continue
        # Find function definitions
        for m in re.finditer(
            r"^([ \t]*)def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*\S+\s*)?:", s, re.MULTILINE
        ):
            indent = m.group(1)
            fname = m.group(2)
            params_str = m.group(3)
            full_match = m.group(0)

            # Skip if already has type hints
            if ":" in params_str and not params_str.strip().startswith("self"):
                # Check if it looks like type annotations (not dict defaults)
                type_hint_like = re.search(r"\w+\s*:\s*(?!.*=)", params_str)
                if type_hint_like:
                    documented.append(f"{fname}() — already has type hints (skipped)")
                    continue

            # Parse params
            params = []
            for p in re.split(r",\s*", params_str):
                p = p.strip()
                if not p or p == "self":
                    params.append(("self", None, None))
                    continue
                eq = p.split("=", 1)
                pname = eq[0].strip().split(":")[0].strip()
                default = eq[1].strip() if len(eq) > 1 else None
                typ = _infer_type(pname, default)
                if typ and "Optional" in typ:
                    typing_needed.add("Optional")
                    typing_needed.add("Any")
                params.append((pname, typ, default))

            # Infer return type
            # Find function body (from def line to next def or end)
            def_end = m.end()
            next_def = re.search(r"^(?:[ \t]*)def\s+", s[def_end:], re.MULTILINE)
            body = s[def_end : def_end + next_def.start()] if next_def else s[def_end:]
            ret_type = _infer_return_type(body)

            # Check for existing docstring
            has_docstring = re.match(r'\s*"""', body) or re.match(r"\s*'''", body)

            # Build new signature
            typed_params = []
            hints_added = 0
            for pname, typ, default in params:
                if pname == "self":
                    typed_params.append("self")
                    continue
                p_str = pname
                if typ:
                    p_str += f": {typ}"
                    hints_added += 1
                if default is not None:
                    p_str += f" = {default}"
                typed_params.append(p_str)

            ret_str = f" -> {ret_type}" if ret_type else ""

            # Format signature
            sig = f"{indent}def {fname}({', '.join(typed_params)}){ret_str}:"
            if len(sig) > 88:
                inner = f",\n{indent}    ".join(typed_params)
                sig = f"{indent}def {fname}(\n{indent}    {inner},\n{indent}){ret_str}:"

            # Build replacement
            new_block = sig
            if not has_docstring:
                doc = _make_docstring(fname)
                new_block += f'\n{indent}    """{doc}"""'

            # Replace in source
            s = s.replace(full_match, new_block, 1)
            set_src(cells[i], s)
            documented.append(
                f"{fname}({', '.join(p[0] for p in params if p[0] != 'self')})"
                f" -> {hints_added} type hints"
                + (" + docstring" if not has_docstring else "")
            )

    # Add typing imports if needed
    if typing_needed:
        for i, cell in enumerate(cells):
            if cell["cell_type"] == "code" and re.search(r"^\s*import ", src(cell), re.M):
                s = src(cell)
                existing = re.search(r"from typing import (.+)", s)
                if existing:
                    # Add missing types
                    current = {t.strip() for t in existing.group(1).split(",")}
                    needed = typing_needed - current
                    if needed:
                        all_types = sorted(current | needed)
                        s = s.replace(
                            existing.group(0),
                            f"from typing import {', '.join(all_types)}",
                        )
                        set_src(cells[i], s)
                else:
                    types_str = ", ".join(sorted(typing_needed))
                    s = s.rstrip() + f"\nfrom typing import {types_str}\n"
                    set_src(cells[i], s)
                break

    if documented:
        report.append(f"  Documented {len(documented)} functions:")
        for d in documented:
            report.append(f"    - {d}")
    else:
        report.append("  No undocumented functions found.")
    return cells


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Format a Jupyter notebook with standardised structure and style."
    )
    parser.add_argument("notebook", help="Path to .ipynb file")
    parser.add_argument(
        "--steps",
        default="1,2,3,4,5,6",
        help="Comma-separated step numbers to run (default: 1,2,3,4,5,6)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print report without saving"
    )
    parser.add_argument(
        "--ai", action="store_true", help="Use Anthropic API for Steps 5-6"
    )
    args = parser.parse_args()

    nb_path = args.notebook
    if not os.path.isfile(nb_path):
        print(f"Error: {nb_path} not found", file=sys.stderr)
        sys.exit(1)

    steps = {int(s.strip()) for s in args.steps.split(",")}

    with open(nb_path) as f:
        nb = json.load(f)

    cells = nb["cells"]
    report = [f"Formatting: {nb_path}"]
    report.append(f"Steps: {sorted(steps)}")
    report.append(f"Cells before: {len(cells)}")

    # Always analyze headings (needed by steps 3, 4)
    plan, title_idx = analyze_headings(cells)

    if 1 in steps:
        cells = step1(cells, plan, title_idx, report)
        # Re-analyze after step 1 modifications (indices may have shifted)
        plan, title_idx = analyze_headings(cells)

    if 2 in steps:
        cells = step2(cells, report)

    if 3 in steps:
        cells = step3(cells, report)
        # Re-analyze after possible cell insertions
        plan, title_idx = analyze_headings(cells)

    if 4 in steps:
        cells = step4(cells, plan, nb_path, report, title_idx=title_idx)

    if 5 in steps:
        cells = step5(cells, report, use_ai=args.ai)

    if 6 in steps:
        cells = step6(cells, report, use_ai=args.ai)

    report.append(f"\nCells after: {len(cells)}")

    # Print report
    print("=" * 60)
    print("NOTEBOOK FORMATTER")
    print("=" * 60)
    for line in report:
        print(line)

    if args.dry_run:
        print("\n[DRY RUN] No changes written.")
    else:
        import shutil
        shutil.copy2(nb_path, nb_path + ".bak")
        os.makedirs(Path(nb_path).resolve().parent / "images", exist_ok=True)
        nb["cells"] = cells
        with open(nb_path, "w") as f:
            json.dump(nb, f, indent=1, ensure_ascii=False)
        print(f"\nBackup: {nb_path}.bak")
        print(f"Saved: {nb_path}")


if __name__ == "__main__":
    main()
