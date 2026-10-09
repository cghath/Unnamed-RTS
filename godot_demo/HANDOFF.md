# Handoff: where work stopped (2026-10-09)

Godot 4.5.1 project. Compile check: `--headless --path . res://tests/compile.tscn` (prints "COMPILE DONE").
Export: `--export-release "Windows Desktop" build/windows/StarshipDemo.exe`, then split into 28 MB parts with PLAY.bat.
GDScript warnings count as errors: give explicit types when reading from a Dictionary or Variant.

## Done in the last build (compiled, not playtested)
- **Escape pods**: placed only indoors (`ship.gd` `_inside_hull`: inside a zone, with a ceiling and walls on 4 sides).
- **Boarding shuttle**: reverses into hangars rear-first (`shuttle.gd` stage 3). Airlock docking already backed in.
- **Ships inside asteroids**: pushed out to the rock's surface once a second (`match.gd` `_clear_of_rocks`).
- **City lots**: the 45° offset is fixed (`campaign/ruins.gd` lines 89-90). The grid axes now match `Basis(UP, th)`.
- **Breachable walls (#25)**:
  - `vessel.gd` "breachable walls" section: `_find_breach_walls`, `wall_near`, `wall_sides`, `_open_wall` (adds a NavigationServer3D link plus rubble).
  - Walls are door-shaped dicts with `kind == "wall"`, so `plant_charge`, `breach_door`, squad stacking and `_start_clear` all work on them.
  - Player: E at a hazard-striped wall with a charge.
  - Squad order 4 ("breach") also targets walls (`match.gd` `squad_command` `door_at`).
  - AI (`squad.gd` `_consider_wall`, every 3 s while in contact): if 3 or more hostiles are within 10 m of the enemy position, the squad has a charge, and a wall within 18 m has its far side toward the enemy (within 16 m), the squad stacks on it and breaches and clears.
- **EMP grenades (#26)**:
  - Riflemen and breachers carry 1 (their second grenade slot, tinted blue). The array is `character.emps`.
  - `grenade.gd` `emp`: 1.8 s fuse, 7 m pulse with line of sight, calls `c.stun(2.0)`.
  - `character.stun_t` stops the character moving, shooting and seeing, and makes them twitch.
  - Player: G throws a frag; Shift+G (or G with no frags left) throws an EMP.
- **Bang before entry (#27)**: `squad._start_clear` against a hostile room. The nearest member with an EMP (else a frag) throws it in. `_clear_slot` holds the squad beside the doorway until `clear.go_at` (detonation), then they flow in.

## Still to do
1. **EMP screen static for the player.**
   - `character.stun()` already calls `G.commander.emp_static(t)` if that method exists.
   - Add `emp_static(t)` to `commander.gd`: a full-screen ColorRect with a noise shader, faded over t, plus a blurred or dimmed view.
   - Network: `network.gd` "grenade" action calls `_throw_grenade(args[0])`. Pass the EMP flag as `args[1]`.
2. **Bullpup battle rifle (#28)**: an original CQB bullpup, not a copy of the reference.
   - Design: magazine behind the pistol grip, short shrouded barrel, compact.
   - Stats for `data/weapons_and_armor.json` class `battle_rifle`:
     - F1: damage ~24, rpm ~780, full auto (remove `burst`), 32 rounds, reload 2.3 s, range 45 m.
     - F2: scale damage by about 1.3.
   - `viewmodel.gd` line ~183: switch BattleRifle from "scope" to "holo".
   - Model:
     - No Blender in the container. Write a headless tool script that builds the mesh from primitives and saves `res://models/weapons/weapon_F1_BattleRifle.tscn` and `weapon_P_BattleRifle.tscn`.
     - Use the same marker names and rough positions as the GLB: Grip (0,-0.06,-0.01), SupportHand (0,0,0.48), Muzzle (0,0.05,0.83), Sight (0,0.16,0), MagWell, Mag.
     - In a bullpup, the Mag/MagWell sit behind the Grip (negative z) and the gun is about 0.75 m long.
     - `character.give_weapon` (line ~207) loads `.glb`; prefer `.tscn` when it exists. `viewmodel.gd` loads `rig.weapon.scene_file_path`, so it picks the new scene up automatically.
3. **Grenadier role replaces marksman (#29).**
   - Rename "marksman" in every role list: `character.COMBAT_ROLES`, `match.gd` (lines ~59, REQ_ROLES, ~1388), `ship.gd` BOARD_ROLES and drop lists, `station.gd` SQUAD, `squad.gd` `_promote`, `campaign/minidrop.gd`, `commander.gd` CLASSES, `hud.gd` role blurbs, and `G.TECH`/HUD text if any.
   - Role data:
     - Add `grenadier` to `roles` in the JSON for factions 1 and 2. Copy the rifleman's armor pieces.
     - Primary: the bullpup with an underslung grenade launcher. Make a separate model, `<fac>_BullpupGL` (bullpup plus a tube under the barrel), with its own weapon class entry and stats.
     - Kit: 4 mags, 1 pistol mag, 1 medpen.
     - There's no char_*_grenadier.glb, so `setup()` falls back to the rifleman model.
   - Kit visuals (procedural, in `character.setup`):
     - Bones have identity rest rotation. Attach with `node.position = model_space_pos - rig._model_pos(bone)`.
     - UpperChest front is at z ≈ 0.21, mags at y 1.3-1.5. Hips are at y 1.0. The back pack is around z -0.25.
     - Add a diagonal chest bandolier with 6 × 40 mm shells (`gl_rounds`, hide one per shot) and 2 breaching rounds in holders on the pack sides (`breach_rounds`, hide as used).
   - GL frag: reuse `grenade.gd` with higher velocity and impact detonation (add an `impact` flag). AI fires at 8-35 m at clustered or covered targets. Player: a key (B is free in FPS? check commander key list) toggles GL.
   - Breaching round (Ash, R6-style), new `breach_round.gd`:
     - Look: finned cylinder (dark grey, ~0.14 m long) with a red band. The nose is a serrated hole-saw cup crown: a ring plus about 10 small teeth. Four curved fins lie folded along the body and flip out on firing.
     - Behaviour: flies straight and sticks to the first world or door surface. The crown spins and sparks for ~1 s, then it calls `vessel.breach_door(d, by, push)` on a `wall_near`/`door_near` within 1.5 m (secure doors included). Otherwise it's a small `G.blast`.
     - AI: in `squad.stack_breacher`, a grenadier with rounds scores 4 for non-"door" kinds (a charge-carrying breacher scores 5). In `character._follow_squad`, a grenadier breacher stops at ≤12 m with line of sight and fires instead of walking up. Set `stack_door["charged"] = true` so others wait.
4. **Earlier report**: the infected visuals, the T station layout and the cities are unverified in play.
