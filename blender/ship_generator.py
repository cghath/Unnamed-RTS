"""
Boardable Warship Generator for Blender (4.x, also works in 3.6)
================================================================

Builds Halo-inspired, hard-surface craft in five size classes:

  XS      Crew-carried craft, flown or ridden into battle:
            XS_FIGHTER    ~15 m single-seat fighter
            XS_BOMBER     ~15 m two-seat bomber with bomb-bay doors
            XS_DROPSHIP   ~14 m boarding dropship for a 12-soldier squad,
                          walkable troop bay and rear ramp; fits every hangar
            XS_POD        ~8 m boarding pod for one 8-soldier team, sized to
                          punch through a breach panel; nose hatch pops off
            XS_DROPPOD    ~3.5 m ODST-style drop pod for one trooper, fired
                          only by SMALL_DROP_FRIGATE; the door blows off
            XS_DARTER     ~10 m Darter-inspired cargo / crew transfer ferry:
                          4 cargo pallets or 6 armed soldiers, rear ramp
            XS_MINER      ~16 m mining ship: mining laser turret, ore hold,
                          4 docked mining drones (Drone_n objects to launch)
            XS_MINING_DRONE ~2.4 m drone that mines and returns to its miner
  SMALL   One-deck fleet ships. No hangar and no pod breach zones: boarded
          only through their two airlocks (a boarding dropship docks to the
          collar, or EVA troops cut in) or a Darter landing in the cargo bay.
            SMALL_FRIGATE      ~87 m mass-attack frigate with missile banks
            SMALL_SUPPORT      ~85 m fleet supply ship (runs the Darter ferry)
            SMALL_DROP_FRIGATE ~117 m Paris-class-inspired drop frigate with an
                               interior bay of 12 drop pods
  MEDIUM  Boardable, 1 deck,  ~109 m
  LARGE   Boardable, 2 decks, ~153 m
  XL      Boardable, 3 decks, ~209 m
  BOARDING POD LAUNCHERS
    SMALL: 3 tubes a side, MEDIUM: 5 a side, LARGE: 7 a side. Tubes run
    across the ship under the deck, alternating port/starboard; only the
    side facing the target fires, so turn the ship to use the other side.
    XL: a 12-silo dorsal battery that can fire all at once at a big target.
    Markers: PodTube_<Side>_n (pod position, nose outward), _Muzzle, the
    PodTube_<Side>_n_Hatch-col door, PodSilo_n, DropPod_n (the racked pod
    object itself), and *_Muster
    points where troops gather inside before loading.
  CARGO BAYS (every SMALL, MEDIUM, LARGE and XL ship)
    A dedicated, boardable bay on deck 0 with a starboard bay door, an energy
    shield and Darter pads: SMALL 1, MEDIUM 2, LARGE 3, XL 4. The receiving
    ship's crew unloads Darters into storage (CargoStorage_n markers, worked
    from CargoBay_DarterPad_n_CrewWork_A/B); on the supply ship
    (SMALL_SUPPORT) its crew loads the docked Darter from storage. A Darter can
    also land 6 soldiers, so an open bay is a way aboard.
  DROP BAY (SMALL_DROP_FRIGATE): a two-section bay inside the ship with 12
    drop pods racked along the walls, doors facing the walkway
    (DropPod_n_Board); each drops through its own floor and hull hatch.
  CREW & LOADOUTS
    Crew is standardized by size (STANDARD_CREW). Every ship's fighters,
    bombers, dropships, pods, crew and troops can be customized in LOADOUTS;
    resolve_loadout() checks them against hangar slots and launch tubes.

Every boardable ship (MEDIUM, LARGE, XL) has:
  * A two-storey HANGAR at the rear, open on both sides, with an energy
    shield across each opening (switch it off in-game to allow landings).
  * BREACH ZONES: outer rooms built for boarding-pod assaults. Each has a
    hull panel the pod punches through (a separate object you can remove
    or hide when the pod hits), hazard markings outside for pod pilots,
    cover inside for defenders, and a wide door into the corridor.
  * A central corridor on every deck, side rooms, ramps between decks, a
    bridge at the front of the top deck, and a reactor room behind the
    hangar.

HOW TO USE
  1. Blender -> "Scripting" tab -> New -> paste this file -> Run Script.
  2. Pick classes and faction in SETTINGS and run again. Each run replaces
     the ships it made before.
  3. Export for Godot: File > Export > glTF 2.0 (.glb), or set EXPORT_GLB.

UNITS & AXES
  1 Blender unit = 1 meter. Each ship's nose points along Blender +Y, which
  becomes Godot's forward (-Z) after glTF export. Deck 0's floor is at 0.
  Deck heights are 4 m, and ramps are about 30 degrees, which Godot's
  CharacterBody3D can walk up with default settings.

GODOT IMPORT NOTES
  * Names ending in "-col" get collision automatically on import.
  * BreachPanel_N-col: hide/free this node when a pod breaches there.
  * HangarShield_Port / _Starboard have NO collision on purpose: add an
    Area3D or StaticBody3D in Godot and toggle it when shields drop.
  * Turret_N objects pivot at their base, so they can rotate in code.
  * Empties import as Node3D markers: PlayerSpawn_Deck0, Bridge_PilotSeat,
    Reactor, Hangar_LandingPad_N, BreachZone_N_Interior,
    BreachZone_N_PodTarget, BreachZone_N_PodApproach, Ramp_DeckX_to_Y,
    plus seats, exits and gun muzzles on the XS and SMALL craft.
  * Interiors: sealable compartments (2 sections each) joined by sliding
    BlastDoor_Cx_Cy_Dk-col doors (modeled open; slide -1.65 m on X to close),
    room-to-room passages along the hull, elevators (car starts at deck 0;
    ElevatorDoor_n_Dk-col slide 1.85 m on Y), escape-pod bays on every deck
    (EscapePod_n objects outside the hull), and furnished quarters, mess,
    medbay, armory, systems, comms and storage rooms.
  * Zone_Cx_Dk empties are boxes (their scale = half-size) covering each
    compartment on each deck: use them as Area3Ds for infection spread,
    alarms and evac logic.
  * Explosive breaching: BreachWall_n-col (weak wall sections, marked with
    hazard stripes) and BreachDoor_n-col (locked doors on armories, comms and
    systems rooms) are separate objects to free when a charge goes off. Every
    compartment-sealing wall has one, so a blocked blast door can be bypassed.
    _ChargeA/_ChargeB markers show where charges go; blast doors have them
    too (for heavy charges).
  * Armories (one per deck on 2-3 deck ships) hold full kit; every
    compartment also has a corridor ReadyLocker_Cx_Dk with light gear, so a
    crew boarded by surprise fights with what's close until it can gear up.
  * ship_stats.json (plain Python run) or custom properties on each ship's
    root (glTF extras) list crew berths, escape-pod seats, compartments and
    more, for manpower and production systems.
  * SMALL ship airlocks: Airlock_n_OuterDoor-col is modeled closed (slide
    +2.1 m on Y to open) and Airlock_n_InnerDoor-col open (slide -1.7 m on Y
    to close). Airlock_n_DropshipDock is where a dropship's ramp meets the
    docking collar; Airlock_n_EVAEntry is the approach point for EVA troops;
    the outer door has charge points for a forced entry.
  * XS_POD_Hatch-col: hide/free it when the pod hits so the squad can exit.
  * XS_DROPSHIP_Ramp-col: modeled closed with its pivot on the hinge;
    rotate it around X (about -70 degrees) to open it.
  * Export each craft as its own .glb (EXPORT_GLB) so you can spawn pods,
    fighters and dropships as separate scenes.

You can also run this file with plain Python (no Blender). It then writes
ship_<CLASS>.obj/.mtl files instead, which Godot can import too.
"""

import math
import random

# ---------------------------------------------------------------- SETTINGS
SHIP_CLASSES = [         # which ships to build (side by side); delete any you don't need
    "XS_FIGHTER", "XS_BOMBER", "XS_DROPSHIP", "XS_POD", "XS_DROPPOD", "XS_DARTER",
    "XS_MINER", "XS_MINING_DRONE",
    "SMALL_FRIGATE", "SMALL_SUPPORT", "SMALL_DROP_FRIGATE",
    "MEDIUM", "LARGE", "XL",
]
BUILD_STATIONS = True          # also build the station / outpost / ground-base kits
BUILD_SINGLE_MODULES = False   # also build every module on its own (24 extra models)
FACTION = 1              # 1 = grey-green hull, amber lights  |  2 = graphite hull, red lights
SEED = 7                 # change for different armor/turret/breach layouts
EXPORT_GLB = False       # True = also save ship_<CLASS>.glb next to your saved .blend
VARIANT = 0              # interior layout variant: 0 = the classic layout, 1+ = other procedural layouts

CLASSES = {
    #          decks  rooms-segments  hangar-segments  side-room depth  breach zones  turrets  nose length
    # SMALL ships: one deck, no hangar, no pod breach zones; boarded only through
    # their two airlocks, by boarding dropships docking or EVA troops.
    "SMALL_FRIGATE": dict(decks=1, front_segs=5, hangar_segs=0, room_depth=5.0, breaches=0, turrets=4,
                          prow=10.0, tall_decks=1, airlocks=2, style="frigate", pod_tubes_per_side=3,
                          cargo_segs=1),
    "SMALL_SUPPORT": dict(decks=1, front_segs=5, hangar_segs=0, room_depth=5.0, breaches=0, turrets=2,
                          prow=8.0, tall_decks=1, airlocks=2, style="support", pod_tubes_per_side=3,
                          cargo_segs=1, supply_depot=True),
    # Paris-class-inspired drop frigate: the only ship that fires ODST-style drop pods
    "SMALL_DROP_FRIGATE": dict(decks=1, front_segs=7, hangar_segs=0, room_depth=4.5, breaches=0, turrets=4,
                               prow=20.0, tall_decks=1, airlocks=2, style="paris", pod_tubes_per_side=3,
                               drop_pods=12, cargo_segs=1),
    # hangars: 5 sections (50 m) and about 20 m wide, room for two fighters and a boarding
    # shuttle on their own pads with space to walk round them and taxi out of either side
    "MEDIUM": dict(decks=1, front_segs=4,  hangar_segs=5, room_depth=8.0, breaches=2, turrets=4,  prow=12.0,
                   pod_tubes_per_side=5, hangar_slots=4, cargo_segs=2),
    "LARGE":  dict(decks=2, front_segs=6,  hangar_segs=5, room_depth=8.5, breaches=4, turrets=8,  prow=16.0,
                   pod_tubes_per_side=7, hangar_slots=4, cargo_segs=3),
    "XL":     dict(decks=3, front_segs=10, hangar_segs=5, room_depth=9.0, breaches=6, turrets=12, prow=22.0,
                   pod_tubes_per_side=6, hangar_slots=4, cargo_segs=4),   # XL darter count assumed
}

# ---------------------------------------------------------------- CREW & LOADOUTS
# Size class of every model
SIZE_CLASS = {"XS_FIGHTER": "XS", "XS_BOMBER": "XS", "XS_DROPSHIP": "XS", "XS_POD": "XS", "XS_DROPPOD": "XS",
              "XS_DARTER": "XS", "XS_MINER": "XS", "XS_MINING_DRONE": "XS",
              "SMALL_FRIGATE": "SMALL", "SMALL_SUPPORT": "SMALL", "SMALL_DROP_FRIGATE": "SMALL",
              "MEDIUM": "MEDIUM", "LARGE": "LARGE", "XL": "XL"}

# Standard operating crew by ship size (souls needed to run the ship fully).
# Security/boarding troops and craft crews are counted separately.
STANDARD_CREW = {"SMALL": 15, "MEDIUM": 30, "LARGE": 60, "XL": 100}   # robot ships are heavily automated
BERTHED_TROOPS = {"SMALL": 12, "MEDIUM": 16, "LARGE": 24, "XL": 48}   # boarders living aboard (12 a berthing room)
MIN_CREW_FRACTION = 0.5       # below this a ship is under-crewed (your game decides the penalty)
XS_CREW = {"XS_FIGHTER": 1, "XS_BOMBER": 2, "XS_DROPSHIP": 2, "XS_POD": 0, "XS_DROPPOD": 0, "XS_DARTER": 2, "XS_MINER": 3,
           "XS_MINING_DRONE": 0}

# What each kind of carried craft needs and holds.
CRAFT_TYPES = {
    "fighters":      dict(model="XS_FIGHTER",  crew=1, hangar_slots=1, troops=0),
    "bombers":       dict(model="XS_BOMBER",   crew=2, hangar_slots=2, troops=0),
    "dropships":     dict(model="XS_DROPSHIP", crew=2, hangar_slots=2, troops=12),   # a 12-soldier squad
    "boarding_pods": dict(model="XS_POD",      crew=0, launcher="pod_tubes", troops=8),   # one 8-soldier team
    "drop_pods":     dict(model="XS_DROPPOD",  crew=0, launcher="drop_tubes", troops=1),  # one trooper each
    # cargo / crew transfer ferry: lands in cargo bays, carries cargo pallets or 6 armed soldiers
    "darters":       dict(model="XS_DARTER",   crew=2, launcher="cargo_pads", troops=6, ferry=True),
}

# Default complement per ship. Troops default to "enough to fill every carried craft".
DEFAULT_LOADOUT = {
    # every ship carries at least one boarding craft: a shuttle in the hangar, or (SMALL
    # ships) one docked at an airlock collar, plus its boarding pods
    "SMALL_FRIGATE":      dict(boarding_pods=6, dropships=1),
    "SMALL_SUPPORT":      dict(boarding_pods=6, darters=1, dropships=1),   # the supply ship runs the ferry
    "SMALL_DROP_FRIGATE": dict(boarding_pods=6, drop_pods=12, dropships=1),
    "MEDIUM":             dict(fighters=2, dropships=1, boarding_pods=10),
    "LARGE":              dict(fighters=2, dropships=1, boarding_pods=14),
    "XL":                 dict(fighters=2, dropships=1, boarding_pods=12),
}

# YOUR CUSTOM LOADOUTS go here; anything you leave out uses the default. Example:
#   LOADOUTS = {"LARGE": dict(crew=100, fighters=0, bombers=3, dropships=0, troops=80)}
LOADOUTS = {}


def capacity(cls):
    """What a ship can physically carry, from its class settings."""
    if SIZE_CLASS[cls] == "XS":
        return {}
    cfg = CLASSES[cls]
    return dict(hangar_slots=cfg.get("hangar_slots", 0),
                pod_tubes=2 * cfg.get("pod_tubes_per_side", 0) + cfg.get("dorsal_pods", 0),
                drop_tubes=cfg.get("drop_pods", 0), cargo_pads=cfg.get("cargo_segs", 0))


def resolve_loadout(cls, custom=None):
    """Default loadout + LOADOUTS + `custom`, checked against capacity.
    Returns the loadout with totals and a list of problems (empty = valid)."""
    size = SIZE_CLASS[cls]
    if size == "XS":
        return dict(crew=XS_CREW[cls], troops=0, total_souls=XS_CREW[cls], problems=[])
    lo = dict(crew=STANDARD_CREW[size], **{c: 0 for c in CRAFT_TYPES})
    lo.update(DEFAULT_LOADOUT.get(cls, {}))
    lo["troops"] = sum(CRAFT_TYPES[c]["troops"] * lo[c] for c in CRAFT_TYPES
                       if not CRAFT_TYPES[c].get("ferry"))     # ferries usually carry cargo
    lo.update(LOADOUTS.get(cls, {}))
    lo.update(custom or {})
    cap = capacity(cls)
    problems = []
    docked = CLASSES[cls].get("airlocks")           # SMALL ships dock their dropship at an airlock collar
    slots = sum(CRAFT_TYPES[c].get("hangar_slots", 0) * lo[c] for c in CRAFT_TYPES if not (docked and c == "dropships"))
    if slots > cap["hangar_slots"]:
        problems.append(f"hangar needs {slots} slots, has {cap['hangar_slots']}")
    for c, spec in CRAFT_TYPES.items():
        if "launcher" in spec and lo[c] > cap[spec["launcher"]]:
            problems.append(f"{lo[c]} {c} but only {cap[spec['launcher']]} {spec['launcher']}")
    if lo["crew"] < STANDARD_CREW[size] * MIN_CREW_FRACTION:
        problems.append(f"under-crewed: {lo['crew']} of {STANDARD_CREW[size]} standard")
    seats = sum(CRAFT_TYPES[c]["troops"] * lo[c] for c in CRAFT_TYPES)
    pilots = sum(CRAFT_TYPES[c]["crew"] * lo[c] for c in CRAFT_TYPES)
    lo.update(hangar_slots_used=slots, troop_seats_in_craft=seats, craft_crew=pilots,
              total_souls=lo["crew"] + lo["troops"] + pilots, problems=problems)
    return lo


SEG_LEN = 10.0           # length of one section along the ship (m)
DECK_H = 4.0             # floor-to-floor height (m)
CORRIDOR_W = 3.5         # corridor width (m)
HANGAR_DECKS = 2         # hangar and reactor room are this many decks tall
COMPARTMENT_SEGS = 2     # sections per sealable compartment (blast doors between them)

# ---------------------------------------------------------------- CONSTANTS
WALL_T = 0.2             # interior wall thickness
HULL_T = 0.5             # outer hull thickness
SLAB_T = 0.3             # floor/ceiling thickness
DOOR_W, DOOR_H = 1.6, 2.6
BREACH_DOOR_W = 2.6
BREACH_W, BREACH_H = 3.2, 3.0    # hull panel the pod punches through
RAMP_W = 2.2
PASSAGE_W = 1.2          # room-to-room passages along the outer hull
DOOR_X, DOOR_SLIDE = -0.75, 1.65   # blast doorway center (x) and door panel width
BLAST_DOOR_H = 2.8
BREACH_WALL_W, BREACH_WALL_H = 1.6, 2.6   # explosive-breachable wall sections
AIRLOCK_W, AIRLOCK_H = 2.0, 2.6           # outer airlock door (SMALL ships)
TUBE_PITCH, TUBE_LEN = 3.6, 8.6           # (old transverse tubes, kept for reference)
POD_PITCH, DROP_PITCH = 11.0, 4.4         # troop deck: boarding-pod cradle and drop-pod rack spacing
SILO_W, SILO_PITCH = 3.6, 8.6             # XL dorsal pod silos: width and length

FACTIONS = {   # name: (RGB, metallic, roughness, emission strength, alpha)
    1: {
        "Hull":       ((0.36, 0.39, 0.35), 0.55, 0.50, 0.0, 1.0),
        "Armor":      ((0.44, 0.47, 0.42), 0.55, 0.45, 0.0, 1.0),
        "Trim":       ((0.15, 0.16, 0.16), 0.70, 0.40, 0.0, 1.0),
        "Lights":     ((1.00, 0.70, 0.30), 0.00, 0.30, 6.0, 1.0),
        "EngineGlow": ((0.35, 0.70, 1.00), 0.00, 0.30, 8.0, 1.0),
        "Turret":     ((0.30, 0.33, 0.30), 0.60, 0.45, 0.0, 1.0),
        "Accent":     ((0.80, 0.82, 0.78), 0.40, 0.45, 0.0, 1.0),   # white hull bands and numbers
    },
    2: {
        "Hull":       ((0.17, 0.18, 0.20), 0.65, 0.40, 0.0, 1.0),
        "Armor":      ((0.24, 0.25, 0.28), 0.65, 0.35, 0.0, 1.0),
        "Trim":       ((0.07, 0.07, 0.08), 0.80, 0.35, 0.0, 1.0),
        "Lights":     ((1.00, 0.15, 0.10), 0.00, 0.30, 6.0, 1.0),
        "EngineGlow": ((1.00, 0.35, 0.15), 0.00, 0.30, 8.0, 1.0),
        "Turret":     ((0.20, 0.21, 0.23), 0.70, 0.40, 0.0, 1.0),
        "Accent":     ((0.55, 0.05, 0.08), 0.60, 0.30, 0.6, 1.0),   # crimson blades, faintly lit
    },
    3: {   # pirates: rust, scrap plating, green running lights
        "Hull":       ((0.36, 0.22, 0.13), 0.45, 0.70, 0.0, 1.0),
        "Armor":      ((0.30, 0.28, 0.22), 0.50, 0.65, 0.0, 1.0),
        "Trim":       ((0.55, 0.42, 0.10), 0.40, 0.55, 0.0, 1.0),
        "Lights":     ((0.40, 1.00, 0.35), 0.00, 0.30, 6.0, 1.0),
        "EngineGlow": ((0.55, 1.00, 0.40), 0.00, 0.30, 8.0, 1.0),
        "Turret":     ((0.25, 0.20, 0.15), 0.55, 0.60, 0.0, 1.0),
        "Accent":     ((0.85, 0.65, 0.10), 0.30, 0.60, 0.0, 1.0),   # yellow warning paint, slapped on
    },
    4: {   # derelict (the infection's nest): dead grey hull, violet glow
        "Hull":       ((0.14, 0.13, 0.15), 0.40, 0.80, 0.0, 1.0),
        "Armor":      ((0.18, 0.16, 0.19), 0.40, 0.80, 0.0, 1.0),
        "Trim":       ((0.08, 0.07, 0.09), 0.50, 0.70, 0.0, 1.0),
        "Lights":     ((0.70, 0.20, 1.00), 0.00, 0.30, 6.0, 1.0),
        "EngineGlow": ((0.10, 0.08, 0.12), 0.00, 0.30, 0.0, 1.0),
        "Turret":     ((0.12, 0.11, 0.13), 0.50, 0.70, 0.0, 1.0),
        "Accent":     ((0.10, 0.09, 0.11), 0.30, 0.90, 0.0, 1.0),   # scorched
    },
}
# Hull design per faction: 1 naval (slab hull, hammerhead, stepped tower), 2 sleek (blade
# prow, low spine, fins, swept wings, twin nacelles), 3 scrap (asymmetric, welded-on junk,
# mismatched engines), 4 wreck (the naval hull, gutted and torn open)
STYLE = {1: "naval", 2: "sleek", 3: "scrap", 4: "wreck"}
SHARED_MATERIALS = {
    "Deck":        ((0.20, 0.21, 0.22), 0.30, 0.70, 0.0, 1.0),
    "Interior":    ((0.52, 0.54, 0.55), 0.30, 0.60, 0.0, 1.0),
    "Engine":      ((0.09, 0.09, 0.10), 0.80, 0.35, 0.0, 1.0),
    "Glass":       ((0.55, 0.80, 1.00), 0.00, 0.05, 0.0, 0.25),
    "Hazard":      ((0.95, 0.62, 0.08), 0.20, 0.50, 0.0, 1.0),
    "BreachPanel": ((0.28, 0.27, 0.25), 0.60, 0.55, 0.0, 1.0),
    "Shield":      ((0.30, 0.60, 1.00), 0.00, 0.10, 3.0, 0.30),
    "Reactor":     ((0.40, 0.85, 1.00), 0.00, 0.20, 5.0, 1.0),
    "Cover":       ((0.30, 0.32, 0.33), 0.50, 0.55, 0.0, 1.0),
    "Door":        ((0.34, 0.35, 0.36), 0.70, 0.40, 0.0, 1.0),
    "Furniture":   ((0.24, 0.25, 0.27), 0.40, 0.60, 0.0, 1.0),
    "Medical":     ((0.82, 0.84, 0.85), 0.20, 0.40, 0.0, 1.0),
    "BreachWall":  ((0.60, 0.58, 0.52), 0.30, 0.65, 0.0, 1.0),
    "Rock":        ((0.17, 0.15, 0.14), 0.10, 0.95, 0.0, 1.0),
    "Growth":      ((0.16, 0.04, 0.20), 0.10, 0.45, 1.6, 1.0),    # the infection's growth on a hull
    "Scrap":       ((0.42, 0.30, 0.16), 0.50, 0.75, 0.0, 1.0),    # pirates' welded-on plating
}


def materials():
    m = dict(SHARED_MATERIALS)
    m.update(FACTIONS[FACTION])
    return m


# =========================================================================
# Pure-Python geometry (no Blender needed for this part)
# =========================================================================

