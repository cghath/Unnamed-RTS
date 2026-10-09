# Handoff: where work stopped (2026-10-09, end of session 4)

Work happens in the fork `cghath/unnamed-rts` on branch **`handoff-tasks`** (upstream: `noahgonzalez4506/Unnamed-RTS`).
Do not commit to `main`; it stays in sync with upstream. PRs go from `handoff-tasks` to upstream when Noah is ready.

Godot 4.5.1 project in `godot_demo/`. Compile check: `--headless --path . res://tests/compile.tscn` (prints "COMPILE DONE" and
exits 0; any script that fails to load prints "COMPILE FAIL <file>", then "COMPILE FAILED <n>" and exits 1).
Export: `--export-release "Windows Desktop" build/windows/StarshipDemo.exe`, then split into 28 MB parts with PLAY.bat.
GDScript warnings count as errors: give explicit types when reading from a Dictionary or Variant.

## Start here: open loose ends (sessions 3-4)
Everything below this section is done and pushed to `handoff-tasks`. Session 4 ran on the user's Windows PC: Godot 4.5.1
is at `Documents\tools\godot`, and a project audit was fixed (see "Done in session 4"). What's still open:

1. **Windows build repo: done.** Private repo **`cghath/StarshipDemo-windows`** holds builds, one folder per build
   named `<date>_<commit>/`, newest listed first in its README table. `2026-10-09_dd88742/` = `handoff-tasks` at
   dd88742 (`PLAY.bat`, `StarshipDemo.part1`-`part5`, README; joined SHA-256 verified from a fresh clone).
   For a new build: rebuild (see "Windows build" below), add a folder and a README row, push to its `main`.
   GitHub refuses files over 100 MB, so never push the joined .exe. `.gitattributes` keeps parts binary and
   `PLAY.bat` byte for byte (CRLF). Claude can't create repos (403), but can push to this one.
2. **PR to upstream not opened yet.** Claude can't open it: `noahgonzalez4506/Unnamed-RTS` has the same name as
   this fork, so the two can't be attached to one session. The user opens it themselves from
   https://github.com/noahgonzalez4506/Unnamed-RTS/compare/main...cghath:Unnamed-RTS:handoff-tasks?expand=1
   (they were given a title and description). Ask whether it's open or merged before building on it.
