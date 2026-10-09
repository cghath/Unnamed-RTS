"""
Write game-ready .glb files straight from the generators, without Blender.

    python tools/export_glb.py                # every ship (both factions) and station
    python tools/export_glb.py LARGE XS_POD   # just these classes

Output goes to godot_test/models/ (the test project) unless you pass --out <folder>.

The files follow the same rules as the Blender export:
  * one root node "Ship_<CLASS>" with the stats as glTF extras;
  * one mesh node per part, named exactly like the Blender object, so names ending
    in "-col" get collision when Godot imports them;
  * markers as empty nodes, zone boxes as empty nodes scaled to their half-size;
  * Blender's Z-up / Y-forward turned into glTF's Y-up / -Z-forward.
The Blender route is still the one to use when you want to edit models by hand.
"""
import json
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "blender"))
import ship_generator as sg  # noqa: E402


def conv(p):
    """Blender (x, y, z) -> glTF (x, z, -y)."""
    return (p[0], p[2], -p[1])


def triangulate(part, offset=(0.0, 0.0, 0.0)):
    """Flat-shaded triangles in the part's local space (minus `offset`, Blender axes):
    positions and normals in glTF axes. `part` needs .verts and .faces."""
    pos, nor = [], []
    ox, oy, oz = offset
    for f in part.faces:
        vs = [conv((part.verts[i][0] - ox, part.verts[i][1] - oy, part.verts[i][2] - oz)) for i in f]
        for k in range(1, len(vs) - 1):
            a, b, c = vs[0], vs[k], vs[k + 1]
            u = [b[i] - a[i] for i in range(3)]
            w = [c[i] - a[i] for i in range(3)]
            n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
            ln = math.sqrt(sum(x * x for x in n))
            if ln < 1e-12:
                continue
            n = tuple(x / ln for x in n)
            pos += [a, b, c]
            nor += [n, n, n]
    return pos, nor


class GLB:
    def __init__(self):
        self.bin = bytearray()
        self.g = dict(asset=dict(version="2.0", generator="starship-kit export_glb.py"), scene=0,
                      scenes=[dict(nodes=[0])], nodes=[], meshes=[], materials=[], accessors=[],
                      bufferViews=[], buffers=[], extensionsUsed=["KHR_materials_emissive_strength"])
        self.mat_index = {}

    def _view(self, data, target):
        while len(self.bin) % 4:
            self.bin.append(0)
        self.g["bufferViews"].append(dict(buffer=0, byteOffset=len(self.bin), byteLength=len(data), target=target))
        self.bin += data
        return len(self.g["bufferViews"]) - 1

    def _accessor(self, vecs):
        flat = [x for v in vecs for x in v]
        view = self._view(struct.pack(f"<{len(flat)}f", *flat), 34962)
        acc = dict(bufferView=view, componentType=5126, count=len(vecs), type="VEC3")
        acc["min"] = [min(v[i] for v in vecs) for i in range(3)]
        acc["max"] = [max(v[i] for v in vecs) for i in range(3)]
        self.g["accessors"].append(acc)
        return len(self.g["accessors"]) - 1

    def material(self, name, mats, prefix):
        if name not in self.mat_index:
            rgb, metal, rough, emit, alpha = mats[name]
            m = dict(name=f"{prefix}_{name}", pbrMetallicRoughness=dict(
                baseColorFactor=[*rgb, alpha], metallicFactor=metal, roughnessFactor=rough))
            if emit:                       # Blender strengths (5-6) blow out in Godot: scale them down
                m["emissiveFactor"] = list(rgb)
                if emit / 4 > 1:
                    m["extensions"] = dict(KHR_materials_emissive_strength=dict(emissiveStrength=emit / 4))
            if alpha < 1:
                m["alphaMode"] = "BLEND"
                m["doubleSided"] = True
            self.g["materials"].append(m)
            self.mat_index[name] = len(self.g["materials"]) - 1
        return self.mat_index[name]

    def node(self, **kw):
        self.g["nodes"].append(kw)
        return len(self.g["nodes"]) - 1

    def mesh(self, name, pos, nor, mat):
        return self.mesh_multi(name, [(pos, nor, mat)])

    def mesh_multi(self, name, prims):
        """One mesh with a primitive per (positions, normals, material index)."""
        out = [dict(attributes=dict(POSITION=self._accessor(p), NORMAL=self._accessor(n)), material=m)
               for p, n, m in prims if p]
        self.g["meshes"].append(dict(name=name, primitives=out))
        return len(self.g["meshes"]) - 1

    def write(self, path):
        while len(self.bin) % 4:
            self.bin.append(0)
        self.g["buffers"] = [dict(byteLength=len(self.bin))]
        js = json.dumps(self.g, separators=(",", ":")).encode()
        js += b" " * (-len(js) % 4)
        with open(path, "wb") as f:
            f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(self.bin)))
            f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
            f.write(struct.pack("<II", len(self.bin), 0x004E4942) + bytes(self.bin))


