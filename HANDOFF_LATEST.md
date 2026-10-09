# Handoff: where work stopped (2026-10-09, session 3)

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
  First-person gun pictures: `... res://match.tscn -- --weaponshots [--only <text>] <out folder>` (tests/weapon_shots.gd).
  Rendering is software (llvmpipe): about 15 s a shot, so the full list (~45 shots) takes over 10 minutes.
  Use `--only BattleRifle`, `--only BullpupGL`, `--only kit` (matches gun or pose names).
- Headless match tests need no Xvfb: `$GODOT --headless --path godot_demo res://match.tscn -- --selftest`
  (a few minutes, ends "SELFTEST RESULT: PASS") and `-- --grenadiertest` (about a minute, "GRENADIER TEST DONE 0").
- Ask the user before launching the game under Xvfb; they stopped one such run in session 2. In session 3 they said
  to go ahead with weaponshots re-runs without asking each time.

## Done in session 3 (branch handoff-tasks)
- **Bullpup (task 2) finished**: see the session 2 entry below; the fix was trimming its own sight to a mount.
- **Grenadier replaces marksman (#29): done.** Automated tests and renders only; nobody has played it yet.
  - Decisions from the user: B switches to the launcher (V stays dash); marksman removed outright, including its data
    and its tighter AI aim; the BullpupGL has the bullpup's stats with about 15% less recoil (KICK 0.77 vs 0.9).
  - Role lists: grenadier sits where marksman was everywhere (character, match, ship, station, squad,
    minidrop, commander CLASSES, HUD blurb, README, `tools/export_characters_glb.py`).
  - Data: `blender/character_generator.py` is the source; it runs in plain Python (`python3 -I` from `blender/`,
    `combat_data()`), and both JSON copies were regenerated from it (everything else came out identical).
    New: role `grenadier` (rifleman armour, BullpupGL + sidearm, 4 mags, 1 pistol mag, 1 medpen), weapon class
    `bullpup_gl` (F1_BullpupGL / F2_BullpupGL), items `GLShell` and `BreachRound` (launcher stats).
    There's no char_*_grenadier.glb: `setup()` falls back to the rifleman model (same armour).
  - Model: `tests/make_bullpup.gd` also writes `weapon_F1/F2/P_BullpupGL.tscn`: the bullpup with a 40 mm tube under
    the shroud. SupportHand moves onto the tube (0,-0.07,0.25); new GLMuzzle marker (0,-0.07,0.385). F2 borrows the
    PulseCarbine's materials and gets a glowing cell for a magazine.
  - Kit (`character._grenadier_kit`): 6 x 40 mm shells upright in loops on the belt, in an arc round the right hip
    from the front to the side, and a breaching round in a sleeve on each hip (the right one behind the shells).
    The user moved it from a chest bandolier to the belt. Hung on Hips and measured off the hips mesh; the rifleman
    model's hip grenade pouches are hidden (grenadiers carry no hand grenades). `gl_ammo`/`breach_ammo` count them,
    `kit_refresh()` hides the spent ones, and the armory refills both.
    Shell model: `grenade.gd shell_model()`; round model:
    `breach_round.gd build_model()`.
  - Launcher frag (`grenade.gd fire_shell`, `character.fire_launcher`): 50 m/s, bursts on impact (world, door or
    character) once it has flown 4 m to arm; before that it's a dud (no blast). 85 damage, 4 m radius, 1.6 s between
    shells. AI (`_ai_launcher`, from `_ai_fire`): 8-35 m, the target must have another hostile within 4.5 m or be in
    cover, no friendly near the burst, a ballistic lob (`_lob`), then 5-8 s before the next.
  - Breaching round (`breach_round.gd`): flies straight, sticks to the first wall or door and reparents to that ship,
    the crown spins and sparks for 1 s, then `vessel.breach_door()` on the aimed or nearest wall/door within 1.5 m
    (secure included). Otherwise it's a small blast, and the target's "charged" flag is released.
    AI: `squad.stack_breacher` scores a grenadier with rounds 4 for non-"door" kinds (a breacher with charges 5).
    In `_follow_squad` it fires from 12 m or less with a clear line (`_breach_shot`) and sets "charged".
  - Player: B ("launcher" action) cycles rifle -> launcher frag -> breaching round -> rifle, skipping empty ones.
    HUD shows the mode and counts; F1 help lists B. Network actions "gl" and "breach".
  - Checked: weaponshots of the BullpupGL (F1 first and third person, F2 hip and side), the kit front/back (F1), and a
    picture of a round drilling a wall. `tests/grenadier_test.gd` (26 checks) passes; `--selftest` passes.
  - Not checked / open:
    - Nobody has played a grenadier yet, and nobody has looked at the F2 kit.
    - Kit counts and which shells show on the belt aren't in network snapshots, so other peers see a full kit.
    - The player's breaching round isn't tied to a door: it opens whatever it sticks near.

## Done in session 2 (branch handoff-tasks)
- **EMP screen static (task 1): done, compiled, overlay rendered and looked at.**
  - `commander.gd` `emp_static(t)`: CanvasLayer 10 (over the HUD, under the pause menu, which is 60) with a ColorRect
    and the `EMP_SHADER` canvas shader: blurred screen texture, washed out and dimmed, snow, scanlines and row tearing.
    Full strength, then it fades over the last 60 % of t. `_emp_frame` clears it when the possessed body isn't alive.
  - The network "grenade" action now sends `[at, emp]` (`character.gd` player input, `network.gd` `_action`).
  - Snapshot flag 128 = `stun_t > 0`. On a client, the possessed body calls `stun(2.0)` when that flag rises
    (meta `net_stun`), so EMPs thrown on the host also stun and blind the client's player.
- **Bullpup battle rifle (task 2): done, rendered and looked at in first and third person (session 3).**
  - `tests/make_bullpup.gd` (run: `$GODOT --headless --path godot_demo -s res://tests/make_bullpup.gd`) builds the gun
    from boxes and cylinders, using the materials from the old `.glb` of the same faction. It writes
    `models/weapons/weapon_F1_BattleRifle.tscn` and `weapon_P_BattleRifle.tscn`. Re-run it after changing the shape.
  - Shape: about 0.75 m (butt z -0.345, flash hider ends z 0.42), magazine behind the grip, vented shroud over a
    short barrel, top rail and a sight mount. Markers: Grip (0,-0.06,-0.01), SupportHand (0,0,0.29), Muzzle (0,0.05,0.42),
    Sight (0,0.12,0.05), MagWell (0,-0.02,-0.165). The Mag mesh is built around its own top centre, so the reload
    hand-mag (`rig._hand_mag`) sits in the hand properly.
    The shorter SupportHand and Muzzle are on purpose: it's a bullpup.
  - `character.give_weapon` loads `weapon_<x>.tscn` when it exists, otherwise the `.glb`.
  - Stats (`blender/character_generator.py` WEAPON_CLASSES and both `data/` and `godot_demo/data/` JSON copies):
    damage 24 (F2 31.2), rpm 780, no `burst`, 32 rounds, reload 2.3 s, range 45 m.
  - `viewmodel.gd`: BattleRifle gets the holo sight. PulseCarbine (the F2 battle rifle) keeps its 3x scope.
  - Session 3: the model's own holo (posts, roof, opaque `Optic` pane) sat under the holo that `viewmodel.gd`
    adds to every rifle, so ADS looked into a solid pane. The model now has only a mount block on the rail with
    `Sight` on top of it (y 0.12); the viewmodel's sight rides on it. Checked: hip, up/down, ADS (dot on the
    crosshair), reload, and third person (right hand on the grip, butt in the shoulder, left hand on the shroud,
    no missing faces).
  - `tests/weapon_shots.gd` now has a bullpup reload and `tp_*` third-person shots, and takes `--only <text>`
    (e.g. `-- --weaponshots --only BattleRifle <folder>`). Under Xvfb with llvmpipe each shot takes about 15 s,
    so the full list (33 shots) runs about 8 minutes; use `--only` for one gun.

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
1. ~~Finish the bullpup check~~ (done in session 3).
2. ~~Grenadier role replaces marksman (#29)~~ (done in session 3, see above; needs a playtest).
3. **Earlier report**: the infected visuals, the T station layout and the cities are unverified in play.
4. **Grenadier follow-ups**:
   - Playtest it: B cycling, the launcher's arc at range, and AI grenadiers in a boarding action.
   - Render the F2 kit: spawn an F2 grenadier, or extend weapon_shots, which only looks at a flag1 rifleman.
   - Optionally send `gl_ammo`/`breach_ammo` in snapshots so other peers see the spent shells.
