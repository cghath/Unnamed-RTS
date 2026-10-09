"""
Robot Soldier, Crew, Weapon & Item Generator for Blender (4.x)
==============================================================

Two robotic factions, built from rigid hard-surface parts on a standard
humanoid skeleton:

  FACTION 1  heavy, ODST-like. Bulky armor that soaks damage (high damage
             reduction); ballistic weapons inspired by Halo and Marathon.
  FACTION 2  sleek, Black Ops 3-like. Light armor (low damage reduction);
             energy weapons inspired by Covenant and BO3 / Infinite designs
             that hit harder.

ROLES & UNIFORMS
  Every role wears a different uniform. Combat roles wear armor; ship crew
  wear department coveralls and carry no combat gear (they gear up at the
  ships' armories and ready lockers). Combat: rifleman, breacher, medic,
  heavy, grenadier, squad_leader, eva_boarder, drop_trooper. Crew: pilot,
  bridge_officer, engineer, cargo_handler, medical_officer, scientist, security.
  Scientists carry purge emitters: the only thing that clears the infection.

HOW IT'S BUILT (and why)
  * One armature per faction using Godot's humanoid bone names (Hips, Spine,
    Chest, UpperChest, Neck, Head, LeftUpperArm, ...). Godot can retarget
    standard humanoid animations (e.g. Mixamo) onto it automatically.
  * Each armor / uniform piece is its own mesh, rigidly bound to the bones it
    covers (robots have no soft skin). A role is a list of pieces to show, so
    one character file holds the whole wardrobe and Godot just toggles
    visibility. ROLE_PREVIEW picks which role shows in Blender.
  * PHYSICAL INVENTORY: empties parented to bones mark where items sit:
    MagSlot_1..6, GrenadeSlot_1..4, MedpenSlot_1..4, ReviveKitSlot,
    ChargeSlot_1..2, Holster, BackWeapon, ToolSlot, RightHandGrip,
    LeftHandGrip. Godot imports them as BoneAttachment3D nodes, so items you
    attach there move with the body. Spend a magazine and its pouch empties.
  * Weapons are separate models with markers (Grip at the origin, Muzzle,
    SupportHand, Sight, MagWell/CellPort). The magazine or power cell is its
    own object so reloads can pull it out, and the same mag/cell is exported
    as an inventory item.

HOW TO USE
  Blender -> Scripting -> Open this file -> Run Script. Change SETTINGS and
  run again. With EXPORT_GLB = True (and the .blend saved), it writes:
    character_F1.glb / character_F2.glb   whole wardrobe + skeleton + sockets
    character_F1_<role>.glb ...            one file per role (if EXPORT_ROLES)
    weapon_<name>.glb, item_<name>.glb     every weapon and item
  Run with plain Python (no Blender) to get .obj files and the data JSON.

UNITS & AXES
  Meters, feet at 0. Characters face Blender -Y, which is +Z in Godot (the
  usual direction for imported humanoids). Weapons point their muzzles the
  same way. Rest pose is a T-pose.
"""

import json
import math
import random

# ---------------------------------------------------------------- SETTINGS
FACTIONS_TO_BUILD = [1, 2]
ROLE_PREVIEW = "rifleman"      # which role is visible in Blender after running
EXPORT_GLB = False             # True = write .glb files next to the saved .blend
EXPORT_ROLES = True            # also write one .glb per role
SEED = 3

# =========================================================================
# Geometry helpers (same as the ship generator)
# =========================================================================


def _orient_faces(verts, faces):
    n = len(verts)
    c = [sum(v[i] for v in verts) / n for i in range(3)]
    out = []
    for f in faces:
        nx = ny = nz = 0.0
        for i in range(len(f)):
            a, b = verts[f[i]], verts[f[(i + 1) % len(f)]]
            nx += (a[1] - b[1]) * (a[2] + b[2])
            ny += (a[2] - b[2]) * (a[0] + b[0])
            nz += (a[0] - b[0]) * (a[1] + b[1])
        fc = [sum(verts[i][k] for i in f) / len(f) for k in range(3)]
        d = (fc[0] - c[0]) * nx + (fc[1] - c[1]) * ny + (fc[2] - c[2]) * nz
        out.append(list(f) if d >= 0 else list(reversed(f)))
    return out


_HEX_FACES = [(0, 2, 6, 4), (1, 3, 7, 5), (0, 1, 5, 4), (2, 3, 7, 6), (0, 1, 3, 2), (4, 5, 7, 6)]


def hexa(corners):
    return list(corners), _orient_faces(corners, _HEX_FACES)


def box(x0, x1, y0, y1, z0, z1):
    xs, ys, zs = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return hexa([(xs[i & 1], ys[(i >> 1) & 1], zs[(i >> 2) & 1]) for i in range(8)])


def tbox(z0, z1, bottom, top, cx=0.0):
    """Block from z0 to z1. bottom/top = (half_width_x, y_front, y_back)."""
    corners = []
    for i in range(8):
        hx, yf, yb = top if (i >> 2) & 1 else bottom
        corners.append((cx + (-hx, hx)[i & 1], (yf, yb)[(i >> 1) & 1], (z0, z1)[(i >> 2) & 1]))
    return hexa(corners)


def ytaper(y0, y1, back, front, cz=0.0):
    """Block along Y. back (at y0) / front (at y1) = (half_width, z_bottom, z_top)."""
    corners = []
    for i in range(8):
        hx, zb, zt = front if (i >> 1) & 1 else back
        corners.append(((-hx, hx)[i & 1], (y0, y1)[(i >> 1) & 1], cz + (zb, zt)[(i >> 2) & 1]))
    return hexa(corners)


def cyl(axis, c1, c2, a0, a1, r, seg=12, phase=0.0):
    """Capped cylinder along 'x' (c1=y, c2=z), 'y' (c1=x, c2=z) or 'z' (c1=x, c2=y)."""
    verts = []
    for a in (a0, a1):
        for k in range(seg):
            t = phase + 2 * math.pi * k / seg
            u, v = c1 + r * math.cos(t), c2 + r * math.sin(t)
            verts.append({"x": (a, u, v), "y": (u, a, v), "z": (u, v, a)}[axis])
    faces = [(k, (k + 1) % seg, seg + (k + 1) % seg, seg + k) for k in range(seg)]
    faces += [tuple(range(seg)), tuple(range(seg, 2 * seg))]
    return verts, _orient_faces(verts, faces)


def mirror(solid):
    """Mirror a solid across X (left side -> right side)."""
    v, f = solid
    nv = [(-x, y, z) for x, y, z in v]
    return nv, _orient_faces(nv, f)


def transform(solid, fn):
    v, f = solid
    nv = [fn(p) for p in v]
    return nv, _orient_faces(nv, f)


class Mesh:
    """A named mesh made of solids, each assigned to a bone (or None)."""
    def __init__(self, name, material, slot=None):
        self.name, self.material, self.slot = name, material, slot
        self.items = []                       # (bone, (verts, faces))

    def add(self, bone, solid):
        self.items.append((bone, solid))
        return self

    def sym(self, bone_l, solid_l):
        """Add a left-side solid and its mirror on the right-side bone."""
        self.items.append((bone_l, solid_l))
        self.items.append((bone_l.replace("Left", "Right"), mirror(solid_l)))
        return self


# =========================================================================
# Factions: palettes and body styles
# =========================================================================

PALETTES = {   # material: (RGB, metallic, roughness, emission, alpha)
    1: {
        "Chassis": ((0.30, 0.31, 0.32), 0.8, 0.40, 0, 1), "Joint": ((0.08, 0.08, 0.09), 0.6, 0.5, 0, 1),
        "Eye": ((1.00, 0.62, 0.15), 0, 0.3, 6, 1), "Armor": ((0.42, 0.45, 0.38), 0.4, 0.55, 0, 1),
        "ArmorDark": ((0.15, 0.16, 0.15), 0.4, 0.5, 0, 1), "Trim": ((0.11, 0.11, 0.11), 0.3, 0.6, 0, 1),
        "Visor": ((0.95, 0.55, 0.12), 0.9, 0.1, 0.4, 1), "Light": ((1.00, 0.62, 0.15), 0, 0.3, 5, 1),
        "Suit": ((0.74, 0.75, 0.72), 0.1, 0.7, 0, 1),
        "Command": ((0.12, 0.16, 0.28), 0.1, 0.6, 0, 1), "Engineering": ((0.85, 0.42, 0.08), 0.1, 0.7, 0, 1),
        "Cargo": ((0.88, 0.72, 0.10), 0.1, 0.7, 0, 1), "Medical": ((0.90, 0.92, 0.92), 0.1, 0.6, 0, 1),
        "Flight": ((0.30, 0.33, 0.22), 0.1, 0.7, 0, 1), "Security": ((0.22, 0.25, 0.30), 0.2, 0.6, 0, 1),
        "HiVis": ((0.75, 0.95, 0.10), 0, 0.5, 0.3, 1), "Reflect": ((0.85, 0.86, 0.88), 0.6, 0.2, 0, 1),
        "MedMark": ((0.10, 0.75, 0.45), 0, 0.5, 0.5, 1), "Rank": ((0.95, 0.75, 0.25), 0.9, 0.3, 0, 1),
        "Science": ((0.10, 0.52, 0.55), 0.1, 0.6, 0, 1), "Purge": ((0.60, 0.95, 1.00), 0, 0.2, 8, 1),
        # weapons (Marathon-style: dark bodies with bold flat panels)
        "WBody": ((0.20, 0.22, 0.20), 0.3, 0.6, 0, 1), "WDark": ((0.06, 0.06, 0.07), 0.5, 0.5, 0, 1),
        "WAccent": ((1.00, 0.55, 0.05), 0.1, 0.5, 0, 1), "WPanel": ((0.88, 0.86, 0.80), 0.1, 0.6, 0, 1),
        "Optic": ((0.30, 0.80, 1.00), 0, 0.1, 1.5, 1), "Energy": ((1.00, 0.62, 0.15), 0, 0.3, 4, 1),
    },
    2: {
        "Chassis": ((0.56, 0.57, 0.60), 0.9, 0.30, 0, 1), "Joint": ((0.07, 0.07, 0.08), 0.6, 0.4, 0, 1),
        "Eye": ((1.00, 0.12, 0.10), 0, 0.3, 7, 1), "Armor": ((0.15, 0.16, 0.18), 0.5, 0.40, 0, 1),
        "ArmorDark": ((0.05, 0.05, 0.06), 0.5, 0.4, 0, 1), "Trim": ((0.03, 0.03, 0.035), 0.4, 0.5, 0, 1),
        "Visor": ((0.04, 0.04, 0.05), 0.9, 0.05, 0, 1), "Light": ((1.00, 0.12, 0.10), 0, 0.3, 6, 1),
        "Suit": ((0.22, 0.23, 0.25), 0.2, 0.6, 0, 1),
        "Command": ((0.06, 0.06, 0.07), 0.2, 0.5, 0, 1), "Engineering": ((0.80, 0.35, 0.06), 0.1, 0.6, 0, 1),
        "Cargo": ((0.85, 0.68, 0.08), 0.1, 0.6, 0, 1), "Medical": ((0.85, 0.87, 0.88), 0.1, 0.5, 0, 1),
        "Flight": ((0.18, 0.19, 0.21), 0.2, 0.6, 0, 1), "Security": ((0.32, 0.08, 0.08), 0.2, 0.6, 0, 1),
        "HiVis": ((0.75, 0.95, 0.10), 0, 0.5, 0.3, 1), "Reflect": ((0.85, 0.86, 0.88), 0.6, 0.2, 0, 1),
        "MedMark": ((0.10, 0.75, 0.45), 0, 0.5, 0.5, 1), "Rank": ((0.85, 0.85, 0.88), 0.9, 0.2, 0, 1),
        "Science": ((0.08, 0.42, 0.46), 0.2, 0.5, 0, 1), "Purge": ((0.60, 0.95, 1.00), 0, 0.2, 8, 1),
        # weapons (Covenant / BO3 energy: graphite with glowing channels)
        "WBody": ((0.12, 0.12, 0.14), 0.6, 0.35, 0, 1), "WDark": ((0.04, 0.04, 0.05), 0.6, 0.4, 0, 1),
        "WAccent": ((0.90, 0.10, 0.12), 0.2, 0.4, 0, 1), "WPanel": ((0.55, 0.56, 0.60), 0.9, 0.25, 0, 1),
        "Optic": ((1.00, 0.20, 0.35), 0, 0.1, 2, 1), "Energy": ((1.00, 0.18, 0.40), 0, 0.2, 6, 1),
    },
    3: {   # pirates: faction 1 bodies in rust, scrap and hazard green
        "Chassis": ((0.28, 0.24, 0.20), 0.6, 0.55, 0, 1), "Joint": ((0.08, 0.07, 0.06), 0.6, 0.5, 0, 1),
        "Eye": ((0.40, 1.00, 0.35), 0, 0.3, 6, 1), "Armor": ((0.45, 0.26, 0.12), 0.4, 0.65, 0, 1),
        "ArmorDark": ((0.20, 0.13, 0.08), 0.4, 0.6, 0, 1), "Trim": ((0.60, 0.48, 0.10), 0.3, 0.6, 0, 1),
        "Visor": ((0.40, 1.00, 0.35), 0.9, 0.1, 0.4, 1), "Light": ((0.40, 1.00, 0.35), 0, 0.3, 5, 1),
        "Suit": ((0.32, 0.30, 0.24), 0.1, 0.8, 0, 1),
        "Command": ((0.20, 0.10, 0.08), 0.1, 0.6, 0, 1), "Engineering": ((0.55, 0.30, 0.08), 0.1, 0.7, 0, 1),
        "Cargo": ((0.55, 0.50, 0.15), 0.1, 0.7, 0, 1), "Medical": ((0.65, 0.62, 0.55), 0.1, 0.6, 0, 1),
        "Flight": ((0.25, 0.22, 0.16), 0.1, 0.7, 0, 1), "Security": ((0.30, 0.18, 0.12), 0.2, 0.6, 0, 1),
        "HiVis": ((0.40, 1.00, 0.35), 0, 0.5, 0.3, 1), "Reflect": ((0.70, 0.66, 0.55), 0.6, 0.3, 0, 1),
        "MedMark": ((0.10, 0.75, 0.45), 0, 0.5, 0.5, 1), "Rank": ((0.75, 0.60, 0.20), 0.9, 0.3, 0, 1),
        "Science": ((0.20, 0.40, 0.30), 0.1, 0.6, 0, 1), "Purge": ((0.60, 0.95, 1.00), 0, 0.2, 8, 1),
        "WBody": ((0.30, 0.22, 0.14), 0.3, 0.7, 0, 1), "WDark": ((0.07, 0.06, 0.05), 0.5, 0.5, 0, 1),
        "WAccent": ((0.40, 1.00, 0.35), 0.1, 0.5, 0, 1), "WPanel": ((0.60, 0.55, 0.45), 0.1, 0.6, 0, 1),
        "Optic": ((0.40, 1.00, 0.35), 0, 0.1, 1.5, 1), "Energy": ((0.40, 1.00, 0.35), 0, 0.3, 4, 1),
    },
}