BLOCKING = ("Hull-col", "Interior-col", "Furniture-col", "Cover-col", "Machinery-col", "Glass-col",
            "ControlConsole-col", "Railings-col", "Door-col")


def cover_points(parts):
    """AI cover spots beside cover, furniture and machinery: CoverPt_<L|H>_<dir>_<n>.
    L = low cover (crouch behind it), H = high cover (lean out). <dir> is the way the
    cover lies from the point, in Blender axes (XP = +X, XN = -X, YP = +Y, YN = -Y)."""
    boxes, cands = [], []
    for q in parts:
        if not q.name.endswith(BLOCKING) or q.rot_z:
            continue
        for v, _ in q.solids:
            w = [(x + q.origin[0], y + q.origin[1], z + q.origin[2]) for x, y, z in v]
            b = [min(p[0] for p in w), max(p[0] for p in w), min(p[1] for p in w), max(p[1] for p in w),
                 min(p[2] for p in w), max(p[2] for p in w)]
            boxes.append(b)
            if not q.name.endswith(("Cover-col", "Furniture-col", "Machinery-col")):
                continue
            hgt, sx, sy = b[5] - b[4], b[1] - b[0], b[3] - b[2]
            if hgt < 0.9 or sx < 0.4 or sy < 0.4 or max(sx, sy) > 14 or b[4] % 4.0 > 0.3:
                continue
            kind = "L" if hgt < 1.45 else "H"
            z = b[4] + 0.05
            for axis, lo, hi, other_lo, other_hi in ((0, b[0], b[1], b[2], b[3]), (1, b[2], b[3], b[0], b[1])):
                n = max(1, int((other_hi - other_lo) // 1.6))
                for k in range(n):
                    t = other_lo + (other_hi - other_lo) * (k + 0.5) / n
                    for edge, d, tag in ((lo - 0.7, 1, "P"), (hi + 0.7, -1, "N")):
                        pt = (edge, t, z) if axis == 0 else (t, edge, z)
                        cands.append((pt, kind, ("X" if axis == 0 else "Y") + tag))
    cell = 4.0
    grid = {}
    for i, b in enumerate(boxes):
        for gx in range(int(b[0] // cell), int(b[1] // cell) + 1):
            for gy in range(int(b[2] // cell), int(b[3] // cell) + 1):
                grid.setdefault((gx, gy), []).append(i)
    out = []
    for pt, kind, d in cands:
        x, y, z = pt
        free = True
        for i in grid.get((int(x // cell), int(y // cell)), []):
            b = boxes[i]
            if b[5] <= z + 0.3 or b[4] >= z + 1.8:
                continue
            if b[0] - 0.35 < x < b[1] + 0.35 and b[2] - 0.35 < y < b[3] + 0.35:
                free = False
                break
        if free:
            out.append((f"CoverPt_{kind}_{d}_{len(out) + 1}", pt))
    return out


def _outer_faces(parts):
    """Outward-facing hull faces that can see open space: [(centroid, normal, size_u, size_v)]."""
    boxes, faces = [], []
    for q in parts:
        if not (q.name.endswith(("Hull-col", "Hull")) or "_Armor" in q.name) or q.rot_z:
            continue
        for v, f in q.solids:
            w = [(x + q.origin[0], y + q.origin[1], z + q.origin[2]) for x, y, z in v]
            boxes.append([min(p[i] for p in w) for i in range(3)] + [max(p[i] for p in w) for i in range(3)])
            for face in f:
                pts = [w[i] for i in face]
                c = [sum(p[i] for p in pts) / len(pts) for i in range(3)]
                ax = [max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)]
                flat = [i for i in range(3) if ax[i] < 0.05]
                if len(flat) != 1:
                    continue
                k = flat[0]
                # which way is out: away from the solid's own centre
                sc = sum(p[k] for p in w) / len(w)
                n = [0.0, 0.0, 0.0]
                n[k] = 1.0 if c[k] > sc else -1.0
                u, vv = [ax[i] for i in range(3) if i != k]
                if u * vv < 4.0:
                    continue
                faces.append((c, n, u, vv, k))
    out = []
    for c, n, u, vv, k in faces:
        o = [c[i] + n[i] * 0.06 for i in range(3)]
        hit = False
        for b in boxes:                                     # ray o + t*n against every box
            ok = True
            for i in range(3):
                if i == k:
                    if n[k] > 0 and b[3 + k] <= o[k] or n[k] < 0 and b[k] >= o[k]:
                        ok = False
                        break
                elif not (b[i] - 0.01 <= o[i] <= b[3 + i] + 0.01):
                    ok = False
                    break
            if ok:
                hit = True
                break
        if not hit:
            out.append((c, n, u, vv, k))
    return out


def reskin(cls, parts, fac):
    """Faction-specific dressing for pirates (3) and the infected derelict (4)."""
    import random
    if fac not in (3, 4):
        return []
    rr = random.Random(f"reskin-{cls}-{fac}")
    faces = _outer_faces(parts)
    if not faces:
        return []
    xs = [p[0] for q in parts for v, _ in q.solids for p in v]
    ys = [p[1] for q in parts for v, _ in q.solids for p in v]
    span = max(max(ys) - min(ys), max(xs) - min(xs))
    out = []
    if fac == 3:
        plates = sg.Part(f"{cls}_ScrapPlates", "Scrap")
        trim = sg.Part(f"{cls}_ScrapTrim", "Trim")
        spikes = sg.Part(f"{cls}_RamSpikes", "Turret")
        n_plates = int(min(70, max(6, span * 0.5)))
        for _ in range(n_plates):
            c, n, u, vv, k = rr.choice(faces)
            a, b = [i for i in range(3) if i != k]
            half = [0.0, 0.0, 0.0]
            half[a] = min(rr.uniform(0.6, 2.4), max(0.4, (u if a < b else vv) * 0.45))
            half[b] = min(rr.uniform(0.6, 2.4), max(0.4, (vv if a < b else u) * 0.45))
            half[k] = rr.uniform(0.08, 0.18)
            ctr = [c[i] + n[i] * half[k] for i in range(3)]
            for i in (a, b):
                ctr[i] += rr.uniform(-0.3, 0.3) * ((u if i == a else vv))
            (plates if rr.random() < 0.7 else trim).add(sg.box(ctr[0] - half[0], ctr[0] + half[0], ctr[1] - half[1],
                                                               ctr[1] + half[1], ctr[2] - half[2], ctr[2] + half[2]))
        # ram spikes on the bow and a couple of jury-rigged masts
        y_nose = max(ys)
        zs = [p[2] for q in parts for v, _ in q.solids for p in v]
        zc = (max(zs) + min(zs)) / 2
        w = (max(xs) - min(xs)) * 0.3
        for k in (range(3 if span > 30 else 1) if not cls.startswith(("GROUND", "STATION", "OUTPOST")) else []):
            x = (k - 1) * w * 0.5 if span > 30 else 0.0
            l = span * 0.08
            spikes.add(sg.hexa([(x + (-1, 1)[i & 1] * (0.6 if not (i >> 1) & 1 else 0.05),
                                 y_nose - 1.0 + ((i >> 1) & 1) * l,
                                 zc + (-1, 1)[(i >> 2) & 1] * (0.6 if not (i >> 1) & 1 else 0.05)) for i in range(8)]))
        tops = [f for f in faces if f[1][2] > 0.5]
        for _ in range(2 if span > 30 else 0):
            if tops:
                c = rr.choice(tops)[0]
                h = rr.uniform(4, 9) * (1 if span > 30 else 0.3)
                trim.add(sg.box(c[0] - 0.12, c[0] + 0.12, c[1] - 0.12, c[1] + 0.12, c[2], c[2] + h))
                trim.add(sg.box(c[0] - 1.2, c[0] + 1.2, c[1] - 0.08, c[1] + 0.08, c[2] + h * 0.8, c[2] + h * 0.8 + 0.15))
        out = [plates, trim, spikes]
    else:
        growth = sg.Part(f"{cls}_Growth", "Growth")
        n_clusters = int(min(45, max(3, span * 0.22)))
        for _ in range(n_clusters):
            c, n, u, vv, k = rr.choice(faces)
            a, b = [i for i in range(3) if i != k]
            for _ in range(rr.randint(3, 7)):
                r0 = rr.uniform(0.4, 2.2) * (1.0 if span > 30 else 0.12)
                ctr = list(c)
                ctr[a] += rr.uniform(-0.4, 0.4) * u
                ctr[b] += rr.uniform(-0.4, 0.4) * vv
                ctr[k] += n[k] * r0 * 0.3
                growth.add(sg.hexa([(ctr[0] + (-1, 1)[i & 1] * r0 * rr.uniform(0.5, 1.2),
                                     ctr[1] + (-1, 1)[(i >> 1) & 1] * r0 * rr.uniform(0.5, 1.2),
                                     ctr[2] + (-1, 1)[(i >> 2) & 1] * r0 * rr.uniform(0.5, 1.2)) for i in range(8)]))
            # a tendril creeping across the surface
            l = rr.uniform(4, 14) * (1.0 if span > 30 else 0.1)
            d = rr.choice([a, b])
            t0 = list(c)
            t0[k] += n[k] * 0.15
            half = [0.18, 0.18, 0.18] if span > 30 else [0.05, 0.05, 0.05]
            half[d] = l / 2
            t0[d] += (l / 2) * rr.choice([-1, 1])
            growth.add(sg.box(t0[0] - half[0], t0[0] + half[0], t0[1] - half[1], t0[1] + half[1],
                              t0[2] - half[2], t0[2] + half[2]))
        out = [growth]
    return [q for q in out if q.verts]


def export(cls, path):
    parts, markers, info = sg.generate(cls)
    parts = list(parts) + reskin(cls, parts, sg.FACTION)
    if not cls.startswith("XS_"):
        markers = list(markers) + cover_points(parts)
    mats = sg.materials()
    g = GLB()
    root = g.node(name=f"Ship_{cls}", children=[], extras={k: (v if not isinstance(v, (dict, list)) else json.dumps(v))
                                                           for k, v in info.get("stats", {}).items()})
    kids = g.g["nodes"][root]["children"]
    for p in parts:
        barrels = None
        if "_Turret_" in p.name and len(p.solids) >= 4 and not p.name.endswith("-col"):
            # split the twin barrels off so they can recoil: child node "<turret>_Barrels"
            body, bar = sg.Part(p.name, p.material), sg.Part(p.name + "_Barrels", p.material)
            body.add_many(p.solids[:2])
            bar.add_many(p.solids[2:])
            bpos, bnor = triangulate(bar)
            barrels = g.node(name=bar.name, mesh=g.mesh(bar.name, bpos, bnor, g.material(p.material, mats, f"F{sg.FACTION}")))
            pos, nor = triangulate(body)
        else:
            pos, nor = triangulate(p)
        if not pos:
            continue
        n = dict(name=p.name, mesh=g.mesh(p.name, pos, nor, g.material(p.material, mats, f"F{sg.FACTION}")))
        if barrels is not None:
            n["children"] = [barrels]
        if any(p.origin):
            n["translation"] = list(conv(p.origin))
        if p.rot_z:
            n["rotation"] = [0.0, math.sin(p.rot_z / 2), 0.0, math.cos(p.rot_z / 2)]
        kids.append(g.node(**n))
    for m in markers:
        n = dict(name=f"{cls}_{m[0]}", translation=list(conv(m[1])))
        if len(m) > 2:                                  # zone: scale = half-size
            sx, sy, sz = m[2]
            n["scale"] = [sx, sz, sy]
        kids.append(g.node(**n))
    g.write(path)
    return len(parts), len(markers)


VARIANT_CLASSES = ["SMALL_FRIGATE", "SMALL_SUPPORT", "SMALL_DROP_FRIGATE", "MEDIUM", "LARGE", "XL"]   # boardable warships: several interior layouts
N_VARIANTS = 3


def _export_set(folder, fac, classes, out, variants=True, stations=False):
    sg.FACTION = fac
    d = os.path.join(out, folder)
    os.makedirs(d, exist_ok=True)
    for cls in classes:
        name = f"{cls}.glb" if stations else f"ship_{cls}.glb"
        sg.VARIANT = 0
        np_, nm = export(cls, os.path.join(d, name))
        print(f"{folder} {cls}: {np_} parts, {nm} markers")
        if variants and not stations and cls in VARIANT_CLASSES:
            for v in range(1, N_VARIANTS + 1):
                sg.VARIANT = v
                export(cls, os.path.join(d, f"ship_{cls}_v{v}.glb"))
            print(f"{folder} {cls}: layout variants 1-{N_VARIANTS}")
    sg.VARIANT = 0


def main():
    args = sys.argv[1:]
    out = os.path.join(HERE, "..", "godot_demo", "models")
    if "--out" in args:
        i = args.index("--out")
        out = args[i + 1]
        args = args[:i] + args[i + 2:]
    ships = [c for c in args if c in sg.SHIP_CLASSES] if args else list(sg.SHIP_CLASSES)
    stations = [c for c in args if c not in sg.SHIP_CLASSES] if args else list(sg.STATION_KITS)
    for fac in (1, 2):
        _export_set(f"ships_F{fac}", fac, ships, out)
        _export_set(f"stations_F{fac}", fac, stations, out, stations=True)
    if not args:                                      # pirates (palette 3) and the infected derelict (4)
        _export_set("ships_P", 3, ["SMALL_FRIGATE", "MEDIUM", "LARGE", "XS_FIGHTER", "XS_POD", "XS_DROPSHIP", "XS_DARTER"], out)
        _export_set("stations_P", 3, ["GROUND_FORT", "GROUND_MINE"], out, stations=True)
        _export_set("ships_X", 4, ["XL", "LARGE", "XS_POD"], out)
    sg.FACTION = 1


if __name__ == "__main__":
    main()