def _orient_faces(verts, faces):
    """Flip faces so normals point away from the piece's center (all pieces are convex)."""
    n = len(verts)
    c = [sum(v[i] for v in verts) / n for i in range(3)]
    out = []
    for f in faces:
        nx = ny = nz = 0.0
        for i in range(len(f)):  # Newell's method
            a, b = verts[f[i]], verts[f[(i + 1) % len(f)]]
            nx += (a[1] - b[1]) * (a[2] + b[2])
            ny += (a[2] - b[2]) * (a[0] + b[0])
            nz += (a[0] - b[0]) * (a[1] + b[1])
        fc = [sum(verts[i][k] for i in f) / len(f) for k in range(3)]
        d = (fc[0] - c[0]) * nx + (fc[1] - c[1]) * ny + (fc[2] - c[2]) * nz
        out.append(list(f) if d >= 0 else list(reversed(f)))
    return out


# Corner index i: bit0 = x side, bit1 = y side, bit2 = z side.
_HEX_FACES = [(0, 2, 6, 4), (1, 3, 7, 5), (0, 1, 5, 4),
              (2, 3, 7, 6), (0, 1, 3, 2), (4, 5, 7, 6)]


def hexa(corners):
    """Six-sided convex solid from 8 corners (box, wedge, ramp, tapered block)."""
    return list(corners), _orient_faces(corners, _HEX_FACES)


def box(x0, x1, y0, y1, z0, z1):
    xs, ys, zs = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return hexa([(xs[i & 1], ys[(i >> 1) & 1], zs[(i >> 2) & 1]) for i in range(8)])


def taper(y0, y1, back, front):
    """Block from y0 to y1, centered on x=0. back/front = (half_width, z_bottom, z_top)."""
    corners = []
    for i in range(8):
        hw, zb, zt = front if (i >> 1) & 1 else back
        corners.append(((-hw, hw)[i & 1], (y0, y1)[(i >> 1) & 1], (zb, zt)[(i >> 2) & 1]))
    return hexa(corners)


def prism(y0, y1, hw_bottom, hw_top, z0, z1):
    """Block from y0 to y1 whose top is narrower (or wider) than its bottom."""
    corners = []
    for i in range(8):
        hw = hw_top if (i >> 2) & 1 else hw_bottom
        corners.append(((-hw, hw)[i & 1], (y0, y1)[(i >> 1) & 1], (z0, z1)[(i >> 2) & 1]))
    return hexa(corners)


def cylinder(axis, c1, c2, a0, a1, r, seg=16, phase=0.0):
    """Capped cylinder along 'y' (c1=x, c2=z) or 'z' (c1=x, c2=y)."""
    verts = []
    for a in (a0, a1):
        for k in range(seg):
            t = phase + 2 * math.pi * k / seg
            u, v = c1 + r * math.cos(t), c2 + r * math.sin(t)
            verts.append((u, a, v) if axis == "y" else (u, v, a))
    faces = [(k, (k + 1) % seg, seg + (k + 1) % seg, seg + k) for k in range(seg)]
    faces += [tuple(range(seg)), tuple(range(seg, 2 * seg))]
    return verts, _orient_faces(verts, faces)


def wing(side, x_root, x_tip, root_y, tip_y, z_root, z_tip, t_root, t_tip):
    """Tapered, swept slab from the body (root) out to the tip.
    root_y / tip_y = (back edge, front edge); side = -1 left, 1 right."""
    corners = []
    for i in range(8):
        tip = i & 1
        zc, t = (z_tip, t_tip) if tip else (z_root, t_root)
        corners.append((side * (x_tip if tip else x_root),
                        (tip_y if tip else root_y)[(i >> 1) & 1],
                        zc + (t / 2 if (i >> 2) & 1 else -t / 2)))
    return hexa(corners)


def oct_shell(y0, y1, cz, r, t):
    """Hollow octagonal tube along Y (flat floor, walls and roof), as 8 panels."""
    solids = []
    for k in range(8):
        a0 = math.pi / 8 + k * math.pi / 4
        a1 = a0 + math.pi / 4
        corners = []
        for i in range(8):
            a, rr = (a0, a1)[i & 1], (r - t, r)[(i >> 2) & 1]
            corners.append((rr * math.cos(a), (y0, y1)[(i >> 1) & 1], cz + rr * math.sin(a)))
        solids.append(hexa(corners))
    return solids


def wall(axis, f0, f1, a0, a1, z0, z1, openings=()):
    """Wall running along `axis` ('x' or 'y') from a0 to a1, occupying f0..f1 on
    the other axis. openings = [(center, width, bottom, top)] become holes,
    built from solid slabs so collision stays simple."""
    def slab(a, b, za, zb):
        if b - a < 1e-6 or zb - za < 1e-6:
            return None
        return box(a, b, f0, f1, za, zb) if axis == "x" else box(f0, f1, a, b, za, zb)

    pieces, cur = [], a0
    for c, w, ob, ot in sorted(openings):
        s, e = c - w / 2, c + w / 2
        pieces += [slab(cur, s, z0, z1), slab(s, e, z0, ob), slab(s, e, ot, z1)]
        cur = e
    pieces.append(slab(cur, a1, z0, z1))
    return [p for p in pieces if p]


def rect_minus(r, h):
    """Rectangle r=(x0,x1,y0,y1) minus hole h, as up to 4 rectangles."""
    x0, x1, y0, y1 = r
    hx0, hx1, hy0, hy1 = max(h[0], x0), min(h[1], x1), max(h[2], y0), min(h[3], y1)
    if hx0 >= hx1 or hy0 >= hy1:
        return [r]
    out = [(x0, hx0, y0, y1), (hx1, x1, y0, y1), (hx0, hx1, y0, hy0), (hx0, hx1, hy1, y1)]
    return [q for q in out if q[1] - q[0] > 1e-6 and q[3] - q[2] > 1e-6]


class Part:
    """A group of solids that becomes one Blender object."""
    def __init__(self, name, material, origin=(0, 0, 0), rot_z=0.0):
        self.name, self.material, self.origin, self.rot_z = name, material, origin, rot_z
        self.verts, self.faces = [], []
        self.solids = []          # kept for the floor-plan preview

    def add(self, solid):
        v, f = solid
        off = len(self.verts)
        self.verts += v
        self.faces += [[i + off for i in face] for face in f]
        self.solids.append(solid)

    def add_many(self, solids):
        for s in solids:
            self.add(s)


def turret_part(name, origin, rot_z, s):
    """Twin-barrel turret, pivot at the base, barrels along +Y."""
    t = Part(name, "Turret", origin=origin, rot_z=rot_z)
    t.add(cylinder("z", 0, 0, 0, 0.35 * s, 0.95 * s))
    t.add(prism(-0.8 * s, 0.9 * s, 0.8 * s, 0.55 * s, 0.35 * s, 1.15 * s))
    for bx in (-0.32, 0.32):
        t.add(box((bx - 0.09) * s, (bx + 0.09) * s, 0.6 * s, 3.2 * s, 0.65 * s, 0.83 * s))
    return t


# =========================================================================
# Ship layout
# =========================================================================