# Body scale per faction: (x, y, z). Faction 2 is slimmer and slightly shorter.
BODY_SCALE = {1: (1.0, 1.0, 1.0), 2: (0.88, 0.88, 0.965)}
# Armor bulk per faction: how far plates stand off the body.
PAD = {1: 0.035, 2: 0.018}

# =========================================================================
# Skeleton (Godot humanoid bone names). Base proportions = faction 1.
# =========================================================================

_SKEL_CENTER = [
    ("Root", None, (0, 0, 0), (0, 0.25, 0)),
    ("Hips", "Root", (0, 0, 1.00), (0, 0, 1.10)),
    ("Spine", "Hips", (0, 0, 1.10), (0, 0, 1.24)),
    ("Chest", "Spine", (0, 0, 1.24), (0, 0, 1.38)),
    ("UpperChest", "Chest", (0, 0, 1.38), (0, 0, 1.56)),
    ("Neck", "UpperChest", (0, 0, 1.56), (0, 0, 1.66)),
    ("Head", "Neck", (0, 0, 1.66), (0, 0, 1.92)),
]
_SKEL_LEFT = [   # mirrored to Right* with x -> -x
    ("LeftShoulder", "UpperChest", (0.04, 0, 1.50), (0.21, 0, 1.52)),
    ("LeftUpperArm", "LeftShoulder", (0.22, 0, 1.52), (0.50, 0, 1.52)),
    ("LeftLowerArm", "LeftUpperArm", (0.50, 0, 1.52), (0.77, 0, 1.52)),
    ("LeftHand", "LeftLowerArm", (0.77, 0, 1.52), (0.95, 0, 1.52)),
    ("LeftUpperLeg", "Hips", (0.12, 0, 0.98), (0.12, 0, 0.54)),
    ("LeftLowerLeg", "LeftUpperLeg", (0.12, 0, 0.54), (0.12, 0, 0.10)),
    ("LeftFoot", "LeftLowerLeg", (0.12, 0, 0.10), (0.12, -0.14, 0.03)),
    ("LeftToes", "LeftFoot", (0.12, -0.14, 0.03), (0.12, -0.22, 0.03)),
]


def skeleton(fac):
    sx, sy, sz = BODY_SCALE[fac]
    sc = lambda p: (p[0] * sx, p[1] * sy, p[2] * sz)
    out = [(n, par, sc(h), sc(t)) for n, par, h, t in _SKEL_CENTER]
    for n, par, h, t in _SKEL_LEFT:
        out.append((n, par, sc(h), sc(t)))
        out.append((n.replace("Left", "Right"), par.replace("Left", "Right"),
                    sc((-h[0], h[1], h[2])), sc((-t[0], t[1], t[2]))))
    return out


BONES = [b[0] for b in skeleton(1)]

# =========================================================================
# Bodies: the robot chassis everyone has
# =========================================================================


def chassis(fac):
    sleek = fac == 2
    body, joints, eyes = Mesh("Chassis", "Chassis"), Mesh("ChassisJoints", "Joint"), Mesh("Eyes", "Eye")
    body.add("Hips", box(-0.15, 0.15, -0.09, 0.08, 0.93, 1.10))
    joints.add("Spine", box(-0.07, 0.07, -0.05, 0.05, 1.08, 1.26))
    for sx in (-1, 1):
        joints.add("Spine", box(*sorted((sx * 0.09, sx * 0.115)), -0.02, 0.02, 1.08, 1.26))
    body.add("Chest", tbox(1.24, 1.40, (0.15, -0.09, 0.08), (0.17, -0.10, 0.09)))
    body.add("UpperChest", tbox(1.40, 1.56, (0.18, -0.11, 0.10), (0.20, -0.10, 0.09)))
    joints.add("Neck", cyl("z", 0, 0, 1.55, 1.67, 0.045, seg=10))
    if sleek:      # BO3-like: tall faceted head, vertical eye slit and side lights
        body.add("Head", tbox(1.66, 1.93, (0.065, -0.12, 0.08), (0.07, -0.08, 0.09)))
        eyes.add("Head", box(-0.012, 0.012, -0.124, -0.114, 1.72, 1.86))
        for sx in (-1, 1):
            eyes.add("Head", box(*sorted((sx * 0.066, sx * 0.072)), -0.06, -0.02, 1.80, 1.82))
    else:          # heavy: blocky head with a wide visor strip
        body.add("Head", tbox(1.66, 1.90, (0.085, -0.11, 0.09), (0.075, -0.09, 0.08)))
        eyes.add("Head", box(-0.07, 0.07, -0.116, -0.104, 1.77, 1.80))
        joints.add("Head", box(-0.05, 0.05, -0.115, -0.10, 1.69, 1.73))
    # arms (left; mirrored)
    joints.sym("LeftShoulder", cyl("x", 0, 1.52, 0.19, 0.26, 0.06))
    body.sym("LeftUpperArm", box(0.25, 0.48, -0.055, 0.055, 1.465, 1.575))
    joints.sym("LeftLowerArm", cyl("y", 0.50, 1.52, -0.05, 0.05, 0.045))
    body.sym("LeftLowerArm", box(0.52, 0.76, -0.048, 0.048, 1.475, 1.565))
    joints.sym("LeftHand", box(0.78, 0.89, -0.045, 0.045, 1.485, 1.555))
    joints.sym("LeftHand", box(0.89, 0.96, -0.04, 0.04, 1.50, 1.54))
    joints.sym("LeftHand", box(0.80, 0.86, -0.08, -0.045, 1.50, 1.54))
    # legs
    joints.sym("LeftUpperLeg", cyl("x", 0, 0.97, 0.06, 0.19, 0.06))
    body.sym("LeftUpperLeg", box(0.06, 0.19, -0.07, 0.07, 0.58, 0.95))
    joints.sym("LeftLowerLeg", cyl("x", 0, 0.54, 0.07, 0.18, 0.055))
    body.sym("LeftLowerLeg", box(0.07, 0.18, -0.06, 0.06, 0.13, 0.51))
    joints.sym("LeftFoot", cyl("x", 0, 0.10, 0.08, 0.17, 0.04))
    body.sym("LeftFoot", box(0.065, 0.185, -0.15, 0.07, 0.0, 0.08))
    joints.sym("LeftToes", box(0.07, 0.18, -0.23, -0.15, 0.0, 0.06))
    return [body, joints, eyes]


# =========================================================================
# Wardrobe: every armor / uniform piece. A role shows a subset.
# Each piece function returns Mesh objects (slot tells you where it goes).
# =========================================================================

def _shell_torso(m, bone_c, bone_uc, t):
    """Thin uniform shell over the torso (coveralls, coats, suits)."""
    m.add(bone_c, tbox(1.22, 1.40, (0.15 + t, -0.09 - t, 0.08 + t), (0.17 + t, -0.10 - t, 0.09 + t)))
    m.add(bone_uc, tbox(1.40, 1.57, (0.18 + t, -0.11 - t, 0.10 + t), (0.20 + t, -0.10 - t, 0.09 + t)))
    m.add("Hips", box(-0.15 - t, 0.15 + t, -0.09 - t, 0.08 + t, 0.92, 1.10))
    return m


def _shell_limbs(m, t, arms=True, legs=True):
    if arms:
        m.sym("LeftUpperArm", box(0.25, 0.48, -0.055 - t, 0.055 + t, 1.465 - t, 1.575 + t))
        m.sym("LeftLowerArm", box(0.52, 0.75, -0.048 - t, 0.048 + t, 1.475 - t, 1.565 + t))
    if legs:
        m.sym("LeftUpperLeg", box(0.06 - t, 0.19 + t, -0.07 - t, 0.07 + t, 0.58, 0.95))
        m.sym("LeftLowerLeg", box(0.07 - t, 0.18 + t, -0.06 - t, 0.06 + t, 0.14, 0.51))
    return m