3. **Noah's handoff doc.** Noah shared a Claude Doc ("another handoff doc") from his own account. Claude couldn't
   read it (outside the user's organisation: access denied). Ask the user to paste its text, then compare it with
   this file and say which tasks are new.
4. **Playtest.** Nobody has played the grenadier yet. The user is testing on their Windows PC from a local
   desktop-app session (see "Working locally on the user's Windows PC" below) or with the build in
   `StarshipDemo-windows`. Their terminal Claude Code is signed in with an API key, so `claude --teleport` fails
   until they run `claude auth login` with their claude.ai account.
5. **For Noah**, who is new to Git: a cheatsheet doc "Getting the merged changes onto your computer"
   (https://claude.ai/code/artifact/2a7bbf2d-4d6a-49b1-82b1-2e32a897c7e0) covers merging the PR and pulling with
   GitHub Desktop or the command line. The user shares it with him.

6. **Multiplayer fixes are untested with two players.** Session 4 changed the client/host split a lot (see below).
   `tests/run_net_test.sh` (host + client on one machine) hasn't been run since: on Windows the host's listening
   port may raise a Windows Firewall prompt, so ask the user first. Then try two real PCs.

Working with this user: ask clarifying questions before big or ambiguous work; commit and push to `handoff-tasks`
as each piece finishes; send screenshots of anything visual. The rest of the to-do list is at the end of this file.

## Done in session 4 (branch handoff-tasks): audit fixes
A read-only audit (4 areas, each finding re-checked by a skeptic agent) found about 42 problems; all were fixed.
Compile check, `--selftest` (PASS), `--grenadiertest` (26/26) and `--camptest` were run after the fixes. Not playtested.
- **Crash / leak**: station module repair no longer errors on queued room-repair jobs (`station.gd`, so repaired
  modules come back online). Vessels and the ground free their NavigationServer map and regions on delete
  (`vessel.gd` `_notification`/`_free_nav`, `ground.gd` override): the "NavMap3D/NavRegion3D RIDs leaked" is gone.
- **Grenadier**: no hand grenades from the armory; AI grenadiers rearm shells and rounds at a locker
  (`_resupply_possible`); the stack breacher is re-chosen when it can't open a wall; the launcher's friendly check
  counts downed allies; no rifle fire until the trigger is released after a launcher shot (`_gl_latch`); kit counts
  ride in snapshot flags (bits 8-12) so other players see spent shells.
- **Gameplay**: a wrecked armory blocks every resupply mark; faction 2 EMPs keep the 1.8 s fuse; supply shuttles that
  come home loaded give their crew, troops and supplies back (`_return_cargo`); boarders with `retreat_to` run for
  the exit before fighting (`character._think2`); `mrap.gd` no longer spams `get_meta("escort", null)` errors.
- **Campaign saves**: research lives in `Campaign.research`/`researching` (saved; `G.reset` points `G.research[1]` at
  it). Salvage cache ids are compared as ints and every cache draws its random numbers before the "taken" check
  (taking one no longer moves the others). Spreaders skip player outposts. Fleet ships keep their interior
  `variant` (`_ship(..., want_variant)`) and their hangar (`e["hangar"]`, `match.restore_hangar`). Surface captures
  are recorded (`spawn_team` meta). Mini dropships out (and followers) go back to their ship's record when the
  scene goes, and are saved as docked (`minidrop.owed_to`, `Campaign.to_dict`). DEPLOY VEHICLES takes each vehicle
  off the bay as it rolls out. Miners count while you're on a planet in their system and go with a lost station.
  New fighters/bombers are delivered only in the station's system (else they wait in its queue). City buildings
  are sized to stay off the sidewalks. The dead `_deliveries` stub is gone.
- **Multiplayer**: a client's `vessel_process` only animates (charges, captures, infection and swarmers are the
  host's). Client fighter hits reach the host (vessel index or net id). Breached walls are in the slow sync
  (`walls`). A client's breaching round and EMP are visual only; puppets show the EMP twitch from flag 128.
  Auto-reload is sent to the host. E on a client sends "use" (the host defuses, sets demo charges, kicks doors,
  plants charges, resupplies) and runs `player_use` locally to mirror its own kit; purge and sabotage are sent too.
  The helm is networked: "helm" action to take/leave it, `_helm_in` streams throttle/turn/aim/fire at 20 Hz, and the
  lock rides in the slow sync. The pause menu doesn't pause the tree in multiplayer. Lobby buttons show your real
  side and role.
- **Tests/docs**: `tests/compile.gd` reports failures and exits 1. `tests/campaign_test.gd` gives `_city` a city site
  (it used to crash there and fail the gravemind check). START_HERE, HANDOFF.md (roadmap, first-person controller),
  both READMEs, the F1 help (Up/Down for decks) and `godot_demo/HANDOFF.md` (now a pointer here) were corrected.
  `scripts/player.gd` is marked unused (it holds the only EVA movement code).

## Working locally on the user's Windows PC
For a session running on the user's PC (Claude desktop app, Code tab, Environment: Local). The cloud setup further
down is for Linux containers and doesn't apply. The user's Windows profile folder has spaces in it: quote every path.

- **Repos** (both cloned in the user's `Documents`):
  - `Documents\Unnamed-RTS` is this fork. A fresh clone is on `main`, so run `git fetch origin` and
    `git checkout handoff-tasks` first, and work only there.
  - `Documents\StarshipDemo-windows` holds builds. If it's missing, clone
    `https://github.com/cghath/StarshipDemo-windows.git` next to it.
  - Git is Git for Windows (2.55), so Claude's Bash tool runs in Git Bash. `git push` uses the user's own GitHub
    login: the first push may open a browser window to sign in.
- **Godot 4.5.1**: download `https://github.com/godotengine/godot/releases/download/4.5.1-stable/Godot_v4.5.1-stable_win64.exe.zip`
  into a tools folder outside the repo, e.g. `Documents\tools\godot`, and extract it.
  - Use `Godot_v4.5.1-stable_win64_console.exe` for commands, since it prints output to the terminal.
  - The plain `.exe` is the editor.
  - First run: `--headless --path godot_demo --import` (about a minute), then the compile check from the top of this file.
- **Run the game** (opens a window, which is what the user wants for playtesting): `<godot console exe> --path godot_demo`.
  - Editor: add `-e`.
  - The headless tests run the same as in the cloud: `-- --grenadiertest`, `-- --selftest`.
  - `--weaponshots` needs no Xvfb here, but it opens a window and takes over the screen for a few minutes:
    ask first.
- **Windows build from this PC**:
  1. Export templates go in `%APPDATA%\Godot\export_templates\4.5.1.stable\`. Get them from the `.tpz` named under
     "Windows build" below (1.3 GB, a zip). Only `templates\version.txt` and the `windows_*_x86_64*.exe` files are needed.
  2. Export with the line at the top of this file.
  3. To test locally, just run `godot_demo\build\windows\StarshipDemo.exe`. No splitting is needed.
  4. To publish to `StarshipDemo-windows`:
     - Split with Git Bash's `split` (the command under "Windows build" below).
     - Copy `PLAY.bat` from the newest build folder there, and update its part count, the `copy /b` list and the
       SHA-256 (`Get-FileHash StarshipDemo.exe -Algorithm SHA256`).
     - Add a `<date>_<commit>/` folder with the parts, `PLAY.bat` and a README, plus a row in the repo README.
     - Push to its `main`. Keep every file under 100 MB.

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
- Windows build: the export needs Godot's export templates. Download
  `https://github.com/godotengine/godot/releases/download/4.5.1-stable/Godot_v4.5.1-stable_export_templates.tpz` (1.3 GB),
  unzip only `templates/version.txt` and `templates/windows_*_x86_64*.exe` into
  `~/.local/share/godot/export_templates/4.5.1.stable/`, delete the .tpz, then run the Export line above from `godot_demo`.
  Check the pack with `$GODOT --headless --main-pack build/windows/StarshipDemo.exe res://match.tscn -- --grenadiertest`.
  Split with `split -b 28M --numeric-suffixes=1 -a 1 StarshipDemo.exe StarshipDemo.part`. PLAY.bat joins the parts with
  `copy /b`, checks the SHA-256 with `certutil`, and starts the game. Session 3 built commit dd88742 this way (5 parts).
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
    - Nobody has played a grenadier yet. The F2 kit has been rendered (`--weaponshots --only kit` swaps in a real F2
      grenadier) and fits its narrower hips.
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
   - ~~Send `gl_ammo`/`breach_ammo` in snapshots~~ (session 4).
   - The player's breaching round opens whatever it sticks near (not tied to a chosen door).
5. **Roadmap left**: zero-g / EVA in the game (port it from `player.gd`), a two-storey hangar, walkable pod and
   shuttle interiors.
6. **Playtest the session 4 fixes**, especially campaign save/load (research, caches, hangars, mini dropships) and
   multiplayer (helm, E actions, walls, fighters).
