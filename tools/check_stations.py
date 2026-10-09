"""
Sanity checks for the stations built by blender/ship_generator.py:

    python tools/check_stations.py

For every station, outpost and ground base (and every module on its own):
valid outward-facing geometry, unique names, the module list matching the
economy data, and that you can walk from the root module's control room to
every module's control room, crew room, ready locker and sabotage point through
the hubs and connector tubes (connector doors counted as open).
"""
import os
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "blender"))
sys.path.insert(0, os.path.join(HERE, "..", "economy"))
import ship_generator as sg  # noqa: E402
import economy_data as E     # noqa: E402

problems = []
BLOCK_SUFFIXES = ("Hull-col", "Interior-col", "Furniture-col", "Cover-col", "Machinery-col", "Glass-col",
                  "ControlConsole-col", "Asteroid-col")
TARGETS = ("ControlRoom", "CrewRoom", "ReadyLocker", "Hub", "Garrison", "Operations", "_Inside")
ROOT_SUFFIX = "_ControlRoom"


def signed_volume(v, f):
    vol = 0.0
    for face in f:
        a = v[face[0]]
        for i in range(1, len(face) - 1):
            b, c = v[face[i]], v[face[i + 1]]
            vol += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
                    + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6
    return vol


def walk(cls, parts, markers):
    cell, R = 0.25, 0.3
    pts = [p for q in parts for v, _ in q.solids for p in v]
    x0, y0 = min(p[0] for p in pts) - 1, min(p[1] for p in pts) - 1
    nx = int((max(p[0] for p in pts) + 1 - x0) / cell) + 1
    ny = int((max(p[1] for p in pts) + 1 - y0) / cell) + 1
    grid = bytearray(nx * ny)
    for q in parts:
        if not q.name.endswith(BLOCK_SUFFIXES):
            continue
        for v, _ in q.solids:
            wv = [(x + q.origin[0], y + q.origin[1], z + q.origin[2]) for x, y, z in v]
            zs = [p[2] for p in wv]
            if max(zs) <= 0.35 or min(zs) >= 1.8:
                continue
            xs, ys = [p[0] for p in wv], [p[1] for p in wv]
            i0, i1 = max(0, int((min(xs) - R - x0) / cell)), min(nx - 1, int((max(xs) + R - x0) / cell))
            j0, j1 = max(0, int((min(ys) - R - y0) / cell)), min(ny - 1, int((max(ys) + R - y0) / cell))
            for i in range(i0, i1 + 1):
                base = i * ny
                for j in range(j0, j1 + 1):
                    grid[base + j] = 1
    cell_of = lambda x, y: (int((x - x0) / cell), int((y - y0) / cell))
    root = next(pos for n, pos in markers if n.startswith("M01") and n.endswith(ROOT_SUFFIX))
    s = cell_of(root[0], root[1])
    if grid[s[0] * ny + s[1]]:
        return [f"{cls}: root control room marker is inside something solid"]
    seen = bytearray(nx * ny)
    seen[s[0] * ny + s[1]] = 1
    q = deque([s])
    while q:
        i, j = q.popleft()
        for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
            if 0 <= a < nx and 0 <= b < ny:
                k = a * ny + b
                if not grid[k] and not seen[k]:
                    seen[k] = 1
                    q.append((a, b))
    bad = []
    for n, pos in markers:
        if len(pos) != 3 or abs(pos[2]) > 0.5:
            continue
        if not (n.endswith(TARGETS) or ("SabotagePoint_" in n and not n.endswith("ChargeA"))):
            continue
        i, j = cell_of(pos[0], pos[1])
        if not (0 <= i < nx and 0 <= j < ny and seen[i * ny + j]):
            bad.append(n)
    return [f"{cls}: can't walk to {bad}"] if bad else []


for cls in list(sg.STATION_KITS) + [f"MODULE_{m}" for m in sg.MODULE_SPECS]:
    parts, markers, info = sg.generate(cls)
    names = [p.name for p in parts] + [f"{cls}_{m[0]}" for m in markers]
    if len(names) != len(set(names)):
        problems.append(f"{cls}: duplicate names")
    if max(len(n) for n in names) > 63:
        problems.append(f"{cls}: a name is longer than Blender's 63 characters "
                        f"({max(names, key=len)})")
    for p in parts:
        if p.material not in sg.materials():
            problems.append(f"{cls}: unknown material {p.material}")
        for v, f in p.solids:
            if signed_volume(v, f) < -1e-9:
                problems.append(f"{cls}: inside-out solid in {p.name}")
                break
    problems += walk(cls, parts, [m for m in markers if len(m) == 2])

# the generator's module list must agree with the economy data
for m, (sections, decks, sab) in sg.MODULE_SPECS.items():
    d = E.MODULES.get(m)
    if not d:
        problems.append(f"module {m} is not in economy_data.MODULES")
    elif tuple(d["interior"]) != (sections, decks) or d["sabotage_points"] != sab:
        problems.append(f"module {m}: size/sabotage points differ from economy_data")
for m in E.MODULES:
    if m not in sg.MODULE_SPECS:
        problems.append(f"economy module {m} has no 3D model")
if sg.STATION_KITS["STATION_HOME"] != E.HOME_STATION["modules"]:
    problems.append("STATION_HOME differs from economy_data.HOME_STATION")
for kit, key in (("STATION_INDUSTRIAL", "industrial_station"), ("STATION_FORTRESS", "fortress"),
                 ("STATION_FUEL_HUB", "fuel_hub")):
    if sg.STATION_KITS[kit] != E.CONSTRUCTION["station_kits"][key]:
        problems.append(f"{kit} differs from economy_data station kit {key}")
for kit, key in (("OUTPOST_MINING", "mining_outpost"), ("OUTPOST_SKIMMER", "skimmer_outpost"),
                 ("GROUND_MINE", "ground_mine"), ("GROUND_FORT", "ground_fort")):
    if sg.STATION_KITS[kit] != E.CONSTRUCTION["outpost_kits"][key]:
        problems.append(f"{kit} differs from economy_data outpost kit {key}")

if problems:
    print("PROBLEMS FOUND:")
    for p in problems:
        print("  -", p)
    sys.exit(1)
print(f"All station checks passed ({len(sg.STATION_KITS)} kits, {len(sg.MODULE_SPECS)} modules).")