def wardrobe(fac):
    """All pieces for a faction: {piece_name: [Mesh, ...]}."""
    p, sleek = PAD[fac], fac == 2
    W = {}
    fy = -0.10 - p - 0.02        # front face of chest armor

    def piece(name, *meshes):
        W[name] = list(meshes)

    # ------------------------------------------------------------ helmets
    if sleek:
        h = Mesh("Helmet_Combat", "Armor", "head")
        h.add("Head", tbox(1.64, 1.95, (0.10, -0.15, 0.11), (0.085, -0.10, 0.10)))
        h.add("Head", ytaper(-0.17, -0.12, (0.06, 1.64, 1.72), (0.03, 1.65, 1.70)))   # jaw wedge
        hv = Mesh("Helmet_Combat_Visor", "Light", "head")
        hv.add("Head", box(-0.08, 0.08, -0.158, -0.150, 1.78, 1.80))
        for sx in (-1, 1):
            h.add("Head", box(*sorted((sx * 0.10, sx * 0.115)), -0.05, 0.08, 1.80, 1.90))   # side fins
        piece("Helmet_Combat", h, hv)
    else:
        h = Mesh("Helmet_Combat", "Armor", "head")
        h.add("Head", tbox(1.63, 1.95, (0.125, -0.145, 0.13), (0.105, -0.11, 0.11)))
        h.add("Head", box(-0.02, 0.02, -0.08, 0.10, 1.95, 1.975))
        h.add("Head", box(-0.12, 0.12, -0.15, -0.08, 1.63, 1.71))          # jaw guard
        hv = Mesh("Helmet_Combat_Visor", "Visor", "head")
        hv.add("Head", box(-0.105, 0.105, -0.158, -0.145, 1.72, 1.84))     # ODST-style wide visor
        piece("Helmet_Combat", h, hv)
    eva = Mesh("Helmet_EVA", "Suit", "head")
    eva.add("Head", cyl("z", 0, -0.01, 1.62, 1.93, 0.16, seg=12))
    eva.add("Head", cyl("z", 0, -0.01, 1.58, 1.62, 0.17, seg=12))         # collar ring
    ev = Mesh("Helmet_EVA_Visor", "Visor", "head").add("Head", box(-0.11, 0.11, -0.178, -0.15, 1.70, 1.86))
    el = Mesh("Helmet_EVA_Lamp", "Light", "head").add("Head", box(0.10, 0.14, -0.17, -0.13, 1.88, 1.92))
    piece("Helmet_EVA", eva, ev, el)
    pil = Mesh("Helmet_Pilot", "Flight", "head")
    pil.add("Head", tbox(1.64, 1.93, (0.11, -0.13, 0.12), (0.095, -0.10, 0.10)))
    pv = Mesh("Helmet_Pilot_Visor", "Visor", "head").add("Head", box(-0.095, 0.095, -0.142, -0.13, 1.70, 1.86))
    piece("Helmet_Pilot", pil, pv)
    cap = Mesh("Cap_Officer", "Command", "head")
    cap.add("Head", box(-0.10, 0.10, -0.12, 0.10, 1.89, 1.95))
    capb = Mesh("Cap_Officer_Brim", "Trim", "head").add("Head", box(-0.09, 0.09, -0.17, -0.10, 1.89, 1.905))
    capr = Mesh("Cap_Officer_Badge", "Rank", "head").add("Head", box(-0.02, 0.02, -0.125, -0.12, 1.91, 1.935))
    piece("Cap_Officer", cap, capb, capr)
    hs = Mesh("Headset", "Trim", "head")
    hs.add("Head", box(-0.095, 0.095, -0.01, 0.02, 1.89, 1.91))
    for sx in (-1, 1):
        hs.add("Head", box(*sorted((sx * 0.08, sx * 0.105)), -0.03, 0.03, 1.74, 1.82))
    hs.add("Head", box(0.07, 0.09, -0.14, -0.03, 1.71, 1.73))
    piece("Headset", hs)
    wv = Mesh("WeldVisor", "Trim", "head")
    wv.add("Head", box(-0.095, 0.095, -0.01, 0.02, 1.88, 1.90))
    wvp = Mesh("WeldVisor_Plate", "Visor", "head").add("Head", box(-0.10, 0.10, -0.14, -0.04, 1.90, 1.93))
    piece("WeldVisor", wv, wvp)

    # ------------------------------------------------------------ torso armor
    ch = Mesh("Chest_Heavy", "Armor", "torso")
    ch.add("UpperChest", tbox(1.38, 1.58, (0.20 + p / 2, fy, -0.10), (0.21 + p / 2, fy + 0.01, -0.10)))
    ch.add("UpperChest", box(-0.20 - p / 2, 0.20 + p / 2, 0.09, 0.10 + p + 0.02, 1.38, 1.57))
    for sx in (-1, 1):
        ch.add("UpperChest", box(*sorted((sx * 0.19, sx * (0.22 + p / 2))), -0.10, 0.09, 1.38, 1.54))
    ch.add("UpperChest", box(-0.12, 0.12, -0.12, 0.11, 1.56, 1.62))
    ch.add("Chest", box(-0.16 - p / 2, 0.16 + p / 2, fy + 0.02, -0.09, 1.24, 1.38))
    ch.add("Chest", box(-0.16, 0.16, 0.08, 0.10 + p, 1.24, 1.38))
    meshes = [ch]
    if sleek:
        meshes.append(Mesh("Chest_Heavy_Light", "Light", "torso").add(
            "UpperChest", box(-0.10, 0.10, fy - 0.004, fy, 1.50, 1.51)))
    piece("Chest_Heavy", *meshes)
    cm = Mesh("Chest_Medium", "Armor", "torso")
    cm.add("UpperChest", box(-0.17, 0.17, fy + 0.01, -0.10, 1.40, 1.56))
    cm.add("UpperChest", box(-0.17, 0.17, 0.09, 0.11 + p / 2, 1.40, 1.56))
    cm.add("Chest", box(-0.14, 0.14, fy + 0.02, -0.09, 1.28, 1.38))
    piece("Chest_Medium", cm)
    vest = Mesh("Vest_Light", "Security", "torso")
    vest.add("UpperChest", box(-0.17, 0.17, -0.135, -0.10, 1.36, 1.55))
    vest.add("UpperChest", box(-0.17, 0.17, 0.09, 0.12, 1.36, 1.55))
    vest.add("Chest", box(-0.15, 0.15, -0.125, -0.09, 1.26, 1.36))
    piece("Vest_Light", vest)

    # ------------------------------------------------------------ uniforms by department
    for dept in ("Engineering", "Cargo", "Flight", "Security", "Suit", "Science"):
        name = {"Suit": "EVA_Suit", "Flight": "FlightSuit"}.get(dept, f"Coverall_{dept}")
        t = 0.02 if dept == "Suit" else 0.008
        m = _shell_limbs(_shell_torso(Mesh(name, dept, "uniform"), "Chest", "UpperChest", t), t)
        stripe = Mesh(f"{name}_Stripe", "Reflect" if dept != "Suit" else "Light", "uniform")
        stripe.add("UpperChest", box(-0.19 - t, 0.19 + t, -0.115 - t - 0.004, -0.11 - t, 1.47, 1.49))
        stripe.sym("LeftUpperArm", box(0.36, 0.38, -0.06 - t, 0.06 + t, 1.46 - t, 1.58 + t))
        piece(name, m, stripe)
    coat = _shell_limbs(_shell_torso(Mesh("OfficerCoat", "Command", "uniform"), "Chest", "UpperChest", 0.01), 0.01)
    coat.add("Hips", box(-0.16, 0.16, -0.11, -0.095, 0.80, 0.95))
    coat.add("Hips", box(-0.16, 0.16, 0.085, 0.10, 0.80, 0.95))
    rank = Mesh("OfficerCoat_Rank", "Rank", "uniform")
    rank.sym("LeftShoulder", box(0.10, 0.20, -0.05, 0.05, 1.57, 1.585))
    rank.add("UpperChest", box(0.08, 0.13, -0.124, -0.12, 1.49, 1.51))
    piece("OfficerCoat", coat, rank)
    mc = _shell_limbs(_shell_torso(Mesh("MedCoat", "Medical", "uniform"), "Chest", "UpperChest", 0.01), 0.01)
    mc.add("Hips", box(-0.16, 0.16, -0.11, -0.095, 0.70, 0.95))
    mc.add("Hips", box(-0.16, 0.16, 0.085, 0.10, 0.70, 0.95))
    mm = Mesh("MedCoat_Mark", "MedMark", "uniform").sym("LeftUpperArm", box(0.30, 0.40, -0.068, 0.068, 1.588, 1.592))
    piece("MedCoat", mc, mm)

    # ------------------------------------------------------------ shoulders, arms, legs
    pa = Mesh("Pauldrons_Heavy", "Armor", "shoulders")
    if sleek:
        pa.sym("LeftUpperArm", tbox(1.52, 1.62, (0.08, -0.09, 0.09), (0.06, -0.07, 0.07), cx=0.29))
    else:
        pa.sym("LeftUpperArm", box(0.20, 0.37, -0.10 - p / 2, 0.10 + p / 2, 1.53, 1.64))
        pa.sym("LeftUpperArm", box(0.30, 0.38, -0.10, 0.10, 1.46, 1.53))
    piece("Pauldrons_Heavy", pa)
    pl = Mesh("Pauldrons_Light", "Armor", "shoulders").sym("LeftUpperArm", box(0.22, 0.34, -0.08, 0.08, 1.575, 1.62))
    piece("Pauldrons_Light", pl)
    br = Mesh("Bracers", "Armor", "arms").sym("LeftLowerArm", box(0.54, 0.74, -0.048 - p, 0.048 + p, 1.475 - p, 1.565 + p))
    piece("Bracers", br)
    th = Mesh("Thigh_Plates", "Armor", "legs")
    th.sym("LeftUpperLeg", box(0.05, 0.20, -0.07 - p - 0.02, -0.07, 0.62, 0.92))
    th.sym("LeftUpperLeg", box(0.19, 0.19 + p + 0.015, -0.06, 0.06, 0.64, 0.90))
    piece("Thigh_Plates", th)
    sh = Mesh("Shin_Plates", "Armor", "legs")
    sh.sym("LeftLowerLeg", box(0.06, 0.19, -0.06 - p - 0.02, -0.06, 0.15, 0.48))
    sh.sym("LeftLowerLeg", box(0.07, 0.18, -0.06 - p - 0.04, -0.04, 0.47, 0.60))     # knee pad
    sh.sym("LeftFoot", box(0.06, 0.19, -0.16, 0.08, 0.0, 0.10))                     # boot shell
    piece("Shin_Plates", sh)
    mb = Mesh("Boots_Mag", "Suit", "legs").sym("LeftFoot", box(0.055, 0.195, -0.17, 0.085, -0.01, 0.12))
    mbl = Mesh("Boots_Mag_Glow", "Light", "legs").sym("LeftFoot", box(0.07, 0.18, -0.16, 0.07, -0.02, -0.01))
    piece("Boots_Mag", mb, mbl)

    # ------------------------------------------------------------ belts, rigs, harnesses
    bc = Mesh("Belt_Combat", "Trim", "belt")
    bc.add("Hips", box(-0.17, 0.17, -0.11, 0.10, 0.99, 1.05))
    for sx in (-1, 1):
        bc.add("Hips", box(*sorted((sx * 0.10, sx * 0.16)), -0.15, -0.11, 0.97, 1.06))   # mag pouches
        bc.add("Hips", box(*sorted((sx * 0.155, sx * 0.20)), -0.04, 0.01, 0.97, 1.05))   # grenade loops
    piece("Belt_Combat", bc)
    tb = Mesh("ToolBelt", "Trim", "belt")
    tb.add("Hips", box(-0.17, 0.17, -0.11, 0.10, 0.99, 1.04))
    tb.add("Hips", box(0.15, 0.21, -0.02, 0.06, 0.92, 1.04))
    piece("ToolBelt", tb)
    rig = Mesh("Rig_Mags", "Trim", "rig")
    for x in (-0.09, -0.03, 0.03, 0.09):
        rig.add("UpperChest", box(x - 0.026, x + 0.026, fy - 0.05, fy, 1.33, 1.42))
    rig.add("UpperChest", box(0.12, 0.16, fy - 0.03, fy, 1.42, 1.56))                  # grenade strap
    rig.add("UpperChest", box(-0.16, -0.12, fy - 0.03, fy, 1.42, 1.56))
    piece("Rig_Mags", rig)
    ms = Mesh("Strap_Medpens", "Trim", "rig")
    ms.add("UpperChest", box(0.13, 0.19, fy - 0.03, fy, 1.36, 1.56))
    msm = Mesh("Strap_Medpens_Mark", "MedMark", "rig").add("UpperChest", box(0.14, 0.18, fy - 0.034, fy - 0.03, 1.53, 1.55))
    piece("Strap_Medpens", ms, msm)
    hv = Mesh("CargoHarness", "HiVis", "rig")
    for sx in (-1, 1):
        hv.add("UpperChest", box(*sorted((sx * 0.06, sx * 0.10)), -0.135, -0.11, 1.38, 1.57))
        hv.add("Chest", box(*sorted((sx * 0.06, sx * 0.10)), -0.125, -0.10, 1.22, 1.38))
        hv.add("UpperChest", box(*sorted((sx * 0.06, sx * 0.10)), 0.10, 0.125, 1.30, 1.57))
    hvr = Mesh("CargoHarness_Reflect", "Reflect", "rig").add("UpperChest", box(-0.19, 0.19, -0.138, -0.13, 1.42, 1.45))
    hvr.sym("LeftLowerLeg", box(0.065, 0.185, -0.075, -0.065, 0.30, 0.33))
    piece("CargoHarness", hv, hvr)

    # ------------------------------------------------------------ backpacks
    def pack(name, mat, w, d, z0, z1, extra=()):
        m = Mesh(name, mat, "back").add("UpperChest", box(-w, w, 0.10 + p, 0.10 + p + d, z0, z1))
        piece(name, m, *extra)
        return m
    pack("Pack_Assault", "Armor", 0.14, 0.11, 1.22, 1.52)
    rings = Mesh("Pack_PurgeEmitter_Field", "Purge", "back")
    for k in range(3):                                   # field rings around the emitter mast
        rings.add("UpperChest", cyl("z", 0, 0.10 + p + 0.07, 1.56 + k * 0.08, 1.575 + k * 0.08, 0.07 - k * 0.012, seg=10))
    mast = Mesh("Pack_PurgeEmitter_Mast", "Trim", "back").add(
        "UpperChest", cyl("z", 0, 0.10 + p + 0.07, 1.50, 1.78, 0.012, seg=6))
    pack("Pack_PurgeEmitter", "Science", 0.13, 0.13, 1.20, 1.52, [mast, rings])
    hz = Mesh("Helmet_Hazmat", "Science", "head")
    hz.add("Head", tbox(1.62, 1.95, (0.12, -0.14, 0.12), (0.10, -0.11, 0.10)))
    hzv = Mesh("Helmet_Hazmat_Visor", "Visor", "head").add("Head", box(-0.10, 0.10, -0.152, -0.138, 1.70, 1.86))
    hzf = Mesh("Helmet_Hazmat_Filter", "Trim", "head").add("Head", cyl("y", 0, 1.66, -0.17, -0.14, 0.035, seg=8))
    piece("Helmet_Hazmat", hz, hzv, hzf)
    pack("Pack_Medic", "Medical", 0.14, 0.12, 1.20, 1.52,
         [Mesh("Pack_Medic_Mark", "MedMark", "back").add("UpperChest", box(-0.05, 0.05, 0.10 + p + 0.12, 0.10 + p + 0.125, 1.32, 1.42))])
    pack("Pack_Heavy", "Armor", 0.18, 0.16, 1.12, 1.56,
         [Mesh("Pack_Heavy_Feed", "Trim", "back").add("UpperChest", box(-0.20, -0.17, 0.0, 0.20, 1.18, 1.26))])
    eva_n = Mesh("Pack_EVA_Nozzles", "Joint", "back")
    eva_g = Mesh("Pack_EVA_Glow", "Light", "back")
    for sx in (-1, 1):
        eva_n.add("UpperChest", cyl("z", sx * 0.10, 0.10 + p + 0.08, 1.06, 1.16, 0.035, seg=8))
        eva_g.add("UpperChest", cyl("z", sx * 0.10, 0.10 + p + 0.08, 1.05, 1.06, 0.025, seg=8))
    pack("Pack_EVA", "Suit", 0.16, 0.14, 1.16, 1.56, [eva_n, eva_g])
    pack("Pack_Breacher", "Armor", 0.12, 0.08, 1.26, 1.50,
         [Mesh("Pack_Breacher_Rails", "Trim", "back").add("UpperChest", box(-0.17, 0.17, 0.10 + p + 0.08, 0.10 + p + 0.10, 1.30, 1.46))])
    pack("Pack_Radio", "Armor", 0.12, 0.10, 1.26, 1.52,
         [Mesh("Pack_Radio_Antenna", "Trim", "back").add("UpperChest", cyl("z", 0.08, 0.10 + p + 0.05, 1.52, 1.95, 0.006, seg=6))])
    return W