def generate_ship(cls):
    cfg = CLASSES[cls]
    rng = random.Random(f"{SEED}-{cls}" if VARIANT == 0 else f"{SEED}-{cls}-v{VARIANT}")
    H, HD = DECK_H, cfg.get("tall_decks", HANGAR_DECKS)
    decks = cfg["decks"]
    levels = max(decks, HD)
    z_top = levels * H
    cw = CORRIDOR_W / 2
    hw = cw + WALL_T + cfg["room_depth"]          # interior half-width
    ox = hw + HULL_T                              # outer hull surface
    n_hangar = cfg["hangar_segs"]
    n_cargo = cfg.get("cargo_segs", 0)
    cargo_s0 = 1 + n_hangar                       # first cargo-bay section
    aft_segs = 1 + n_hangar + n_cargo             # reactor room + hangar + cargo bay
    n = aft_segs + cfg["front_segs"]
    y_back = -n * SEG_LEN / 2
    y_front = y_back + n * SEG_LEN
    y_aft_end = y_back + aft_segs * SEG_LEN
    yb, yf = y_back - HULL_T, y_front + HULL_T    # outer hull ends
    seg_y = lambda s: (y_back + s * SEG_LEN, y_back + (s + 1) * SEG_LEN)
    seg_c = lambda s: y_back + (s + 0.5) * SEG_LEN
    D = cfg["room_depth"]
    U0 = cw + WALL_T                              # where side rooms start (|x|)
    rooms_x = U0 + D / 2                          # side-room center |x|
    drop_segs = set()        # (the old interior drop bay: drop pods now rack in the troop deck)

    def rbox(side, u0, u1, y0, y1, z0, z1):
        """Box inside a side room. u = distance out from the corridor wall."""
        a, b = sorted((side * (U0 + u0), side * (U0 + u1)))
        return box(a, b, y0, y1, z0, z1)

    # ---------- compartments: sealable groups of sections (for infection & evac)
    def comp(s):
        if s == 0:
            return 0                              # reactor
        if s < cargo_s0:
            return 1                              # hangar
        base = 1 + (1 if n_hangar else 0)
        if s < aft_segs:
            return base                           # cargo bay
        return base + (1 if n_cargo else 0) + (s - aft_segs) // COMPARTMENT_SEGS

    # ---------- what is where: section type per (level, segment)
    def stype(k, s):
        if s < aft_segs:
            if k < HD:
                if s == 0:
                    return "reactor"
                return "hangar" if s < cargo_s0 else "cargo"
            return "rooms" if k < decks else "void"
        if k >= decks:
            return "void"
        if s == n - 1 and k == decks - 1:
            return "bridge"
        if k == 0 and s in drop_segs:
            return "dropbay"
        return "rooms"

    def walkable(k, s):
        t = stype(k, s)
        return t in ("rooms", "bridge", "dropbay") or (t in ("reactor", "hangar", "cargo") and k == 0)

    # ---------- side-room roles: ramps and breach zones (placed by the layout seed)
    room_role = {}   # (k, s, side) -> "ramp" | "ramp_top" | "breach"
    ramps = []
    mid = [s for s in range(aft_segs + 1, n - 1) if s not in drop_segs]
    ramp_segs = rng.sample(mid, min(len(mid), max(0, decks - 1))) if decks > 1 else []
    for k in range(decks - 1):
        side = rng.choice((-1, 1))
        s = ramp_segs[k]
        room_role[(k, s, side)] = "ramp"
        room_role[(k + 1, s, side)] = "ramp_top"
        ramps.append((k, s, side))

    # elevator shaft through every deck (2+ deck ships)
    elevators = []
    if decks >= 2:
        opts = [(s_, sd) for s_ in mid for sd in (-1, 1) if all((k, s_, sd) not in room_role for k in range(decks))]
        es, eside = opts[rng.randrange(len(opts))] if opts else (min(aft_segs + 2, n - 2), -1)
        for k in range(decks):
            room_role[(k, es, eside)] = "elevator"
        elevators.append((es, eside))

    airlocks = []
    if cfg.get("airlocks"):
        mids = [s for s in range(aft_segs, n - 1) if s not in drop_segs]
        s_air = mids[len(mids) // 2]
        for side in (-1, 1):
            room_role[(0, s_air, side)] = "airlock"
            airlocks.append((0, s_air, side))

    # ---------- TROOP DECK: a full-length level under deck 0 (floor at z = -H). Aft: the pod
    # bay, a central walkway with boarding-pod cradles either side (each drops out of a belly
    # hatch, then flies to its target) and, on the drop frigate, racks of ODST drop pods over
    # their own belly hatches. Forward: troop rooms (berthing, armory, medbay, ready room)
    # either side of the walkway. Ramps in "bay access" rooms on deck 0 lead down to it.
    TZ = -H
    tp_side = cfg.get("pod_tubes_per_side", 0)
    td_side = cfg.get("drop_pods", 0) // 2
    bay_y0 = y_back + 2.0
    pod_ys = [bay_y0 + j * POD_PITCH for j in range(tp_side)]                 # cradle start (aft end)
    drop_y0 = bay_y0 + tp_side * POD_PITCH
    drop_ys = [drop_y0 + j * DROP_PITCH + DROP_PITCH / 2 for j in range(td_side)]
    bay_y1 = drop_y0 + td_side * DROP_PITCH + 1.0
    sr0 = min(n - 1, int(math.ceil((bay_y1 - y_back) / SEG_LEN)))          # first troop-room section
    troop_slots = [(s_, sd) for s_ in range(sr0, n) for sd in (-1, 1)]
    troop_role = {}
    acc_n = 1 if n - sr0 < 4 else 2
    acc_cands = [(s_, sd) for (s_, sd) in troop_slots if stype(0, s_) == "rooms" and (0, s_, sd) not in room_role]
    rng.shuffle(acc_cands)
    bay_access = []
    for (s_, sd) in acc_cands:
        if len(bay_access) >= acc_n:
            break
        if any(a[0] == s_ for a in bay_access):
            continue
        room_role[(0, s_, sd)] = "bay_access"
        troop_role[(s_, sd)] = "access"
        bay_access.append((s_, sd))
    rest = [t for t in troop_slots if t not in troop_role]
    rng.shuffle(rest)
    for role_ in ["ready", "medbay", "armory", "berthing", "berthing", "storage", "berthing", "armory", "storage"]:
        if rest:
            troop_role[rest.pop()] = role_
    for t in rest:
        troop_role[t] = "berthing"

    cands = [(k, s, side) for k in range(decks) for s in range(aft_segs, n)
             for side in (-1, 1) if stype(k, s) == "rooms" and (k, s, side) not in room_role]
    rng.shuffle(cands)
    breaches = []
    for i in range(cfg["breaches"]):
        want_k = i % decks
        for pool in ([c for c in cands if c[0] == want_k], cands):
            pick = next((c for c in pool if c not in breaches and all(
                not (b[0] == c[0] and b[2] == c[2] and abs(b[1] - c[1]) < 2) for b in breaches)), None)
            if pick:
                breaches.append(pick)
                break
    breaches.sort()
    for b in breaches:
        room_role[b] = "breach"

    # ---------- every other side room gets a job. The layout seed decides where:
    #   escape     escape-pod bay (one per deck)
    #   armory     weapons, armor and ammunition: the only place to gear up or resupply
    #              (one per deck, plus one by the pod bays on big ships)
    #   berthing   troop berthing: 12 bunks a section; the boarders the ship can carry
    #              (big ships often get a two-section berthing hall)
    #   quarters   crew cabins: each section split into two 2-berth cabins
    #   mess       galley and mess hall (sometimes a two-section hall)
    #   medbay, comms, storage (the ship's supply stores), workshop, systems
    free = [(k, s, side) for k in range(decks) for s in range(n) for side in (-1, 1)
            if stype(k, s) == "rooms" and (k, s, side) not in room_role]
    merged = set()      # (k, s, side): this room has no partition toward s + 1 (one hall)
    split = set()       # (k, s, side): two cabins with their own doors

    def take(role, pool, hall=False):
        if not pool:
            return None
        slot = pool[0]
        free.remove(slot)
        room_role[slot] = role
        k_, s_, sd = slot
        nxt = (k_, s_ + 1, sd)
        if hall and nxt in free and comp(s_) == comp(s_ + 1) and rng.random() < 0.65:
            free.remove(nxt)
            room_role[nxt] = role
            merged.add(slot)
        return slot

    def near(k, target):
        pool = [f for f in free if f[0] == k]
        rng.shuffle(pool)
        return sorted(pool, key=lambda f: abs(f[1] - target) + rng.random() * 2.0)

    centre = (aft_segs + n) / 2
    for k in range(decks):
        take("escape", near(k, rng.uniform(aft_segs, n)))
        take("armory", near(k, centre + rng.uniform(-2, 2)))
    if cfg.get("pod_tubes_per_side", 0) >= 5 or cfg.get("dorsal_pods"):
        take("armory", near(0, aft_segs + 1))                  # by the pod bays: boarders kit up here
    take("medbay", near(0, aft_segs + rng.uniform(0, 2)))
    if decks >= 2:
        take("medbay", near(decks - 1, n - 2))
        take("comms", near(decks - 1, n - 2))                  # near the bridge
    else:
        take("comms", near(0, n - 2))
    # the ship's own boarding complement lives aboard; pods are refilled from the station
    berths_needed = max(1, math.ceil(BERTHED_TROOPS[SIZE_CLASS[cls]] / 12))
    b_rooms = 0
    while b_rooms < berths_needed and free:
        k = rng.randrange(decks)
        slot = take("berthing", near(k, aft_segs + 1 + rng.uniform(0, 3)), hall=True)
        if slot is None:
            break
        b_rooms += 2 if slot in merged else 1
    take("mess", near(0, centre + rng.uniform(-3, 3)), hall=decks >= 2)
    take("workshop", near(rng.randrange(decks), aft_segs + 1))
    take("storage", near(0, aft_segs + rng.uniform(0, 2)))
    rng.shuffle(free)
    fillers = ["quarters", "quarters", "storage", "systems", "quarters", "workshop"]
    for i, slot in enumerate(list(free)):
        if slot in free:
            take(fillers[i % len(fillers)], [slot])
    for key, role in room_role.items():
        if role == "quarters":
            split.add(key)

    M = materials()
    P = lambda name, mat: Part(f"{cls}_{name}", mat)
    decks_p = P("Decks-col", "Deck")
    inner = P("Interior-col", "Interior")
    hull = P("Hull-col", "Hull")
    armor = P("Armor", "Armor")
    trim = P("Trim", "Trim")
    hazard = P("Hazard", "Hazard")
    lights = P("Lights", "Lights")
    glass = P("Glass-col", "Glass")
    cover = P("Cover-col", "Cover")
    rails = P("Railings-col", "Trim")
    engines = P("Engines", "Engine")
    glow = P("EngineGlow", "EngineGlow")
    reactor = P("Reactor-col", "Reactor")
    details = P("Details", "Trim")
    furniture = P("Furniture-col", "Furniture")
    medical = P("Medical-col", "Medical")
    hatches = P("EscapeHatches", "Engine")
    parts = [decks_p, inner, hull, armor, trim, hazard, lights, glass, cover,
             rails, engines, glow, reactor, details, furniture, medical, hatches]
    markers = []
    doors = []          # (name, compartment_a, compartment_b, deck)

    def sliding_door(name, y_wall, z0, opened=False, secure=False):
        """Door panel for the off-center opening in a bulkhead, modeled CLOSED
        (the game slides it +1.65 m along X to open it).
        secure = a heavy security door (bridge, hangar, cargo bay, reactor):
        thicker, hazard-striped frame; only a breaching charge gets through."""
        th = 0.09 if secure else 0.04
        d = Part(f"{cls}_{name}-col", "Armor" if secure else "Door",
                 origin=(DOOR_X + (DOOR_SLIDE if opened else 0.0), y_wall + WALL_T / 2 + 0.05 + th, z0))
        d.add(box(-DOOR_SLIDE / 2, DOOR_SLIDE / 2, -th, th, 0, BLAST_DOOR_H))
        parts.append(d)
        if secure:            # yellow/black frame on both faces of the doorway
            xa_, xb_ = DOOR_X - DOOR_SLIDE / 2 - 0.12, DOOR_X + DOOR_SLIDE / 2 + 0.12
            for f in (y_wall - WALL_T / 2 - 0.03, y_wall + WALL_T / 2):
                hazard.add(box(xa_, xb_, f, f + 0.03, z0 + BLAST_DOOR_H, z0 + BLAST_DOOR_H + 0.14))
                hazard.add(box(xa_, xa_ + 0.12, f, f + 0.03, z0, z0 + BLAST_DOOR_H))
                hazard.add(box(xb_ - 0.12, xb_, f, f + 0.03, z0, z0 + BLAST_DOOR_H))
            lights.add(box(DOOR_X - 0.15, DOOR_X + 0.15, y_wall - WALL_T / 2 - 0.05, y_wall - WALL_T / 2,
                           z0 + BLAST_DOOR_H + 0.2, z0 + BLAST_DOOR_H + 0.3))
        # where a (heavy) charge goes on each side of the doorway
        markers.extend([(f"{name}_ChargeA", (DOOR_X, y_wall - 0.4, z0 + 1.2)),
                        (f"{name}_ChargeB", (DOOR_X, y_wall + 0.5, z0 + 1.2))])

    # ---------- explosive-breachable walls and locked doors
    breachables = []    # (name, kind, deck)
    wall_rooms = {key for key, role in room_role.items()
                  if role in ("quarters", "storage", "mess", "escape", "systems") and rng.random() < 0.35}
    locked_rooms = {key for key, role in room_role.items() if role in ("armory", "comms", "systems")}

    def breach_panel(kind, axis, center, f0, f1, z0, w, h):
        """Fill a wall opening with a separate panel that explosives can remove.
        kind = "BreachWall" (weak wall section) or "BreachDoor" (locked door)."""
        i = len(breachables) + 1
        name = f"{kind}_{i}"
        bp_ = Part(f"{cls}_{name}-col", "BreachWall" if kind == "BreachWall" else "Door")
        if axis == "y":       # wall runs along Y, panel plane is X = f0..f1
            bp_.add(box(f0, f1, center - w / 2, center + w / 2, z0, z0 + h))
            for f in (f0 - 0.02, f1):                      # hazard stripes on both faces
                hazard.add(box(f, f + 0.02, center - w / 2, center + w / 2, z0 + h - 0.15, z0 + h))
                hazard.add(box(f, f + 0.02, center - w / 2, center + w / 2, z0, z0 + 0.15))
            fm = (f0 + f1) / 2
            ca, cb = (fm - 0.4, center, z0 + 1.2), (fm + 0.4, center, z0 + 1.2)
        else:                 # wall runs along X, panel plane is Y = f0..f1
            bp_.add(box(center - w / 2, center + w / 2, f0, f1, z0, z0 + h))
            for f in (f0 - 0.02, f1):
                hazard.add(box(center - w / 2, center + w / 2, f, f + 0.02, z0 + h - 0.15, z0 + h))
                hazard.add(box(center - w / 2, center + w / 2, f, f + 0.02, z0, z0 + 0.15))
            fm = (f0 + f1) / 2
            ca, cb = (center, fm - 0.4, z0 + 1.2), (center, fm + 0.4, z0 + 1.2)
        parts.append(bp_)
        markers.extend([(f"{name}_ChargeA", ca), (f"{name}_ChargeB", cb)])
        breachables.append((name, kind, int(z0 // H)))

    # elevator shaft footprint (port side, against the corridor wall)
    shafts = []
    for (es, eside) in elevators:
        y0, _ = seg_y(es)
        shafts.append((es, eside, y0 + 1.0, y0 + 4.0))

    # ---------- floors / ceilings (holes above ramps and elevator shafts)
    holes = {}
    for (k, s, side) in ramps:
        y0, y1 = seg_y(s)
        xa, xb = sorted((side * (hw - RAMP_W - 0.3), side * hw))
        holes.setdefault((k + 1, s), []).append((xa, xb, y0 + 1.6, y1 - 1.6))
    for (es, eside, ys0, ys1) in shafts:
        xa, xb = sorted((eside * U0, eside * (U0 + 3.0)))
        for L in range(1, decks):
            holes.setdefault((L, es), []).append((xa, xb, ys0, ys1))
    for (s_, sd) in bay_access:                  # the top of each troop-deck ramp comes up through deck 0
        y0_, _ = seg_y(s_)
        xa, xb = sorted((sd * (hw - RAMP_W - 0.3), sd * (hw - 0.3)))
        holes.setdefault((0, s_), []).append((xa, xb, y0_ + 3.6, y0_ + 8.6))   # ends where the ramp meets the deck
    drop_spots = []                               # (x, y, side) of each racked drop pod
    if drop_segs:
        by0 = seg_y(min(drop_segs))[0]
        per_row = cfg["drop_pods"] // 2
        for side in (-1, 1):
            for i in range(per_row):
                drop_spots.append((side * (hw - 1.3), by0 + 1.8 + i * (2 * SEG_LEN - 3.6) / (per_row - 1), side))
        for (dx, dy, _) in drop_spots:
            s_ = int((dy - y_back) // SEG_LEN)
            holes.setdefault((0, s_), []).append((dx - 1.0, dx + 1.0, dy - 1.0, dy + 1.0))
    for L in range(levels + 1):
        z0, z1 = L * H - SLAB_T, L * H
        for s in range(n):
            if 0 < L < levels and s < aft_segs and L < HD:
                continue                          # open space inside hangar/reactor
            if 0 < L < levels and stype(L, s) == "void" and stype(L - 1, s) == "void":
                continue
            y0, y1 = seg_y(s)
            rects = [(-hw, hw, y0, y1)]
            for h in holes.get((L, s), []):
                rects = [q for r in rects for q in rect_minus(r, h)]
            target = hull if L == levels else decks_p
            for x0, x1, ry0, ry1 in rects:
                target.add(box(x0, x1, ry0, ry1, z0, z1))

    # ---------- interior walls, level by level
    for k in range(levels):
        z0, z1 = k * H, (k + 1) * H
        for s in range(n):
            t = stype(k, s)
            y0, y1 = seg_y(s)
            if t == "rooms":
                for side in (-1, 1):
                    role = room_role.get((k, s, side))
                    if role == "elevator":
                        ops = [(y0 + 2.5, 1.8, z0, z0 + 2.6), (y0 + 7.2, DOOR_W, z0, z0 + DOOR_H)]
                    else:
                        w = BREACH_DOOR_W if role == "breach" else DOOR_W
                        ops = [(seg_c(s), w, z0, z0 + DOOR_H)]
                    is_split = (k, s, side) in split
                    door_ys = [seg_c(s)]
                    if is_split:                  # two cabins: a door each, a wall between them
                        door_ys = [y0 + 2.5, y0 + 7.5]
                        ops = [(dy_, DOOR_W, z0, z0 + DOOR_H) for dy_ in door_ys]
                        ra, rb = sorted((side * U0, side * hw))
                        inner.add_many(wall("x", seg_c(s) - WALL_T / 2, seg_c(s) + WALL_T / 2, ra, rb, z0, z1))
                    xa, xb = sorted((side * cw, side * (cw + WALL_T)))
                    if (k, s, side) in wall_rooms and not is_split:
                        ops.append((y0 + 8.0, BREACH_WALL_W, z0, z0 + BREACH_WALL_H))
                        breach_panel("BreachWall", "y", y0 + 8.0, xa, xb, z0, BREACH_WALL_W, BREACH_WALL_H)
                    if role == "airlock":
                        a_i = airlocks.index((k, s, side)) + 1
                        d = Part(f"{cls}_Airlock_{a_i}_InnerDoor-col", "Door",
                                 origin=(side * (cw - 0.06), seg_c(s) + 1.7, z0))   # modeled open
                        d.add(box(-0.04, 0.04, -0.85, 0.85, 0, DOOR_H))
                        parts.append(d)
                    if (k, s, side) in locked_rooms:
                        breach_panel("BreachDoor", "y", seg_c(s), xa, xb, z0, DOOR_W, DOOR_H)
                    elif role not in ("elevator", "airlock"):
                        # an ordinary sliding room door (modeled closed): opens for the
                        # crew; boarders kick it in, shoot it down or blow it
                        for di, dy_ in enumerate(door_ys):
                            suffix = "" if len(door_ys) == 1 else "ab"[di]
                            rd = Part(f"{cls}_RoomDoor_{k}_{s}_{'P' if side < 0 else 'S'}{suffix}-col", "Door",
                                      origin=((xa + xb) / 2, dy_, z0))
                            rd.add(box(-0.04, 0.04, -w / 2, w / 2, 0, DOOR_H))
                            parts.append(rd)
                    inner.add_many(wall("y", xa, xb, y0, y1, z0, z1, ops))
                lights.add(box(-0.3, 0.3, y0 + 1.5, y1 - 1.5, z1 - SLAB_T - 0.08, z1 - SLAB_T))
            # boundary with the previous section
            if s == 0:
                continue
            a, b = stype(k, s - 1), t
            if a == b == "void" or (a == b and a in ("hangar", "reactor", "cargo", "dropbay")):
                continue
            yb_ = y0
            sealed = comp(s - 1) != comp(s)
            door_op = [(DOOR_X, DOOR_SLIDE - 0.05, z0, z0 + BLAST_DOOR_H)]
            if a == b == "rooms":
                if sealed:          # blast door across the corridor
                    inner.add_many(wall("x", yb_ - WALL_T / 2, yb_ + WALL_T / 2, -cw, cw, z0, z1, door_op))
                    name = f"BlastDoor_C{comp(s - 1)}_C{comp(s)}_D{k}"
                    sliding_door(name, yb_, z0)
                    doors.append((name, comp(s - 1), comp(s), k))
                for side in (-1, 1):  # side-room partitions: a passage, or a breachable wall if sealed
                    if (k, s - 1, side) in merged and not sealed:
                        continue          # one hall across both sections: no partition
                    xa, xb = sorted((side * U0, side * hw))
                    pw = BREACH_WALL_W if sealed else PASSAGE_W
                    ops = [(side * (hw - 2.2), pw, z0, z0 + 2.4)]
                    if sealed:
                        breach_panel("BreachWall", "x", side * (hw - 2.2),
                                     yb_ - WALL_T / 2, yb_ + WALL_T / 2, z0, pw, 2.4)
                    inner.add_many(wall("x", yb_ - WALL_T / 2, yb_ + WALL_T / 2, xa, xb, z0, z1, ops))
                continue
            ops = []
            if walkable(k, s - 1) and walkable(k, s):
                ops = door_op
                area = next((t_.capitalize() for t_ in ("bridge", "cargo", "hangar", "reactor") if t_ in (a, b)), "")
                if area:            # high-security area: breach-only door
                    name = f"SecureDoor_{area}_S{s}_D{k}"
                else:
                    name = (f"BlastDoor_C{comp(s - 1)}_C{comp(s)}_D{k}" if sealed else f"Door_S{s}_D{k}")
                sliding_door(name, yb_, z0, secure=bool(area))
                doors.append((name, comp(s - 1), comp(s), k))
            inner.add_many(wall("x", yb_ - WALL_T / 2, yb_ + WALL_T / 2, -hw, hw, z0, z1, ops))

    # ---------- elevators: shaft, car (starts at deck 0) and a door on every deck
    for e_i, (es, eside, ys0, ys1) in enumerate(shafts, 1):
        top = decks * H
        inner.add(rbox(eside, 3.0, 3.2, ys0 - 0.2, ys1 + 0.2, 0, top))
        inner.add(rbox(eside, 0.0, 3.0, ys0 - 0.2, ys0, 0, top))
        inner.add(rbox(eside, 0.0, 3.0, ys1, ys1 + 0.2, 0, top))
        ex, ey = eside * (U0 + 1.5), (ys0 + ys1) / 2
        car = Part(f"{cls}_Elevator_{e_i}-col", "Door", origin=(ex, ey, 0))
        car.add(box(-1.4, 1.4, -1.4, 1.4, -0.15, 0))
        car.add(box(-1.4, 1.4, -1.4, -1.3, 0, 1.0))
        car.add(box(-1.4, 1.4, 1.3, 1.4, 0, 1.0))
        parts.append(car)
        for k in range(decks):
            d = Part(f"{cls}_ElevatorDoor_{e_i}_D{k}-col", "Door",
                     origin=(eside * (cw - 0.06), ey + (1.85 if k == 0 else 0.0), k * H))
            d.add(box(-0.04, 0.04, -0.925, 0.925, 0, 2.6))
            parts.append(d)
            markers.append((f"Elevator_{e_i}_Stop_Deck{k}", (ex, ey, k * H + 0.05)))
            fa, fb = sorted((eside * (cw - 0.12), eside * cw))
            hazard.add(box(fa, fb, ey - 1.05, ey - 0.9, k * H, k * H + 2.7))
            hazard.add(box(fa, fb, ey + 0.9, ey + 1.05, k * H, k * H + 2.7))

    # ---------- the troop deck (see the plan above)
    tb = TZ - SLAB_T                                 # underside of the troop deck floor
    pod_cx = cw + 0.35 + 1.55                        # |x| of a boarding-pod cradle's axis
    floor_holes = []                                 # (x0, x1, y0, y1): cradles and drop hatches
    belly_hatches = []                               # (name, x0, x1, y0, y1)
    tube_n = {-1: 0, 1: 0}
    for side in (-1, 1):
        sname = "Port" if side < 0 else "Starboard"
        for py in pod_ys:
            tube_n[side] += 1
            j = tube_n[side]
            px = side * pod_cx
            pa, pb = px - 1.55, px + 1.55
            floor_holes.append((min(pa, pb), max(pa, pb), py + 0.5, py + POD_PITCH - 0.5))
            belly_hatches.append((f"PodTube_{sname}_{j}_Hatch", min(pa, pb), max(pa, pb), py + 0.6, py + POD_PITCH - 0.6))
            # the racked pod itself, lying nose-forward in its cradle (hide it when it launches)
            pod_parts, _ = generate_pod(f"{cls}_PodRack_{sname}_{j}")
            rack = Part(f"{cls}_PodRack_{sname}_{j}", "Armor", origin=(px, py + POD_PITCH / 2 + 0.2, TZ - 1.25))
            for q in pod_parts:
                for solid in q.solids:
                    rack.add(solid)
            parts.append(rack)
            for e in (-1, 1):                        # cradle rails and hazard edging
                rx = px + e * 1.7
                trim.add(box(rx - 0.08, rx + 0.08, py + 0.4, py + POD_PITCH - 0.4, TZ - 0.02, TZ + 0.5))
                hazard.add(box(rx - 0.12, rx + 0.12, py + 0.4, py + POD_PITCH - 0.4, TZ, TZ + 0.02))
            lights.add(box(px - 0.3, px + 0.3, py + 1.0, py + POD_PITCH - 1.0, -SLAB_T - 0.08, -SLAB_T))
            markers += [(f"PodTube_{sname}_{j}", (px, py + POD_PITCH / 2, TZ + 0.2)),
                        (f"PodTube_{sname}_{j}_Muzzle", (px, py + POD_PITCH / 2, tb - 4.0)),
                        (f"PodTube_{sname}_{j}_Board", (side * (cw - 0.6), py + POD_PITCH / 2, TZ + 0.05))]
            # lockers along the hull outboard of the cradle, if there's room
            if hw - (pod_cx + 1.9) > 1.2:
                furniture.add(box(*sorted((side * (hw - 0.6), side * hw)), py + 1.0, py + POD_PITCH - 1.0, TZ, TZ + 2.1))
    for d_i, dy in enumerate([y for y in drop_ys for _ in (0, 1)], 1):
        side = -1 if d_i % 2 == 1 else 1
        dx = side * (cw + 1.6)
        floor_holes.append((dx - 1.0, dx + 1.0, dy - 1.0, dy + 1.0))
        belly_hatches.append((f"DropTube_{d_i}_Hatch", dx - 1.0, dx + 1.0, dy - 1.0, dy + 1.0))
        pod_parts, _ = generate_droppod(f"{cls}_DropPod_{d_i}")
        body = Part(f"{cls}_DropPod_{d_i}", "Armor", origin=(dx, dy, TZ - 0.6), rot_z=side * -math.pi / 2)
        door = Part(f"{cls}_DropPod_{d_i}_Door-col", "Armor", origin=(dx, dy, TZ - 0.6), rot_z=side * -math.pi / 2)
        for q in pod_parts:
            for solid in q.solids:
                (door if q.name.endswith("Door-col") else body).add(solid)
        parts += [body, door]
        hazard.add_many([box(dx - 1.15, dx + 1.15, dy - 1.15, dy - 1.0, TZ, TZ + 0.02),
                         box(dx - 1.15, dx + 1.15, dy + 1.0, dy + 1.15, TZ, TZ + 0.02)])
        for e in (-1, 1):
            trim.add(box(dx - 1.15, dx + 1.15, dy + e * 1.25 - 0.08, dy + e * 1.25 + 0.08, TZ, -SLAB_T))
        markers += [(f"DropPod_{d_i}_Board", (side * (cw - 0.6), dy, TZ + 0.05)),
                    (f"DropPod_{d_i}_Exit", (dx, dy, tb - 5.0))]
    if pod_ys or drop_ys:
        bm = (bay_y0 + bay_y1) / 2
        markers += [("PodBay_Port_Muster", (-0.6, bm, TZ + 0.05)), ("PodBay_Starboard_Muster", (0.6, bm + 2.0, TZ + 0.05))]
        if drop_ys:
            markers.append(("DropBay_Muster", (0, (drop_y0 + bay_y1) / 2, TZ + 0.05)))
        lights.add(box(-0.35, 0.35, bay_y0 + 1.0, bay_y1 - 1.0, -SLAB_T - 0.08, -SLAB_T))
    # floor (walkable), belly plating with the launch hatches, and the hull sides of the deck
    rects = [(-hw, hw, y_back, y_front)]
    for h_ in floor_holes:
        rects = [q for r in rects for q in rect_minus(r, h_)]
    for x0_, x1_, ry0, ry1 in rects:
        decks_p.add(box(x0_, x1_, ry0, ry1, tb, TZ))
    brects = [(-ox, ox, yb, yf)]
    for (_, hx0, hx1, hy0, hy1) in belly_hatches:
        brects = [q for r in brects for q in rect_minus(r, (hx0, hx1, hy0, hy1))]
    for x0_, x1_, ry0, ry1 in brects:
        hull.add(box(x0_, x1_, ry0, ry1, tb - 0.4, tb))
    for (nm_, hx0, hx1, hy0, hy1) in belly_hatches:
        hp = Part(f"{cls}_{nm_}-col", "BreachPanel")
        hp.add(box(hx0, hx1, hy0, hy1, tb - 0.4, tb))
        parts.append(hp)
        hazard.add_many([box(hx0 - 0.2, hx1 + 0.2, hy0 - 0.2, hy0, tb - 0.45, tb - 0.4),
                         box(hx0 - 0.2, hx1 + 0.2, hy1, hy1 + 0.2, tb - 0.45, tb - 0.4)])
    for side in (-1, 1):
        xa, xb = sorted((side * hw, side * ox))
        hull.add(box(xa, xb, y_back, y_front, tb, -SLAB_T))
    hull.add(box(-ox, ox, y_front, yf, tb, -SLAB_T))
    hull.add(box(-ox, ox, yb, y_back, tb, -SLAB_T))
    # the bulkhead between the bay and the troop rooms (open walkway in the middle)
    yb_t = seg_y(sr0)[0]
    if sr0 < n:
        inner.add_many(wall("x", yb_t - WALL_T / 2, yb_t + WALL_T / 2, -hw, hw, TZ, -SLAB_T,
                            [(0.0, 2 * cw - 0.4, TZ, TZ + 2.8)]))
    # troop rooms: walls to the walkway with a door each (the access rooms are open),
    # partitions between sections, and their furnishings
    tcount = {}
    for (s_, side), role_ in sorted(troop_role.items()):
        y0_, y1_ = seg_y(s_)
        cy_ = seg_c(s_)
        xa, xb = sorted((side * cw, side * (cw + WALL_T)))
        if role_ == "access":
            ops = [(cy_, 6.0, TZ, TZ + 3.0)]
        else:
            ops = [(cy_, DOOR_W, TZ, TZ + DOOR_H)]
            rd = Part(f"{cls}_RoomDoor_T_{s_}_{'P' if side < 0 else 'S'}-col", "Door", origin=((xa + xb) / 2, cy_, TZ))
            rd.add(box(-0.04, 0.04, -DOOR_W / 2, DOOR_W / 2, 0, DOOR_H))
            parts.append(rd)
        inner.add_many(wall("y", xa, xb, y0_, y1_, TZ, -SLAB_T, ops))
        if s_ + 1 < n:                                               # partition toward the next section
            ra, rb = sorted((side * U0, side * hw))
            inner.add_many(wall("x", y1_ - WALL_T / 2, y1_ + WALL_T / 2, ra, rb, TZ, -SLAB_T))
        tcount[role_] = tcount.get(role_, 0) + 1
        tag = f"T{tcount[role_]}"
        z = TZ
        if role_ == "access":
            ya, yb2 = y0_ + 1.4, y0_ + 8.6           # 1.3 m clear at both ends to step on and off
            ra_, rb_ = sorted((side * (hw - RAMP_W - 0.3), side * (hw - 0.3)))
            inner.add(hexa([((ra_, rb_)[i & 1], (ya, yb2)[(i >> 1) & 1],
                             TZ if not (i >> 2) & 1 else (TZ + 0.02 if not (i >> 1) & 1 else 0.0)) for i in range(8)]))
            xr = side * (hw - RAMP_W - 0.3)
            q0, q1 = sorted((xr, xr - side * 0.08))
            rails.add(hexa([((q0, q1)[i & 1], (ya, yb2)[(i >> 1) & 1],
                             (TZ if not (i >> 1) & 1 else 0.0) + (1.0 if (i >> 2) & 1 else 0.0)) for i in range(8)]))
            markers += [(f"BayAccess_{tcount[role_]}_Bottom", (side * (hw - 1.4), ya - 0.7, TZ + 0.05)),
                        (f"BayAccess_{tcount[role_]}_Top", (side * (hw - 1.4), yb2 + 0.7, 0.05))]
        elif role_ == "berthing":
            for j in range(4):
                yc = y0_ + 1.4 + j * 2.4
                for zb in (0.2, 1.1, 2.0):
                    furniture.add(rbox(side, D - 1.0, D - 0.1, yc - 1.0, yc + 1.0, z + zb, z + zb + 0.2))
                for e in (-1, 1):
                    furniture.add(rbox(side, D - 1.0, D - 0.1, yc + e * 1.0 - 0.05, yc + e * 1.0 + 0.05, z, z + 2.5))
                markers.append((f"Bunk_Berthing_{tag}_{j + 1}", (side * (U0 + D - 2.5), yc, z + 0.05)))
            markers.append((f"Berthing_{tag}_Deck-1", (side * (U0 + 1.3), cy_, z + 0.05)))
        elif role_ == "armory":
            for j in range(3):
                ry = y0_ + 1.2 + j * 2.9
                furniture.add(rbox(side, D - 0.6, D - 0.1, ry, ry + 2.2, z, z + 2.1))
                lights.add(rbox(side, D - 0.62, D - 0.6, ry + 0.2, ry + 2.0, z + 2.0, z + 2.05))
            for j in range(3):
                cover.add(rbox(side, 0.3, 1.1, y0_ + 0.8 + j * 0.9, y0_ + 1.55 + j * 0.9, z, z + 0.7))
            furniture.add(rbox(side, 0.9, 1.5, y1_ - 3.4, y1_ - 0.6, z, z + 1.05))
            markers += [(f"Armory_{tag}_Resupply", (side * (U0 + 2.6), cy_, z + 0.05)),
                        (f"Armory_{tag}_Counter", (side * (U0 + 2.3), y1_ - 2.0, z + 0.05))]
        elif role_ == "medbay":
            for j in range(3):
                yc = y0_ + 1.8 + j * 3.1
                medical.add(rbox(side, D - 2.2, D - 0.2, yc - 0.5, yc + 0.5, z, z + 0.7))
                markers.append((f"Medbay_{tag}_Bed_{j + 1}", (side * (U0 + D - 1.2), yc, z + 0.75)))
            medical.add(rbox(side, 0.0, 0.55, y0_ + 6.4, y0_ + 9.4, z, z + 1.9))
            markers.append((f"Medbay_{tag}_MedpenResupply", (side * (U0 + 1.4), y0_ + 7.9, z + 0.05)))
        elif role_ == "ready":
            for j in range(3):                                       # benches facing a briefing screen
                by_ = y0_ + 2.0 + j * 2.2
                furniture.add(rbox(side, 1.0, D - 1.6, by_ - 0.25, by_ + 0.25, z, z + 0.45))
            lights.add(rbox(side, 0.5, D - 1.0, y1_ - 0.6, y1_ - 0.5, z + 1.0, z + 2.4))
            markers.append((f"ReadyRoom_{tag}", (side * (U0 + 1.0), cy_, z + 0.05)))
        elif role_ == "storage":
            for _ in range(5):
                u = rng.uniform(1.2, D - 1.0)
                yy = rng.uniform(y0_ + 1.0, y1_ - 1.0)
                if abs(yy - cy_) < 1.4 and u < 2.5:
                    continue
                sz = rng.uniform(0.9, 1.3)
                cover.add(rbox(side, u - sz / 2, u + sz / 2, yy - sz / 2, yy + sz / 2, z, z + sz))
            markers.append((f"Storage_{tag}_Stores_Deck-1", (side * (U0 + 1.0), cy_, z + 0.05)))
    for s_ in range(sr0, n):
        y0_, y1_ = seg_y(s_)
        lights.add(box(-0.3, 0.3, y0_ + 1.5, y1_ - 1.5, -SLAB_T - 0.08, -SLAB_T))
    markers.append(("TroopDeck_Walkway", (0, (bay_y1 + y_front) / 2, TZ + 0.05)))

    # ---------- ramps between decks
    for (k, s, side) in ramps:
        y0, y1 = seg_y(s)
        ya, yb2 = y0 + 1.6, y1 - 1.6
        xa, xb = sorted((side * (hw - RAMP_W - 0.3), side * (hw - 0.3)))
        za, zb = k * H, (k + 1) * H
        inner.add(hexa([(( xa, xb)[i & 1], (ya, yb2)[(i >> 1) & 1],
                         za if not (i >> 2) & 1 else (za + 0.02 if not (i >> 1) & 1 else zb))
                        for i in range(8)]))
        # railing on the open side of the ramp
        xr = side * (hw - RAMP_W - 0.3)
        ra, rb = sorted((xr, xr - side * 0.08))
        rails.add(hexa([((ra, rb)[i & 1], (ya, yb2)[(i >> 1) & 1],
                         (za if not (i >> 1) & 1 else zb) + (1.0 if (i >> 2) & 1 else 0.0))
                        for i in range(8)]))
        # railing around the hole on the deck above (exit end left open)
        hx = side * (hw - RAMP_W - 0.3)
        ha, hb = sorted((hx, hx - side * 0.1))
        rails.add(box(ha, hb, ya, yb2 - 2.0, zb, zb + 1.1))
        ea, eb = sorted((side * (hw - RAMP_W - 0.3), side * hw))
        rails.add(box(ea, eb, ya - 0.1, ya, zb, zb + 1.1))
        markers.append((f"Ramp_Deck{k}_to_{k + 1}", (side * (hw - 1.4), ya - 0.8, za + 0.05)))

    # ---------- outer hull walls
    win_k = decks - 1
    win_w = min(10.0, 2 * hw - 4)
    win_z0, win_z1 = win_k * H + 1.4, win_k * H + 2.8
    hull.add_many(wall("x", y_front, yf, -ox, ox, -SLAB_T, z_top, [(0, win_w, win_z0, win_z1)]))
    hull.add_many(wall("x", yb, y_back, -ox, ox, -SLAB_T, z_top))
    glass.add(box(-win_w / 2, win_w / 2, y_front + 0.2, y_front + 0.28, win_z0, win_z1))

    hangar_y0, hangar_y1 = seg_y(1)[0] + 1.0, seg_y(n_hangar)[1] - 1.0
    cargo_y0, cargo_y1 = seg_y(cargo_s0)[0] + 0.8, seg_y(aft_segs - 1)[1] - 0.8
    cargo_z0, cargo_z1 = 0.2, (HD * H - 1.2 if HD > 1 else H - 0.4)
    hangar_z0, hangar_z1 = 0.5, HD * H - 1.2
    breach_info = []
    for side, sname in ((-1, "Port"), (1, "Starboard")):
        xa, xb = sorted((side * hw, side * ox))
        # aft part: tall hangar wall, plus normal bands above it
        hangar_op = ([((hangar_y0 + hangar_y1) / 2, hangar_y1 - hangar_y0, hangar_z0, hangar_z1)]
                     if n_hangar else [])
        if n_cargo and side == 1:
            hangar_op.append(((cargo_y0 + cargo_y1) / 2, cargo_y1 - cargo_y0, cargo_z0, cargo_z1))
        hull.add_many(wall("y", xa, xb, y_back, y_aft_end, -SLAB_T, HD * H, hangar_op))
        for k in range(HD, levels):
            hull.add_many(wall("y", xa, xb, y_back, y_aft_end, k * H, (k + 1) * H))
        # front part: one band per level, with breach panels
        for k in range(levels):
            zb0 = -SLAB_T if k == 0 else k * H
            ops = []
            for (bk, bs, bside) in breaches:
                if bk == k and bside == side:
                    ops.append((seg_c(bs), BREACH_W, k * H + 0.3, k * H + 0.3 + BREACH_H))
            for (ak, as_, aside) in airlocks:
                if ak == k and aside == side:
                    ops.append((seg_c(as_), AIRLOCK_W, k * H, k * H + AIRLOCK_H))
            hull.add_many(wall("y", xa, xb, y_aft_end, y_front, zb0, (k + 1) * H, ops))
        if not n_hangar:
            continue
        # hangar shield, frame and lights
        sh = Part(f"{cls}_HangarShield_{sname}", "Shield")
        sa, sb = sorted((side * (hw + 0.22), side * (hw + 0.28)))
        sh.add(box(sa, sb, hangar_y0, hangar_y1, hangar_z0, hangar_z1))
        parts.append(sh)
        fa, fb = sorted((side * ox, side * (ox + 0.6)))
        trim.add_many([box(fa, fb, hangar_y0 - 0.6, hangar_y0, hangar_z0 - 0.6, hangar_z1 + 0.6),
                       box(fa, fb, hangar_y1, hangar_y1 + 0.6, hangar_z0 - 0.6, hangar_z1 + 0.6),
                       box(fa, fb, hangar_y0, hangar_y1, hangar_z1, hangar_z1 + 0.6),
                       box(fa, fb, hangar_y0, hangar_y1, hangar_z0 - 0.6, hangar_z0)])
        la, lb = sorted((side * (ox + 0.6), side * (ox + 0.7)))
        lights.add(box(la, lb, hangar_y0 + 0.5, hangar_y1 - 0.5, hangar_z1 + 0.2, hangar_z1 + 0.35))

    # ---------- breach zones
    for i, (k, s, side) in enumerate(breaches, 1):
        cy, zb0 = seg_c(s), k * H + 0.3
        bp = Part(f"{cls}_BreachPanel_{i}-col", "BreachPanel")
        pa, pb = sorted((side * hw, side * ox))
        bp.add(box(pa, pb, cy - BREACH_W / 2, cy + BREACH_W / 2, zb0, zb0 + BREACH_H))
        parts.append(bp)
        fa, fb = sorted((side * ox, side * (ox + 0.45)))
        e = 0.35
        hazard.add_many([box(fa, fb, cy - BREACH_W / 2 - e, cy - BREACH_W / 2, zb0 - e, zb0 + BREACH_H + e),
                         box(fa, fb, cy + BREACH_W / 2, cy + BREACH_W / 2 + e, zb0 - e, zb0 + BREACH_H + e),
                         box(fa, fb, cy - BREACH_W / 2, cy + BREACH_W / 2, zb0 + BREACH_H, zb0 + BREACH_H + e),
                         box(fa, fb, cy - BREACH_W / 2, cy + BREACH_W / 2, zb0 - e, zb0)])
        # cover inside: two low walls staggered between the breach and the door, plus crates
        z = k * H
        mx = side * (cw + WALL_T + cfg["room_depth"] * 0.5)
        for dy, dx in ((-2.4, 0.6), (2.4, -0.6)):
            ca, cb = sorted((mx + side * dx - 0.2, mx + side * dx + 0.2))
            cover.add(box(ca, cb, cy + dy - 1.3, cy + dy + 1.3, z, z + 1.15))
        for dy in (-1, 1):
            cx = side * (cw + WALL_T + 0.9)
            cover.add(box(cx - 0.6, cx + 0.6, cy + dy * (SEG_LEN / 2 - 1.2) - 0.6,
                          cy + dy * (SEG_LEN / 2 - 1.2) + 0.6, z, z + 1.2))
        markers += [(f"BreachZone_{i}_Interior", (side * rooms_x, cy, z + 0.05)),
                    (f"BreachZone_{i}_PodTarget", (side * ox, cy, zb0 + BREACH_H / 2)),
                    (f"BreachZone_{i}_PodApproach", (side * (ox + 30), cy, zb0 + BREACH_H / 2))]
        breach_info.append((k, s, side))

    # ---------- airlocks (SMALL ships): the only way aboard
    airlock_info = []
    for a_i, (k, s, side) in enumerate(airlocks, 1):
        cy, z = seg_c(s), k * H
        # outer door: just inside the hull, modeled closed; slide +2.1 m on Y to open
        od = Part(f"{cls}_Airlock_{a_i}_OuterDoor-col", "Door", origin=(side * (hw - 0.06), cy, z))
        od.add(box(-0.05, 0.05, -AIRLOCK_W / 2 - 0.05, AIRLOCK_W / 2 + 0.05, 0, AIRLOCK_H))
        parts.append(od)
        # docking collar the boarding dropship's ramp seals against
        xa, xb = sorted((side * ox, side * (ox + 0.8)))
        d = AIRLOCK_W / 2
        hull.add_many([box(xa, xb, cy - d - 0.4, cy - d, z - 0.4, z + AIRLOCK_H + 0.4),
                       box(xa, xb, cy + d, cy + d + 0.4, z - 0.4, z + AIRLOCK_H + 0.4),
                       box(xa, xb, cy - d - 0.4, cy + d + 0.4, z + AIRLOCK_H, z + AIRLOCK_H + 0.4),
                       box(xa, xb, cy - d - 0.4, cy + d + 0.4, z - 0.4, z)])
        ha, hb = sorted((side * (ox + 0.8), side * (ox + 0.85)))
        hazard.add_many([box(ha, hb, cy - d - 0.4, cy - d, z - 0.4, z + AIRLOCK_H + 0.4),
                         box(ha, hb, cy + d, cy + d + 0.4, z - 0.4, z + AIRLOCK_H + 0.4)])
        lights.add(box(ha, hb, cy - d, cy + d, z + AIRLOCK_H + 0.1, z + AIRLOCK_H + 0.3))
        # EVA suit lockers along the partition walls
        for e in (-1, 1):
            yy = cy + e * (SEG_LEN / 2 - 0.45)
            furniture.add(rbox(side, 1.2, D - 2.9, yy - 0.3, yy + 0.3, z, z + 2.1))
        markers += [(f"Airlock_{a_i}_Interior", (side * rooms_x, cy, z + 0.05)),
                    (f"Airlock_{a_i}_DropshipDock", (side * (ox + 0.85), cy, z + 0.05)),
                    (f"Airlock_{a_i}_EVAEntry", (side * (ox + 3.0), cy, z + 1.3)),
                    (f"Airlock_{a_i}_OuterDoor_ChargeA", (side * (ox + 0.4), cy, z + 1.2)),
                    (f"Airlock_{a_i}_OuterDoor_ChargeB", (side * (hw - 0.5), cy, z + 1.2))]
        airlock_info.append((k, s, side))

    # ---------- hangar contents: two fighter pads and a boarding-shuttle pad, evenly spaced
    # down the hangar (16 m apart: a 15 m fighter has room fore and aft), crates kept to
    # the ends so nothing is in the way of craft taxiing out of either side
    if n_hangar:
        hc = (hangar_y0 + hangar_y1) / 2
        pad_ys = [hc + 16.0, hc, hc - 16.0]             # fighter, fighter, shuttle (aftmost)
        for j, cy in enumerate(pad_ys):
            shuttle = j == 2
            half = 5.5 if shuttle else 7.2
            for (a_, b_, c_, d_) in ((-half, half, cy - half - 0.2, cy - half), (-half, half, cy + half, cy + half + 0.2),
                                     (-half - 0.2, -half, cy - half, cy + half), (half, half + 0.2, cy - half, cy + half)):
                hazard.add(box(a_, b_, c_, d_, 0, 0.02))
            if shuttle:                                 # a big "S" stripe across the shuttle pad
                hazard.add(box(-0.3, 0.3, cy - half + 0.6, cy + half - 0.6, 0, 0.02))
                markers.append(("Hangar_ShuttlePad", (0, cy, 0.05)))
            else:
                markers.append((f"Hangar_LandingPad_{j + 1}", (0, cy, 0.05)))
            lights.add(box(-0.4, 0.4, cy - 4.0, cy + 4.0, HD * H - SLAB_T - 0.08, HD * H - SLAB_T))
        for end_y, dirn in ((seg_y(1)[0] + 1.6, 1), (seg_y(n_hangar)[1] - 1.6, -1)):
            for _ in range(3):
                side = rng.choice((-1, 1))
                cx = side * rng.uniform(3.0, hw - 2.0)        # keep the centre walkway clear
                sz = rng.uniform(0.9, 1.4)
                cy = end_y + dirn * rng.uniform(0.0, 0.8)
                cover.add(box(cx - sz / 2, cx + sz / 2, cy - sz / 2, cy + sz / 2, 0, sz))

    # ---------- reactor room
    ry = seg_c(0)
    reactor.add(cylinder("z", 0, ry, 0, HD * H - SLAB_T, 1.6, seg=20))
    trim.add_many([cylinder("z", 0, ry, 0, 0.6, 2.4, seg=20),
                   cylinder("z", 0, ry, HD * H - SLAB_T - 0.6, HD * H - SLAB_T, 2.4, seg=20)])
    markers.append(("Reactor", (0, ry - 3.5, 0.05)))

    # ---------- bridge
    by0, by1 = seg_y(n - 1)
    bz = (decks - 1) * H
    for x in (-3.0, 0.0, 3.0):
        cover.add(box(x - 1.1, x + 1.1, by1 - 2.6, by1 - 1.8, bz, bz + 1.1))
    cover.add(box(-2.5, 2.5, by0 + 3.0, by0 + 4.0, bz, bz + 1.0))   # command table
    lights.add(box(-2.0, 2.0, by0 + 1.5, by1 - 1.5, bz + H - SLAB_T - 0.08, bz + H - SLAB_T))
    markers += [("Bridge_PilotSeat", (0, by1 - 3.2, bz + 0.05)),
                ("Bridge_CaptainChair", (0, by0 + 5.5, bz + 0.05))]
    for k in range(decks):
        markers.append((f"PlayerSpawn_Deck{k}", (0, seg_c(aft_segs + 1), k * H + 0.05)))
    if n_hangar:
        markers.append(("Evac_Hangar", (0, (hangar_y0 + hangar_y1) / 2, 0.05)))

    # ---------- cargo bay: Darter pads, bay door + shield, storage racks, crew work points.
    # Receiving ship: its crew unloads the Darter into storage. Supply ship: its crew
    # loads the docked Darter from storage. A Darter can also land 6 armed soldiers here,
    # so the bay is a boarding point whenever its door is open.
    storage_slots = 0
    if n_cargo:
        cz1 = HD * H - SLAB_T
        bd = Part(f"{cls}_CargoBayDoor-col", "Door")          # modeled closed: hide/slide to open
        bd.add(box(hw + 0.05, hw + 0.15, cargo_y0, cargo_y1, cargo_z0, cargo_z1))
        parts.append(bd)
        sh = Part(f"{cls}_CargoBayShield", "Shield")          # no collision: toggle in Godot
        sh.add(box(hw + 0.3, hw + 0.36, cargo_y0, cargo_y1, cargo_z0, cargo_z1))
        parts.append(sh)
        trim.add_many([box(ox, ox + 0.5, cargo_y0 - 0.5, cargo_y0, cargo_z0 - 0.5, cargo_z1 + 0.5),
                       box(ox, ox + 0.5, cargo_y1, cargo_y1 + 0.5, cargo_z0 - 0.5, cargo_z1 + 0.5),
                       box(ox, ox + 0.5, cargo_y0, cargo_y1, cargo_z1, cargo_z1 + 0.5)])
        hazard.add(box(ox, ox + 0.55, cargo_y0, cargo_y1, cargo_z0 - 0.5, cargo_z0))
        lights.add(box(ox + 0.5, ox + 0.6, cargo_y0 + 0.4, cargo_y1 - 0.4, cargo_z1 + 0.15, cargo_z1 + 0.3))
        for i in range(n_cargo):
            s_ = cargo_s0 + i
            yc = seg_c(s_)
            px, py = 5.2, 3.2                                   # pad half-size
            hazard.add_many([box(-px, px, yc - py, yc - py + 0.2, 0, 0.02), box(-px, px, yc + py - 0.2, yc + py, 0, 0.02),
                             box(-px, -px + 0.2, yc - py, yc + py, 0, 0.02), box(px - 0.2, px, yc - py, yc + py, 0, 0.02)])
            lights.add(box(-3.0, 3.0, yc - 0.3, yc + 0.3, cz1 - 0.08, cz1))
            markers += [(f"CargoBay_DarterPad_{i + 1}", (0, yc, 0.05)),
                        (f"CargoBay_DarterPad_{i + 1}_Approach", (ox + 25, yc, (cargo_z0 + cargo_z1) / 2)),
                        (f"CargoBay_DarterPad_{i + 1}_CrewWork_A", (min(hw - 0.8, px + 0.6), yc - 1.2, 0.05)),
                        (f"CargoBay_DarterPad_{i + 1}_CrewWork_B", (min(hw - 0.8, px + 0.6), yc + 1.2, 0.05))]
        # storage racks across both ends of the bay (gap left for the bulkhead doorway)
        rack_h = min(3.0, cz1 - 0.4)
        for yend, dirn in ((seg_y(cargo_s0)[0] + 0.15, 1), (seg_y(aft_segs - 1)[1] - 0.15, -1)):
            ya_, yb2 = sorted((yend, yend + dirn * 0.9))
            for xa_, xb_ in ((-hw + 0.3, -2.0), (0.8, hw - 1.6)):
                furniture.add(box(xa_, xb_, ya_, yb2, 0, rack_h))
                for xs_ in [xa_ + 0.75 + 1.5 * j for j in range(int((xb_ - xa_) // 1.5))]:
                    storage_slots += 1
                    markers.append((f"CargoStorage_{storage_slots}", (xs_, yend + dirn * 1.6, 0.05)))
        muster = (-(hw - 1.0), (cargo_y0 + cargo_y1) / 2)
        keep_clear = [m[1][:2] for m in markers if m[0].startswith(("CargoStorage", "CargoBay_DarterPad"))]
        keep_clear.append(muster)
        placed_c = 0
        for _ in range(60):                                     # loose crates for cover (port side)
            if placed_c >= 3 * n_cargo:
                break
            sz = rng.uniform(0.9, 1.4)
            cx_ = -rng.uniform(5.6, max(5.7, hw - 0.9))
            cy_ = rng.uniform(seg_y(cargo_s0)[0] + 2.0, seg_y(aft_segs - 1)[1] - 2.0)
            if any(math.hypot(cx_ - a, cy_ - b) < 1.6 for a, b in keep_clear):
                continue
            cover.add(box(cx_ - sz / 2, cx_ + sz / 2, cy_ - sz / 2, cy_ + sz / 2, 0, sz))
            keep_clear.append((cx_, cy_))
            placed_c += 1
        markers.append(("CargoBay_Muster", (muster[0], muster[1], 0.05)))

    # ---------- interior drop bay (drop frigate): pods racked along both walls, doors facing
    # the center walkway; each launches straight down through its floor and hull hatch
    for d_i, (dx, dy, side) in enumerate(drop_spots, 1):
        pod_parts, _ = generate_droppod(f"{cls}_DropPod_{d_i}")
        body = Part(f"{cls}_DropPod_{d_i}", "Armor", origin=(dx, dy, -SLAB_T), rot_z=side * -math.pi / 2)
        door = Part(f"{cls}_DropPod_{d_i}_Door-col", "Armor", origin=(dx, dy, -SLAB_T), rot_z=side * -math.pi / 2)
        for q in pod_parts:
            for solid in q.solids:
                (door if q.name.endswith("Door-col") else body).add(solid)
        parts += [body, door]
        hp = Part(f"{cls}_DropTube_{d_i}_Hatch-col", "BreachPanel")
        hp.add(box(dx - 1.0, dx + 1.0, dy - 1.0, dy + 1.0, -SLAB_T - 0.4, -SLAB_T))
        parts.append(hp)
        hazard.add_many([box(dx - 1.15, dx + 1.15, dy - 1.15, dy - 1.0, 0, 0.02),
                         box(dx - 1.15, dx + 1.15, dy + 1.0, dy + 1.15, 0, 0.02)])
        for e in (-1, 1):                                       # rack posts beside each pod
            trim.add(box(*sorted((side * (hw - 0.2), side * (hw - 0.45))), dy + e * 1.1 - 0.1, dy + e * 1.1 + 0.1,
                         0, H - SLAB_T))
        markers += [(f"DropPod_{d_i}_Board", (dx - side * 1.7, dy, 0.05)),
                    (f"DropPod_{d_i}_Exit", (dx, dy, -6.0))]
    if drop_spots:
        by0, by1 = seg_y(min(drop_segs))[0], seg_y(max(drop_segs))[1]
        for side in (-1, 1):                                    # overhead gantry rails
            trim.add(box(*sorted((side * (hw - 0.2), side * (hw - 2.4))), by0 + 0.4, by1 - 0.4,
                         H - SLAB_T - 0.25, H - SLAB_T))
        lights.add(box(-0.4, 0.4, by0 + 1.0, by1 - 1.0, H - SLAB_T - 0.08, H - SLAB_T))
        markers.append(("DropBay_Muster", (0, (by0 + by1) / 2, 0.05)))

    # ---------- no corridor lockers any more: weapons, armor and ammunition live in the
    # armories (and come aboard as supplies), so a ship's armories are what keep it fighting
    ready_lockers = 0

    # ---------- furnish the side rooms
    crew_berths, troop_berths, pod_i, escape_info = 0, 0, 0, []
    counters = {}
    fr = random.Random(f"{SEED}-{cls}-furnish-{VARIANT}")
    for (k, s, side), role in sorted(room_role.items()):
        y0, y1 = seg_y(s)
        z, cy = k * H, seg_c(s)
        counters[role] = counters.get(role, 0) + 1
        tag = f"{role.capitalize()}_{counters[role]}"
        if role == "quarters":
            # two cabins, each: a double bunk against the hull, a desk, a locker
            for ci, (ca, cb) in enumerate(((y0 + 0.1, cy - 0.1), (cy + 0.1, y1 - 0.1))):
                furniture.add(rbox(side, D - 1.0, D - 0.1, ca + 0.3, ca + 2.4, z + 0.3, z + 0.55))
                furniture.add(rbox(side, D - 1.0, D - 0.1, ca + 0.3, ca + 2.4, z + 1.5, z + 1.75))
                furniture.add(rbox(side, D - 1.0, D - 0.1, ca + 0.25, ca + 0.35, z, z + 2.2))
                furniture.add(rbox(side, D - 1.0, D - 0.1, ca + 2.35, ca + 2.45, z, z + 2.2))
                furniture.add(rbox(side, D - 1.6, D - 0.9, cb - 1.4, cb - 0.2, z, z + 0.75))   # desk
                furniture.add(rbox(side, 0.0, 0.5, cb - 1.1, cb - 0.2, z, z + 2.0))            # locker
                lights.add(rbox(side, D - 1.5, D - 1.0, cb - 1.2, cb - 1.0, z + 0.75, z + 0.95))
                crew_berths += 2
                markers.append((f"{tag}_Cabin{ci + 1}_Deck{k}", (side * (U0 + 1.4), (ca + cb) / 2, z + 0.05)))
                markers.append((f"Bunk_{tag}_{ci + 1}", (side * (U0 + D - 1.6), ca + 1.35, z + 0.05)))
        elif role == "berthing":
            # troop berthing: four 3-high bunk stacks, foot lockers, a muster spot by the door
            for j in range(4):
                yc = y0 + 1.4 + j * 2.4
                for zb in (0.25, 1.2, 2.15):
                    furniture.add(rbox(side, D - 1.0, D - 0.1, yc - 1.0, yc + 1.0, z + zb, z + zb + 0.2))
                for e in (-1, 1):
                    furniture.add(rbox(side, D - 1.0, D - 0.1, yc + e * 1.0 - 0.05, yc + e * 1.0 + 0.05, z, z + 2.6))
                furniture.add(rbox(side, D - 1.6, D - 1.05, yc - 0.6, yc + 0.6, z, z + 0.45))     # foot locker
                troop_berths += 3
                markers.append((f"Bunk_{tag}_{j + 1}", (side * (U0 + D - 2.5), yc, z + 0.05)))
            lights.add(rbox(side, 0.05, 0.1, y0 + 1.0, y1 - 1.0, z + 2.3, z + 2.4))
            markers.append((f"{tag}_Deck{k}", (side * (U0 + 1.3), cy, z + 0.05)))
        elif role == "mess":
            for tt in (-1, 1):                       # two long tables with benches
                ty = cy + tt * 2.4
                furniture.add(rbox(side, 1.6, D - 1.6, ty - 0.5, ty + 0.5, z + 0.72, z + 0.8))
                furniture.add(rbox(side, 1.8, D - 1.8, ty - 0.15, ty + 0.15, z, z + 0.72))
                for e in (-1, 1):
                    furniture.add(rbox(side, 1.6, D - 1.6, ty + e * 0.85 - 0.18, ty + e * 0.85 + 0.18, z, z + 0.45))
            furniture.add(rbox(side, D - 0.8, D - 0.1, y0 + 1.0, y1 - 1.0, z, z + 1.0))       # galley counter
            lights.add(rbox(side, D - 0.75, D - 0.7, y0 + 1.2, y1 - 1.2, z + 1.0, z + 1.05))
            markers.append((f"{tag}_Deck{k}", (side * (U0 + 1.0), cy, z + 0.05)))
            markers.append((f"{tag}_Galley", (side * (U0 + D - 1.4), cy, z + 0.05)))
        elif role == "medbay":
            for j in range(3):
                yc = y0 + 1.8 + j * 3.1
                medical.add(rbox(side, D - 2.2, D - 0.2, yc - 0.5, yc + 0.5, z, z + 0.7))
                markers.append((f"{tag}_Bed_{j + 1}", (side * (U0 + D - 1.2), yc, z + 0.75)))
            medical.add(rbox(side, 0.0, 0.55, y0 + 6.4, y0 + 9.4, z, z + 1.9))    # supply cabinets
            lights.add(rbox(side, 0.55, 0.6, y0 + 7.4, y0 + 8.4, z + 1.2, z + 1.6))
            markers.append((f"{tag}_MedpenResupply", (side * (U0 + 1.4), y0 + 7.9, z + 0.05)))
        elif role == "armory":
            # weapon racks along the hull wall, armor stands, ammo crates and an issue counter
            for j in range(3):
                ry = y0 + 1.2 + j * 2.9
                furniture.add(rbox(side, D - 0.6, D - 0.1, ry, ry + 2.2, z, z + 2.1))       # rack
                trim.add(rbox(side, D - 0.75, D - 0.6, ry + 0.1, ry + 2.1, z + 1.0, z + 1.1))
                lights.add(rbox(side, D - 0.62, D - 0.6, ry + 0.2, ry + 2.0, z + 2.0, z + 2.05))
            for j in range(2):                                                       # armor stands
                ay = cy - 1.8 + j * 3.6
                furniture.add(rbox(side, 2.0, 2.6, ay - 0.3, ay + 0.3, z, z + 1.9))
            for j in range(4):                                                       # ammo crates
                cyy = y0 + 0.8 + j * 0.9
                cover.add(rbox(side, 0.3, 1.1, cyy, cyy + 0.75, z, z + 0.7))
            furniture.add(rbox(side, 0.9, 1.5, y1 - 3.4, y1 - 0.6, z, z + 1.05))    # issue counter
            markers.append((f"{tag}_Resupply", (side * (U0 + 2.6), cy, z + 0.05)))
            markers.append((f"{tag}_Counter", (side * (U0 + 2.3), y1 - 2.0, z + 0.05)))
        elif role == "systems":
            furniture.add(rbox(side, D - 2.4, D - 0.4, cy - 1.5, cy + 1.5, z, z + 2.4))
            for j in range(3):
                px = side * (U0 + 1.2 + j * 0.7)
                trim.add(cylinder("z", px, y0 + 0.45, z, z + H - SLAB_T, 0.18, seg=8))
            furniture.add(rbox(side, 1.6, 2.4, y1 - 1.2, y1 - 0.4, z, z + 1.1))
            markers.append((f"{tag}_Deck{k}", (side * (U0 + 1.2), cy, z + 0.05)))
        elif role == "comms":
            furniture.add(rbox(side, 2.5, 4.0, cy - 1.0, cy + 1.0, z, z + 0.9))
            lights.add(rbox(side, 2.6, 3.9, cy - 0.9, cy + 0.9, z + 0.9, z + 0.93))
            furniture.add(rbox(side, D - 0.8, D - 0.1, y0 + 1.5, y1 - 1.5, z, z + 1.1))
            markers.append((f"{tag}_Deck{k}", (side * (U0 + 1.2), cy, z + 0.05)))
        elif role == "workshop":
            furniture.add(rbox(side, D - 1.2, D - 0.1, y0 + 1.0, y0 + 4.5, z, z + 0.95))    # workbench
            furniture.add(rbox(side, D - 0.5, D - 0.1, y0 + 1.0, y0 + 4.5, z + 0.95, z + 2.2))  # tool wall
            cover.add(rbox(side, 1.5, 2.7, y1 - 4.0, y1 - 2.2, z, z + 1.3))                  # parts bin
            trim.add(rbox(side, D - 2.4, D - 1.6, y1 - 2.0, y1 - 1.2, z, z + 1.6))           # lathe
            markers.append((f"{tag}_Deck{k}", (side * (U0 + D - 1.8), y0 + 2.7, z + 0.05)))
        elif role == "bay_access":
            ha, hb = sorted((side * (hw - RAMP_W - 0.3), side * (hw - 0.3)))
            hx = side * (hw - RAMP_W - 0.3)
            r0, r1 = sorted((hx, hx - side * 0.1))
            rails.add(box(r0, r1, y0 + 3.6, y0 + 8.6, z, z + 1.1))
            rails.add(box(ha, hb, y0 + 3.5, y0 + 3.6, z, z + 1.1))
            hazard.add(box(ha, hb, y0 + 3.3, y0 + 3.5, z, z + 0.02))
            markers.append((f"BayAccess_{counters[role]}_Deck0", (side * (U0 + 1.2), cy, z + 0.05)))
        elif role in ("storage", "elevator"):
            u_min = 3.6 if role == "elevator" else 1.2
            for _ in range(6 if role == "storage" else 4):
                u = fr.uniform(u_min, D - 1.0)
                yy = fr.uniform(y0 + 1.0, y1 - 1.0)
                if abs(yy - cy) < 1.4 and u < 2.5:
                    continue
                sz = fr.uniform(0.9, 1.4)
                cover.add(rbox(side, u - sz / 2, u + sz / 2, yy - sz / 2, yy + sz / 2, z, z + sz))
            if role == "storage":
                markers.append((f"{tag}_Stores_Deck{k}", (side * (U0 + 1.0), cy, z + 0.05)))
        elif role == "escape":
            for e in (-1, 1):
                pod_i += 1
                yc = cy + e * 2.4
                hatches.add(rbox(side, D - 0.08, D, yc - 0.7, yc + 0.7, z, z + 2.2))
                for (ya_, yb3, za_, zb_) in ((yc - 0.9, yc - 0.7, z, z + 2.4), (yc + 0.7, yc + 0.9, z, z + 2.4),
                                             (yc - 0.9, yc + 0.9, z + 2.2, z + 2.4)):
                    hazard.add(rbox(side, D - 0.15, D, ya_, yb3, za_, zb_))
                # the pod itself, docked outside the hull; launch it by moving it outward
                pod = Part(f"{cls}_EscapePod_{pod_i}", "Armor", origin=(side * ox, yc, z + 1.2))
                pod.add(box(*sorted((0, side * 2.2)), -0.85, 0.85, -0.85, 0.85))
                pod.add(box(*sorted((side * 2.2, side * 2.7)), -0.6, 0.6, -0.6, 0.6))
                parts.append(pod)
                markers.append((f"EscapePod_{pod_i}_Hatch", (side * (hw - 0.8), yc, z + 0.05)))
            escape_info.append((k, s, side))
            markers.append((f"{tag}_Deck{k}", (side * (U0 + D / 2), cy, z + 0.05)))

    # =====================================================================
    # Exterior (Halo-inspired: long slab hull, hammerhead nose, layered armor)
    # =====================================================================
    style = STYLE.get(FACTION, "naval")
    xr = random.Random(f"{SEED}-{cls}-exterior-{FACTION}")     # faction look: same for every interior variant
    accent = P("Accent", "Accent")
    parts.append(accent)
    sharp = {"sleek": 0.12, "scrap": 0.62}.get(style, 0.42)
    prow = cfg["prow"] * (1.45 if style == "sleek" else (0.8 if style == "scrap" else 1.0))
    # roof and belly plates
    hull.add(box(-ox, ox, yb, yf, z_top, z_top + 0.4))
    # (the belly is the troop deck's plating, with the pod hatches: built with the troop deck)
    bz = tb - 0.4                                   # bottom of the hull
    chin_top = win_z0 - 0.4
    vis_b = win_z1 + 0.4
    if style == "sleek":
        # a long blade prow: the chin sweeps to a needle point, the visor is a thin upper blade
        hull.add(taper(yf, yf + prow, (ox + 0.3, bz + 0.2, chin_top), (0.25, bz * 0.45, bz * 0.45 + 0.4)))
        hull.add(taper(yf - 2, yf + prow * 0.8, (ox + 0.2, vis_b, z_top + 0.6), (0.2, vis_b + 0.2, vis_b + 0.5)))
        accent.add(taper(yf + prow * 0.25, yf + prow * 0.95, (ox * 0.5, chin_top - 0.05, chin_top + 0.08),
                         (0.12, bz * 0.45 + 0.35, bz * 0.45 + 0.45)))
        mz, mh = bz * 0.45 + 0.2, 0.35
    else:
        hull.add(taper(yf, yf + prow, (ox + 0.3, bz, chin_top), (ox * sharp, bz * 0.6, chin_top - 0.25 * (chin_top - bz))))
        hull.add(taper(yf - 2, yf + prow * 0.6, (ox + 0.3, vis_b, z_top + 0.9),
                       (ox * (sharp + 0.15), vis_b + 0.4 * (z_top + 0.9 - vis_b), z_top + 0.5)))
        mz = (bz * 0.6 + chin_top - 0.25 * (chin_top - bz)) / 2
        mh = min(1.4, ox * sharp * 0.6)
        if style == "naval":           # white band across the visor
            accent.add(taper(yf + 1.0, yf + prow * 0.45, (ox + 0.32, z_top + 0.55, z_top + 0.95),
                             (ox * (sharp + 0.25), z_top + 0.4, z_top + 0.75)))
        if style == "scrap":           # a welded battering ram on the chin
            armor.add(box(-ox * 0.5, ox * 0.5, yf + prow - 1.0, yf + prow + 2.5, bz * 0.6, chin_top - 0.6))
            accent.add(box(-ox * 0.5 - 0.02, ox * 0.5 + 0.02, yf + prow + 1.6, yf + prow + 2.0, bz * 0.6 - 0.05, chin_top - 0.55))
    # main gun muzzle at the tip of the chin
    engines.add(box(-mh, mh, yf + prow - 0.4, yf + prow + 0.3, mz - mh * 0.7, mz + mh * 0.7))
    # ---------- launchers live in the troop deck now (pod and drop hatches in the belly)
    n_side = cfg.get("pod_tubes_per_side", 0)
    n_drop = cfg.get("drop_pods", 0)
    n_dorsal = 0
    belly_gaps, top_gaps = [], []

    def spans(a, b, gaps):
        out, cur = [], a
        for g0, g1 in sorted(gaps):
            if g1 <= cur or g0 >= b:
                continue
            if g0 - cur > 0.5:
                out.append((cur, g0))
            cur = max(cur, g1)
        if b - cur > 0.5:
            out.append((cur, b))
        return out

    # keel, flares and superstructure: the faction's silhouette
    if style == "sleek":
        for a_, b_ in spans(yb + 4, yf + prow * 0.5, belly_gaps):           # a thin ventral blade
            hull.add(prism(a_, b_, 0.25, 0.9, bz - 3.2, bz))
            accent.add(prism(a_ + 0.5, b_ - 0.5, 0.05, 0.26, bz - 3.25, bz - 3.15))
        for a_, b_ in spans(yb + 6, yf - 2, top_gaps):                      # a low sloped spine
            hull.add(prism(a_, b_, hw * 0.62, hw * 0.12, z_top + 0.4, z_top + 3.4))
            lights.add(box(-hw * 0.12 - 0.02, hw * 0.12 + 0.02, a_ + 2, b_ - 2, z_top + 3.4, z_top + 3.45))
        for side in (-1, 1):                                               # twin swept dorsal fins
            fx = side * hw * 0.3
            armor.add(hexa([(fx + (-0.12, 0.12)[i & 1], (yb + 2, yb + 14)[(i >> 1) & 1] + (5.0 if (i >> 2) & 1 else 0.0),
                             (z_top + 2.0, z_top + 2.0 + min(9.0, 2.5 * levels))[(i >> 2) & 1]) for i in range(8)]))
            accent.add(hexa([(fx + (-0.13, 0.13)[i & 1], (yb + 12.5, yb + 14)[(i >> 1) & 1] + (5.0 if (i >> 2) & 1 else 0.0),
                              (z_top + 2.0, z_top + 2.0 + min(9.0, 2.5 * levels))[(i >> 2) & 1]) for i in range(8)]))
            # swept wings at deck 0, light strip on the leading edge
            wy0, wy1 = yb + 6, yb + 6 + (yf - yb) * 0.35
            armor.add(wing(side, ox, ox + hw * 0.9, (wy0, wy1), (wy0 - 6, wy0 + 2), H * 0.5, H * 0.35, 0.6, 0.2))
            lights.add(wing(side, ox, ox + hw * 0.9, (wy1 - 0.3, wy1), (wy0 + 1.7, wy0 + 2), H * 0.5, H * 0.35, 0.62, 0.22))
    elif style == "scrap":
        for a_, b_ in spans(yb + 4, yf + 2, belly_gaps):
            hull.add(prism(a_, b_, hw * 0.4, hw * 0.7, bz - 1.6, bz))
        # an off-centre bridge tower, cobbled from blocks
        tx = xr.choice((-1, 1)) * hw * 0.45
        ty = yf - 14 - xr.uniform(0, 6)
        for j in range(3):
            w_, l_ = xr.uniform(2.0, 4.0), xr.uniform(4.0, 9.0)
            hull.add(box(tx - w_, tx + w_, ty - l_, ty + l_ * 0.6, z_top + 0.4 + j * 1.6, z_top + 2.0 + j * 1.6))
        trim.add(cylinder("z", tx, ty, z_top + 5.2, z_top + 10.5, 0.15, seg=6))
        armor.add(cylinder("z", tx, ty, z_top + 9.0, z_top + 9.2, 1.6, seg=10))
        # welded-on cargo containers along the roof, sloppy and uneven
        y = yb + 6
        while y < yf - 22:
            l_ = xr.uniform(5.0, 8.0)
            x_ = xr.uniform(-hw * 0.4, hw * 0.4)
            if abs(x_ - tx) > 4.0:
                (accent if xr.random() < 0.3 else armor).add(box(x_ - 1.3, x_ + 1.3, y, y + l_, z_top + 0.4, z_top + 2.9))
                trim.add(box(x_ - 1.35, x_ + 1.35, y + 0.3, y + 0.5, z_top + 0.4, z_top + 2.95))
            y += l_ + xr.uniform(0.5, 4.0)
        # bare girders hung off one flank
        gs = -1 if tx > 0 else 1
        for j in range(4):
            gy = yb + 8 + j * (yf - yb - 20) / 3
            trim.add(box(*sorted((gs * ox, gs * (ox + 2.6))), gy - 0.15, gy + 0.15, H * 0.4, H * 0.4 + 0.3))
            trim.add(box(*sorted((gs * (ox + 2.4), gs * (ox + 2.6))), gy - 0.15, gy + 0.15, -0.6, H * 0.4 + 0.3))
    else:   # naval and wreck share the warship silhouette
        for a_, b_ in spans(yb + 4, yf + 2, belly_gaps):
            hull.add(prism(a_, b_, hw * 0.3, hw * 0.6, bz - 1.7, bz))
        for side in (-1, 1):
            for a_, b_ in spans(yb + 3, yf + prow * 0.4, belly_gaps):
                def corner(i, a_=a_, b_=b_, side=side):
                    outer = i & 1
                    x = side * (ox + 2.2 if outer else ox)
                    z = ((-0.8, -0.4) if outer else (-1.0, 0.0))[(i >> 2) & 1] + TZ
                    return (x, (a_, b_)[(i >> 1) & 1], z)
                hull.add(hexa([corner(i) for i in range(8)]))
        tower_ok = style == "naval" or xr.random() < 0.5
        for a_, b_ in spans(yb + 6, yf - 4, top_gaps):
            hull.add(prism(a_, b_, hw * 0.55, hw * 0.38, z_top + 0.4, z_top + 2.2))
        for a_, b_ in spans(yb + 12, yf - 16, top_gaps):
            if tower_ok:
                hull.add(prism(a_, b_, hw * 0.33, hw * 0.24, z_top + 2.2, z_top + 3.4))
            else:                   # the wreck's tower is sheared off: a jagged stump
                hull.add(prism(a_, a_ + (b_ - a_) * 0.4, hw * 0.33, hw * 0.2, z_top + 2.2, z_top + 2.9))
                trim.add(prism(a_ + (b_ - a_) * 0.4, b_, hw * 0.3, hw * 0.05, z_top + 2.2, z_top + 2.6))
        if style == "naval":
            # command tower over the bridge, and white bands round the hull
            tw = hw * 0.22
            hull.add(prism(yf - 15, yf - 7, tw, tw * 0.7, z_top + 2.2, z_top + 5.4))
            glass.add(box(-tw * 0.75, tw * 0.75, yf - 7.05, yf - 6.95, z_top + 4.3, z_top + 4.9))
            for bandy in (yb + 3.0, yf - 2.5):
                accent.add(box(-ox - 0.02, ox + 0.02, bandy, bandy + 1.2, z_top + 0.4, z_top + 0.45))
                for side in (-1, 1):
                    accent.add(box(*sorted((side * ox, side * (ox + 0.04))), bandy, bandy + 1.2, 0.4, z_top))
        lights.add(box(-hw * 0.38 - 0.02, hw * 0.38 + 0.02, yf - 5.2, yf - 4.9, z_top + 1.6, z_top + 1.8))
        details.add(cylinder("z", 0, yb + 9, z_top + 2.2, z_top + 7.0, 0.12, seg=8))
        details.add(box(-1.2, 1.2, yb + 9 - 0.1, yb + 9 + 0.1, z_top + 5.5, z_top + 5.7))

    # side armor: layered plates per level, avoiding the hangar and breach panels
    def blocked(side, k, ya, yb_):
        if k < 0:
            return False                              # the troop deck: solid hull, plate it all
        for (bk, bs, bside) in breach_info:
            c = seg_c(bs)
            if bside == side and bk == k and ya < c + BREACH_W / 2 + 0.8 and yb_ > c - BREACH_W / 2 - 0.8:
                return True
        if n_cargo and side == 1 and k < HD and ya < cargo_y1 + 0.8 and yb_ > cargo_y0 - 0.8:
            return True
        if n_hangar and k < HD and ya < hangar_y1 + 0.8 and yb_ > hangar_y0 - 0.8:
            return True
        for (ak, as_, aside) in airlock_info:
            c = seg_c(as_)
            if aside == side and ak == k and ya < c + AIRLOCK_W / 2 + 1.2 and yb_ > c - AIRLOCK_W / 2 - 1.2:
                return True
        for (ek, es_, eside) in escape_info:
            c = seg_c(es_)
            if eside == side and ek == k and ya < c + 3.6 and yb_ > c - 3.6:
                return True
        return False

    for side in (-1, 1):
        for k in range(-1, levels):
            y = yb + 0.5
            while y < yf - 1:
                ln = xr.uniform(5, 13) if style != "sleek" else xr.uniform(7, 11)
                if style == "scrap":
                    ln = xr.uniform(2.5, 9)
                ya, yb_ = y, min(y + ln, yf - 0.5)
                y = yb_ + (0.35 if style != "scrap" else xr.uniform(0.1, 1.5))
                if blocked(side, k, ya, yb_):
                    continue
                za, zb_ = k * H + 0.5, (k + 1) * H - 0.45
                if style == "sleek":
                    # angled chevron plates: the outer face leans and narrows, with a lit seam
                    def chev(i, ya=ya, yb_=yb_, za=za, zb_=zb_, side=side):
                        outer = i & 1
                        y_ = (ya + (0.8 if outer else 0.0), yb_ - (0.8 if outer else 0.0))[(i >> 1) & 1]
                        z_ = (za + (0.6 if outer else 0.0), zb_ - (0.2 if outer else 0.0))[(i >> 2) & 1]
                        return (side * (ox + (0.55 if outer else 0.0)), y_, z_)
                    armor.add(hexa([chev(i) for i in range(8)]))
                    la_, lb_ = sorted((side * (ox + 0.2), side * (ox + 0.26)))
                    lights.add(box(la_, lb_, ya + 0.6, yb_ - 0.6, za + 0.15, za + 0.25))
                    continue
                if style == "wreck" and xr.random() < 0.4:
                    # plating blown away: a scorched hole with ribs showing
                    ra_, rb_ = sorted((side * (ox - 0.02), side * (ox + 0.02)))
                    accent.add(box(ra_, rb_, ya + 0.5, yb_ - 0.5, za + 0.3, zb_ - 0.3))
                    for rib in range(int((yb_ - ya) // 1.5)):
                        ry = ya + 0.75 + rib * 1.5
                        trim.add(box(*sorted((side * ox, side * (ox + 0.3))), ry - 0.1, ry + 0.1, za, zb_))
                    continue
                pa, pb = sorted((side * ox, side * (ox + (0.35 if style != "scrap" else xr.uniform(0.15, 0.6)))))
                if style == "scrap":
                    za += xr.uniform(-0.3, 0.6)
                    zb_ -= xr.uniform(-0.2, 0.8)
                    (armor if xr.random() < 0.6 else trim).add(box(pa, pb, ya, yb_, za, zb_))
                    if xr.random() < 0.3:            # a rusty patch riveted over the top
                        qa, qb = sorted((side * (pb if side > 0 else pa), side * (abs(pb if side > 0 else pa) + 0.08)))
                        accent.add(box(qa, qb, ya + 0.4, ya + 0.4 + xr.uniform(1, 2.5), za + 0.3, za + 1.5))
                    continue
                armor.add(box(pa, pb, ya, yb_, za, zb_))
                if xr.random() < 0.45 and yb_ - ya > 4:
                    qa, qb = sorted((side * (ox + 0.35), side * (ox + 0.6)))
                    m = xr.uniform(0.6, 1.4)
                    armor.add(box(qa, qb, ya + m, yb_ - m, za + 0.5, zb_ - 0.5))
            if k > 0:   # dark seam band between levels
                ta, tb = sorted((side * ox, side * (ox + 0.5)))
                gaps = []
                if k < HD and n_hangar:
                    gaps.append((hangar_y0 - 0.8, hangar_y1 + 0.8))
                if k < HD and n_cargo and side == 1:
                    gaps.append((cargo_y0 - 0.8, cargo_y1 + 0.8))
                ranges = spans(yb, yf, gaps)
                for ra, rb in ranges:
                    trim.add(box(ta, tb, ra, rb, k * H - 0.35, k * H + 0.1))

    # engines
    eb = yb - 3
    engines.add(box(-ox + 0.3, ox - 0.3, eb, yb, bz, z_top))
    if style == "sleek":
        # two big outboard nacelles on pylons, long glowing exhausts, plus a slim central drive
        nr = min(ox * 0.42, (z_top + 2.0) * 0.45)
        for side in (-1, 1):
            nx_ = side * (ox + nr * 0.9)
            nz_ = z_top * 0.45
            engines.add(cylinder("y", nx_, nz_, eb - 4.0, yb + 14.0, nr, seg=12))
            accent.add(cylinder("y", nx_, nz_, yb + 6.0, yb + 7.0, nr + 0.08, seg=12))
            glow.add(cylinder("y", nx_, nz_, eb - 4.1, eb - 4.0, nr * 0.8, seg=12))
            armor.add(box(*sorted((side * (ox - 0.2), side * (ox + nr * 0.4))), yb + 2, yb + 11, nz_ - 0.4, nz_ + 0.4))
        engines.add(cylinder("y", 0, z_top * 0.45, eb - 2.0, eb + 0.2, min(ox, z_top) * 0.35, seg=12))
        glow.add(cylinder("y", 0, z_top * 0.45, eb - 2.1, eb - 2.0, min(ox, z_top) * 0.28, seg=12))
    else:
        cols, rows = 3, levels + 1
        cs, rs = (2 * ox - 0.6) / cols, (z_top - bz) / rows
        r = min(cs, rs) * 0.38
        for ci in range(cols):
            for ri in range(rows):
                ex = -ox + 0.3 + cs * (ci + 0.5)
                ez = bz + rs * (ri + 0.5)
                rr_ = r
                if style == "scrap":             # mismatched, salvaged drives
                    rr_ = r * xr.uniform(0.55, 1.15)
                    ex += xr.uniform(-0.3, 0.3)
                    ez += xr.uniform(-0.3, 0.3)
                if style == "wreck" and xr.random() < 0.5:
                    engines.add(cylinder("y", ex, ez, eb - 1.0, eb + 0.2, rr_ * 0.9))   # dead, stubby
                    continue
                engines.add(cylinder("y", ex, ez, eb - 2.5, eb + 0.2, rr_))
                engines.add(cylinder("y", ex, ez, eb - 3.1, eb - 2.5, rr_ * 0.9))
                glow.add(cylinder("y", ex, ez, eb - 3.2, eb - 3.1, rr_ * 0.72))
        if style == "scrap":                     # and one huge strapped-on booster
            bs = xr.choice((-1, 1))
            engines.add(cylinder("y", bs * (ox + 1.6), z_top * 0.5, eb - 3.0, yb + 10.0, 1.5))
            glow.add(cylinder("y", bs * (ox + 1.6), z_top * 0.5, eb - 3.1, eb - 3.0, 1.15))
            trim.add(box(*sorted((bs * ox, bs * (ox + 0.4))), yb + 2, yb + 3, z_top * 0.5 - 0.3, z_top * 0.5 + 0.3))
            trim.add(box(*sorted((bs * ox, bs * (ox + 0.4))), yb + 7, yb + 8, z_top * 0.5 - 0.3, z_top * 0.5 + 0.3))

    # turrets: on the superstructure and along the roof edges
    s_t = {"MEDIUM": 1.0, "LARGE": 1.25, "XL": 1.5}.get(cls, 0.85)
    top_z = z_top + 3.4 if style in ("naval", "sleek") else z_top + 2.2
    spots = [(0, yf - 18, top_z, 0.0), (0, yb + 14, top_z, math.pi)]
    if style == "scrap":       # guns bolted wherever there's room
        spots = [(xr.uniform(-hw * 0.3, hw * 0.3), yf - 10, z_top + 0.4, 0.0),
                 (xr.uniform(-hw * 0.3, hw * 0.3), yb + 4, z_top + 0.4, math.pi)]
    edge_n = max(0, cfg["turrets"] - 2)
    for j in range(edge_n):
        side = (-1, 1)[j % 2]
        frac = (j // 2 + 0.5) / max(1, math.ceil(edge_n / 2))
        ty = yb + 8 + frac * (yf - yb - 16)
        spots.append((side * (ox - 1.6), ty, z_top + 0.4, 0.0 if ty > 0 else math.pi))
    turret_xy = []
    for t_i, (tx, ty, tz, rz) in enumerate(spots[:cfg["turrets"]], 1):
        parts.append(turret_part(f"{cls}_Turret_{t_i}", (tx, ty, tz), rz, s_t))
        turret_xy.append((tx, ty))

    # SMALL ship identities
    style = cfg.get("style")
    if style == "frigate":
        # mass-attack missile banks: one block per side (where the hull is free) plus two on the roof
        for side in (-1, 1):
            for s in range(n - 2, aft_segs - 1, -1):
                y0, y1 = seg_y(s)
                if not blocked(side, 0, y0 + 0.5, y1 - 0.5):
                    break
            else:
                continue
            ba, bb = sorted((side * ox, side * (ox + 0.8)))
            armor.add(box(ba, bb, y0 + 0.5, y1 - 0.5, 0.5, H - 0.4))
            for yi in range(int((SEG_LEN - 1.6) // 1.4)):
                for zi in range(2):
                    hy, hz = y0 + 0.9 + yi * 1.4, 0.9 + zi * 1.4
                    ea, eb_ = sorted((side * (ox + 0.8), side * (ox + 0.86)))
                    engines.add(box(ea, eb_, hy, hy + 0.9, hz, hz + 0.9))
            markers.append((f"MissileBank_{'Port' if side < 0 else 'Starboard'}", (side * (ox + 1.0), (y0 + y1) / 2, H / 2)))
        for side in (-1, 1):
            ba, bb = sorted((side * (hw * 0.6), side * (ox - 0.4)))
            armor.add(box(ba, bb, yb + 1.5, yb + 8.5, z_top + 0.4, z_top + 1.0))
            for yi in range(4):
                for xi in range(2):
                    hx = side * (hw * 0.6 + 0.3 + xi * 0.95)
                    engines.add(box(*sorted((hx, hx + side * 0.75)), yb + 2 + yi * 1.6, yb + 2.75 + yi * 1.6,
                                    z_top + 1.0, z_top + 1.06))
        markers.append(("MissileBank_Dorsal", (0, yb + 5, z_top + 1.1)))
    elif style == "support":
        # fuel / cargo tanks along the roof either side of the spine, comms dish aft
        tz = z_top + 0.4 + 1.2
        for side in (-1, 1):
            tx = side * (hw * 0.55 + 1.6)
            for t0 in range(int(yb + 8), int(yf - 14), 11):
                armor.add(cylinder("y", tx, tz, t0, t0 + 9, 1.2))
                for ry in (t0 + 0.6, t0 + 8.4):
                    trim.add(cylinder("y", tx, tz, ry - 0.25, ry + 0.25, 1.3))
        trim.add(cylinder("z", 0, yb + 5, z_top + 0.4, z_top + 2.6, 0.25, seg=8))
        armor.add(cylinder("z", 0, yb + 5, z_top + 2.6, z_top + 2.8, 2.2, seg=20))
        markers += [("DockingClamp_Port", (-(ox + 6), 0, 0)), ("DockingClamp_Starboard", (ox + 6, 0, 0))]
    elif style == "paris":
        # long dorsal gun spine running out over the nose, and big outboard engine nacelles
        armor.add(box(-0.8, 0.8, yb + 4, yf + prow * 0.55, z_top + 2.2, z_top + 3.0))
        engines.add(box(-0.5, 0.5, yf + prow * 0.55, yf + prow * 0.55 + 0.4, z_top + 2.35, z_top + 2.85))
        markers.append(("SpineGunMuzzle", (0, yf + prow * 0.55 + 0.6, z_top + 2.6)))
        for side in (-1, 1):
            nx = side * (ox + 1.4)
            engines.add(cylinder("y", nx, 1.6, yb - 6.0, yb + 7.0, 1.6))
            glow.add(cylinder("y", nx, 1.6, yb - 6.1, yb - 6.0, 1.25))
            pa, pb = sorted((side * ox, side * (ox + 0.6)))
            armor.add(box(pa, pb, yb + 1.0, yb + 6.0, 1.0, 2.2))           # pylon
            armor.add(wing(side, ox, ox + 4.0, (yb - 2, yb + 6), (yb - 4, yb - 1), H + 0.2, H - 0.4, 0.3, 0.12))

    # roof greebles
    placed, tries = 0, 0
    while placed < 14 * levels and tries < 2000:
        tries += 1
        x = rng.uniform(-ox + 0.6, ox - 0.6)
        y = rng.uniform(yb + 1, yf - 3)
        w, l, h = rng.uniform(0.5, 1.8), rng.uniform(0.6, 3.0), rng.uniform(0.15, 0.5)
        if abs(x) < hw * 0.55 + w / 2 + 0.2 and yb + 6 < y < yf - 4:
            continue
        if any(math.hypot(x - a, y - b) < 2.6 * s_t for a, b in turret_xy):
            continue
        details.add(box(x - w / 2, x + w / 2, y - l / 2, y + l / 2, z_top + 0.4, z_top + 0.4 + h))
        placed += 1

    # ---------- compartment zones: one box per compartment per deck, for infection
    # spread, alarms and evac logic (the 3rd value is the box's half-size)
    zones = {}
    for k in range(levels):
        for s in range(n):
            t = stype(k, s)
            if t == "void" or (t in ("hangar", "reactor", "cargo") and k > 0):
                continue
            ztop = HD * H if t in ("hangar", "reactor", "cargo") else (k + 1) * H
            y0, y1 = seg_y(s)
            key = (comp(s), k)
            if key in zones:
                zy0, zy1, _, _ = zones[key]
                zones[key] = (min(zy0, y0), max(zy1, y1), k * H, ztop)
            else:
                zones[key] = (y0, y1, k * H, ztop)
    for (c, k), (zy0, zy1, zz0, zz1) in sorted(zones.items()):
        markers.append((f"Zone_C{c}_D{k}", (0, (zy0 + zy1) / 2, (zz0 + zz1) / 2),
                        (hw, (zy1 - zy0) / 2, (zz1 - zz0) / 2)))

    parts = [p for p in parts if p.verts]
    stats = dict(
        ship_class=cls, length_m=round((yf + prow) - (eb - 3.2), 1), decks=decks,
        standard_crew=STANDARD_CREW[SIZE_CLASS[cls]], capacity=capacity(cls),
        loadout=resolve_loadout(cls),
        bunks_modeled=crew_berths + troop_berths, crew_berths=crew_berths, troop_berths=troop_berths,
        escape_pods=pod_i, escape_pod_seats=pod_i * 4,
        compartments=len({c for c, _ in zones}), blast_doors=sum(1 for d in doors if d[1] != d[2]),
        elevators=len(shafts), ramps=len(ramps), breach_zones=len(breach_info),
        hangar_landing_pads=n_hangar, airlocks=len(airlock_info), turrets=cfg["turrets"],
        boarding_pod_tubes=2 * n_side + n_dorsal, drop_pod_tubes=n_drop,
        cargo_bay_darter_pads=n_cargo, cargo_storage_slots=storage_slots,
        supply_depot=bool(cfg.get("supply_depot")),
        medbays=counters.get("medbay", 0), armories=counters.get("armory", 0),
        ready_lockers=ready_lockers,
        breachable_walls=sum(1 for b in breachables if b[1] == "BreachWall"),
        locked_doors=sum(1 for b in breachables if b[1] == "BreachDoor"),
        rooms={r: c for r, c in sorted(counters.items())},
    )
    info = dict(cls=cls, decks=decks, levels=levels, hw=hw, ox=ox, y_back=y_back, y_front=y_front,
                yb=yb, yf=yf, z_top=z_top, length=(yf + prow) - (eb - 3.2), width=2 * ox + 4.4,
                breaches=breach_info, ramps=ramps, n=n, aft_segs=aft_segs,
                hangar=(hangar_y0, hangar_y1), seg_y=seg_y, seg_c=seg_c, stype=stype,
                room_role=room_role, comp=comp, doors=doors, stats=stats)
    return parts, markers, info


# =========================================================================
# XS craft: fighter, boarding dropship, boarding pod
# =========================================================================

def _craft_parts(cls, names):
    """Make the standard set of parts for a craft, keyed by short name."""
    mats = {"hull": ("Hull-col", "Hull"), "armor": ("Armor", "Armor"), "trim": ("Trim", "Trim"),
            "engines": ("Engines", "Engine"), "glow": ("EngineGlow", "EngineGlow"),
            "glass": ("Glass-col", "Glass"), "lights": ("Lights", "Lights"),
            "hazard": ("Hazard", "Hazard"), "cover": ("Interior-col", "Cover")}
    return {n: Part(f"{cls}_{mats[n][0]}", mats[n][1]) for n in names}


def generate_fighter(cls):
    p = _craft_parts(cls, ["hull", "armor", "trim", "engines", "glow", "glass", "lights"])
    hull, armor, trim, eng, glow = p["hull"], p["armor"], p["trim"], p["engines"], p["glow"]
    hull.add(taper(-5.0, 6.0, (1.3, -0.6, 0.9), (0.35, -0.25, 0.25)))           # fuselage
    armor.add(prism(-5.0, 0.8, 0.9, 0.5, 0.9, 1.3))                            # spine
    p["glass"].add(taper(0.8, 3.8, (0.5, 0.5, 1.15), (0.3, 0.33, 0.55)))       # canopy
    eng.add(box(-1.5, 1.5, -7.0, -4.5, -0.6, 0.85))                            # engine block
    for side in (-1, 1):
        eng.add(cylinder("y", side * 0.75, 0.12, -7.6, -7.0, 0.6))
        glow.add(cylinder("y", side * 0.75, 0.12, -7.7, -7.6, 0.45))
        hull.add(wing(side, 1.1, 6.5, (-5.2, 0.5), (-6.6, -4.8), -0.1, -0.35, 0.35, 0.12))
        armor.add(wing(side, 1.0, 2.4, (-6.8, -4.6), (-7.4, -6.4), 0.9, 2.3, 0.18, 0.1))  # canted fins
        xa, xb = sorted((side * 6.3, side * 6.7))
        trim.add(box(xa, xb, -6.8, -3.5, -0.45, -0.2))                         # wingtip rails
        ga, gb = sorted((side * 0.35, side * 0.55))
        eng.add(box(ga, gb, 4.0, 7.2, -0.3, -0.12))                            # nose guns
        ia, ib = sorted((side * 1.0, side * 1.35))
        trim.add(box(ia, ib, -2.0, 0.6, -0.45, 0.35))                          # intakes
        la, lb = sorted((side * 6.4, side * 6.6))
        p["lights"].add(box(la, lb, -4.75, -4.6, -0.42, -0.25))
    markers = [("PilotSeat", (0, 2.2, 0.4)), ("Gun_Left", (-0.45, 7.3, -0.2)),
               ("Gun_Right", (0.45, 7.3, -0.2)), ("Missile_Left", (-6.5, -3.4, -0.33)),
               ("Missile_Right", (6.5, -3.4, -0.33))]
    return list(p.values()), markers


DROPSHIP_DOOR_Y = -5.0


def generate_dropship(cls):
    p = _craft_parts(cls, ["hull", "armor", "trim", "engines", "glow", "glass", "lights", "cover"])
    hull, armor, trim, eng, glow = p["hull"], p["armor"], p["trim"], p["engines"], p["glow"]
    y0, y1 = DROPSHIP_DOOR_Y, 3.0
    # walkable troop bay (inside: 3.2 m wide, 2.4 m tall)
    hull.add(box(-1.75, 1.75, y0, y1, -0.2, 0))
    hull.add(box(-1.75, 1.75, y0, y1, 2.4, 2.6))
    hull.add(box(-1.75, 1.75, y1, y1 + 0.15, 0, 2.4))
    for side in (-1, 1):
        xa, xb = sorted((side * 1.6, side * 1.75))
        hull.add(box(xa, xb, y0, y1, 0, 2.4))
        ba, bb = sorted((side * 1.1, side * 1.6))
        p["cover"].add(box(ba, bb, y0 + 1.0, y1 - 0.5, 0, 0.5))                # benches
    armor.add(prism(y0, y1, 1.9, 1.4, 2.6, 3.2))                               # roof hump
    armor.add(prism(y0, y1, 1.4, 1.9, -0.8, -0.2))                             # belly
    # rear ramp: separate object, pivot on the hinge, modeled closed
    ramp = Part(f"{cls}_Ramp-col", "Hull", origin=(0, y0, 0))
    ramp.add(box(-1.6, 1.6, -0.15, 0, 0, 2.4))
    # cockpit nose and canopy
    hull.add(taper(y1, 8.0, (1.9, -0.8, 3.2), (0.7, -0.3, 1.6)))
    p["glass"].add(taper(3.5, 6.8, (1.4, 2.8, 3.4), (0.6, 1.8, 2.15)))
    for side in (-1, 1):
        hull.add(wing(side, 1.9, 4.2, (-2.5, 1.0), (-2.2, 0.4), 1.4, 1.6, 0.35, 0.25))
        ea, eb = sorted((side * 3.7, side * 4.7))
        eng.add(box(ea, eb, -3.0, 1.5, 0.9, 2.2))                              # engine pods
        ga, gb = sorted((side * 3.85, side * 4.55))
        glow.add(box(ga, gb, -3.05, -3.0, 1.05, 2.05))
        glow.add(box(ga, gb, -2.6, 1.1, 0.85, 0.9))                            # lift jets
        fa, fb = sorted((side * 1.1, side * 1.3))
        armor.add(box(fa, fb, y0, y0 + 1.8, 3.2, 4.4))                         # tail fins
        sa, sb = sorted((side * 1.2, side * 1.5))
        trim.add(box(sa, sb, -4.0, 2.0, -1.2, -1.0))                           # skids
        trim.add(box(sa, sb, -3.2, -2.8, -1.0, -0.8))
        trim.add(box(sa, sb, 1.0, 1.4, -1.0, -0.8))
        na, nb = sorted((side * 0.15, side * 0.35))
        eng.add(box(na, nb, 7.5, 9.0, -0.15, 0.05))                            # nose guns
        la, lb = sorted((side * 1.75, side * 1.8))
        p["lights"].add(box(la, lb, y0 + 0.3, y0 + 0.5, 0.2, 2.2))
    markers = [("PilotSeat", (0, 5.0, 0.6)), ("RampExit", (0, y0 - 3.0, 0.05)),
               ("Gun_Nose", (0, 9.1, -0.05))]
    for i in range(12):                                    # a 12-soldier squad
        side = (-1, 1)[i % 2]
        markers.append((f"Seat_{i + 1}", (side * 1.35, y0 + 1.4 + (i // 2) * 1.05, 0.5)))
    return list(p.values()) + [ramp], markers


POD_R, POD_T = 1.45, 0.12          # outer radius (to corners) and wall thickness
POD_CZ = (POD_R - POD_T) * math.cos(math.pi / 8)   # puts the inside floor at z = 0


def generate_pod(cls):
    p = _craft_parts(cls, ["hull", "trim", "engines", "glow", "hazard", "cover", "lights"])
    hull, eng, glow, hz = p["hull"], p["engines"], p["glow"], p["hazard"]
    y0, y1, cz, r = -3.0, 2.6, POD_CZ, POD_R          # room for 8 troops
    hull.add_many(oct_shell(y0, y1, cz, r, POD_T))
    hull.add(cylinder("y", 0, cz, y0 - 0.3, y0, r, seg=8, phase=math.pi / 8))   # rear wall
    hatch = Part(f"{cls}_Hatch-col", "BreachPanel")
    hatch.add(cylinder("y", 0, cz, y1, y1 + 0.25, r, seg=8, phase=math.pi / 8))
    # breaching ram: hazard collar and four claws around the nose
    hz.add_many(oct_shell(y1 - 0.4, y1 + 0.3, cz, r + 0.12, 0.25))
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        cx, cz2 = (r - 0.15) * math.cos(a), cz + (r - 0.15) * math.sin(a)
        hz.add(hexa([(cx + (-1, 1)[i & 1] * (0.04 if (i >> 1) & 1 else 0.16),
                      (y1 + 0.3, y1 + 1.0)[(i >> 1) & 1],
                      cz2 + (-1, 1)[(i >> 2) & 1] * (0.04 if (i >> 1) & 1 else 0.16)) for i in range(8)]))
    # thruster and four stabilizer fins (+X, -X, +Z, -Z)
    eng.add(cylinder("y", 0, cz, y0 - 1.2, y0 - 0.3, 1.0))
    glow.add(cylinder("y", 0, cz, y0 - 1.3, y0 - 1.2, 0.75))
    for side in (-1, 1):
        p["trim"].add(box(*sorted((side * 0.9, side * (r + 0.1))), y0 - 1.1, y0 + 0.4, cz - 0.04, cz + 0.04))
        p["trim"].add(box(-0.04, 0.04, y0 - 1.1, y0 + 0.4, *sorted((cz + side * 0.9, cz + side * (r + 0.1)))))
    # seats: 4 a side, facing in
    for side in (-1, 1):
        sa, sb = sorted((side * 0.7, side * 1.1))
        p["cover"].add(box(sa, sb, y0 + 0.2, y1 - 0.6, 0, 0.5))
        la, lb = sorted((side * 0.3, side * 0.6))
        p["lights"].add(box(la, lb, y0 + 0.3, y1 - 0.3, 2.38, 2.42))
    markers = [("ExitPoint", (0, y1 + 1.5, 0.05)), ("ImpactPoint", (0, y1 + 1.0, cz))]
    for i in range(8):
        side = (-1, 1)[i % 2]
        markers.append((f"Seat_{i + 1}", (side * 0.9, y0 + 0.8 + (i // 2) * 1.35, 0.5)))
    return list(p.values()) + [hatch], markers


def generate_bomber(cls):
    p = _craft_parts(cls, ["hull", "armor", "trim", "engines", "glow", "glass", "lights"])
    hull, armor, trim, eng, glow = p["hull"], p["armor"], p["trim"], p["engines"], p["glow"]
    hull.add(taper(-6.0, 6.5, (1.8, -0.9, 1.1), (0.6, -0.4, 0.4)))             # fuselage
    armor.add(prism(-6.0, 1.0, 1.3, 0.8, 1.1, 1.6))                            # spine
    p["glass"].add(taper(1.0, 4.6, (0.75, 0.65, 1.45), (0.45, 0.45, 0.75)))    # two-seat canopy
    eng.add(box(-1.3, 1.3, -7.0, -5.5, -0.7, 1.0))
    bay = Part(f"{cls}_BombBayDoors", "Trim")                                  # open these to drop
    bay.add(box(-0.95, 0.95, -3.2, 2.2, -1.0, -0.9))
    for side in (-1, 1):
        hull.add(wing(side, 1.5, 6.4, (-5.0, 1.2), (-5.6, -3.2), -0.2, -0.35, 0.45, 0.18))
        nx = side * 2.7
        eng.add(cylinder("y", nx, -0.55, -6.6, -0.8, 0.85))                   # engine nacelles
        glow.add(cylinder("y", nx, -0.55, -6.7, -6.6, 0.65))
        armor.add(wing(side, 0.9, 2.2, (-7.0, -5.0), (-7.6, -6.6), 1.4, 2.6, 0.18, 0.1))   # twin tails
        ga, gb = sorted((side * 0.45, side * 0.65))
        eng.add(box(ga, gb, 5.0, 7.4, -0.55, -0.35))                          # nose guns
        la, lb = sorted((side * 6.3, side * 6.5))
        p["lights"].add(box(la, lb, -5.45, -5.3, -0.45, -0.3))
        for k in range(2):                                                    # wing hardpoints
            hx = side * (3.8 + k * 1.2)
            trim.add(box(hx - 0.12, hx + 0.12, -4.4, -1.6, -0.75, -0.45))
    markers = [("PilotSeat", (0, 3.6, 0.5)), ("BombardierSeat", (0, 2.2, 0.5)),
               ("BombRelease", (0, -0.5, -1.2)), ("Gun_Left", (-0.55, 7.5, -0.45)),
               ("Gun_Right", (0.55, 7.5, -0.45))]
    for side, nm in ((-1, "Left"), (1, "Right")):
        for k in range(2):
            markers.append((f"Hardpoint_{nm}_{k + 1}", (side * (3.8 + k * 1.2), -3.0, -0.9)))
    return list(p.values()) + [bay], markers


def generate_darter(cls):
    """Darter-inspired cargo / crew transfer ferry. 2 crew; the hold takes 4 cargo
    pallets or 6 armed soldiers; rear ramp. Lands sideways in any cargo bay."""
    p = _craft_parts(cls, ["hull", "armor", "trim", "engines", "glow", "glass", "lights", "cover", "hazard"])
    hull, armor, trim, eng, glow = p["hull"], p["armor"], p["trim"], p["engines"], p["glow"]
    y0, y1 = -4.6, 1.4                                  # hold: 2.9 m wide, 2.1 m tall inside
    hull.add(box(-1.6, 1.6, y0, y1, -0.15, 0))
    hull.add(box(-1.6, 1.6, y0, y1, 2.1, 2.3))
    hull.add(box(-1.6, 1.6, y1, y1 + 0.15, 0, 2.1))
    for side in (-1, 1):
        hull.add(box(*sorted((side * 1.45, side * 1.6)), y0, y1, 0, 2.1))
        p["cover"].add(box(*sorted((side * 1.0, side * 1.45)), y0 + 0.4, y0 + 3.0, 0, 0.45))   # 3 seats a side
    armor.add(prism(y0, y1 + 0.15, 1.75, 1.3, 2.3, 2.65))                     # roof hump
    armor.add(prism(y0, y1 + 0.15, 1.3, 1.75, -0.4, -0.15))                   # belly
    ramp = Part(f"{cls}_Ramp-col", "Hull", origin=(0, y0, 0))                 # hinge; rotate on X to open
    ramp.add(box(-1.45, 1.45, -0.12, 0, 0, 2.1))
    hull.add(taper(y1 + 0.15, 5.0, (1.75, -0.4, 2.65), (0.9, -0.2, 1.3)))      # cockpit nose
    p["glass"].add(taper(2.0, 3.9, (1.3, 1.9, 2.6), (0.75, 1.3, 1.75)))
    for side in (-1, 1):
        for yc in (-3.4, 0.6):                                                # four swivel thrusters
            tx = side * 2.35
            eng.add(cylinder("y", tx, 1.3, yc - 0.9, yc + 0.9, 0.62))
            glow.add(cylinder("y", tx, 1.3, yc - 0.95, yc - 0.9, 0.48))
            glow.add(box(tx - 0.35, tx + 0.35, yc - 0.5, yc + 0.5, 0.64, 0.68))   # lift jet
            armor.add(box(*sorted((side * 1.6, side * 1.8)), yc - 0.35, yc + 0.35, 1.05, 1.55))
        trim.add(box(*sorted((side * 1.0, side * 1.25)), -4.0, 1.6, -0.55, -0.4))  # skids
        p["lights"].add(box(*sorted((side * 1.6, side * 1.63)), y0 + 0.2, y0 + 0.4, 0.3, 1.8))
    for (cx_, cy_) in ((-0.6, y0 + 3.9), (0.6, y0 + 3.9), (-0.6, y0 + 5.1), (0.6, y0 + 5.1)):
        p["hazard"].add(box(cx_ - 0.5, cx_ + 0.5, cy_ - 0.52, cy_ - 0.5, 0, 0.02))
    markers = [("PilotSeat", (-0.45, 3.0, 0.6)), ("CoPilotSeat", (0.45, 3.0, 0.6)),
               ("RampExit", (0, y0 - 2.5, 0.05))]
    for i in range(6):
        side = (-1, 1)[i % 2]
        markers.append((f"Seat_{i + 1}", (side * 1.2, y0 + 0.85 + (i // 2) * 0.85, 0.45)))
    for i, (cx_, cy_) in enumerate(((-0.6, y0 + 3.9), (0.6, y0 + 3.9), (-0.6, y0 + 5.1), (0.6, y0 + 5.1)), 1):
        markers.append((f"CargoSlot_{i}", (cx_, cy_, 0.05)))
    return list(p.values()) + [ramp], markers


def _drone_solids(ox=0.0, oy=0.0, oz=0.0):
    """Mining drone geometry as (material, solid) pairs, offset by (ox, oy, oz)."""
    def mv(solid):
        v, f = solid
        return [(x + ox, y + oy, z + oz) for x, y, z in v], f
    out = [("Armor", box(-0.5, 0.5, -0.6, 0.6, -0.25, 0.25)),
           ("Trim", box(-0.35, 0.35, -0.5, 0.0, -0.55, -0.25)),                     # ore bin
           ("Engine", box(-0.06, 0.06, 0.2, 0.9, -0.45, -0.3)),                     # cutting laser
           ("EngineGlow", box(-0.05, 0.05, 0.9, 0.95, -0.44, -0.31))]
    for sx in (-1, 1):
        for sy in (-1, 1):
            out.append(("Trim", box(*sorted((sx * 0.45, sx * 0.85)), *sorted((sy * 0.45, sy * 0.85)), -0.05, 0.05)))
            out.append(("Engine", cylinder("z", sx * 0.85, sy * 0.85, -0.15, 0.15, 0.28, seg=10)))
            out.append(("EngineGlow", cylinder("z", sx * 0.85, sy * 0.85, -0.2, -0.15, 0.2, seg=10)))
    out.append(("Lights", box(-0.15, 0.15, 0.6, 0.62, 0.0, 0.1)))
    return [(m, mv(sol)) for m, sol in out]


def generate_mining_drone(cls):
    """~2.4 m mining drone: four thrusters, a cutting laser and an ore bin."""
    parts = {}
    for mat, sol in _drone_solids():
        name = "Hull-col" if mat == "Armor" else mat
        parts.setdefault(mat, Part(f"{cls}_{name}", mat)).add(sol)
    markers = [("Laser", (0, 0.97, -0.38)), ("Dock", (0, 0, 0.3)), ("OreBin", (0, -0.25, -0.55))]
    return list(parts.values()), markers


def generate_miner(cls):
    """~16 m mining ship: ore hold, a mining laser turret under the nose and four
    docked mining drones. Fills its hold, then docks to unload through its belly chute."""
    p = _craft_parts(cls, ["hull", "armor", "trim", "engines", "glow", "glass", "lights", "hazard"])
    hull, armor, trim, eng, glow = p["hull"], p["armor"], p["trim"], p["engines"], p["glow"]
    hull.add(box(-2.4, 2.4, -6.0, 3.0, -1.6, 1.6))                               # ore hold
    hull.add(taper(3.0, 7.5, (1.8, -1.2, 1.4), (0.8, -0.6, 0.6)))                 # cockpit
    p["glass"].add(taper(3.4, 6.2, (1.2, 1.0, 1.75), (0.6, 0.4, 0.95)))
    hatch = Part(f"{cls}_HoldHatch-col", "Trim")                                  # opens to load / unload
    hatch.add(box(-2.0, 2.0, -5.5, 2.5, 1.6, 1.75))
    eng.add(box(-0.6, 0.6, -2.0, 0.0, -2.0, -1.6))                                # unload chute
    p["hazard"].add(box(-0.7, 0.7, -2.1, -2.0, -2.0, -1.6))
    p["hazard"].add(box(-0.7, 0.7, 0.0, 0.1, -2.0, -1.6))
    laser = Part(f"{cls}_MiningLaser", "Engine", origin=(0, 5.0, -1.0))            # turret: pivots at the top
    laser.add(cylinder("z", 0, 0, -0.45, 0.0, 0.5))
    laser.add(box(-0.15, 0.15, 0.0, 2.6, -0.6, -0.3))
    laser_tip = Part(f"{cls}_MiningLaser_Tip", "EngineGlow", origin=(0, 5.0, -1.0))
    laser_tip.add(cylinder("y", 0, -0.45, 2.6, 2.7, 0.12, seg=10))
    drones = []
    racks = [(-3.0, -4.0), (-3.0, -0.8), (3.0, -4.0), (3.0, -0.8)]
    for i, (dx, dy) in enumerate(racks, 1):
        ra, rb = sorted((dx * 0.8, dx * 1.18))
        trim.add(box(ra, rb, dy - 1.0, dy + 1.0, 0.25, 0.45))                     # cradle
        trim.add(box(*sorted((dx * 0.8, dx * 0.8 + (0.1 if dx > 0 else -0.1))), dy - 1.0, dy + 1.0, -0.6, 0.45))
        d = Part(f"{cls}_Drone_{i}", "Armor", origin=(dx, dy, 0.95))              # launch these in-game
        for mat, sol in _drone_solids():
            d.add(sol)
        drones.append(d)
    eng.add(box(-2.0, 2.0, -7.0, -6.0, -1.2, 1.2))
    for sx in (-1, 1):
        eng.add(cylinder("y", sx * 1.0, 0.0, -7.8, -7.0, 0.8))
        glow.add(cylinder("y", sx * 1.0, 0.0, -7.9, -7.8, 0.6))
        armor.add(box(*sorted((sx * 2.4, sx * 2.6)), -5.6, 2.6, -1.3, -0.2))     # side plates
        p["lights"].add(box(*sorted((sx * 2.6, sx * 2.62)), 2.0, 2.3, 0.6, 0.9))
    markers = [("PilotSeat", (0, 5.0, 0.4)), ("CoPilotSeat", (0, 4.0, 0.4)), ("EngineerSeat", (0, 3.4, 0.4)),
               ("LaserMuzzle", (0, 7.75, -1.45)), ("UnloadPort", (0, -1.0, -2.1)), ("DockPort", (0, -1.5, 1.8))]
    markers += [(f"DroneBay_{i}", (dx, dy, 0.95)) for i, (dx, dy) in enumerate(racks, 1)]
    return list(p.values()) + [hatch, laser, laser_tip] + drones, markers


def _shell_up(z0, z1, r, t):
    """Hollow octagonal tube standing upright (axis along Z), as 8 panels.
    Panel 1 faces +Y (used as the door)."""
    out = []
    for v, f in oct_shell(z0, z1, 0.0, r, t):
        nv = [(x, zz, yy) for x, yy, zz in v]          # swap Y and Z
        out.append((nv, _orient_faces(nv, f)))
    return out


def generate_droppod(cls):
    """Single-trooper ODST-style drop pod, standing nose-down: cone at the
    bottom (z=0), seat inside, door on the +Y side that blows off on landing."""
    p = _craft_parts(cls, ["hull", "armor", "trim", "engines", "glow", "hazard", "lights"])
    hull, armor, trim, eng, hz = p["hull"], p["armor"], p["trim"], p["engines"], p["hazard"]
    r, t = 0.9, 0.08
    b0, b1 = 0.9, 3.0                                   # body (hollow) from 0.9 m to 3.0 m
    shell = _shell_up(b0, b1, r, t)
    door = Part(f"{cls}_Door-col", "Armor")             # free/launch this on landing
    for k, solid in enumerate(shell):
        (door if k == 1 else hull).add(solid)
    hull.add(cylinder("z", 0, 0, b0 - 0.1, b0, r, seg=8, phase=math.pi / 8))           # floor
    hull.add(cylinder("z", 0, 0, b1, b1 + 0.15, r, seg=8, phase=math.pi / 8))          # roof
    # nose cone (impact end) as a tapered octagon, and an ablative ring
    cone = []
    for i in range(8):
        a0 = math.pi / 8 + i * math.pi / 4
        cone.append((0.35 * math.cos(a0), 0.35 * math.sin(a0), 0.0))
    for i in range(8):
        a0 = math.pi / 8 + i * math.pi / 4
        cone.append((r * math.cos(a0), r * math.sin(a0), b0 - 0.1))
    faces = [(k, (k + 1) % 8, 8 + (k + 1) % 8, 8 + k) for k in range(8)] + [tuple(range(8)), tuple(range(8, 16))]
    armor.add((cone, _orient_faces(cone, faces)))
    eng.add(cylinder("z", 0, 0, -0.05, 0.0, 0.3, seg=8))
    hz.add(cylinder("z", 0, 0, b0 + 0.1, b0 + 0.25, r + 0.06, seg=8, phase=math.pi / 8))
    # top: four stabilizer fins (kept inside the tube width) and braking thrusters
    for side in (-1, 1):
        trim.add(box(*sorted((side * (r - 0.25), side * r)), -0.04, 0.04, b1 - 0.7, b1 + 0.3))
        trim.add(box(-0.04, 0.04, *sorted((side * (r - 0.25), side * r)), b1 - 0.7, b1 + 0.3))
    for k in range(4):
        a = k * math.pi / 2
        eng.add(cylinder("z", 0.5 * math.cos(a), 0.5 * math.sin(a), b1 + 0.15, b1 + 0.45, 0.14, seg=8))
        p["glow"].add(cylinder("z", 0.5 * math.cos(a), 0.5 * math.sin(a), b1 + 0.45, b1 + 0.48, 0.1, seg=8))
    p["lights"].add(box(-0.3, 0.3, -0.05, 0.05, b1 - 0.1, b1 - 0.05))
    markers = [("Seat_1", (0, -0.1, b0 + 0.05)), ("ExitPoint", (0, 1.8, 0.05)), ("ImpactPoint", (0, 0, 0))]
    return list(p.values()) + [door], markers


def generate(cls):
    """Build any class. Returns (parts, markers, info)."""
    if cls in CLASSES:
        return generate_ship(cls)
    if cls in STATION_KITS or cls.startswith("MODULE_"):
        parts, markers, extra = generate_station(cls)
        parts = [q for q in parts if q.verts]
        pts = [v for q in parts for v in _world_verts(q)]
        info = dict(cls=cls, width=max(v[0] for v in pts) - min(v[0] for v in pts),
                    length=max(v[1] for v in pts) - min(v[1] for v in pts),
                    height=max(v[2] for v in pts) - min(v[2] for v in pts))
        info["stats"] = dict(station=cls, modules=extra["modules"], length_m=round(info["length"], 1),
                             width_m=round(info["width"], 1))
        return parts, markers, info
    rng = random.Random(f"{SEED}-{cls}")
    builders = {"XS_FIGHTER": generate_fighter, "XS_BOMBER": generate_bomber, "XS_DROPSHIP": generate_dropship,
                "XS_POD": generate_pod, "XS_DROPPOD": generate_droppod, "XS_DARTER": generate_darter,
                "XS_MINER": generate_miner, "XS_MINING_DRONE": generate_mining_drone}
    parts, markers = builders[cls](cls)
    parts = [q for q in parts if q.verts]
    pts = [v for q in parts for v in _world_verts(q)]
    info = dict(cls=cls, width=max(v[0] for v in pts) - min(v[0] for v in pts),
                length=max(v[1] for v in pts) - min(v[1] for v in pts),
                height=max(v[2] for v in pts) - min(v[2] for v in pts))
    seats = sum(1 for m in markers if m[0].startswith("Seat_"))
    info["stats"] = dict(ship_class=cls, length_m=round(info["length"], 1),
                         crew=XS_CREW[cls], passenger_seats=seats)
    return parts, markers, info


# =========================================================================
# STATIONS: every module is a boardable building; stations, outposts and ground
# bases are modules hung off a spine of hub junctions joined by walkable tubes.
# =========================================================================
#
# Every module has (module axis along local +Y, deck floor at z = 0):
#   * a CREW SECTION at the front: corridor, CONTROL ROOM (the capture point and
#     on/off console) and a crew room with a ready locker
#   * a MACHINE HALL behind it, full module height, with the module's machinery
#   * SABOTAGE POINTS (junction boxes on the machinery) with charge markers
#   * two side AIRLOCKS (outer doors closed) for EVA boarders
#   * CONNECTOR DOORS at both ends (closed panels; open = hide the panel)
#   * a zone box for infection / alarms, and a StatusLight on the roof
# Station doors are closed panels with collision: to open one, hide it and turn
# off its collision (godot/ship_helpers.gd: set_door()).

# name: (sections, decks, sabotage_points) - must match economy/economy_data.py MODULES
MODULE_SPECS = {
    "command_core": (3, 2, 3), "outpost_core": (2, 1, 2), "reactor": (2, 2, 3), "mining_rig": (2, 1, 2),
    "gas_skimmer": (2, 1, 2), "refinery": (2, 2, 3), "breeder_reactor": (2, 2, 3), "fabricator": (2, 1, 2),
    "core_foundry": (2, 2, 3), "assembly_plant": (2, 1, 2), "shipyard_small": (3, 1, 3),
    "shipyard_medium": (4, 2, 4), "shipyard_large": (5, 2, 5), "storage_depot": (2, 1, 1),
    "fuel_depot": (2, 1, 2), "docking_ring": (2, 1, 1), "barracks": (2, 2, 1), "defense_platform": (1, 1, 2),
    "shield_generator": (2, 1, 2), "comm_relay": (1, 1, 1), "ground_core": (2, 1, 2), "surface_drill": (1, 1, 2),
    "ground_battery": (1, 1, 2), "landing_pads": (1, 1, 1),
}
GROUND_MODULES = {"ground_core", "surface_drill", "ground_battery", "landing_pads"}
STATION_KITS = {   # must match economy_data.py HOME_STATION / CONSTRUCTION kits
    "STATION_HOME": ["command_core", "reactor", "reactor", "reactor", "refinery", "breeder_reactor", "fabricator",
                     "core_foundry", "assembly_plant", "shipyard_small", "shipyard_medium", "storage_depot",
                     "fuel_depot", "docking_ring", "barracks", "defense_platform", "defense_platform",
                     "shield_generator", "comm_relay"],
    "STATION_INDUSTRIAL": ["command_core", "reactor", "reactor", "refinery", "shipyard_medium", "core_foundry",
                           "docking_ring"],
    "STATION_FORTRESS": ["command_core", "reactor", "reactor", "defense_platform", "defense_platform",
                         "shield_generator", "barracks", "docking_ring"],
    "STATION_FUEL_HUB": ["command_core", "reactor", "breeder_reactor", "fuel_depot", "storage_depot", "docking_ring"],
    # campaign: the player's station grows through these stages
    "STATION_STARTER": ["command_core", "reactor", "refinery", "fabricator", "docking_ring"],
    "STATION_STARTER_2": ["command_core", "reactor", "refinery", "fabricator", "docking_ring", "barracks",
                          "storage_depot", "assembly_plant"],
    "STATION_STARTER_3": ["command_core", "reactor", "reactor", "refinery", "fabricator", "docking_ring", "barracks",
                          "storage_depot", "assembly_plant", "shipyard_small", "defense_platform", "shield_generator"],
    "OUTPOST_MINING": ["outpost_core", "mining_rig"],
    "OUTPOST_SKIMMER": ["outpost_core", "gas_skimmer"],
    "GROUND_MINE": ["ground_core", "surface_drill"],
    "GROUND_FORT": ["ground_core", "ground_battery", "landing_pads"],
}
STATION_CLASSES = list(STATION_KITS) + [f"MODULE_{m}" for m in MODULE_SPECS]
MOD_HW, MOD_OX = 8.5, 9.0            # module interior half-width, outer hull half-width
MOD_CODE = {   # short codes keep object names under Blender's 63-character limit
    "command_core": "CMD", "outpost_core": "OUT", "reactor": "RCT", "mining_rig": "MIN", "gas_skimmer": "GAS",
    "refinery": "REF", "breeder_reactor": "BRD", "fabricator": "FAB", "core_foundry": "CFD",
    "assembly_plant": "ASM", "shipyard_small": "YDS", "shipyard_medium": "YDM", "shipyard_large": "YDL",
    "storage_depot": "STO", "fuel_depot": "FUE", "docking_ring": "DOK", "barracks": "BAR",
    "defense_platform": "DEF", "shield_generator": "SHD", "comm_relay": "COM", "ground_core": "GCR",
    "surface_drill": "DRL", "ground_battery": "GBT", "landing_pads": "PAD",
}
CONN_DOOR_W, CONN_DOOR_H = 1.8, 2.8  # connector doorways (centered)
HUB_HALF, CONN_LEN = 4.0, 6.0        # hub interior half-size, connector tube length


def _module_dims(name):
    sections, decks, sab = MODULE_SPECS[name]
    L = max(sections * SEG_LEN, 14.0)
    crew = min(10.0, L * 0.5)
    return L, crew, decks * DECK_H, sab


def build_module(name, tag, attached=(False, False), turret_scale=1.4):
    """One module in local coordinates. attached = (back connector used, front connector used).
    Returns (parts, markers, zones, pivots): pivots are turrets that keep their own origin."""
    L, C, Hh, n_sab = _module_dims(name)
    hw, ox, H = MOD_HW, MOD_OX, DECK_H
    P = lambda nm, mat: Part(f"{tag}_{nm}", mat)
    deck, hull, inner = P("Deck-col", "Deck"), P("Hull-col", "Hull"), P("Interior-col", "Interior")
    furn, cover, haz = P("Furniture-col", "Furniture"), P("Cover-col", "Cover"), P("Hazard", "Hazard")
    lights, trim, mach = P("Lights", "Lights"), P("Trim", "Trim"), P("Machinery-col", "Engine")
    glow, armor = P("Glow", "EngineGlow"), P("Armor", "Armor")
    parts = [deck, hull, inner, furn, cover, haz, lights, trim, mach, glow, armor]
    markers, zones, pivots = [], [], []
    y_hall_end = L - C                       # hall: 0..y_hall_end, crew section: y_hall_end..L
    # ---- shell
    deck.add(box(-hw, hw, 0, L, -SLAB_T, 0))
    hull.add(box(-ox, ox, -0.4, L + 0.4, Hh, Hh + 0.4))
    hull.add(box(-ox, ox, -0.4, L + 0.4, -SLAB_T - 0.4, -SLAB_T))
    if Hh > H:                               # crew section keeps a normal ceiling
        deck.add(box(-hw, hw, y_hall_end, L, H - SLAB_T, H))
    ya = y_hall_end / 2                      # airlocks open into the hall
    for side, sname in ((-1, "Port"), (1, "Stbd")):
        xa, xb = sorted((side * hw, side * ox))
        hull.add_many(wall("y", xa, xb, 0, L, -SLAB_T, Hh, [(ya, AIRLOCK_W, 0, AIRLOCK_H)]))
        od = P(f"Airlock{sname}_Door-col", "Door")
        od.add(box(*sorted((side * (hw + 0.2), side * (hw + 0.3))), ya - AIRLOCK_W / 2 - 0.05,
                   ya + AIRLOCK_W / 2 + 0.05, 0, AIRLOCK_H))
        parts.append(od)
        fa, fb = sorted((side * ox, side * (ox + 0.12)))
        haz.add_many([box(fa, fb, ya - AIRLOCK_W / 2 - 0.3, ya - AIRLOCK_W / 2, 0, AIRLOCK_H + 0.3),
                      box(fa, fb, ya + AIRLOCK_W / 2, ya + AIRLOCK_W / 2 + 0.3, 0, AIRLOCK_H + 0.3)])
        markers += [(f"Airlock{sname}_EVAEntry", (side * (ox + 3.0), ya, 1.3)),
                    (f"Airlock{sname}_Inside", (side * (hw - 1.2), ya, 0.05)),       # where boarders come in
                    (f"Airlock{sname}_ChargeA", (side * (ox + 0.4), ya, 1.2))]
    for end, (y0, y1), used in (("Back", (-0.4, 0.0), attached[0]), ("Front", (L, L + 0.4), attached[1])):
        hull.add_many(wall("x", y0, y1, -ox, ox, -SLAB_T, Hh, [(0, CONN_DOOR_W, 0, CONN_DOOR_H)]))
        d = P(f"Connector_{end}_Door-col", "Door")
        d.add(box(-CONN_DOOR_W / 2 - 0.05, CONN_DOOR_W / 2 + 0.05, y0 + 0.15, y0 + 0.25, 0, CONN_DOOR_H))
        parts.append(d)
        markers += [(f"Connector_{end}", (0, y1 if end == "Front" else y0, 0.05)),
                    (f"Connector_{end}_ChargeA", (0, (y0 - 0.4) if end == "Back" else (y1 + 0.4), 1.2))]
        if not used:
            haz.add(box(-1.2, 1.2, y0 - 0.04 if end == "Back" else y1, y0 if end == "Back" else y1 + 0.04,
                        CONN_DOOR_H, CONN_DOOR_H + 0.2))
    # ---- crew section: corridor, control room (+x), crew room (-x)
    cw = 1.2
    yc = (y_hall_end + L) / 2
    inner.add_many(wall("x", y_hall_end - WALL_T / 2, y_hall_end + WALL_T / 2, -hw, hw, 0, H,
                        [(0, 2.4, 0, 3.0)]))
    for side in (-1, 1):
        inner.add_many(wall("y", *sorted((side * cw, side * (cw + WALL_T))), y_hall_end, L, 0, H,
                            [(yc, DOOR_W, 0, DOOR_H)]))
    cx0 = cw + WALL_T
    furn.add(box(hw - 0.8, hw - 0.1, y_hall_end + 0.6, L - 0.6, 0, 1.1))           # console bank
    lights.add(box(hw - 0.82, hw - 0.8, y_hall_end + 0.8, L - 0.8, 0.8, 1.05))
    console = P("ControlConsole-col", "Furniture")                                    # interact: on/off, capture
    console.add(box(cx0 + 1.2, cx0 + 2.4, yc - 0.8, yc + 0.8, 0, 1.0))
    parts.append(console)
    lights.add(box(cx0 + 1.3, cx0 + 2.3, yc - 0.7, yc + 0.7, 1.0, 1.03))
    furn.add(box(-hw + 0.1, -hw + 0.6, y_hall_end + 0.6, y_hall_end + 3.0, 0, 2.0))   # lockers
    furn.add(box(-cx0 - 2.6, -cx0 - 1.2, yc - 0.6, yc + 0.6, 0, 0.75))               # crew table
    furn.add(box(cw - 0.35, cw, y_hall_end + 0.4, y_hall_end + 1.6, 0, 2.0))          # ready locker
    lights.add(box(-0.3, 0.3, y_hall_end + 0.5, L - 0.5, H - SLAB_T - 0.08, H - SLAB_T))
    markers += [("ControlRoom", (cx0 + 2.6 if cx0 + 3.4 < hw else (cx0 + hw) / 2, yc + 1.4, 0.05)),
                ("ControlConsole", (cx0 + 1.0, yc, 0.05)),
                ("CrewRoom", (-(cx0 + hw) / 2, yc + 1.2, 0.05)),
                ("ReadyLocker", (cw - 1.05, y_hall_end + 1.0, 0.05))]
    # ---- machine hall
    hall_y0, hall_y1 = 0.4, y_hall_end - 0.4
    lights.add(box(-0.4, 0.4, hall_y0 + 0.5, hall_y1 - 0.5, Hh - 0.12, Hh - 0.04))
    machine_hall(name, mach, glow, furn, cover, haz, trim, armor, hw, hall_y0, hall_y1, Hh, markers)
    # sabotage points: junction boxes on the hall walls, spread along it
    for i in range(n_sab):
        side = (-1, 1)[i % 2]
        sy = hall_y0 + (i + 1) * (hall_y1 - hall_y0) / (n_sab + 1)
        xa, xb = sorted((side * (hw - 0.45), side * (hw - 0.05)))
        furn.add(box(xa, xb, sy - 0.5, sy + 0.5, 0.6, 2.0))
        haz.add(box(*sorted((side * (hw - 0.47), side * (hw - 0.45))), sy - 0.5, sy + 0.5, 1.8, 2.0))
        markers += [(f"SabotagePoint_{i + 1}", (side * (hw - 1.1), sy, 0.05)),
                    (f"SabotagePoint_{i + 1}_ChargeA", (side * (hw - 0.5), sy, 1.3))]
    # ---- outside
    sl = P("StatusLight", "Lights")                         # recolor in Godot by state
    sl.add(box(-0.5, 0.5, L - 1.5, L - 0.5, Hh + 0.4, Hh + 0.7))
    parts.append(sl)
    exterior(name, tag, hull, armor, trim, mach, glow, haz, lights, L, Hh, markers, pivots, turret_scale)
    zones.append(("Zone", (0, L / 2, Hh / 2), (hw, L / 2, Hh / 2)))
    return [p for p in parts if p.verts], markers, zones, pivots


def machine_hall(name, mach, glow, furn, cover, haz, trim, armor, hw, y0, y1, Hh, markers):
    """Type-specific machinery. The lane x in [-2.2, 1.0] stays clear so people can walk
    from the back connector to the crew section."""
    mid = (y0 + y1) / 2
    span = y1 - y0
    xs = 1.6                                  # starboard machinery: x in [xs, xm]
    xm, xp = hw - 2.0, -hw + 2.0              # port machinery: x in [xp, -2.6]; walls keep a walkway
    top = min(Hh - 0.4, 6.0)
    if name in ("reactor", "outpost_core", "ground_core", "breeder_reactor"):
        r = 2.2 if name in ("reactor", "breeder_reactor") else 1.4
        mach.add(cylinder("z", xs + r + 0.3, mid, 0, top, r, seg=16))
        glow.add(cylinder("z", xs + r + 0.3, mid, top, top + 0.05, r * 0.6, seg=16))
        for k in range(3):
            trim.add(cylinder("z", xs + r + 0.3, mid, 0.8 + k * 1.6, 1.0 + k * 1.6, r + 0.15, seg=16))
        if name == "breeder_reactor":
            mach.add(cylinder("z", xp + 1.6, mid, 0, top * 0.8, 1.4, seg=12))
        markers.append(("Core", (xs + r + 0.3, mid, 0.05)))
    elif name == "refinery":
        for k in range(3):
            mach.add(cylinder("z", xm - 1.2, y0 + span * (k + 1) / 4, 0, 3.5, 1.2, seg=12))
        furn.add(box(xp, -2.8, y0 + 1.0, y1 - 1.0, 0, 0.9))                        # conveyor
        trim.add(box(xp, -2.8, y0 + 1.0, y1 - 1.0, 0.9, 1.0))
    elif name in ("fabricator", "assembly_plant", "core_foundry"):
        for k in range(2):
            y = y0 + span * (k + 1) / 3
            furn.add(box(xs, xm, y - 0.8, y + 0.8, 0, 1.0))                         # benches / line
            trim.add(box(xs + 0.6, xs + 0.8, y - 0.1, y + 0.1, 1.0, 2.2))            # robot arm
            trim.add(box(xs + 0.6, xs + 2.4, y - 0.1, y + 0.1, 2.1, 2.3))
        furn.add(box(xp, -2.8, y0 + 1.0, y1 - 1.0, 0, 0.9))
        if name == "core_foundry":                                                   # clean room
            mach.add(box(xs - 0.1, xs, y0 + 1.5, y1 - 1.5, 0, 3.0))
            glow.add(box(xp + 0.1, -2.9, y0 + 1.2, y1 - 1.2, 0.9, 0.93))
    elif name.startswith("shipyard") or name == "docking_ring" or name == "landing_pads":
        for k in range(2):                                                           # crew & cargo handling
            y = y0 + span * (k + 1) / 3
            cover.add(box(xs + 0.5, xs + 1.8, y - 0.65, y + 0.65, 0, 1.3))
            cover.add(box(xp, xp + 1.3, y - 0.65, y + 0.65, 0, 1.3))
        for k in range(int(span // 3)):
            markers.append((f"CargoStorage_{k + 1}", (xs + 2.8, y0 + 1.5 + k * 3.0, 0.05)))
    elif name in ("storage_depot", "barracks"):
        for k in range(int(span // 3)):
            y = y0 + 1.5 + k * 3.0
            furn.add(box(xs + 0.5, xm, y - 0.4, y + 0.4, 0, min(top, 3.2)))          # racks / bunks
            furn.add(box(xp, -2.9, y - 0.4, y + 0.4, 0, min(top, 3.2)))
        if name == "barracks":
            markers.append(("Garrison", (-0.6, mid, 0.05)))
    elif name in ("defense_platform", "ground_battery"):
        mach.add(cylinder("z", xs + 1.6, mid, 0, top, 0.9, seg=10))                    # ammo hoist
        furn.add(box(xp, -2.8, mid - 1.2, mid + 1.2, 0, 1.2))                          # fire control
    elif name in ("shield_generator", "comm_relay"):
        mach.add(cylinder("z", xs + 1.8, mid, 0, top * 0.7, 1.1, seg=12))
        glow.add(cylinder("z", xs + 1.8, mid, top * 0.7, top * 0.7 + 0.1, 0.8, seg=12))
        furn.add(box(xp, -2.8, y0 + 1.4, y1 - 1.4, 0, 2.0))                            # server racks
    elif name in ("mining_rig", "surface_drill", "gas_skimmer", "fuel_depot", "command_core"):
        mach.add(box(xs, xm, y0 + 1.0, y1 - 1.0, 0, 2.4))                                # hoppers / pumps / ops
        if name == "command_core":
            furn.add(cylinder("z", -3.6, mid, 0, 0.9, 1.2, seg=12))                     # holo table
            glow.add(cylinder("z", -3.6, mid, 0.9, 0.93, 1.0, seg=12))
            markers.append(("Operations", (-1.0, mid, 0.05)))
        else:
            furn.add(box(xp, -2.8, y0 + 1.0, y1 - 1.0, 0, 1.0))
    for k in range(2):                                                              # a little cover
        y = y0 + span * (0.25 + 0.5 * k)
        cover.add(box(-3.6, -2.6, y - 0.5, y + 0.5, 0, 1.1))


def exterior(name, tag, hull, armor, trim, mach, glow, haz, lights, L, Hh, markers, pivots, ts):
    ox, top = MOD_OX, Hh + 0.4
    if name in ("defense_platform", "ground_battery"):
        for k, y in enumerate((L * 0.3, L * 0.7), 1):
            t = turret_part(f"{tag}_Turret_{k}", (2.0, y, top), 0.0, ts * 1.6)
            pivots.append(t)
        markers.append(("PointDefense", (-3.0, L / 2, top + 1.0)))
    elif name == "shield_generator":
        mach.add(cylinder("z", 0, L / 2, top, top + 1.5, 0.6, seg=10))
        armor.add(cylinder("z", 0, L / 2, top + 1.5, top + 1.8, 4.0, seg=20))
        glow.add(cylinder("z", 0, L / 2, top + 1.8, top + 1.85, 3.0, seg=20))
    elif name == "comm_relay":
        trim.add(cylinder("z", 0, L / 2, top, top + 14.0, 0.2, seg=6))
        armor.add(cylinder("z", 0, L / 2, top + 8, top + 8.3, 2.5, seg=16))
    elif name in ("reactor", "breeder_reactor", "outpost_core"):
        for side in (-1, 1):                                                         # radiator fins
            armor.add(box(*sorted((side * ox, side * (ox + 8.0))), L * 0.25, L * 0.75, top - 0.6, top - 0.4))
    elif name == "refinery":
        for side in (-1, 1):
            armor.add(box(*sorted((side * ox, side * (ox + 5.0))), L * 0.2, L * 0.8, top - 0.6, top - 0.4))
        mach.add(cylinder("z", 3.0, L * 0.3, top, top + 3.0, 1.0, seg=10))
    elif name == "fuel_depot":
        for k, y in enumerate((L * 0.25, L * 0.75)):
            armor.add(cylinder("z", ox + 4.0, y, 0, 6.0, 3.2, seg=16))                 # tanks
            trim.add(box(ox, ox + 1.0, y - 0.4, y + 0.4, 2.0, 2.8))
        markers.append(("RefuelBoom", (-(ox + 6.0), L / 2, 2.0)))
    elif name == "docking_ring":
        # small-craft deck each side (Darters, shuttles, miners land here to unload) ...
        for k, side in enumerate((-1, 1)):
            xa, xb = sorted((side * ox, side * (ox + 22.0)))
            trim.add(box(xa, xb, L * 0.08, L * 0.92, -0.6, -0.3))
            for j, py in enumerate((L * 0.3, L * 0.7)):
                px = side * (ox + 11.0)
                for (a_, b_, c_, d_) in ((px - 4.5, px + 4.5, py - 4.7, py - 4.5), (px - 4.5, px + 4.5, py + 4.5, py + 4.7),
                                         (px - 4.7, px - 4.5, py - 4.5, py + 4.5), (px + 4.5, px + 4.7, py - 4.5, py + 4.5)):
                    haz.add(box(a_, b_, c_, d_, -0.3, -0.28))
                glow.add(box(px - 0.3, px + 0.3, py - 0.3, py + 0.3, -0.3, -0.25))
                markers.append((f"DarterPad_{2 * k + j + 1}", (px, py, -0.25)))
            markers.append((f"MinerBerth_{k + 1}", (side * (ox + 11.0), L * 0.5, -7.0)))
            # ... and a long docking arm with clamps: a warship ties up alongside its end
            arm0, arm1 = ox + 22.0, ox + 70.0
            armor.add(box(*sorted((side * arm0, side * arm1)), L * 0.45, L * 0.55, -1.2, 1.2))         # the arm
            trim.add(box(*sorted((side * arm0, side * arm1)), L * 0.47, L * 0.53, 1.2, 1.5))
            for cz in (-1, 1):                                                                         # clamps
                armor.add(box(*sorted((side * (arm1 - 2.0), side * (arm1 + 3.0))), L * 0.5 + cz * 9.0 - 1.0,
                              L * 0.5 + cz * 9.0 + 1.0, -2.0, 2.0))
                glow.add(box(*sorted((side * (arm1 + 3.0), side * (arm1 + 3.1))), L * 0.5 + cz * 9.0 - 0.5,
                             L * 0.5 + cz * 9.0 + 0.5, -0.5, 0.5))
            markers.append((f"ShipBerth_{k + 1}", (side * (arm1 + 28.0), L * 0.5, 0.0)))
        markers.append(("DarterPad_5", (0, L + 12.0, 0.0)))
    elif name == "mining_rig":
        trim.add(box(-0.6, 0.6, L * 0.4, L * 0.6, -14.0, -0.7))                        # drill boom
        mach.add(cylinder("z", 0, L * 0.5, -16.0, -14.0, 1.4, seg=10))
        glow.add(cylinder("z", 0, L * 0.5, -16.1, -16.0, 0.8, seg=10))
    elif name == "gas_skimmer":
        mach.add(taper(L * 0.2, L * 0.8, (2.0, -12.0, -0.7), (4.0, -14.0, -0.7)))      # scoop
        armor.add(cylinder("z", 0, L * 0.5, -20.0, -14.0, 3.0, seg=12))
    elif name == "surface_drill":
        trim.add(box(-0.8, 0.8, L * 0.4, L * 0.6, top, top + 10.0))                    # derrick
        mach.add(box(-1.5, 1.5, L * 0.35, L * 0.65, top + 9.0, top + 11.0))
    elif name == "landing_pads":
        for k, side in enumerate((-1, 1)):
            xa, xb = sorted((side * ox, side * (ox + 16.0)))
            trim.add(box(xa, xb, -2.0, L + 2.0, -0.3, 0.0))
            haz.add(box(*sorted((side * (ox + 3.0), side * (ox + 13.0))), L / 2 - 5, L / 2 - 4.8, 0.0, 0.02))
            markers += [(f"DropshipPad_{k + 1}", (side * (ox + 8.0), L / 2, 0.05)),
                        (f"DarterPad_{k + 1}", (side * (ox + 8.0), L / 2 + 6.0, 0.05))]
    elif name.startswith("shipyard"):
        size = {"shipyard_small": (30, 14), "shipyard_medium": (120, 30), "shipyard_large": (220, 34)}[name]
        bl, bw = size
        y0 = L + 6.0                                   # the bay hangs off the far end, away from the spine
        for xx in (-bw / 2 - 1.2, bw / 2):                                             # gantry frame
            for zz in (-bw * 0.4, bw * 0.4):
                trim.add(box(xx, xx + 1.2, y0, y0 + bl, zz, zz + 1.2))
        for k in range(6):
            y = y0 + k * (bl - 1.2) / 5
            for zz in (-bw * 0.4, bw * 0.4):
                trim.add(box(-bw / 2 - 1.2, bw / 2 + 1.2, y, y + 1.2, zz, zz + 1.2))
        trim.add(box(-1.0, 1.0, L + 0.4, y0, 3.0, 4.0))                                 # arm to the module
        markers.append(("BuildBay", (0.0, y0 + bl / 2, 0.0)))
    elif name == "command_core":
        armor.add(prism(L * 0.3, L * 0.9, 4.0, 2.5, top, top + 2.5))                   # command tower
        lights.add(box(-2.6, 2.6, L * 0.9 - 0.05, L * 0.9 + 0.02, top + 1.6, top + 1.9))
    elif name == "barracks":
        lights.add(box(ox, ox + 0.04, L * 0.2, L * 0.8, 2.6, 2.8))


def _rot_pt(p, quarter):
    """Rotate a point about Z by quarter * 90 degrees."""
    x, y, z = p
    for _ in range(quarter % 4):
        x, y = -y, x
    return (x, y, z)


def _place(parts, markers, zones, pivots, quarter, offset, out_parts, out_markers, out_zones):
    ox_, oy_, oz_ = offset
    mv = lambda p: tuple(a + b for a, b in zip(_rot_pt(p, quarter), (ox_, oy_, oz_)))
    for p in parts:
        q = Part(p.name, p.material)
        for v, f in p.solids:
            vv = [mv(pt) for pt in v]
            q.add((vv, _orient_faces(vv, f)))
        out_parts.append(q)
    for t in pivots:
        t.origin = mv(t.origin)
        t.rot_z += quarter * math.pi / 2
        out_parts.append(t)
    for n, pos in markers:
        out_markers.append((n, mv(pos)))
    for n, pos, half in zones:
        h = (half[1], half[0], half[2]) if quarter % 2 else half
        out_zones.append((n, mv(pos), h))


def build_hub(tag):
    P = lambda nm, mat: Part(f"{tag}_{nm}", mat)
    deck, hull, lights = P("Deck-col", "Deck"), P("Hull-col", "Hull"), P("Lights", "Lights")
    h, H = HUB_HALF, DECK_H
    deck.add(box(-h, h, -h, h, -SLAB_T, 0))
    hull.add(box(-h - 0.4, h + 0.4, -h - 0.4, h + 0.4, H, H + 0.4))
    hull.add(box(-h - 0.4, h + 0.4, -h - 0.4, h + 0.4, -SLAB_T - 0.4, -SLAB_T))
    for fixed, axis in ((-h - 0.4, "x"), (h, "x"), (-h - 0.4, "y"), (h, "y")):
        hull.add_many(wall(axis, fixed, fixed + 0.4, -h - 0.4, h + 0.4, -SLAB_T, H,
                           [(0, CONN_DOOR_W + 0.4, 0, CONN_DOOR_H + 0.2)]))
    lights.add(box(-1.0, 1.0, -1.0, 1.0, H - 0.08, H))
    return [deck, hull, lights], [("Hub", (0, 0, 0.05))]


def build_tube(tag, length=CONN_LEN):
    """Walkable connector tube along +Y from y=0 to y=length."""
    P = lambda nm, mat: Part(f"{tag}_{nm}", mat)
    deck, hull, lights, glass = P("Deck-col", "Deck"), P("Hull-col", "Hull"), P("Lights", "Lights"), P("Glass-col", "Glass")
    deck.add(box(-1.4, 1.4, 0, length, -SLAB_T, 0))
    hull.add(box(-1.8, 1.8, 0, length, 3.2, 3.6))
    hull.add(box(-1.8, 1.8, 0, length, -SLAB_T - 0.4, -SLAB_T))
    for side in (-1, 1):
        hull.add_many(wall("y", *sorted((side * 1.4, side * 1.8)), 0, length, -SLAB_T, 3.2,
                           [(length / 2, length - 2.0, 1.2, 2.4)]))
        glass.add(box(*sorted((side * 1.55, side * 1.6)), 1.0, length - 1.0, 1.2, 2.4))   # windows
    lights.add(box(-0.3, 0.3, 0.5, length - 0.5, 3.12, 3.2))
    return [deck, hull, lights, glass], []


def generate_station(cls):
    """Assemble a station, outpost or ground base (or one stand-alone module)."""
    if cls.startswith("MODULE_"):
        name = cls[len("MODULE_"):]
        code = f"M01{MOD_CODE[name]}"
        parts, markers, zones, pivots = build_module(name, f"{cls}_{code}")
        out_p, out_m, out_z = [], [], []
        _place(parts, [(f"{code}_{n}", p) for n, p in markers],
               [(f"Zone_{code}", p, h) for _, p, h in zones], pivots, 0, (0, 0, 0), out_p, out_m, out_z)
        return out_p, out_m + out_z, dict(modules=[name])
    kit = STATION_KITS[cls]
    out_p, out_m, out_z = [], [], []
    ground = kit[0] in GROUND_MODULES
    # root module along +Y, back end at y = 0
    root = kit[0]
    rest = kit[1:]
    n_hubs = (len(rest) + 1) // 2
    Lr = _module_dims(root)[0]

    def build(idx, name, attached):
        code = f"M{idx:02d}{MOD_CODE[name]}"
        built = build_module(name, f"{cls}_{code}", attached)
        xs = [abs(x + q.origin[0]) for q in built[0] for v, _ in q.solids for x, _, _ in v]
        return code, built, max(xs)                    # half-width across the module, exterior included

    def place(code, built, quarter, offset):
        parts, markers, zones, pivots = built
        _place(parts, [(f"{code}_{n}", p) for n, p in markers],
               [(f"Zone_{code}", p, h) for _, p, h in zones], pivots, quarter, offset, out_p, out_m, out_z)

    code, built, root_hw = build(1, root, (False, n_hubs > 0))
    place(code, built, 0, (0, 0, 0))
    # side modules lie across the spine, so the spine is stretched until neighbours don't touch
    sides, idx = [], 2
    for h in range(n_hubs):
        pair = []
        for side in (1, -1):
            if rest:
                pair.append((side,) + build(idx, rest.pop(0), (True, False)))
                idx += 1
        sides.append(pair)
    GAP = 3.0
    y, prev_reach = Lr + 0.4, 0.0
    for h, pair in enumerate(sides):
        reach = max([w for *_, w in pair] + [HUB_HALF])
        hub_c = max(y + CONN_LEN + HUB_HALF + 0.4, prev_reach + reach + GAP)
        if h == 0:
            hub_c = max(hub_c, Lr + reach + GAP)
        tube_len = hub_c - HUB_HALF - 0.4 - y
        tp, tm = build_tube(f"{cls}_T{h + 1:02d}", tube_len)
        _place(tp, [], [], [], 0, (0, y, 0), out_p, out_m, out_z)
        hp, hm = build_hub(f"{cls}_H{h + 1:02d}")
        _place(hp, [(f"H{h + 1:02d}_{n}", p) for n, p in hm], [], [], 0, (0, hub_c, 0), out_p, out_m, out_z)
        for side, code, built, _ in pair:                      # a module on each side of the hub
            tp, _ = build_tube(f"{cls}_T{h + 1:02d}{'R' if side > 0 else 'L'}")
            quarter = 3 if side > 0 else 1                     # local +Y -> world +X (3) or -X (1)
            x_start = side * (HUB_HALF + 0.4)
            _place(tp, [], [], [], quarter, (x_start, hub_c, 0), out_p, out_m, out_z)
            place(code, built, quarter, (x_start + side * (CONN_LEN + 0.4), hub_c, 0))
        prev_reach = hub_c + reach
        y = hub_c + HUB_HALF + 0.4
    if ground:                                                 # the asteroid the base is dug into
        rock = Part(f"{cls}_Asteroid-col", "Rock")
        xs = [p[0] for q in out_p for v, _ in q.solids for p in v]
        ys = [p[1] for q in out_p for v, _ in q.solids for p in v]
        cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
        rx, ry = (max(xs) - min(xs)) / 2 + 40, (max(ys) - min(ys)) / 2 + 40
        def slab(z0, z1, bottom, top):
            return hexa([(cx + (-1, 1)[i & 1] * (top if (i >> 2) & 1 else bottom)[0],
                          cy + (-1, 1)[(i >> 1) & 1] * (top if (i >> 2) & 1 else bottom)[1],
                          (z0, z1)[(i >> 2) & 1]) for i in range(8)])
        rock.add(slab(-60.0, -0.75, (rx, ry), (rx * 0.8, ry * 0.8)))          # the flat top the base sits in
        rock.add(slab(-90.0, -60.0, (rx * 0.6, ry * 0.6), (rx, ry)))
        rr = random.Random(f"{SEED}-{cls}-rock")
        crust = Part(f"{cls}_AsteroidCrust", "Rock")                        # lumps, ridges and boulders
        for k in range(26):
            a = rr.uniform(0, math.tau)
            edge = rr.uniform(0.75, 1.05)
            bx, by = cx + math.cos(a) * rx * edge, cy + math.sin(a) * ry * edge
            r0 = rr.uniform(10, 26)
            z0, z1 = rr.uniform(-75, -30), rr.uniform(-8, 6)
            crust.add(hexa([(bx + (-1, 1)[i & 1] * r0 * rr.uniform(0.6, 1.3), by + (-1, 1)[(i >> 1) & 1] * r0 * rr.uniform(0.6, 1.3),
                             (z0, z1)[(i >> 2) & 1] + rr.uniform(-3, 3)) for i in range(8)]))
        for k in range(14):                                                 # boulders on the surface
            bx, by = cx + rr.uniform(-0.85, 0.85) * rx, cy + rr.uniform(-0.85, 0.85) * ry
            if abs(bx - cx) < rx - 45 and abs(by - cy) < ry - 45:
                continue                                                    # keep the base and pads clear
            r0 = rr.uniform(2, 6)
            crust.add(hexa([(bx + (-1, 1)[i & 1] * r0 * rr.uniform(0.6, 1.3), by + (-1, 1)[(i >> 1) & 1] * r0 * rr.uniform(0.6, 1.3),
                             (-1.5, r0 * 0.9)[(i >> 2) & 1] + rr.uniform(-0.6, 0.6)) for i in range(8)]))
        out_p.append(crust)
        out_p.append(rock)
        out_m.append(("SurfaceLanding", (cx, cy - ry + 10.0, -0.7)))
    return out_p, out_m + out_z, dict(modules=list(kit))


# =========================================================================
# Output
# =========================================================================

def _world_verts(part, offset=(0, 0, 0)):
    c, s = math.cos(part.rot_z), math.sin(part.rot_z)
    ox, oy, oz = (part.origin[i] + offset[i] for i in range(3))
    return [(x * c - y * s + ox, x * s + y * c + oy, z + oz) for x, y, z in part.verts]


def write_obj(cls):
    """Fallback for plain Python: writes ship_<CLASS>.obj + .mtl (Y-up)."""
    parts, _, _ = generate(cls)
    path, mtl = f"ship_{cls}.obj", f"ship_{cls}.mtl"
    with open(mtl, "w") as m:
        for name, (rgb, _, _, em, alpha) in materials().items():
            m.write(f"newmtl {name}\nKd {rgb[0]} {rgb[1]} {rgb[2]}\nd {alpha}\n")
            if em:
                m.write(f"Ke {rgb[0]} {rgb[1]} {rgb[2]}\n")
            m.write("\n")
    with open(path, "w") as f:
        f.write(f"mtllib {mtl}\n")
        base = 1
        for p in parts:
            f.write(f"o {p.name}\nusemtl {p.material}\n")
            for x, y, z in _world_verts(p):
                f.write(f"v {x:.4f} {z:.4f} {-y:.4f}\n")
            for face in p.faces:
                f.write("f " + " ".join(str(i + base) for i in face) + "\n")
            base += len(p.verts)
    return path


def _make_material(bpy, name):
    rgb, metal, rough, emit, alpha = materials()[name]
    mname = f"Ship_F{FACTION}_{name}"
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
        if alpha < 1.0:
            bsdf.inputs["Alpha"].default_value = alpha
            for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
                try:
                    setattr(mat, attr, val)
                except (AttributeError, TypeError):
                    pass
    mat.diffuse_color = (*rgb, alpha)
    return mat


def _remove_collection(bpy, name):
    old = bpy.data.collections.get(name)
    if not old:
        return
    for obj in list(old.all_objects):
        data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if data is not None and data.users == 0:
            bpy.data.meshes.remove(data)
    bpy.data.collections.remove(old)


def all_build_classes():
    return (SHIP_CLASSES + (list(STATION_KITS) if BUILD_STATIONS else []) +
            ([f"MODULE_{m}" for m in MODULE_SPECS] if BUILD_SINGLE_MODULES else []))


def build_in_blender():
    import bpy

    x_cursor = 0.0
    for cls in all_build_classes():
        cname = f"Ship_{cls}"
        _remove_collection(bpy, cname)
        coll = bpy.data.collections.new(cname)
        bpy.context.scene.collection.children.link(coll)
        parts, markers, info = generate(cls)

        x_cursor += info["width"] / 2
        root = bpy.data.objects.new(cname, None)
        root.empty_display_type = "PLAIN_AXES"
        root.location = (x_cursor, 0, 0)
        coll.objects.link(root)
        x_cursor += info["width"] / 2 + 15

        for p in parts:
            mesh = bpy.data.meshes.new(p.name)
            mesh.from_pydata(p.verts, [], p.faces)
            mesh.validate()
            mesh.update()
            mesh.materials.append(_make_material(bpy, p.material))
            obj = bpy.data.objects.new(p.name, mesh)
            obj.parent = root
            obj.location = p.origin
            obj.rotation_euler = (0, 0, p.rot_z)
            coll.objects.link(obj)
        for marker in markers:
            name, loc = marker[0], marker[1]
            e = bpy.data.objects.new(f"{cls}_{name}", None)
            if len(marker) > 2:                 # zone box: scale = half-size
                e.empty_display_type = "CUBE"
                e.empty_display_size = 1.0
                e.scale = marker[2]
            else:
                e.empty_display_type = "ARROWS"
                e.empty_display_size = 0.8
            e.parent = root
            e.location = loc
            coll.objects.link(e)
        for key, val in info.get("stats", {}).items():   # exported to glTF as "extras"
            root[key] = val if not isinstance(val, dict) else str(val)

        extra = (f", {info['decks']} deck(s), {len(info['breaches'])} breach zones"
                 if "decks" in info else "")
        print(f"{cls}: ~{info['length']:.0f} m long{extra}")

        if EXPORT_GLB:
            if not bpy.data.filepath:
                print("Save your .blend file first so the .glb files have somewhere to go.")
                continue
            bpy.ops.object.select_all(action="DESELECT")
            for obj in coll.objects:
                obj.select_set(True)
            loc = tuple(root.location)
            root.location = (0, 0, 0)          # export each ship centered
            bpy.context.view_layer.update()
            out = bpy.path.abspath(f"//ship_{cls}.glb")
            bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True,
                                      export_extras=True)
            root.location = loc
            print("Exported", out)


try:
    import bpy  # noqa: F401
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False

if __name__ == "__main__":
    if IN_BLENDER:
        build_in_blender()
    else:
        import json
        all_stats = {}
        for c in all_build_classes():
            print("Not running inside Blender - wrote", write_obj(c))
            all_stats[c] = generate(c)[2]["stats"]
        with open("ship_stats.json", "w") as f:
            json.dump(all_stats, f, indent=2)
        print("Wrote ship_stats.json")
