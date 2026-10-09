"""
Galaxy generator: a fair, mirrored star map for two factions.

    python galaxy_generator.py            (writes data/galaxy.json)

  * Star systems are joined by jump lanes (1-4.5 light years). Lanes form a
    sparse network with natural chokepoints, and ships can only jump along
    lanes, spending tritium per light year (see economy_data.py FUEL).
  * The map is mirrored left/right, so both home systems have exactly the
    same resources at the same jump distances. A column of contested systems
    runs down the middle, holding the richest prizes: crystal fields, lithium,
    derelict warships and the ancient alien sites where the infection sleeps.
  * Every system is a 7 km arena. Each lane has a jump point at the arena edge
    in the direction of the neighboring system; resource anchors (gas giants,
    asteroid fields, derelicts, ancient sites) are placed inside, clear of
    each other and of the jump points.

Change SEED / sizes below for a different map.
"""

import json
import math
import os
import random

SEED = 11
HALF_SYSTEMS = 5           # systems per side (plus the middle column): 12 total = ~2 hour games
MIDDLE_SYSTEMS = 2         # contested systems on the center line
MAP_W, MAP_H = 22.0, 12.0  # light years
MIN_GAP = 2.6              # minimum distance between systems (LY)
MAX_LANE = 4.5             # longest allowed lane (LY)
LOOP_RATIO = 1.4           # lanes per system: >1 adds alternate routes / flanking paths
ARENA_R = 3500.0           # arena radius in meters (7 km across)
JUMP_R = 3200.0            # jump points sit this far from the system center

STARS = [("yellow", 0.40), ("red dwarf", 0.30), ("white", 0.12), ("blue giant", 0.08), ("neutron", 0.05),
         ("binary", 0.05)]
SYLLABLES = ["ka", "ri", "on", "tes", "var", "mol", "dra", "eth", "sol", "ny", "pax", "qua", "zen", "ul",
             "cor", "ves", "thal", "ix", "bel", "aur", "kel", "mir", "do", "sa"]


def pick(rng, weighted):
    r, acc = rng.random(), 0.0
    for item, w in weighted:
        acc += w
        if r <= acc:
            return item
    return weighted[-1][0]


def system_name(rng, used):
    while True:
        n = "".join(rng.sample(SYLLABLES, rng.choice((2, 2, 3)))).capitalize()     # no repeated syllables
        if n not in used and 4 <= len(n) <= 8:
            used.add(n)
            return n


def gen_positions(rng):
    """Left-half points, mirrored to the right, plus a middle column."""
    left = []
    tries = 0
    while len(left) < HALF_SYSTEMS and tries < 20000:
        tries += 1
        p = (rng.uniform(-MAP_W / 2, -MIN_GAP * 0.7), rng.uniform(-MAP_H / 2, MAP_H / 2))
        if (p[0] / (MAP_W / 2)) ** 2 + (p[1] / (MAP_H / 2)) ** 2 > 1.0:
            continue                                   # keep inside an ellipse
        if all(math.dist(p, q) >= MIN_GAP for q in left) and all(math.dist(p, (-q[0], q[1])) >= MIN_GAP for q in left):
            left.append(p)
    mid = [(0.0, -MAP_H * 0.30 + i * (MAP_H * 0.60) / max(1, MIDDLE_SYSTEMS - 1)) for i in range(MIDDLE_SYSTEMS)]
    pts = left + [(-x, y) for x, y in left] + mid
    side = ["F1"] * len(left) + ["F2"] * len(left) + ["mid"] * len(mid)
    mirror = list(range(len(left), 2 * len(left))) + list(range(len(left))) + \
        list(range(2 * len(left), 2 * len(left) + len(mid)))
    return pts, side, mirror


def lanes_for(pts):
    """Relative neighborhood graph: connected, sparse, symmetric for a mirrored point set."""
    n, lanes = len(pts), []
    for i in range(n):
        for j in range(i + 1, n):
            d = math.dist(pts[i], pts[j])
            if d > MAX_LANE:
                continue
            if any(max(math.dist(pts[i], pts[k]), math.dist(pts[j], pts[k])) < d - 1e-9
                   for k in range(n) if k not in (i, j)):
                continue
            lanes.append((i, j, d))
    return lanes