# =========================================================================
# Inventory sockets: (name, bone, position in rest pose, faction-1 scale)
# =========================================================================

def sockets(fac):
    p = PAD[fac]
    fy = -0.10 - p - 0.02
    s = []
    for i, x in enumerate((-0.09, -0.03, 0.03, 0.09), 1):
        s.append((f"MagSlot_{i}", "UpperChest", (x, fy - 0.025, 1.40)))
    for i, x in enumerate((0.13, -0.13), 5):
        s.append((f"MagSlot_{i}", "Hips", (x, -0.13, 1.02)))
    for i, x in enumerate((0.18, -0.18), 1):
        s.append((f"GrenadeSlot_{i}", "Hips", (x, -0.015, 1.01)))
    for i, x in enumerate((0.14, -0.14), 3):
        s.append((f"GrenadeSlot_{i}", "UpperChest", (x, fy - 0.03, 1.50)))
    for i in range(4):
        s.append((f"MedpenSlot_{i + 1}", "UpperChest", (0.16, fy - 0.035, 1.40 + i * 0.045)))
    s += [("ReviveKitSlot", "Hips", (-0.12, 0.16, 1.00)),
          ("ChargeSlot_1", "UpperChest", (0.19, 0.10 + p + 0.06, 1.38)),
          ("ChargeSlot_2", "UpperChest", (-0.19, 0.10 + p + 0.06, 1.38)),
          ("Holster", "RightUpperLeg", (-0.22, -0.02, 0.80)),
          ("BackWeapon", "UpperChest", (0.0, 0.10 + p + 0.18, 1.38)),
          ("ToolSlot", "Hips", (0.18, 0.02, 0.96)),
          ("RightHandGrip", "RightHand", (-0.84, -0.03, 1.52)),
          ("LeftHandGrip", "LeftHand", (0.84, -0.03, 1.52))]
    sx, sy, sz = BODY_SCALE[fac]
    return [(n, b, (x * sx, y * sy, z * sz)) for n, b, (x, y, z) in s]


# =========================================================================
# Roles: which pieces each role wears and what it carries
# =========================================================================

ROLES = {
    # ---- combat (armored) ---------------------------------------------------------
    "rifleman":      dict(dept="combat", pieces=["Helmet_Combat", "Chest_Heavy", "Pauldrons_Heavy", "Bracers",
                          "Thigh_Plates", "Shin_Plates", "Belt_Combat", "Rig_Mags", "Pack_Assault"],
                          primary="rifle", secondary="pistol",
                          inventory={"MagSlot_1": "primary_ammo", "MagSlot_2": "primary_ammo", "MagSlot_3": "primary_ammo",
                                     "MagSlot_4": "primary_ammo", "MagSlot_5": "secondary_ammo", "GrenadeSlot_1": "grenade",
                                     "GrenadeSlot_2": "grenade", "MedpenSlot_1": "medpen"}),
    "breacher":      dict(dept="combat", pieces=["Helmet_Combat", "Chest_Heavy", "Pauldrons_Heavy", "Bracers",
                          "Thigh_Plates", "Shin_Plates", "Belt_Combat", "Rig_Mags", "Pack_Breacher"],
                          primary="shotgun", secondary="pistol",
                          inventory={"MagSlot_1": "primary_ammo", "MagSlot_2": "primary_ammo", "MagSlot_3": "primary_ammo",
                                     "MagSlot_5": "secondary_ammo", "GrenadeSlot_1": "grenade", "ChargeSlot_1": "breach_charge",
                                     "ChargeSlot_2": "breach_charge", "MedpenSlot_1": "medpen"}),
    "medic":         dict(dept="combat", pieces=["Helmet_Combat", "Chest_Medium", "Pauldrons_Light", "Bracers",
                          "Thigh_Plates", "Shin_Plates", "Belt_Combat", "Strap_Medpens", "Pack_Medic"],
                          primary="smg", secondary="pistol",
                          inventory={"MagSlot_5": "primary_ammo", "MagSlot_6": "primary_ammo", "MedpenSlot_1": "medpen",
                                     "MedpenSlot_2": "medpen", "MedpenSlot_3": "medpen", "MedpenSlot_4": "medpen",
                                     "ReviveKitSlot": "revive_kit", "GrenadeSlot_1": "grenade"}),
    "heavy":         dict(dept="combat", pieces=["Helmet_Combat", "Chest_Heavy", "Pauldrons_Heavy", "Bracers",
                          "Thigh_Plates", "Shin_Plates", "Belt_Combat", "Pack_Heavy"],
                          primary="heavy", secondary="pistol",
                          inventory={"MagSlot_5": "primary_ammo", "MagSlot_6": "primary_ammo", "GrenadeSlot_1": "grenade",
                                     "MedpenSlot_1": "medpen"}),
    "grenadier":     dict(dept="combat", pieces=["Helmet_Combat", "Chest_Heavy", "Pauldrons_Heavy", "Bracers",
                          "Thigh_Plates", "Shin_Plates", "Belt_Combat", "Rig_Mags", "Pack_Assault"],
                          primary="bullpup_gl", secondary="pistol",
                          inventory={"MagSlot_1": "primary_ammo", "MagSlot_2": "primary_ammo", "MagSlot_3": "primary_ammo",
                                     "MagSlot_4": "primary_ammo", "MagSlot_5": "secondary_ammo", "MedpenSlot_1": "medpen"}),
    "squad_leader":  dict(dept="combat", pieces=["Helmet_Combat", "Chest_Heavy", "Pauldrons_Heavy", "Bracers",
                          "Thigh_Plates", "Shin_Plates", "Belt_Combat", "Rig_Mags", "Pack_Radio"],
                          primary="battle_rifle", secondary="pistol",
                          inventory={"MagSlot_1": "primary_ammo", "MagSlot_2": "primary_ammo", "MagSlot_3": "primary_ammo",
                                     "MagSlot_5": "secondary_ammo", "GrenadeSlot_1": "grenade", "GrenadeSlot_3": "grenade",
                                     "MedpenSlot_1": "medpen"}),
    "eva_boarder":   dict(dept="combat", pieces=["Helmet_EVA", "EVA_Suit", "Chest_Medium", "Pauldrons_Light",
                          "Boots_Mag", "Belt_Combat", "Rig_Mags", "Pack_EVA"],
                          primary="smg", secondary="pistol",
                          inventory={"MagSlot_1": "primary_ammo", "MagSlot_2": "primary_ammo", "MagSlot_3": "primary_ammo",
                                     "MagSlot_5": "secondary_ammo", "GrenadeSlot_1": "grenade", "ChargeSlot_1": "breach_charge",
                                     "MedpenSlot_1": "medpen"}),
    "drop_trooper":  dict(dept="combat", pieces=["Helmet_Combat", "Chest_Heavy", "Pauldrons_Heavy", "Bracers",
                          "Thigh_Plates", "Shin_Plates", "Belt_Combat", "Rig_Mags", "Pack_Assault"],
                          armor_material="ArmorDark", primary="battle_rifle", secondary="smg",
                          inventory={"MagSlot_1": "primary_ammo", "MagSlot_2": "primary_ammo", "MagSlot_3": "primary_ammo",
                                     "MagSlot_4": "primary_ammo", "MagSlot_5": "secondary_ammo", "MagSlot_6": "secondary_ammo",
                                     "GrenadeSlot_1": "grenade", "GrenadeSlot_2": "grenade", "MedpenSlot_1": "medpen"}),
    # ---- ship crew (no combat gear) -----------------------------------------------
    "pilot":           dict(dept="flight", pieces=["Helmet_Pilot", "FlightSuit", "Vest_Light"], primary=None,
                            secondary="pistol", inventory={"MagSlot_5": "secondary_ammo"}),
    "bridge_officer":  dict(dept="command", pieces=["Cap_Officer", "OfficerCoat"], primary=None, secondary="pistol",
                            inventory={}),
    "engineer":        dict(dept="engineering", pieces=["WeldVisor", "Coverall_Engineering", "ToolBelt"], primary=None,
                            secondary=None, inventory={"ToolSlot": "tool"}),
    "cargo_handler":   dict(dept="cargo", pieces=["Headset", "Coverall_Cargo", "CargoHarness"], primary=None,
                            secondary=None, inventory={}),
    "medical_officer": dict(dept="medical", pieces=["Headset", "MedCoat", "Strap_Medpens"], primary=None, secondary=None,
                            inventory={"MedpenSlot_1": "medpen", "MedpenSlot_2": "medpen", "MedpenSlot_3": "medpen",
                                       "MedpenSlot_4": "medpen", "ReviveKitSlot": "revive_kit"}),
    "scientist":       dict(dept="science", pieces=["Helmet_Hazmat", "Coverall_Science", "ToolBelt",
                            "Pack_PurgeEmitter"], primary=None, secondary=None,
                            inventory={"RightHandGrip": "purge_emitter", "MedpenSlot_1": "medpen"}),
    "security":        dict(dept="security", pieces=["Helmet_Combat", "Coverall_Security", "Vest_Light",
                            "Pauldrons_Light", "Belt_Combat"], primary="smg", secondary="pistol",
                            inventory={"MagSlot_5": "primary_ammo", "MagSlot_6": "primary_ammo", "GrenadeSlot_1": "grenade"}),
}


