"""
Write jointed, animatable character models and weapons as .glb, without Blender.

    python tools/export_characters_glb.py      # -> godot_demo/models/characters, weapons, items

Each character (one file per faction and role) is a hierarchy of joints named after
Godot's humanoid bones (Root > Hips > Spine > ...). Every joint node holds the rigid
robot parts that move with it, so you animate a character by rotating joint nodes.
The rest pose is a T-pose facing +Z.

Physical inventory is built in: every filled socket is its own node named
"Slot_<socket>" (Slot_MagSlot_1, Slot_GrenadeSlot_1, Slot_MedpenSlot_1 ...) under the
joint it rides on, so the game can hide a magazine when it is loaded or a medpen
when it is used.

Weapons: node "Body" (the gun), node "Mag" (the removable magazine or power cell) and
markers Grip, SupportHand, Muzzle, Sight and MagWell/CellPort. The origin is the
right-hand grip and the muzzle points +Z.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "blender"))
sys.path.insert(0, HERE)
import character_generator as cg  # noqa: E402
from export_glb import GLB, conv, triangulate  # noqa: E402


class _Solid:
    def __init__(self, solid):
        self.verts, self.faces = solid[0], cg._orient_faces(*solid) if hasattr(cg, "_orient_faces") else solid[1]


def _prims(g, items, pal, fac, offset=(0, 0, 0)):
    """items: [(material, solid)] -> mesh primitives grouped by material."""
    by_mat = {}
    for mat, solid in items:
        pos, nor = triangulate(_Solid(solid), offset)
        p, n = by_mat.setdefault(mat, ([], []))
        p += pos
        n += nor
    return [(p, n, g.material(m, pal, f"C{fac}")) for m, (p, n) in by_mat.items()]


def pirate_gear(fac):
    """Scavenged extras every pirate wears: a scrap pauldron, a rebreather, a bandolier and a ragged cloak."""
    sx, sy, sz = cg.BODY_SCALE[fac]
    S = lambda solid: cg.transform(solid, lambda p: (p[0] * sx, p[1] * sy, p[2] * sz))
    out = [
        ("LeftShoulder", "ArmorDark", S(cg.box(0.12, 0.33, -0.15, 0.15, 1.47, 1.63))),        # oversized scrap pauldron
        ("LeftShoulder", "Trim", S(cg.box(0.16, 0.34, -0.16, 0.16, 1.60, 1.645))),
        ("Head", "Trim", S(cg.box(-0.055, 0.055, -0.175, -0.11, 1.69, 1.77))),                # rebreather
        ("Head", "WDark", S(cg.cyl("x", -0.15, 1.72, 0.06, 0.11, 0.028, seg=8))),
        ("Head", "WDark", S(cg.cyl("x", -0.15, 1.72, -0.11, -0.06, 0.028, seg=8))),
        ("UpperChest", "Suit", S(cg.box(-0.21, 0.21, 0.12, 0.155, 0.98, 1.52))),             # ragged cloak
        ("Hips", "Suit", S(cg.box(-0.22, 0.22, 0.13, 0.16, 0.62, 0.98))),
    ]
    for i in range(6):                                                                        # bandolier, shoulder to hip
        t = i / 5.0
        x, z = 0.14 - 0.28 * t, 1.5 - 0.42 * t
        out.append(("UpperChest" if z > 1.24 else "Chest", "WAccent", S(cg.box(x - 0.03, x + 0.03, -0.16, -0.12, z - 0.035, z + 0.035))))
    return out


def export_character(fac, role, path, pal_id=None):
    pal = cg.PALETTES[pal_id or fac]
    skel = cg.skeleton(fac)
    heads = {n: h for n, _, h, _ in skel}
    g = GLB()
    root = g.node(name=f"Char_F{fac}_{role}", children=[], extras=dict(faction=fac, role=role))
    ids = {}
    per_bone = {n: [] for n, *_ in skel}
    for m in cg.character_meshes(fac, role):
        for bone, solid in m.items:
            per_bone[bone or "Hips"].append((m.material, solid))
    if pal_id == 3:
        for bone, mat, solid in pirate_gear(fac):
            per_bone[bone].append((mat, solid))
    for name, parent, head, _ in skel:
        ph = heads[parent] if parent else (0, 0, 0)
        nd = dict(name=name, children=[], translation=list(conv(tuple(head[i] - ph[i] for i in range(3)))))
        ids[name] = g.node(**nd)
        (g.g["nodes"][ids[parent]]["children"] if parent else g.g["nodes"][root]["children"]).append(ids[name])
        if per_bone[name]:
            mesh = g.mesh_multi(f"{name}_mesh", _prims(g, per_bone[name], pal, fac, head))
            g.g["nodes"][ids[name]]["children"].append(g.node(name=f"{name}_mesh", mesh=mesh))
    # physical inventory in its sockets
    items = cg.items(fac)
    socks = {n: (b, p) for n, b, p in cg.sockets(fac)}
    for slot, kind in cg.ROLES[role]["inventory"].items():
        if slot.endswith("HandGrip"):
            continue                                   # held items are attached by the game
        item = cg.resolve_item(fac, role, kind)
        if not item or slot not in socks:
            continue
        bone, pos = socks[slot]
        h = heads[bone]
        sl = [(m.material, s) for m in items[item] for _, s in m.items]
        mesh = g.mesh_multi(f"Slot_{slot}", _prims(g, sl, pal, fac))
        node = g.node(name=f"Slot_{slot}", mesh=mesh, translation=list(conv(tuple(pos[i] - h[i] for i in range(3)))),
                      extras=dict(item=item))
        g.g["nodes"][ids[bone]]["children"].append(node)
    # sockets as markers too (for things the game attaches later)
    for slot, (bone, pos) in socks.items():
        h = heads[bone]
        g.g["nodes"][ids[bone]]["children"].append(
            g.node(name=f"Socket_{slot}", translation=list(conv(tuple(pos[i] - h[i] for i in range(3))))))
    g.write(path)


def export_weapon(fac, cls_, path, pal_id=None):
    pal = cg.PALETTES[pal_id or fac]
    wname, builder = cg.WEAPONS[fac][cls_]
    meshes, mag, markers = builder()
    g = GLB()
    root = g.node(name=f"Weapon_{wname}", children=[], extras=dict(faction=fac, weapon_class=cls_, model=wname))
    kids = g.g["nodes"][root]["children"]
    body = [(m.material, s) for m in meshes for _, s in m.items]
    kids.append(g.node(name="Body", mesh=g.mesh_multi("Body", _prims(g, body, pal, fac))))
    if mag:
        kids.append(g.node(name="Mag", mesh=g.mesh_multi("Mag", _prims(g, [(mag.material, s) for _, s in mag.items], pal, fac))))
    for k, p in markers.items():
        kids.append(g.node(name=k, translation=list(conv(p))))
    g.write(path)


def export_item(fac, item, meshes, path):
    pal = cg.PALETTES[fac]
    g = GLB()
    sl = [(m.material, s) for m in meshes for _, s in m.items]
    g.node(name=f"Item_{item}", mesh=g.mesh_multi(item, _prims(g, sl, pal, fac)))
    g.write(path)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "godot_demo", "models")
    for sub in ("characters", "weapons", "items"):
        os.makedirs(os.path.join(out, sub), exist_ok=True)
    n = 0
    for fac in (1, 2):
        for role in cg.ROLES:
            export_character(fac, role, os.path.join(out, "characters", f"char_F{fac}_{role}.glb"))
            n += 1
        for cls_ in cg.WEAPONS[fac]:
            export_weapon(fac, cls_, os.path.join(out, "weapons", f"weapon_{cg.WEAPONS[fac][cls_][0]}.glb"))
        for item, meshes in cg.items(fac).items():
            export_item(fac, item, meshes, os.path.join(out, "items", f"item_{item}.glb"))
    for role in ("rifleman", "heavy", "breacher", "grenadier", "squad_leader", "medic", "engineer", "pilot",
                 "cargo_handler", "security"):                      # pirates: faction 1 bodies, scrap colors
        export_character(1, role, os.path.join(out, "characters", f"char_P_{role}.glb"), pal_id=3)
        n += 1
    for cls_ in cg.WEAPONS[1]:
        export_weapon(1, cls_, os.path.join(out, "weapons", f"weapon_P_{cg.WEAPONS[1][cls_][0][3:]}.glb"), pal_id=3)
    print(f"Wrote {n} characters, {len(cg.WEAPONS[1]) * 2} weapons and their items to {out}")


if __name__ == "__main__":
    main()
