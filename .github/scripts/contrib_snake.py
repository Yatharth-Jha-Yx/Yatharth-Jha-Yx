"""Draw the GitHub contribution calendar (as it appears on a profile) with a
snake that slides across it and eats every square that has contributions.

Usage: GH_TOKEN=... python contrib_snake.py <github-user> <output-dir>
Writes github-snake.svg (light) and github-snake-dark.svg (dark).
Standard library only.
"""
import datetime as dt
import json
import os
import sys
import urllib.request

QUERY = """query($login:String!){user(login:$login){contributionsCollection{
contributionCalendar{totalContributions weeks{contributionDays{
date weekday contributionCount contributionLevel}}}}}}"""

LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]

THEMES = {
    "light": dict(
        bg="#ffffff", border="#d1d9e0", fg="#1f2328", muted="#59636e",
        cells=["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
        cell_stroke="rgba(31,35,40,0.05)", snake=["#6639ba", "#8250df"],
    ),
    "dark": dict(
        bg="#0d1117", border="#3d444d", fg="#f0f6fc", muted="#9198a1",
        cells=["#151b23", "#033a16", "#196c2e", "#2ea043", "#56d364"],
        cell_stroke="rgba(240,246,252,0.05)", snake=["#a371f7", "#bc8cff"],
    ),
}

FONT = ('-apple-system,BlinkMacSystemFont,&quot;Segoe UI&quot;,&quot;Noto Sans&quot;,'
        'Helvetica,Arial,sans-serif')

CELL, GAP = 10, 3
PITCH = CELL + GAP
PAD = 16            # inner padding of the bordered box
LABEL_W = 28        # width of the Mon/Wed/Fri column
HEADER_H = 34       # "N contributions in the last year" + gap
STEP = 0.11         # seconds per snake move
SEGMENTS = 5
PAUSE_STEPS = 18    # empty board is held this many steps before it refills


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "contrib-snake"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def snake_path(cells, weeks):
    """Greedy walk from off-grid left to the nearest uneaten square, then off right.
    Returns the list of (col, row) positions and {cell: step it is eaten at}."""
    todo = set(cells)
    start_row = min(todo)[1] if todo else 3
    pos = (-(SEGMENTS + 1), start_row)
    path, eaten = [pos], {}

    def walk_to(target):
        nonlocal pos
        while pos != target:
            c, r = pos
            if c != target[0]:
                c += 1 if target[0] > c else -1
            else:
                r += 1 if target[1] > r else -1
            pos = (c, r)
            path.append(pos)
            if pos in todo:
                todo.discard(pos)
                eaten[pos] = len(path) - 1

    while todo:
        c0, r0 = pos
        target = min(todo, key=lambda p: (abs(p[0] - c0) + abs(p[1] - r0), p[0], p[1]))
        walk_to(target)
    walk_to((weeks + SEGMENTS + 1, pos[1]))
    return path, eaten


def pct(step, total):
    return f"{step / total * 100:.4f}".rstrip("0").rstrip(".") + "%"


def render(cal, theme):
    t = THEMES[theme]
    weeks = cal["weeks"]
    nweeks = len(weeks)
    width = PAD + LABEL_W + nweeks * PITCH - GAP + PAD
    box_y = HEADER_H
    month_y = box_y + 26
    grid_x, grid_y = PAD + LABEL_W, box_y + 34
    foot_y = grid_y + 7 * PITCH - GAP + 24
    box_h = foot_y - box_y + 14
    height = box_y + box_h + 1

    level_of, cells = {}, []
    for ci, w in enumerate(weeks):
        for d in w["contributionDays"]:
            lvl = LEVELS.index(d["contributionLevel"])
            level_of[(ci, d["weekday"])] = lvl
            if lvl > 0:
                cells.append((ci, d["weekday"]))

    path, eaten = snake_path(cells, nweeks)
    run_steps = len(path) - 1 + SEGMENTS
    total_steps = run_steps + PAUSE_STEPS
    dur = total_steps * STEP

    def xy(col, row):
        return grid_x + col * PITCH, grid_y + row * PITCH

    css = [f"text{{font-family:{FONT}}}",
           f".h{{font-size:16px;fill:{t['fg']}}}",
           f".m{{font-size:12px;fill:{t['muted']}}}",
           f".c{{stroke:{t['cell_stroke']};stroke-width:1}}",
           f".s{{animation:mv {dur:.2f}s linear infinite}}"]

    # snake keyframes: only the points where it changes direction
    keep = [0]
    for i in range(1, len(path) - 1):
        a, b, c = path[i - 1], path[i], path[i + 1]
        if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1]):
            keep.append(i)
    keep.append(len(path) - 1)
    x0, y0 = xy(*path[0])
    frames = []
    for i in keep:
        x, y = xy(*path[i])
        frames.append(f"{pct(i, total_steps)}{{transform:translate({x - x0}px,{y - y0}px)}}")
    xe, ye = xy(*path[-1])
    frames.append(f"100%{{transform:translate({xe - x0}px,{ye - y0}px)}}")
    css.append("@keyframes mv{" + "".join(frames) + "}")

    # each eaten square empties when the head reaches it and refills at the loop end
    empty = t["cells"][0]
    eat_class = {}
    for n, (cell, step) in enumerate(sorted(eaten.items(), key=lambda kv: kv[1])):
        col = t["cells"][level_of[cell]]
        a, b = pct(step, total_steps), pct(step + 0.6, total_steps)
        z = pct(total_steps - 2, total_steps)
        css.append(f"@keyframes e{n}{{0%,{a}{{fill:{col}}}{b},{z}{{fill:{empty}}}100%{{fill:{col}}}}}"
                   f".e{n}{{animation:e{n} {dur:.2f}s linear infinite}}")
        eat_class[cell] = f"e{n}"

    total = cal["totalContributions"]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
           f'viewBox="0 0 {width} {height}" role="img" '
           f'aria-label="{total} contributions in the last year">',
           "<style>" + "".join(css) + "</style>",
           f'<defs><clipPath id="g"><rect x="{grid_x - 1}" y="{grid_y - 1}" '
           f'width="{nweeks * PITCH - GAP + 2}" height="{7 * PITCH - GAP + 2}"/></clipPath></defs>',
           f'<text class="h" x="0" y="20">{total:,} contribution{"s" if total != 1 else ""} '
           f'in the last year</text>',
           f'<rect x="0.5" y="{box_y + 0.5}" width="{width - 1}" height="{box_h}" rx="6" '
           f'fill="{t["bg"]}" stroke="{t["border"]}"/>']

    # month labels (a label that would collide with the next one is dropped, like GitHub)
    labels, prev = [], None
    for ci, w in enumerate(weeks):
        m = dt.date.fromisoformat(w["contributionDays"][0]["date"]).strftime("%b")
        if m != prev:
            labels.append((ci, m))
            prev = m
    for i, (ci, m) in enumerate(labels):
        nxt = labels[i + 1][0] if i + 1 < len(labels) else nweeks + 1
        if nxt - ci < 3:
            continue
        out.append(f'<text class="m" x="{grid_x + ci * PITCH}" y="{month_y}">{m}</text>')
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text class="m" x="{PAD}" y="{grid_y + row * PITCH + 9}">{name}</text>')

    for (ci, row), lvl in sorted(level_of.items()):
        x, y = xy(ci, row)
        cls = "c " + eat_class[(ci, row)] if (ci, row) in eat_class else "c"
        out.append(f'<rect class="{cls}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                   f'rx="2" fill="{t["cells"][lvl]}"/>')

    # snake: every segment runs the same keyframes, one step behind the one in front
    out.append('<g clip-path="url(#g)">')
    for k in reversed(range(SEGMENTS)):
        size = CELL - k * 0.5
        off = (CELL - size) / 2
        colr = t["snake"][0] if k == 0 else t["snake"][1]
        out.append(f'<rect class="s" x="{x0 + off}" y="{y0 + off}" width="{size}" height="{size}" '
                   f'rx="2.5" fill="{colr}" style="animation-delay:{k * STEP:.2f}s"/>')
    out.append("</g>")

    out.append(f'<text class="m" x="{PAD}" y="{foot_y}">Learn how we count contributions</text>')
    more_x = width - PAD
    out.append(f'<text class="m" x="{more_x}" y="{foot_y}" text-anchor="end">More</text>')
    lx = more_x - 32 - 5 * PITCH
    for i, c in enumerate(t["cells"]):
        out.append(f'<rect class="c" x="{lx + i * PITCH}" y="{foot_y - 9}" width="{CELL}" '
                   f'height="{CELL}" rx="2" fill="{c}"/>')
    out.append(f'<text class="m" x="{lx - 5}" y="{foot_y}" text-anchor="end">Less</text>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    login, out_dir = sys.argv[1], sys.argv[2]
    cal = fetch(login, os.environ["GH_TOKEN"])
    os.makedirs(out_dir, exist_ok=True)
    for theme, name in (("light", "github-snake.svg"), ("dark", "github-snake-dark.svg")):
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
            f.write(render(cal, theme))
    print(f"{cal['totalContributions']} contributions, {len(cal['weeks'])} weeks -> {out_dir}")


if __name__ == "__main__":
    main()