# Drop troopers wear the same armor in a darker finish (ODST-style "black" variants).
DARK_VARIANTS = ["Helmet_Combat", "Chest_Heavy", "Pauldrons_Heavy", "Bracers", "Thigh_Plates",
                 "Shin_Plates", "Pack_Assault"]


def full_wardrobe(fac):
    """wardrobe() plus dark variants, scaled to the faction's body."""
    W = wardrobe(fac)
    for name in DARK_VARIANTS:
        W[name + "_Dark"] = []
        for m in W[name]:
            d = Mesh(m.name + "_Dark", "ArmorDark" if m.material == "Armor" else m.material, m.slot)
            d.items = list(m.items)
            W[name + "_Dark"].append(d)
    sx, sy, sz = BODY_SCALE[fac]
    for meshes in W.values():
        for m in meshes:
            m.items = [(b, transform(s, lambda p: (p[0] * sx, p[1] * sy, p[2] * sz))) for b, s in m.items]
    return W


def body(fac):
    sx, sy, sz = BODY_SCALE[fac]
    out = chassis(fac)
    for m in out:
        m.items = [(b, transform(s, lambda p: (p[0] * sx, p[1] * sy, p[2] * sz))) for b, s in m.items]
    return out


def role_pieces(role):
    r = ROLES[role]
    if r.get("armor_material") == "ArmorDark":
        return [p + "_Dark" if p in DARK_VARIANTS else p for p in r["pieces"]]
    return list(r["pieces"])


# =========================================================================
# Weapons. Origin = where the right hand grips; muzzle points -Y; up is +Z.
# Faction 1: ballistic, Halo / Marathon (chunky, bold flat color panels).
# Faction 2: energy, Covenant / BO3 / Infinite (faceted, glowing channels).
# =========================================================================

class WB:
    """Weapon builder: one Mesh per material, plus the mag/cell and markers."""
    def __init__(self, name):
        self.name, self.meshes, self.markers, self.mag = name, {}, {}, None

    def add(self, mat, solid):
        if mat not in self.meshes:
            self.meshes[mat] = Mesh(f"{self.name}_{mat}", mat)
        self.meshes[mat].add(None, solid)

    def sides(self, mat, x0, x1, *rest):
        for sx in (-1, 1):
            self.add(mat, box(*sorted((sx * x0, sx * x1)), *rest))

    def ammo(self, kind, mat, solid, port):
        """The removable magazine / power cell and the point it seats into."""
        self.mag = Mesh(f"{self.name}_{kind}", mat).add(None, solid)
        self.markers["MagWell" if kind == "Mag" else "CellPort"] = port

    def mark(self, **kw):
        self.markers.update(kw)

    def result(self):
        return list(self.meshes.values()), self.mag, self.markers


# ---------- faction 1: ballistic -------------------------------------------------

def w_assault_rifle():                      # bullpup, Halo-inspired
    w = WB("F1_AssaultRifle")
    w.add("WBody", box(-0.035, 0.035, -0.30, 0.32, 0.00, 0.11))
    w.add("WBody", box(-0.04, 0.04, -0.58, -0.30, -0.01, 0.10))
    w.sides("WAccent", 0.04, 0.044, -0.52, -0.32, 0.02, 0.075)
    w.add("WDark", cyl("y", 0, 0.05, -0.74, -0.58, 0.012))
    w.add("WDark", box(-0.018, 0.018, -0.25, 0.05, 0.11, 0.13))
    w.add("WDark", box(-0.025, 0.025, -0.15, -0.03, 0.13, 0.18))
    w.add("Optic", box(-0.018, 0.018, -0.153, -0.149, 0.14, 0.17))
    w.add("WDark", box(-0.02, 0.02, -0.02, 0.04, -0.12, 0.0))
    w.add("WDark", box(-0.006, 0.006, -0.08, 0.0, -0.045, -0.035))
    w.add("WDark", box(-0.04, 0.04, 0.32, 0.36, -0.03, 0.12))
    w.add("Energy", box(-0.015, 0.015, 0.10, 0.16, 0.11, 0.114))      # ammo counter
    w.ammo("Mag", "WPanel", box(-0.022, 0.022, 0.09, 0.17, -0.20, 0.0), (0, 0.13, 0.0))
    w.mark(Grip=(0, 0.01, -0.06), SupportHand=(0, -0.44, -0.01), Muzzle=(0, -0.75, 0.05), Sight=(0, -0.09, 0.17))
    return w.result()


def w_battle_rifle():                       # long rifle with big scope
    w = WB("F1_BattleRifle")
    w.add("WBody", box(-0.034, 0.034, -0.36, 0.10, 0.0, 0.10))
    w.add("WBody", box(-0.038, 0.038, -0.62, -0.36, 0.005, 0.09))
    w.sides("WAccent", 0.038, 0.042, -0.60, -0.40, 0.03, 0.06)
    w.add("WDark", cyl("y", 0, 0.05, -0.80, -0.62, 0.011))
    w.add("WDark", box(-0.02, 0.02, -0.82, -0.78, 0.035, 0.065))
    w.add("WDark", cyl("y", 0, 0.16, -0.30, -0.02, 0.025))           # scope
    w.add("Optic", cyl("y", 0, 0.16, -0.305, -0.30, 0.02))
    w.add("WDark", box(-0.015, 0.015, -0.22, -0.10, 0.10, 0.14))
    w.add("WDark", box(-0.02, 0.02, -0.02, 0.04, -0.12, 0.0))
    w.add("WPanel", box(-0.03, 0.03, 0.10, 0.36, 0.02, 0.09))          # stock
    w.add("WDark", box(-0.035, 0.035, 0.36, 0.40, -0.03, 0.11))
    w.ammo("Mag", "WPanel", box(-0.02, 0.02, -0.12, -0.05, -0.17, 0.0), (0, -0.085, 0.0))
    w.mark(Grip=(0, 0.01, -0.06), SupportHand=(0, -0.48, -0.0), Muzzle=(0, -0.83, 0.05), Sight=(0, 0.0, 0.16))
    return w.result()


def w_smg():                                # compact, suppressed, mag in the grip
    w = WB("F1_SMG")
    w.add("WBody", box(-0.03, 0.03, -0.20, 0.10, 0.0, 0.09))
    w.sides("WAccent", 0.03, 0.034, -0.16, 0.04, 0.02, 0.06)
    w.add("WDark", cyl("y", 0, 0.045, -0.42, -0.20, 0.022))
    w.add("WDark", box(-0.02, 0.02, -0.02, 0.035, -0.11, 0.0))
    w.add("WDark", box(-0.015, 0.015, -0.14, -0.06, -0.06, 0.0))       # front grip
    for sx in (-1, 1):
        w.add("WDark", box(*sorted((sx * 0.012, sx * 0.02)), 0.10, 0.30, 0.02, 0.035))   # folding stock
    w.add("WDark", box(-0.03, 0.03, 0.28, 0.31, -0.02, 0.06))
    w.add("WDark", box(-0.012, 0.012, -0.10, 0.05, 0.09, 0.12))
    w.ammo("Mag", "WPanel", box(-0.015, 0.015, -0.005, 0.03, -0.24, -0.02), (0, 0.012, -0.02))
    w.mark(Grip=(0, 0.01, -0.06), SupportHand=(0, -0.10, -0.04), Muzzle=(0, -0.43, 0.045), Sight=(0, -0.02, 0.12))
    return w.result()


def w_shotgun():                            # magazine-fed combat shotgun
    w = WB("F1_Shotgun")
    w.add("WBody", box(-0.04, 0.04, -0.30, 0.20, -0.02, 0.12))
    w.add("WAccent", box(-0.041, 0.041, -0.28, -0.08, 0.07, 0.11))
    w.add("WDark", cyl("y", 0, 0.07, -0.62, -0.30, 0.02))
    w.add("WDark", cyl("y", 0, 0.025, -0.55, -0.30, 0.018))
    w.add("WBody", box(-0.035, 0.035, -0.52, -0.36, -0.03, 0.04))      # pump / fore grip
    w.add("WDark", box(-0.022, 0.022, -0.02, 0.045, -0.12, -0.02))
    w.add("WBody", box(-0.035, 0.035, 0.20, 0.42, 0.0, 0.10))
    w.add("WDark", box(-0.04, 0.04, 0.42, 0.45, -0.03, 0.12))
    w.add("WDark", box(-0.01, 0.01, -0.62, -0.58, 0.09, 0.11))         # bead sight
    w.ammo("Mag", "WPanel", box(-0.03, 0.03, -0.13, -0.05, -0.18, -0.02), (0, -0.09, -0.02))
    w.mark(Grip=(0, 0.01, -0.07), SupportHand=(0, -0.44, -0.04), Muzzle=(0, -0.63, 0.07), Sight=(0, -0.10, 0.13))
    return w.result()


def w_sniper():                             # long-range rifle with bipod
    w = WB("F1_Sniper")
    w.add("WBody", box(-0.036, 0.036, -0.30, 0.18, 0.0, 0.10))
    w.add("WDark", cyl("y", 0, 0.05, -1.05, -0.30, 0.016))
    w.add("WDark", box(-0.03, 0.03, -1.10, -1.04, 0.025, 0.075))      # muzzle brake
    w.add("WDark", cyl("y", 0, 0.17, -0.28, 0.06, 0.032))            # scope
    w.add("Optic", cyl("y", 0, 0.17, -0.285, -0.28, 0.027))
    w.add("WDark", box(-0.012, 0.012, -0.20, -0.16, 0.10, 0.14))
    w.add("WDark", box(-0.012, 0.012, -0.02, 0.02, 0.10, 0.14))
    w.sides("WAccent", 0.036, 0.04, -0.26, 0.12, 0.03, 0.07)
    w.add("WDark", box(-0.02, 0.02, -0.02, 0.04, -0.12, 0.0))
    w.add("WPanel", box(-0.032, 0.032, 0.18, 0.55, 0.0, 0.09))
    w.add("WDark", box(-0.03, 0.03, 0.30, 0.44, 0.09, 0.12))           # cheek rest
    for sx in (-1, 1):
        w.add("WDark", box(*sorted((sx * 0.01, sx * 0.02)), -0.70, -0.45, -0.01, 0.01))   # folded bipod
    w.ammo("Mag", "WPanel", box(-0.024, 0.024, -0.13, -0.05, -0.13, 0.0), (0, -0.09, 0.0))
    w.mark(Grip=(0, 0.01, -0.06), SupportHand=(0, -0.40, 0.0), Muzzle=(0, -1.11, 0.05), Sight=(0, 0.10, 0.17))
    return w.result()


