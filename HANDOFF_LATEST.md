# Handoff: where work stopped (2026-10-09, session 2)

Work happens in the fork `cghath/unnamed-rts` on branch **`handoff-tasks`** (upstream: `noahgonzalez4506/Unnamed-RTS`).
Do not commit to `main`; it stays in sync with upstream. PRs go from `handoff-tasks` to upstream when Noah is ready.

Godot 4.5.1 project in `godot_demo/`. Compile check: `--headless --path . res://tests/compile.tscn` (prints "COMPILE DONE").
Export: `--export-release "Windows Desktop" build/windows/StarshipDemo.exe`, then split into 28 MB parts with PLAY.bat.
GDScript warnings count as errors: give explicit types when reading from a Dictionary or Variant.

## Cloud container setup (no Godot preinstalled)
- Download: `curl -sSL -o g.zip https://github.com/godotengine/godot/releases/download/4.5.1-stable/Godot_v4.5.1-stable_linux.x86_64.zip && unzip g.zip` (keep it outside the repo, e.g. a scratch dir).
- First run: `$GODOT --headless --path godot_demo --import` (about a minute), then the compile check.
- Rendering works under Xvfb with the compatibility renderer:
  `xvfb-run -a -s "-screen 0 1280x720x24" $GODOT --path godot_demo --resolution 1280x720 --rendering-driver opengl3 <scene> ...`
  First-person gun pictures: `... res://match.tscn -- --weaponshots <out folder>` (tests/weapon_shots.gd, about 26 shots).
- Ask the user before launching the game windowed; they stopped one such run in session 2.

## Done in session 2 (branch handoff-tasks)
- **EMP screen static (task 1): done, compiled, overlay rendered and looked at.**
  - `commander.gd` `emp_static(t)`: CanvasLayer 10 (over the HUD, under the pause menu, which is 60) with a ColorRect
    and the `EMP_SHADER` canvas shader: blurred screen texture, washed out and dimmed, snow, scanlines and row tearing.
    Full strength, then it fades over the last 60 % of t. `_emp_frame` clears it when the possessed body isn't alive.
  - The network "grenade" action now sends `[at, emp]` (`character.gd` player input, `network.gd` `_action`).
  - Snapshot flag 128 = `stun_t > 0`. On a client, the possessed body calls `stun(2.0)` when that flag rises
    (meta `net_stun`), so EMPs thrown on the host also stun and blind the client's player.
- **Bullpup battle rifle (task 2): built and compiled, NOT yet looked at in the hands or first person.**
  - `tests/make_bullpup.gd` (run: `$GODOT --headless --path godot_demo -s res://tests/make_bullpup.gd`) builds the gun
    from boxes and cylinders, using the materials from the old `.glb` of the same faction. It writes
    `models/weapons/weapon_F1_BattleRifle.tscn` and `weapon_P_BattleRifle.tscn`. Re-run it after changing the shape.
  - Shape: about 0.75 m (butt z -0.345, flash hider ends z 0.42), magazine behind the grip, vented shroud over a
    short barrel, top rail and holo sight. Markers: Grip (0,-0.06,-0.01), SupportHand (0,0,0.29), Muzzle (0,0.05,0.42),
    Sight (0,0.15,0.05), MagWell (0,-0.02,-0.165). The Mag mesh is built around its own top centre, so the reload
    hand-mag (`rig._hand_mag`) sits in the hand properly.
    The shorter SupportHand and Muzzle are on purpose: it's a bullpup.
  - `character.give_weapon` loads `weapon_<x>.tscn` when it exists, otherwise the `.glb`.
  - Stats (`blender/character_generator.py` WEAPON_CLASSES and both `data/` and `godot_demo/data/` JSON copies):
    damage 24 (F2 31.2), rpm 780, no `burst`, 32 rounds, reload 2.3 s, range 45 m.
  - `viewmodel.gd`: BattleRifle gets the holo sight. PulseCarbine (the F2 battle rifle) keeps its 3x scope.
  - **To finish:** render it (weaponshots plus a third-person look). Check the grip, support hand and stock against
    the shoulder, the ADS sight line through the holo, reload, and backface/winding (the faces wind clockwise for Godot).
    Then fix and re-run the builder.

## Done in session 1 (compiled, not playtested)
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
1. **Finish the bullpup check** (see above).
2. **Grenadier role replaces marksman (#29).**
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
   - GL frag: reuse `grenade.gd` with higher velocity and impact detonation (add an `impact` flag). AI fires at 8-35 m at clustered or covered targets. Player: a key toggles GL. Note B is bound to "board" in `commander._inputs` (check whether it does anything in FPS before reusing it).
   - Breaching round (Ash, R6-style), new `breach_round.gd`:
     - Look: finned cylinder (dark grey, ~0.14 m long) with a red band. The nose is a serrated hole-saw cup crown: a ring plus about 10 small teeth. Four curved fins lie folded along the body and flip out on firing.
     - Behaviour: flies straight and sticks to the first world or door surface. The crown spins and sparks for ~1 s, then it calls `vessel.breach_door(d, by, push)` on a `wall_near`/`door_near` within 1.5 m (secure doors included). Otherwise it's a small `G.blast`.
     - AI: in `squad.stack_breacher`, a grenadier with rounds scores 4 for non-"door" kinds (a charge-carrying breacher scores 5). In `character._follow_squad`, a grenadier breacher stops at ≤12 m with line of sight and fires instead of walking up. Set `stack_door["charged"] = true` so others wait.
3. **Earlier report**: the infected visuals, the T station layout and the cities are unverified in play.