def _cross(p1, p2, p3, p4):
    """True if segments p1-p2 and p3-p4 properly intersect."""
    def o(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    if len({p1, p2, p3, p4}) < 4:
        return False
    return (o(p1, p2, p3) * o(p1, p2, p4) < 0) and (o(p3, p4, p1) * o(p3, p4, p2) < 0)


def add_loops(pts, lanes, mirror, target_ratio=LOOP_RATIO):
    """Add short, non-crossing lanes (in mirrored pairs) so there are alternate routes."""
    have = {(min(a, b), max(a, b)) for a, b, _ in lanes}
    cands = sorted((math.dist(pts[i], pts[j]), i, j) for i in range(len(pts)) for j in range(i + 1, len(pts))
                   if (i, j) not in have and math.dist(pts[i], pts[j]) <= MAX_LANE * 1.15)
    for d, i, j in cands:
        if len(lanes) >= target_ratio * len(pts):
            break
        pair = {(i, j), (min(mirror[i], mirror[j]), max(mirror[i], mirror[j]))}
        new = [(a, b) for a, b in pair if (a, b) not in have]
        segs = [(pts[a], pts[b]) for a, b, _ in lanes]
        if any(_cross(pts[a], pts[b], s0, s1) for a, b in new for s0, s1 in segs):
            continue
        if len(new) == 2 and _cross(pts[new[0][0]], pts[new[0][1]], pts[new[1][0]], pts[new[1][1]]):
            continue
        for a, b in new:
            lanes.append((a, b, math.dist(pts[a], pts[b])))
            have.add((a, b))
    return lanes


def connected(n, lanes):
    adj = {i: set() for i in range(n)}
    for a, b, _ in lanes:
        adj[a].add(b)
        adj[b].add(a)
    seen, stack = {0}, [0]
    while stack:
        for nb in adj[stack.pop()]:
            if nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return len(seen) == n, adj


def hops_from(adj, start):
    dist, frontier = {start: 0}, [start]
    while frontier:
        nxt = []
        for s in frontier:
            for nb in adj[s]:
                if nb not in dist:
                    dist[nb] = dist[s] + 1
                    nxt.append(nb)
        frontier = nxt
    return dist


def place(rng, taken, r_min=600, r_max=2700, gap=900):
    for _ in range(500):
        a, r = rng.uniform(0, 2 * math.pi), rng.uniform(r_min, r_max)
        p = (r * math.cos(a), r * math.sin(a))
        if all(math.dist(p, q) >= gap for q in taken):
            taken.append(p)
            return p
    return None


def contents(rng, depth, is_home, is_mid, jump_spots):
    """Anchors for one system. depth = 0 at home ... 1 at the center line."""
    taken = list(jump_spots) + [(0.0, 0.0)]
    anchors = []

    def add(kind, **kw):
        p = place(rng, taken)
        if p:
            anchors.append(dict(kind=kind, pos=[round(p[0]), round(p[1]), round(rng.uniform(-250, 250))], **kw))

    if is_home:
        add("gas_giant", richness=1.0)
        add("asteroid_field", resource="ore", richness=1.2)
        add("asteroid_field", resource="ice", richness=1.0)
        return anchors
    if rng.random() < 0.50 + 0.30 * depth:          # big enough for a ground base
        add("large_asteroid", composition=pick(rng, [("ore", 0.45), ("ice", 0.25), ("crystals", 0.2),
                                                      ("lithium", 0.1)]),
            size_km=round(rng.uniform(0.6, 1.6), 1), build_sites=rng.choice((2, 3, 4)))
    for _ in range(pick(rng, [(0, 0.35), (1, 0.50), (2, 0.15)])):
        add("gas_giant", richness=round(rng.uniform(0.8, 1.3), 2))
    for _ in range(rng.choice((1, 1, 2, 2, 3))):
        res = pick(rng, [("ore", 0.42 - 0.17 * depth), ("ice", 0.33 - 0.13 * depth),
                         ("crystals", 0.15 + 0.15 * depth), ("lithium", 0.10 + 0.15 * depth)])
        add("asteroid_field", resource=res, richness=round(rng.uniform(0.7, 1.0 + 0.6 * depth), 2))
    if rng.random() < 0.10 + 0.45 * depth:
        cls = pick(rng, [("SMALL", 0.4), ("MEDIUM", 0.35), ("LARGE", 0.2), ("XL", 0.05)])
        add("derelict", ship_class=cls, salvage=dict(alloys=int(800 * (1 + depth)), circuitry=int(300 * (1 + depth)),
                                                       crystals=int(150 * depth)),
            infection_risk=round(0.1 + 0.5 * depth, 2), repairable=rng.random() < 0.3)
    if is_mid:
        add("ancient_site", infection_source=True, reward="unique upgrade")
        add("asteroid_field", resource="lithium", richness=round(rng.uniform(1.2, 1.6), 2))   # contested lithium
    return anchors


def generate(seed=SEED):
    rng = random.Random(seed)
    for _ in range(200):
        pts, side, mirror = gen_positions(rng)
        lanes = add_loops(pts, lanes_for(pts), mirror)
        ok, adj = connected(len(pts), lanes)
        if ok:
            break
    else:
        raise SystemExit("Couldn't build a connected map - try another SEED")
    n = len(pts)
    home1 = min((i for i in range(n) if side[i] == "F1"), key=lambda i: pts[i][0])
    home2 = mirror[home1]
    d1 = hops_from(adj, home1)
    far = max(d1.values())
    used = set()
    systems = [None] * n
    # jump points per system (direction of each neighbor on the map)
    jp = {i: [] for i in range(n)}
    for a, b, d in lanes:
        for s, t in ((a, b), (b, a)):
            ang = math.atan2(pts[t][1] - pts[s][1], pts[t][0] - pts[s][0])
            jp[s].append(dict(to=t, lane_ly=round(max(1.0, d / 1.4) * 2) / 2,
                              pos=[round(JUMP_R * math.cos(ang)), round(JUMP_R * math.sin(ang)), 0]))
    # contents: generate for F1 + middle, copy mirrored for F2
    for i in range(n):
        if side[i] == "F2":
            continue
        depth = 1.0 if side[i] == "mid" else min(1.0, d1[i] / max(1, far - 1))
        is_home = i == home1
        anchors = contents(rng, depth, is_home, side[i] == "mid", [tuple(j["pos"][:2]) for j in jp[i]])
        star = "yellow" if is_home else pick(rng, STARS)
        systems[i] = dict(id=i, name=system_name(rng, used), star=star, side=side[i], anchors=anchors)
        if side[i] != "mid":
            m = mirror[i]
            systems[m] = dict(id=m, name=system_name(rng, used), star=star, side="F2",
                              anchors=[dict(a, pos=[-a["pos"][0], a["pos"][1], a["pos"][2]]) for a in anchors])
    for i in range(n):
        systems[i].update(map_pos=[round(pts[i][0], 2), round(pts[i][1], 2)], jump_points=jp[i],
                          home=("F1" if i == home1 else "F2" if i == home2 else None),
                          hops_from_F1_home=d1[i], hops_from_F2_home=hops_from(adj, home2)[i])
    # guarantee each side a lithium and a crystal field within 2 jumps of home (mirrored, so fair)
    for res in ("lithium", "crystals"):
        near = [i for i in range(n) if side[i] == "F1" and 1 <= d1[i] <= 2]
        if not any(a.get("resource") == res for i in near for a in systems[i]["anchors"]):
            i = min(near, key=lambda k: (d1[k], len(systems[k]["anchors"])))
            taken = [tuple(a["pos"][:2]) for a in systems[i]["anchors"]] + [tuple(j["pos"][:2]) for j in jp[i]] + [(0, 0)]
            p = place(rng, taken)
            new = dict(kind="asteroid_field", resource=res, richness=0.8, pos=[round(p[0]), round(p[1]), 0])
            systems[i]["anchors"].append(new)
            systems[mirror[i]]["anchors"].append(dict(new, pos=[-new["pos"][0], new["pos"][1], 0]))
    return dict(seed=seed, arena_radius_m=ARENA_R, systems=systems,
                lanes=[dict(a=a, b=b, lane_ly=round(max(1.0, d / 1.4) * 2) / 2) for a, b, d in lanes],
                homes=dict(F1=home1, F2=home2))


# ---------------------------------------------------------------- pirates
VALUE = dict(ore=1.0, ice=0.8, gas_giant=0.8, crystals=2.0, lithium=3.0, derelict=3.0, large_asteroid=1.5,
             ancient_site=4.0)
TIER_CAP_BY_HOPS = {1: 1, 2: 2, 3: 3}
TIER_POWER_CAP = {1: 2.0, 2: 5.0, 3: 9.0, 4: 14.0}
POWER = dict(XS_FIGHTER=0.25, SMALL_FRIGATE=1.0, MEDIUM=3.0, LARGE=6.0, defense_platform=1.5, ground_battery=1.5)


def system_value(anchors):
    return sum(VALUE[a.get("resource", a["kind"])] * a.get("richness", 1.0) for a in anchors)


def pirate_presence(rng, anchors, hops, is_mid):
    """Pirates sized and equipped by what the system holds, capped by distance from home."""
    if hops == 0:
        return None
    value = system_value(anchors)
    if not is_mid and rng.random() > (0.45 if hops == 1 else min(0.95, 0.55 + 0.1 * value)):
        return None
    kinds = {a.get("resource", a["kind"]) for a in anchors}
    cap = 4 if is_mid else TIER_CAP_BY_HOPS.get(hops, 3)
    tier = max(1, min(cap, 1 + int(value // 3)))
    force = dict(XS_FIGHTER=2 * tier, SMALL_FRIGATE=max(0, tier - 1), MEDIUM=1 if tier >= 4 else 0)
    installations, abilities = [], []
    if tier >= 2:
        installations.append("defense_platform")
    if "large_asteroid" in kinds:
        installations += ["ground_core", "ground_battery"] if tier >= 2 else ["ground_core"]
    flagship = None
    if "derelict" in kinds and tier >= 2:
        der = next(a for a in anchors if a["kind"] == "derelict")
        flagship = der["ship_class"] if der["ship_class"] in ("SMALL", "MEDIUM") or tier >= 4 else "SMALL"
    for k in sorted(kinds):
        if k in ("ore", "gas_giant", "ice", "crystals", "lithium", "large_asteroid", "derelict", "ancient_site"):
            abilities.append({"gas_giant": "gas"}.get(k, k))
    shielded = "crystals" in kinds and tier >= 2

    def power():
        p = sum(POWER[k] * n for k, n in force.items())
        p += sum(POWER.get(i, 0) for i in installations)
        if flagship:
            p += {"SMALL": 1.0, "MEDIUM": 3.0, "LARGE": 6.0, "XL": 10.0}[flagship]
        return p * (1.3 if shielded else 1.0)
    # trim to the tier's power cap so a beatable route always exists
    while power() > TIER_POWER_CAP[tier]:
        if force["XS_FIGHTER"] > 1:
            force["XS_FIGHTER"] -= 1
        elif force["SMALL_FRIGATE"] > 0:
            force["SMALL_FRIGATE"] -= 1
        elif "defense_platform" in installations:
            installations.remove("defense_platform")
        elif flagship:
            flagship = None
        else:
            break
    return dict(tier=tier, power=round(power(), 2), value=round(value, 2),
                ships={k: v for k, v in force.items() if v}, flagship=flagship,
                installations=installations, shielded=shielded, abilities=abilities,
                garrison=8 * tier * max(1, len(installations)),
                raids_neighbors="lithium" in kinds, rebuilds_losses="ore" in kinds,
                loot=dict(alloys=int(120 * value), circuitry=int(50 * value)))


def add_pirates(g, seed):
    rng = random.Random(f"{seed}-pirates")
    systems = {s["id"]: s for s in g["systems"]}
    done = set()
    for s in g["systems"]:
        if s["id"] in done:
            continue
        hops = min(s["hops_from_F1_home"], s["hops_from_F2_home"])
        p = pirate_presence(rng, s["anchors"], hops, s["side"] == "mid")
        s["pirates"] = p
        s["controller"] = s["home"]                     # only homes start controlled
        done.add(s["id"])
        if s["side"] != "mid":                          # mirror twin gets the same pirates (fairness)
            twin = next(t for t in g["systems"] if t["side"] != "mid" and t["side"] != s["side"]
                        and t["map_pos"] == [-s["map_pos"][0], s["map_pos"][1]])
            twin["pirates"] = None if p is None else dict(p)
            twin["controller"] = twin["home"]
            done.add(twin["id"])
    return g


def fairness(g):
    """Resources each side can reach within 1, 2, 3 jumps of home."""
    out = {}
    for side in ("F1", "F2"):
        key = f"hops_from_{side}_home"
        row = {}
        for k in (1, 2, 3):
            cnt = {}
            for s in g["systems"]:
                if s[key] <= k:
                    for a in s["anchors"]:
                        t = a.get("resource", a["kind"])
                        cnt[t] = cnt.get(t, 0) + 1
            row[k] = dict(sorted(cnt.items()))
        out[side] = row
    return out


if __name__ == "__main__":
    g = add_pirates(generate(), SEED)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "galaxy.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(g, f, indent=1)
    f = fairness(g)
    print(f"{len(g['systems'])} systems, {len(g['lanes'])} lanes. Wrote {os.path.normpath(out)}")
    print("Within 2 jumps of home:", f["F1"][2], "| fair:", f["F1"] == f["F2"])
    for s in g["systems"]:
        p = s["pirates"]
        hops = min(s["hops_from_F1_home"], s["hops_from_F2_home"])
        print(f"  {s['name']:9s} {s['side']:3s} hops {hops}  value {system_value(s['anchors']):4.1f}  " +
              ("HOME" if s["home"] else "no pirates" if not p else
               f"pirates tier {p['tier']} power {p['power']:4.1f}  ships {p['ships']}"
               + (f" flagship {p['flagship']}" if p['flagship'] else "")
               + (f" installations {p['installations']}" if p['installations'] else "")
               + (" shielded" if p['shielded'] else "")))