def w_magnum():                             # heavy sidearm
    w = WB("F1_Magnum")
    w.add("WBody", box(-0.018, 0.018, -0.20, 0.03, 0.03, 0.075))
    w.sides("WAccent", 0.018, 0.021, -0.17, -0.05, 0.045, 0.065)
    w.add("WDark", box(-0.016, 0.016, -0.16, 0.0, -0.005, 0.03))
    w.add("WDark", box(-0.017, 0.017, -0.005, 0.045, -0.11, 0.0))
    w.add("WDark", box(-0.006, 0.006, -0.07, -0.02, -0.03, -0.02))
    w.add("WDark", box(-0.006, 0.006, -0.19, -0.17, 0.075, 0.085))
    w.ammo("Mag", "WPanel", box(-0.013, 0.013, 0.0, 0.035, -0.125, -0.01), (0, 0.017, -0.01))
    w.mark(Grip=(0, 0.02, -0.05), SupportHand=(0, 0.02, -0.07), Muzzle=(0, -0.205, 0.052), Sight=(0, 0.02, 0.085))
    return w.result()


def w_lmg():                                # squad machine gun
    w = WB("F1_LMG")
    w.add("WBody", box(-0.045, 0.045, -0.36, 0.20, -0.03, 0.13))
    w.add("WBody", box(-0.035, 0.035, -0.70, -0.36, 0.0, 0.10))
    for k in range(5):
        w.sides("WAccent", 0.035, 0.038, -0.68 + k * 0.065, -0.645 + k * 0.065, 0.03, 0.07)
    w.add("WDark", cyl("y", 0, 0.05, -0.86, -0.70, 0.016))
    w.add("WDark", box(-0.012, 0.012, -0.30, -0.06, 0.13, 0.20))
    w.add("WDark", box(-0.04, 0.04, -0.30, -0.26, 0.13, 0.20))        # carry handle posts
    w.add("WDark", box(-0.022, 0.022, -0.02, 0.045, -0.13, -0.03))
    w.add("WBody", box(-0.04, 0.04, 0.20, 0.48, -0.01, 0.11))
    w.add("WDark", box(-0.045, 0.045, 0.48, 0.52, -0.04, 0.13))
    for sx in (-1, 1):
        w.add("WDark", box(*sorted((sx * 0.012, sx * 0.024)), -0.75, -0.48, -0.02, 0.0))
    w.ammo("Mag", "WPanel", box(-0.05, 0.05, -0.20, -0.06, -0.20, -0.03), (0, -0.13, -0.03))
    w.mark(Grip=(0, 0.01, -0.08), SupportHand=(0, -0.45, -0.01), Muzzle=(0, -0.87, 0.05), Sight=(0, -0.18, 0.21))
    return w.result()


# ---------- faction 2: energy -----------------------------------------------------

def w_plasma_rifle():                       # Covenant-inspired twin-prong rifle
    w = WB("F2_PlasmaRifle")
    w.add("WBody", ytaper(-0.42, 0.14, (0.05, -0.02, 0.10), (0.032, 0.0, 0.075)))
    for sx in (-1, 1):
        w.add("WPanel", box(*sorted((sx * 0.018, sx * 0.042)), -0.62, -0.40, 0.012, 0.062))   # prongs
    w.add("Energy", box(-0.008, 0.008, -0.60, -0.42, 0.03, 0.045))     # plasma channel
    w.add("Energy", box(-0.012, 0.012, -0.40, -0.05, 0.095, 0.105))
    w.add("WDark", box(-0.018, 0.018, -0.02, 0.04, -0.12, -0.02))
    w.add("WDark", box(-0.03, 0.03, -0.05, 0.10, -0.03, -0.015))      # grip loop
    w.sides("WAccent", 0.046, 0.05, -0.20, 0.06, 0.02, 0.06)
    w.ammo("Cell", "Energy", box(-0.022, 0.022, 0.06, 0.14, 0.075, 0.11), (0, 0.10, 0.09))
    w.mark(Grip=(0, 0.01, -0.07), SupportHand=(0, -0.30, -0.02), Muzzle=(0, -0.63, 0.037), Sight=(0, -0.10, 0.12))
    return w.result()


def w_pulse_carbine():                      # BO3 / Infinite-style angular carbine
    w = WB("F2_PulseCarbine")
    w.add("WBody", box(-0.032, 0.032, -0.32, 0.12, 0.0, 0.10))
    w.add("WBody", ytaper(-0.62, -0.32, (0.022, 0.025, 0.07), (0.034, 0.005, 0.10)))
    w.sides("Energy", 0.033, 0.036, -0.58, -0.10, 0.06, 0.07)          # glowing rails
    w.add("WDark", cyl("y", 0, 0.05, -0.70, -0.60, 0.012, seg=8))
    w.add("WPanel", box(-0.022, 0.022, -0.16, -0.10, 0.10, 0.17))      # holo sight frame
    w.add("Optic", box(-0.016, 0.016, -0.13, -0.127, 0.115, 0.16))
    w.add("WDark", box(-0.018, 0.018, -0.02, 0.04, -0.12, 0.0))
    w.add("WBody", ytaper(0.12, 0.40, (0.028, 0.0, 0.10), (0.03, -0.02, 0.11)))
    w.add("WAccent", box(-0.031, 0.031, 0.30, 0.40, 0.04, 0.06))
    w.ammo("Cell", "Energy", box(-0.02, 0.02, -0.12, -0.05, -0.12, 0.0), (0, -0.085, 0.0))
    w.mark(Grip=(0, 0.01, -0.06), SupportHand=(0, -0.42, 0.0), Muzzle=(0, -0.71, 0.05), Sight=(0, -0.05, 0.14))
    return w.result()


def w_energy_smg():                         # compact, circular emitter
    w = WB("F2_EnergySMG")
    w.add("WBody", box(-0.03, 0.03, -0.18, 0.10, 0.0, 0.09))
    w.add("WPanel", cyl("y", 0, 0.045, -0.26, -0.18, 0.04, seg=10))
    w.add("Energy", cyl("y", 0, 0.045, -0.265, -0.26, 0.028, seg=10))
    w.sides("Energy", 0.03, 0.033, -0.14, 0.06, 0.03, 0.04)
    w.add("WDark", box(-0.018, 0.018, -0.02, 0.035, -0.11, 0.0))
    w.add("WBody", ytaper(0.10, 0.26, (0.025, 0.01, 0.08), (0.02, 0.0, 0.06)))
    w.ammo("Cell", "Energy", box(-0.014, 0.014, -0.005, 0.03, -0.20, -0.02), (0, 0.012, -0.02))
    w.mark(Grip=(0, 0.01, -0.06), SupportHand=(0, -0.12, -0.02), Muzzle=(0, -0.27, 0.045), Sight=(0, -0.02, 0.10))
    return w.result()


def w_scatter_gun():                        # energy shotgun with a wide slotted muzzle
    w = WB("F2_ScatterGun")
    w.add("WBody", box(-0.04, 0.04, -0.28, 0.18, -0.02, 0.11))
    w.add("WPanel", ytaper(-0.48, -0.28, (0.055, -0.03, 0.12), (0.04, -0.02, 0.11)))
    for k in range(3):
        w.add("Energy", box(-0.045, 0.045, -0.485, -0.48, -0.015 + k * 0.04, 0.0 + k * 0.04))
    w.sides("WAccent", 0.04, 0.044, -0.26, -0.04, 0.03, 0.07)
    w.add("WDark", box(-0.022, 0.022, -0.02, 0.045, -0.12, -0.02))
    w.add("WBody", box(-0.03, 0.03, 0.18, 0.38, 0.0, 0.09))
    w.ammo("Cell", "Energy", box(-0.03, 0.03, -0.12, -0.05, -0.16, -0.02), (0, -0.085, -0.02))
    w.mark(Grip=(0, 0.01, -0.07), SupportHand=(0, -0.38, -0.03), Muzzle=(0, -0.49, 0.04), Sight=(0, -0.10, 0.12))
    return w.result()


def w_beam_rifle():                         # Covenant-inspired split-barrel beam rifle
    w = WB("F2_BeamRifle")
    w.add("WBody", box(-0.034, 0.034, -0.30, 0.16, 0.0, 0.10))
    for sx in (-1, 1):
        w.add("WPanel", box(*sorted((sx * 0.012, sx * 0.03)), -1.10, -0.30, 0.02, 0.08))
    w.add("Energy", box(-0.005, 0.005, -1.08, -0.30, 0.04, 0.06))
    w.add("WDark", cyl("y", 0, 0.165, -0.28, 0.04, 0.03, seg=8))
    w.add("Optic", cyl("y", 0, 0.165, -0.285, -0.28, 0.025, seg=8))
    w.add("WDark", box(-0.012, 0.012, -0.18, -0.02, 0.10, 0.14))
    w.add("WDark", box(-0.018, 0.018, -0.02, 0.04, -0.12, 0.0))
    w.add("WBody", ytaper(0.16, 0.52, (0.03, 0.0, 0.10), (0.03, -0.03, 0.09)))
    w.sides("WAccent", 0.034, 0.038, -0.20, 0.10, 0.03, 0.06)
    w.ammo("Cell", "Energy", box(-0.022, 0.022, -0.13, -0.05, -0.12, 0.0), (0, -0.09, 0.0))
    w.mark(Grip=(0, 0.01, -0.06), SupportHand=(0, -0.40, 0.0), Muzzle=(0, -1.11, 0.05), Sight=(0, 0.08, 0.165))
    return w.result()


def w_plasma_pistol():                      # Covenant-inspired hunched pistol
    w = WB("F2_PlasmaPistol")
    w.add("WBody", ytaper(-0.17, 0.05, (0.028, 0.0, 0.07), (0.022, 0.015, 0.06)))
    w.add("WPanel", cyl("y", 0, 0.038, -0.19, -0.17, 0.026, seg=10))
    w.add("Energy", cyl("y", 0, 0.038, -0.195, -0.19, 0.017, seg=10))
    w.add("Energy", box(-0.004, 0.004, -0.15, 0.0, 0.069, 0.075))
    w.add("WDark", box(-0.016, 0.016, -0.005, 0.045, -0.11, 0.0))
    w.ammo("Cell", "Energy", box(-0.012, 0.012, 0.0, 0.035, -0.125, -0.10), (0, 0.017, -0.10))
    w.mark(Grip=(0, 0.02, -0.05), SupportHand=(0, 0.02, -0.07), Muzzle=(0, -0.20, 0.038), Sight=(0, 0.02, 0.08))
    return w.result()


def w_arc_cannon():                         # heavy energy weapon with coil rings
    w = WB("F2_ArcCannon")
    w.add("WBody", box(-0.05, 0.05, -0.30, 0.25, -0.03, 0.13))
    w.add("Energy", cyl("y", 0, 0.05, -0.75, -0.30, 0.018, seg=8))
    for k in range(4):
        y = -0.36 - k * 0.10
        w.add("WPanel", cyl("y", 0, 0.05, y - 0.03, y, 0.06, seg=10))
    w.add("WDark", box(-0.06, 0.06, -0.78, -0.74, -0.01, 0.11))
    w.add("WDark", box(-0.022, 0.022, -0.02, 0.045, -0.13, -0.03))
    w.add("WDark", box(-0.012, 0.012, -0.28, -0.10, 0.13, 0.19))
    w.add("WDark", box(-0.05, 0.05, -0.28, -0.24, 0.13, 0.19))
    w.sides("WAccent", 0.05, 0.054, -0.26, 0.20, 0.03, 0.09)
    w.add("WBody", box(-0.04, 0.04, 0.25, 0.48, 0.0, 0.11))
    w.ammo("Cell", "Energy", box(-0.045, 0.045, 0.06, 0.22, 0.13, 0.20), (0, 0.14, 0.13))
    w.mark(Grip=(0, 0.01, -0.08), SupportHand=(0, -0.45, 0.0), Muzzle=(0, -0.79, 0.05), Sight=(0, -0.19, 0.20))
    return w.result()


