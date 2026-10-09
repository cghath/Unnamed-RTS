"""
Sanity checks for blender/ship_generator.py — run after changing settings:

    python tools/check_ships.py

Checks every class for: valid outward-facing geometry, unique object names,
craft fitting their launchers / doors / bays, legal default loadouts, and that
every room, ramp end and elevator lobby on every deck can be walked to from
the deck's spawn point (with all breachable walls and locked doors open).
"""
import math
import os
import sys
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blender"))
import ship_generator as sg  # noqa: E402

problems = []


def signed_volume(v, f):
    vol = 0.0
    for face in f:
        a = v[face[0]]
        for i in range(1, len(face) - 1):
            b, c = v[face[i]], v[face[i + 1]]
            vol += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
                    + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6
    return vol


def extents(parts, axis):
    pts = [v for p in parts for v in sg._world_verts(p)]
    return max(v[axis] for v in pts) - min(v[axis] for v in pts)


# ------------------------------------------------------------------ geometry & names
for cls in sg.SHIP_CLASSES:
    parts, markers, info = sg.generate(cls)
    for p in parts:
        if p.material not in sg.materials():
            problems.append(f"{cls}: {p.name} uses unknown material {p.material}")
        for v, f in p.solids:
            if signed_volume(v, f) < -1e-9:
                problems.append(f"{cls}: inside-out solid in {p.name}")
                break
    names = [p.name for p in parts] + [f"{cls}_{m[0]}" for m in markers]
    if len(names) != len(set(names)):
        problems.append(f"{cls}: duplicate object names")
    if max(len(n) for n in names) > 63:
        problems.append(f"{cls}: an object name is longer than Blender's 63 characters")
    lo = info["stats"].get("loadout")
    if lo and lo["problems"]:
        problems.append(f"{cls}: default loadout invalid: {lo['problems']}")

# ------------------------------------------------------------------ fit checks
pod = sg.generate("XS_POD")[0]
if not (extents(pod, 1) < sg.POD_PITCH - 1.0 and extents(pod, 0) < 3.2 and extents(pod, 2) < sg.DECK_H - 0.6):
    problems.append("boarding pod does not fit its troop-deck cradle")
pod_body = [p for p in pod if p.name.endswith(("Hull-col", "Hazard"))]
if not (extents(pod_body, 0) < sg.BREACH_W and extents(pod_body, 2) < sg.BREACH_H):
    problems.append("boarding pod nose does not fit a breach panel")
dp = sg.generate("XS_DROPPOD")[0]
if not (extents(dp, 0) < 2.0 and extents(dp, 1) < 2.0):
    problems.append("drop pod does not fit its hatch")
dt = sg.generate("XS_DARTER")[0]
ds = sg.generate("XS_DROPSHIP")[0]
for cls, cfg in sg.CLASSES.items():
    HD = cfg.get("tall_decks", sg.HANGAR_DECKS)
    hw = sg.CORRIDOR_W / 2 + sg.WALL_T + cfg["room_depth"]
    if cfg.get("cargo_segs"):
        door_h = (HD * sg.DECK_H - 1.2 if HD > 1 else sg.DECK_H - 0.4) - 0.2
        door_len = cfg["cargo_segs"] * sg.SEG_LEN - 1.6
        if not (extents(dt, 2) < door_h and extents(dt, 0) * cfg["cargo_segs"] < door_len
                and extents(dt, 1) < 2 * hw):
            problems.append(f"{cls}: Darters don't fit the cargo bay")
    if cfg["hangar_segs"]:
        open_len = cfg["hangar_segs"] * sg.SEG_LEN - 2.0
        if not (extents(ds, 0) < open_len and extents(ds, 2) < HD * sg.DECK_H - 1.7 and extents(ds, 1) < 2 * hw):
            problems.append(f"{cls}: dropship doesn't fit the hangar")

# ------------------------------------------------------------------ walkability
BLOCKERS = ("Interior-col", "Hull-col", "Furniture-col", "Medical-col", "Cover-col", "Railings-col",
            "Glass-col", "Decks-col", "Reactor-col", "ReadyLockers-col")
SKIP = ("PodTarget", "Approach", "Elevator_", "Bed_", "Ramp_", "EVAEntry", "DropshipDock", "Charge",
        "DockingClamp", "MissileBank", "PodTube", "PodSilo", "_Exit", "SpineGun", "DorsalPodBattery")


def walk_check(cls):
    parts, markers, info = sg.generate(cls)
    H, R, cell = sg.DECK_H, 0.3, 0.2
    x0, y0 = -info["ox"] - 1, info["yb"] - 1
    nx, ny = int((2 * info["ox"] + 2) / cell), int((info["yf"] - info["yb"] + 2) / cell)
    out = []
    for k in range(-1, info["decks"]):                # -1 = the troop deck
        zlo, zhi = k * H + 0.35, k * H + 1.8
        grid = [[False] * ny for _ in range(nx)]
        for p in parts:
            base = p.name[len(cls) + 1:]
            if not (base in BLOCKERS or base.startswith(("BreachPanel", "Elevator_"))):
                continue
            for v, f in p.solids:
                wv = [(x + p.origin[0], y + p.origin[1], z + p.origin[2]) for x, y, z in v]
                zs = [q[2] for q in wv]
                if max(zs) <= zlo or min(zs) >= zhi:
                    continue
                xs, ys = [q[0] for q in wv], [q[1] for q in wv]
                for i in range(max(0, int((min(xs) - R - x0) / cell)), min(nx - 1, int((max(xs) + R - x0) / cell)) + 1):
                    row = grid[i]
                    for j in range(max(0, int((min(ys) - R - y0) / cell)), min(ny - 1, int((max(ys) + R - y0) / cell)) + 1):
                        row[j] = True

        def cell_of(x, y):
            return int((x - x0) / cell), int((y - y0) / cell)
        start = cell_of(0, info["seg_c"](info["aft_segs"] + 1))
        seen = {start}
        q = deque([start])
        while q:
            i, j = q.popleft()
            for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                if 0 <= a < nx and 0 <= b < ny and not grid[a][b] and (a, b) not in seen:
                    seen.add((a, b))
                    q.append((a, b))
        targets = [(m[0], m[1][0], m[1][1]) for m in markers
                   if len(m) == 2 and abs(m[1][2] - k * H) < 1.0 and not any(t in m[0] for t in SKIP)]
        for (rk, s, side) in info["ramps"]:
            ya0, ya1 = info["seg_y"](s)
            if rk == k:
                targets.append((f"ramp{rk} bottom", side * (info["hw"] - 1.4), ya0 + 0.8))
            if rk + 1 == k:
                targets.append((f"ramp{rk} top", side * (info["hw"] - 1.4), ya1 - 0.8))
        bad = [t[0] for t in targets if cell_of(t[1], t[2]) not in seen]
        if bad:
            out.append(f"{cls} deck {k}: can't reach {bad}")
    return out


VARIANTS = [int(a) for a in sys.argv[1:]] or [0, 1, 2, 3]
for v in VARIANTS:
    sg.VARIANT = v
    for cls in sg.CLASSES:
        problems += [f"v{v} {p}" for p in walk_check(cls)]
sg.VARIANT = 0

if problems:
    print("PROBLEMS FOUND:")
    for p in problems:
        print("  -", p)
    sys.exit(1)
print(f"All checks passed for {len(sg.SHIP_CLASSES)} classes, layout variants {VARIANTS}.")
