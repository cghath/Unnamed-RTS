"""
Sanity checks for blender/character_generator.py — run after changing it:

    python tools/check_characters.py

Checks both factions: every mesh is on a real bone with valid geometry, every
role's pieces exist, every inventory slot is a real socket holding a modeled
item, and every weapon has its markers with the muzzle at the front.
"""
import sys; import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blender"))
import character_generator as cg
probs = []
def vol(v, f):
    s = 0
    for face in f:
        a = v[face[0]]
        for i in range(1, len(face) - 1):
            b, c = v[face[i]], v[face[i + 1]]
            s += (a[0]*(b[1]*c[2]-b[2]*c[1]) - a[1]*(b[0]*c[2]-b[2]*c[0]) + a[2]*(b[0]*c[1]-b[1]*c[0])) / 6
    return s
for fac in (1, 2):
    bones = {b[0] for b in cg.skeleton(fac)}
    assert bones == set(cg.BONES)
    W = cg.full_wardrobe(fac)
    allm = cg.body(fac) + [m for ms in W.values() for m in ms]
    names = [m.name for m in allm]
    if len(names) != len(set(names)): probs.append(f"F{fac} duplicate mesh names")
    for m in allm:
        if m.material not in cg.PALETTES[fac]: probs.append(f"F{fac} {m.name} bad material {m.material}")
        for bone, s in m.items:
            if bone not in bones: probs.append(f"F{fac} {m.name} unknown bone {bone}")
            if vol(*s) <= 0: probs.append(f"F{fac} {m.name} inside-out/flat solid on {bone}")
    socks = {n: b for n, b, _ in cg.sockets(fac)}
    for n, b in socks.items():
        if b not in bones: probs.append(f"socket {n} on unknown bone {b}")
    its = cg.items(fac)
    for role, r in cg.ROLES.items():
        for p in cg.role_pieces(role):
            if p not in W: probs.append(f"F{fac} {role}: missing piece {p}")
        for slot, kind in r["inventory"].items():
            if slot not in socks: probs.append(f"{role}: unknown socket {slot}")
            it = cg.resolve_item(fac, role, kind)
            if it not in its: probs.append(f"F{fac} {role}: item {it} not modeled")
        # one piece per slot type for head/torso/back
        slots = [m.slot for p in cg.role_pieces(role) for m in W[p][:1]]
        for sl in ("head", "back"):
            if slots.count(sl) > 1: probs.append(f"{role}: two {sl} pieces")
    for cls_, (wname, b) in cg.WEAPONS[fac].items():
        meshes, mag, mk = b()
        need = {"Grip", "SupportHand", "Muzzle", "Sight"} | ({"MagWell"} if fac == 1 else {"CellPort"})
        if not need <= set(mk): probs.append(f"{wname} missing markers {need - set(mk)}")
        for m in meshes + [mag]:
            for _, s in m.items:
                if vol(*s) <= 0: probs.append(f"{wname} bad solid in {m.name}")
        # muzzle should be the front-most point of the weapon
        ys = [v[1] for m in meshes for _, (vs, _) in m.items for v in vs]
        if mk["Muzzle"][1] > min(ys) + 0.03: probs.append(f"{wname}: muzzle marker not at the front")
    for iname, ms in its.items():
        for m in ms:
            for _, s in m.items:
                if vol(*s) <= 0: probs.append(f"item {iname} bad solid")
if probs:
    print("PROBLEMS FOUND:")
    for p in probs:
        print("  -", p)
    sys.exit(1)
print("All character, weapon and item checks passed.")
# height / proportions
for fac in (1, 2):
    vs = [v for m in cg.character_meshes(fac, "rifleman") for _, (pv, _) in m.items for v in pv]
    print(f"F{fac} rifleman height {max(v[2] for v in vs):.2f} m, span {max(v[0] for v in vs)-min(v[0] for v in vs):.2f} m")