WEAPONS = {   # faction -> weapon class -> (model name, builder)
    # bullpup_gl: the real model is built in Godot (godot_demo/tests/make_bullpup.gd writes a .tscn that
    # replaces the .glb); the builder here only gives the exporters a placeholder.
    1: {"rifle": ("F1_AssaultRifle", w_assault_rifle), "battle_rifle": ("F1_BattleRifle", w_battle_rifle),
        "bullpup_gl": ("F1_BullpupGL", w_battle_rifle),
        "smg": ("F1_SMG", w_smg), "shotgun": ("F1_Shotgun", w_shotgun), "sniper": ("F1_Sniper", w_sniper),
        "pistol": ("F1_Magnum", w_magnum), "heavy": ("F1_LMG", w_lmg)},
    2: {"rifle": ("F2_PlasmaRifle", w_plasma_rifle), "battle_rifle": ("F2_PulseCarbine", w_pulse_carbine),
        "bullpup_gl": ("F2_BullpupGL", w_pulse_carbine),
        "smg": ("F2_EnergySMG", w_energy_smg), "shotgun": ("F2_ScatterGun", w_scatter_gun),
        "sniper": ("F2_BeamRifle", w_beam_rifle), "pistol": ("F2_PlasmaPistol", w_plasma_pistol),
        "heavy": ("F2_ArcCannon", w_arc_cannon)},
}


# =========================================================================
# Inventory items (shown in sockets, held, thrown, used)
# =========================================================================

def items(fac):
    """{item_name: [Mesh]} — item origin is its center."""
    out = {}

    def centered(mesh, name):
        pts = [v for _, (vs, _) in mesh.items for v in vs]
        c = [(max(p[i] for p in pts) + min(p[i] for p in pts)) / 2 for i in range(3)]
        m = Mesh(name, mesh.material)
        m.items = [(None, transform(s, lambda p: (p[0] - c[0], p[1] - c[1], p[2] - c[2]))) for _, s in mesh.items]
        return m

    for cls_, (wname, builder) in WEAPONS[fac].items():
        _, mag, _ = builder()
        kind = "Mag" if fac == 1 else "Cell"
        out[f"{wname}_{kind}"] = [centered(mag, f"Item_{wname}_{kind}")]
    g = f"F{fac}_"
    if fac == 1:
        gr = Mesh(f"Item_{g}FragGrenade", "WBody").add(None, cyl("z", 0, 0, -0.045, 0.035, 0.032, seg=10))
        gr2 = Mesh(f"Item_{g}FragGrenade_Band", "WAccent").add(None, cyl("z", 0, 0, -0.01, 0.01, 0.034, seg=10))
        gr3 = Mesh(f"Item_{g}FragGrenade_Fuse", "WDark").add(None, box(-0.012, 0.012, -0.012, 0.012, 0.035, 0.055))
        out[f"{g}FragGrenade"] = [gr, gr2, gr3]
    else:
        gr = Mesh(f"Item_{g}PlasmaGrenade", "WPanel").add(None, cyl("z", 0, 0, -0.03, 0.03, 0.035, seg=8))
        gr2 = Mesh(f"Item_{g}PlasmaGrenade_Core", "Energy")
        gr2.add(None, cyl("z", 0, 0, 0.03, 0.045, 0.022, seg=8)).add(None, cyl("z", 0, 0, -0.045, -0.03, 0.022, seg=8))
        out[f"{g}PlasmaGrenade"] = [gr, gr2]
    mp = Mesh(f"Item_{g}Medpen", "Medical").add(None, cyl("z", 0, 0, -0.06, 0.05, 0.011, seg=8))
    mp2 = Mesh(f"Item_{g}Medpen_Cap", "MedMark").add(None, cyl("z", 0, 0, 0.05, 0.07, 0.012, seg=8))
    out[f"{g}Medpen"] = [mp, mp2]
    rk = Mesh(f"Item_{g}ReviveKit", "Medical").add(None, box(-0.09, 0.09, -0.04, 0.04, -0.06, 0.06))
    rk2 = Mesh(f"Item_{g}ReviveKit_Mark", "MedMark").add(None, box(-0.04, 0.04, -0.044, -0.04, -0.03, 0.03))
    rk2.add(None, box(-0.05, 0.05, -0.01, 0.01, 0.06, 0.075))
    out[f"{g}ReviveKit"] = [rk, rk2]
    bc = Mesh(f"Item_{g}BreachCharge", "WDark").add(None, box(-0.10, 0.10, -0.02, 0.02, -0.07, 0.07))
    bc2 = Mesh(f"Item_{g}BreachCharge_Stripes", "WAccent").add(None, box(-0.10, 0.10, -0.024, -0.02, 0.05, 0.065))
    bc3 = Mesh(f"Item_{g}BreachCharge_Light", "Light").add(None, box(-0.012, 0.012, -0.026, -0.02, -0.01, 0.01))
    out[f"{g}BreachCharge"] = [bc, bc2, bc3]
    pe = Mesh(f"Item_{g}PurgeEmitter", "Science").add(None, box(-0.03, 0.03, -0.10, 0.12, -0.04, 0.04))
    pe.add(None, box(-0.018, 0.018, 0.04, 0.09, -0.13, -0.04))                     # handle
    pe2 = Mesh(f"Item_{g}PurgeEmitter_Dish", "WPanel").add(None, cyl("y", 0, 0, -0.16, -0.10, 0.06, seg=10))
    pe3 = Mesh(f"Item_{g}PurgeEmitter_Field", "Purge").add(None, cyl("y", 0, 0, -0.17, -0.16, 0.045, seg=10))
    out[f"{g}PurgeEmitter"] = [pe, pe2, pe3]
    tl = Mesh(f"Item_{g}Tool", "WPanel").add(None, box(-0.012, 0.012, -0.012, 0.012, -0.10, 0.08))
    tl2 = Mesh(f"Item_{g}Tool_Head", "WAccent").add(None, box(-0.03, 0.03, -0.015, 0.015, 0.08, 0.12))
    out[f"{g}Tool"] = [tl, tl2]
    return out


def resolve_item(fac, role, kind):
    """Map a role's inventory entry to the actual item for this faction."""
    r = ROLES[role]
    sfx = "Mag" if fac == 1 else "Cell"
    if kind == "primary_ammo":
        return f"{WEAPONS[fac][r['primary']][0]}_{sfx}" if r["primary"] else None
    if kind == "secondary_ammo":
        return f"{WEAPONS[fac][r['secondary']][0]}_{sfx}" if r["secondary"] else None
    return {"grenade": f"F{fac}_{'FragGrenade' if fac == 1 else 'PlasmaGrenade'}", "medpen": f"F{fac}_Medpen",
            "revive_kit": f"F{fac}_ReviveKit", "breach_charge": f"F{fac}_BreachCharge", "tool": f"F{fac}_Tool",
            "purge_emitter": f"F{fac}_PurgeEmitter"}[kind]


# =========================================================================
# Combat data: the damage / armor tradeoff between the factions
# =========================================================================

FACTION_COMBAT = {
    # damage_mult scales every weapon's damage; armor_mult scales every armor piece's
    # damage reduction. Heavy faction: tough armor, normal damage. Sleek faction: hits
    # harder with energy weapons, but its armor stops less.
    1: dict(name="Heavy (ODST-like, ballistic)", damage_mult=1.0, armor_mult=1.0),
    2: dict(name="Sleek (BO3-like, energy)", damage_mult=1.3, armor_mult=0.55),
}
DR_CAP = 0.60          # total damage reduction never exceeds 60%

ARMOR_DR = {           # base damage reduction per piece (heavy faction values)
    "Helmet_Combat": 0.10, "Chest_Heavy": 0.22, "Chest_Medium": 0.14, "Vest_Light": 0.08,
    "Pauldrons_Heavy": 0.06, "Pauldrons_Light": 0.03, "Bracers": 0.03, "Thigh_Plates": 0.05,
    "Shin_Plates": 0.04, "Helmet_EVA": 0.06, "EVA_Suit": 0.06, "Boots_Mag": 0.01, "Helmet_Pilot": 0.03,
}

WEAPON_CLASSES = {     # base stats before the faction damage multiplier (placeholders to tune)
    "rifle":        dict(damage=20, pellets=1, rpm=650, ammo_per_load=36, reload_s=2.2, range_m=60),
    "battle_rifle": dict(damage=24, pellets=1, rpm=780, ammo_per_load=32, reload_s=2.3, range_m=45),   # CQB bullpup
    "bullpup_gl":   dict(damage=24, pellets=1, rpm=780, ammo_per_load=32, reload_s=2.3, range_m=45),   # + 40 mm launcher
    "smg":          dict(damage=14, pellets=1, rpm=900, ammo_per_load=48, reload_s=1.8, range_m=30),
    "shotgun":      dict(damage=12, pellets=8, rpm=70, ammo_per_load=8, reload_s=2.6, range_m=12),
    "sniper":       dict(damage=110, pellets=1, rpm=40, ammo_per_load=5, reload_s=3.0, range_m=300),
    "pistol":       dict(damage=35, pellets=1, rpm=200, ammo_per_load=10, reload_s=1.5, range_m=40),
    "heavy":        dict(damage=22, pellets=1, rpm=750, ammo_per_load=100, reload_s=5.0, range_m=80),
}
HEAVY_OVERRIDES = {2: dict(damage=60, rpm=60, ammo_per_load=12, splash_radius_m=3.0)}   # arc cannon

ITEM_STATS = {
    "FragGrenade":   dict(damage=90, radius_m=5.0, fuse_s=3.0),
    "PlasmaGrenade": dict(damage=90, radius_m=4.0, fuse_s=2.0, sticks=True),
    "Medpen":        dict(heal=40, use_s=1.0, stops_bleedout=True),
    "ReviveKit":     dict(revive_s=4.0, uses=3, revive_health=50),
    "BreachCharge":  dict(damage=150, radius_m=3.0, fuse_s=3.0, breaches=["BreachWall", "BreachDoor",
                          "BlastDoor (2 charges)", "Airlock outer door"]),
    "Tool":          dict(repair_per_s=10, opens=["locked doors (slow)"]),
    "PurgeEmitter":  dict(radius_m=4.0, clear_m2_per_s=6.0, battery_s=180, recharge_s=60,
                          note="The ONLY way to remove the infection. Carried by scientists."),
}


def role_dr(fac, role):
    dr = sum(ARMOR_DR.get(p.replace("_Dark", ""), 0.0) for p in role_pieces(role))
    return round(min(DR_CAP, dr * FACTION_COMBAT[fac]["armor_mult"]), 3)


def combat_data():
    data = dict(
        damage_formula="damage_taken = weapon_damage * attacker.damage_mult * (1 - target_damage_reduction)",
        dr_cap=DR_CAP, factions={}, armor_pieces={}, weapons={}, items={}, roles={})
    for fac in (1, 2):
        fc = FACTION_COMBAT[fac]
        data["factions"][fac] = fc
        data["armor_pieces"][fac] = {k: round(v * fc["armor_mult"], 3) for k, v in ARMOR_DR.items()}
        data["weapons"][fac] = {}
        for cls_, (wname, _) in WEAPONS[fac].items():
            st = dict(WEAPON_CLASSES[cls_])
            if cls_ == "heavy":
                st.update(HEAVY_OVERRIDES.get(fac, {}))
            st["damage"] = round(st["damage"] * fc["damage_mult"], 1)
            st.update(model=wname, type="ballistic" if fac == 1 else "energy",
                      ammo_item=f"{wname}_{'Mag' if fac == 1 else 'Cell'}")
            data["weapons"][fac][cls_] = st
        data["roles"][fac] = {}
        for role, r in ROLES.items():
            data["roles"][fac][role] = dict(
                department=r["dept"], pieces=role_pieces(role),
                primary=WEAPONS[fac][r["primary"]][0] if r["primary"] else None,
                secondary=WEAPONS[fac][r["secondary"]][0] if r["secondary"] else None,
                inventory={slot: resolve_item(fac, role, kind) for slot, kind in r["inventory"].items()},
                damage_reduction=role_dr(fac, role))
    for k, v in ITEM_STATS.items():
        data["items"][k] = v
    # which wardrobe piece each mesh belongs to ("" = always-visible body), so Godot
    # can show a role by hiding every mesh whose piece the role doesn't wear
    data["wardrobe_meshes"] = {}
    for fac in (1, 2):
        mm = {f"F{fac}_{m.name}": "" for m in body(fac)}
        for pname, meshes in full_wardrobe(fac).items():
            for m in meshes:
                mm[f"F{fac}_{m.name}"] = pname
        data["wardrobe_meshes"][fac] = mm
    return data


# =========================================================================
# Posing (used for previews; the exported rest pose stays a T-pose)
# =========================================================================

ARM_BONES = ("Shoulder", "UpperArm", "LowerArm", "Hand")


def pose_arms_down(meshes, fac, angle_deg=70):
    """Return copies of meshes with both arms lowered (A-pose)."""
    sx, _, sz = BODY_SCALE[fac]
    pivot = (0.22 * sx, 1.52 * sz)
    out = []
    for m in meshes:
        c = Mesh(m.name, m.material, m.slot)
        for bone, s in m.items:
            if bone and any(bone.endswith(a) for a in ARM_BONES) and not bone.endswith("Shoulder"):
                side = 1 if bone.startswith("Left") else -1
                th = math.radians(angle_deg) * side
                px, pz = pivot[0] * side, pivot[1]

                def rot(p, th=th, px=px, pz=pz):
                    x, z = p[0] - px, p[2] - pz
                    return (px + x * math.cos(th) + z * math.sin(th), p[1], pz - x * math.sin(th) + z * math.cos(th))
                c.add(bone, transform(s, rot))
            else:
                c.add(bone, s)
        out.append(c)
    return out


# =========================================================================
# Output: plain-Python files (OBJ + JSON)
# =========================================================================

def _write_mtl(path, fac):
    with open(path, "w") as m:
        for name, (rgb, _, _, em, alpha) in PALETTES[fac].items():
            m.write(f"newmtl {name}\nKd {rgb[0]} {rgb[1]} {rgb[2]}\nd {alpha}\n")
            if em:
                m.write(f"Ke {rgb[0]} {rgb[1]} {rgb[2]}\n")
            m.write("\n")


def write_obj(path, meshes, mtl):
    with open(path, "w") as f:
        f.write(f"mtllib {mtl}\n")
        base = 1
        for m in meshes:
            f.write(f"o {m.name}\nusemtl {m.material}\n")
            for _, (vs, fs) in m.items:
                for x, y, z in vs:
                    f.write(f"v {x:.4f} {z:.4f} {-y:.4f}\n")      # Blender Z-up -> OBJ Y-up
                for face in fs:
                    f.write("f " + " ".join(str(i + base) for i in face) + "\n")
                base += len(vs)


def character_meshes(fac, role):
    W = full_wardrobe(fac)
    out = body(fac)
    for pname in role_pieces(role):
        out += W[pname]
    return out


def write_all_obj(folder="."):
    import os
    for fac in FACTIONS_TO_BUILD:
        mtl = f"materials_F{fac}.mtl"
        _write_mtl(os.path.join(folder, mtl), fac)
        for role in ROLES:
            write_obj(os.path.join(folder, f"char_F{fac}_{role}.obj"), character_meshes(fac, role), mtl)
        for cls_, (wname, builder) in WEAPONS[fac].items():
            meshes, mag, _ = builder()
            write_obj(os.path.join(folder, f"weapon_{wname}.obj"), meshes + [mag], mtl)
        for iname, meshes in items(fac).items():
            write_obj(os.path.join(folder, f"item_{iname}.obj"), meshes, mtl)
    with open(os.path.join(folder, "weapons_and_armor.json"), "w") as f:
        json.dump(combat_data(), f, indent=2)


# =========================================================================
# Blender
# =========================================================================

def _material(bpy, fac, name):
    rgb, metal, rough, emit, alpha = PALETTES[fac][name]
    mname = f"Char_F{fac}_{name}"
    mat = bpy.data.materials.get(mname) or bpy.data.materials.new(mname)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Metallic"].default_value = metal
        bsdf.inputs["Roughness"].default_value = rough
        if emit:
            key = "Emission Color" if "Emission Color" in bsdf.inputs else "Emission"
            bsdf.inputs[key].default_value = (*rgb, 1.0)
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emit
    mat.diffuse_color = (*rgb, alpha)
    return mat


def _mesh_object(bpy, fac, m, name, arm=None):
    verts, faces, groups = [], [], {}
    for bone, (vs, fs) in m.items:
        off = len(verts)
        verts += vs
        faces += [[i + off for i in f] for f in fs]
        if bone:
            groups.setdefault(bone, []).extend(range(off, off + len(vs)))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    me.materials.append(_material(bpy, fac, m.material))
    obj = bpy.data.objects.new(name, me)
    if arm is not None:
        for bone, idx in groups.items():
            obj.vertex_groups.new(name=bone).add(idx, 1.0, "REPLACE")
        mod = obj.modifiers.new("Armature", "ARMATURE")
        mod.object = arm
        obj.parent = arm
    return obj


def _fresh_collection(bpy, name):
    old = bpy.data.collections.get(name)
    if old:
        for obj in list(old.all_objects):
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if data is not None and data.users == 0:
                if isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)
                elif isinstance(data, bpy.types.Armature):
                    bpy.data.armatures.remove(data)
        bpy.data.collections.remove(old)
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def _export(bpy, objs, path):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.hide_set(False)
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_extras=True)
    print("Exported", path)


def build_in_blender():
    import bpy
    from mathutils import Matrix, Vector

    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for fac in FACTIONS_TO_BUILD:
        x0 = (fac - 1) * 3.0
        coll = _fresh_collection(bpy, f"Faction{fac}_Character")
        # --- armature
        arm_data = bpy.data.armatures.new(f"F{fac}_RigData")
        arm = bpy.data.objects.new(f"F{fac}_Rig", arm_data)
        coll.objects.link(arm)
        arm.location = (x0, 0, 0)
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.select_all(action="DESELECT")
        arm.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        ebs = {}
        for name, parent, head, tail in skeleton(fac):
            eb = arm_data.edit_bones.new(name)
            eb.head, eb.tail = head, tail
            if parent:
                eb.parent = ebs[parent]
            ebs[name] = eb
        bpy.ops.object.mode_set(mode="OBJECT")
        # --- body + whole wardrobe, each piece its own skinned mesh
        piece_objs = {}
        for m in body(fac):
            o = _mesh_object(bpy, fac, m, f"F{fac}_{m.name}", arm)
            coll.objects.link(o)
            piece_objs.setdefault("__body__", []).append(o)
        for pname, meshes in full_wardrobe(fac).items():
            for m in meshes:
                o = _mesh_object(bpy, fac, m, f"F{fac}_{m.name}", arm)
                o["slot"] = m.slot or ""
                o["piece"] = pname
                coll.objects.link(o)
                piece_objs.setdefault(pname, []).append(o)
        # --- inventory sockets, parented to bones
        bpy.context.view_layer.update()
        sock_objs = []
        for sname, bone, pos in sockets(fac):
            e = bpy.data.objects.new(f"F{fac}_{sname}", None)
            e.empty_display_type = "SPHERE"
            e.empty_display_size = 0.02
            coll.objects.link(e)
            e.parent = arm
            e.parent_type = "BONE"
            e.parent_bone = bone
            bpy.context.view_layer.update()
            e.matrix_world = arm.matrix_world @ Matrix.Translation(Vector(pos))
            sock_objs.append(e)
        # --- roles: store the piece lists on the rig, and show ROLE_PREVIEW
        for role in ROLES:
            arm[f"role_{role}"] = ",".join(role_pieces(role))

        def show_role(role):
            keep = set(role_pieces(role)) | {"__body__"}
            for pname, objs in piece_objs.items():
                for o in objs:
                    o.hide_set(pname not in keep)
                    o.hide_render = pname not in keep
        # --- weapons and items, laid out beside the character
        wcoll = _fresh_collection(bpy, f"Faction{fac}_Weapons")
        weapon_roots = {}
        for i, (cls_, (wname, builder)) in enumerate(WEAPONS[fac].items()):
            meshes, mag, markers = builder()
            root = bpy.data.objects.new(f"Weapon_{wname}", None)
            root.empty_display_type = "PLAIN_AXES"
            root.empty_display_size = 0.05
            root.location = (x0 + 1.2, 0, 0.4 + i * 0.25)
            root["weapon_class"] = cls_
            wcoll.objects.link(root)
            kids = [root]
            for m in meshes + [mag]:
                o = _mesh_object(bpy, fac, m, m.name)
                o.parent = root
                wcoll.objects.link(o)
                kids.append(o)
            for mname, pos in markers.items():
                e = bpy.data.objects.new(f"{wname}_{mname}", None)
                e.empty_display_type = "ARROWS"
                e.empty_display_size = 0.03
                e.parent = root
                e.location = pos
                wcoll.objects.link(e)
                kids.append(e)
            weapon_roots[wname] = kids
        icoll = _fresh_collection(bpy, f"Faction{fac}_Items")
        item_roots = {}
        for i, (iname, meshes) in enumerate(items(fac).items()):
            root = bpy.data.objects.new(f"Item_{iname}", None)
            root.empty_display_size = 0.03
            root.location = (x0 + 1.9, 0, 0.3 + i * 0.12)
            icoll.objects.link(root)
            kids = [root]
            for m in meshes:
                o = _mesh_object(bpy, fac, m, m.name)
                o.parent = root
                icoll.objects.link(o)
                kids.append(o)
            item_roots[iname] = kids
        # --- export
        if EXPORT_GLB:
            if not bpy.data.filepath:
                print("Save your .blend file first so the .glb files have somewhere to go.")
            else:
                every = [o for objs in piece_objs.values() for o in objs]
                _export(bpy, [arm] + every + sock_objs, bpy.path.abspath(f"//character_F{fac}.glb"))
                if EXPORT_ROLES:
                    for role in ROLES:
                        show_role(role)
                        keep = set(role_pieces(role)) | {"__body__"}
                        objs = [o for p, objs in piece_objs.items() if p in keep for o in objs]
                        _export(bpy, [arm] + objs + sock_objs, bpy.path.abspath(f"//character_F{fac}_{role}.glb"))
                for wname, kids in weapon_roots.items():
                    _export(bpy, kids, bpy.path.abspath(f"//weapon_{wname}.glb"))
                for iname, kids in item_roots.items():
                    _export(bpy, kids, bpy.path.abspath(f"//item_{iname}.glb"))
        show_role(ROLE_PREVIEW)
        print(f"Faction {fac}: {len(ROLES)} roles, {sum(len(v) for v in piece_objs.values())} meshes, "
              f"{len(weapon_roots)} weapons, {len(item_roots)} items. Showing role '{ROLE_PREVIEW}'.")
    bpy.ops.object.select_all(action="DESELECT")


try:
    import bpy  # noqa: F401
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False

if __name__ == "__main__":
    if IN_BLENDER:
        build_in_blender()
    else:
        write_all_obj()
        print("Not running inside Blender - wrote .obj files and weapons_and_armor.json")
