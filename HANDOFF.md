# Starship Kit: project handoff

This is the full source of a Godot 4.5.1 space FPS/RTS hybrid, packaged as a base for a new project. Attach the zip parts to a new conversation, rejoin and unzip them, and point Claude at this file first.

## Rejoin and unzip
- **Windows:** `copy /b starship-kit.zip.part0+starship-kit.zip.part1+... starship-kit.zip`, then extract it.
- **Linux/macOS:** `cat starship-kit.zip.part* > starship-kit.zip && unzip starship-kit.zip`

## Layout
```
starship-kit/
  godot_demo/            Godot 4.5.1 project (open project.godot)
    scripts/             core game (~12k lines GDScript)
    scripts/campaign/    campaign / sandbox layer (~5k lines)
    models/              GLB assets: ships_F1 (Vanguard), ships_F2 (Ascendancy), ships_P (pirates),
                         ships_X (infected), stations_*, characters, weapons, items
    nav/                 pre-baked navmeshes per ship/station class (tests/bake_nav.gd regenerates)
    shaders/             planet, atmosphere, space sky
    tests/               headless test scenes (compile.tscn = parse check of every script)
    data/                ship/weapon data tables
  blender/ship_generator.py   procedural ship/station generator (Blender, bpy)
  tools/export_glb.py         batch export of generated ships to GLB
  economy/, data/, models_obj/, previews/   generator inputs and reference renders
```

## Running and testing
- Editor: open `godot_demo/project.godot` in Godot 4.5.1.
- Headless tests: `godot --headless --path godot_demo res://match.tscn -- --camptest` (also `--selftest --opstest --odsttest --fleettest --logtest --medtest`).
- Compile check: `godot --headless --path godot_demo res://tests/compile.tscn`.
- Windows export: `--export-release "Windows Desktop" build/windows/StarshipDemo.exe`.
- GDScript warnings are treated as errors. Type things explicitly (`var x: Vector3 = d["p"]`); `:=` from a Variant fails to parse.

## Core architecture (`scripts/`)

**Globals and the match**
- `game.gd` (autoload `G`):
  - Global registries: `vessels`, `characters`, `vehicles`, `pods`.
  - Teams and diplomacy: `TEAMS`, `standing`, `enemies`, `change_standing`. Teams are 1 player, 2 Ascendancy, 3 pirates/outlaws, 4 infected, 5 Vanguard Navy, 6 Union Merchant Guild, 7 Concord Free Traders.
  - Other state: resources, ship name generators, cutaway height, sfx node, effects (`explosion`, `tracer`).
- `match.gd`: builds a match (skirmish or campaign).
  - Spawns ships and stations, owns the economy tick, jumps, landing and take-off.
  - Ground deploy and recall of troops and vehicles.
  - Hosts the test hooks.

**Vessels**
- `vessel.gd`: base class for anything with decks: rooms, doors, nav, crew, systems, hull, red alert.
- `ship.gd`:
  - Ship movement and per-class gun layouts (`TURRET_SPECS`, `LAYOUTS`).
  - Manned turrets and broadside batteries; penetration vs `ARMOR`.
  - Dropship artillery and napalm; hull repair; altitude while on a surface.
- `station.gd`: stations, segments, production.

**People**
- `character.gd`: every person aboard or on the ground.
  - Roles, AI states and cover use.
  - Medical: pens, revive gun, downed, carrying to medbay.
  - Manning guns; TTK damage table; void rescue; patrols.
- `squad.gd`: squad orders and breach stacking.
- `ai.gd`: commander AI.
- `player.gd` + `viewmodel.gd`: first-person controller and weapon viewmodel (ADS, scopes in a PiP SubViewport).
- `rig.gd`: procedural character rig and animation.

**Small craft and projectiles**
- `pod.gd`, `drop_pod.gd`, `shuttle.gd`, `supply_shuttle.gd`, `fighter.gd`, `missile.gd`, `grenade.gd`.

**Logistics**
- `logistics.gd`: parking zones, ferrying troops, supply runs.

**UI**
- `commander.gd`: RTS camera and selection.
  - Orders: right-click, Ctrl+right force attack.
  - Cutaway by deck (arrow keys, X); taking manual control of a gun.
- `hud.gd`: HUD and selection cards. `action_bar.gd`: bottom command card. `minimap.gd`.
- `menu.gd`: main menu (skirmish and campaign).

**Other**
- `sfx.gd`: all audio is synthesized at runtime (no audio assets).
- `network.gd`: early multiplayer layer.

## Campaign layer (`scripts/campaign/`)

**Galaxy, state and population**
- `galaxy.gd`: 6-system galaxy, biomes, economies, goods. `campaign.gd`: persistent state (fleet, stores, jobs, markets, surface), saved to `user://campaign.json`.
- `sector.gd`: populates a system: planets, gates, NPC ships, job targets.
- `sandbox_ai.gd`: traders, patrols, pirates, infected hives, ground roaming.

**Economy and building**
- `miner.gd`: mining craft. `builder.gd`: build queue for ships, craft, vehicles, squads, and snapping station segments.
- `campaign_ui.gd`: menus for ships, units, station, research, galaxy map and services.
- `cargo_view.gd`: labelled crates in ship holds.

**Planet surfaces**
- `surface.gd`: procedural terrain (height function, water, flora), landing zones.
- `ground.gd`: the ground "vessel". It holds tiled navmesh baked in the background and a cover-point grid (`cover_near`).
- `ruins.gd`:
  - Wrecks and procedural abandoned cities: random-walk streets.
  - Buildings: 1–2 storey with windows, interiors and decay, plus gutted towers with rubble fans.
  - Salvage caches; outlaw or infected occupants.

**Ground vehicles and dropships**
- `vehicle.gd`: tanks, IFVs, MRAPs, mechs and mortars for both factions (procedural models). `mrap.gd`: outlaw MRAP.
- `bays.gd`: vehicle ramps and mech bay. `minidrop.gd`: mini dropships (dock, load on foot or by elevator, fly, unload).

## Key conventions
- Turrets are dictionaries: `root/node/bar/kind/mount/spec/gunner/seat/player`.
- Ground positions come from `match.ground_y(x, z)`, which uses `SURFACE.height(terrain_P, system, x, z)`, with `GROUND_Y = -160`.
- Cover points are `[world_pos, low:bool, facing_dir]`, stored in `match.ground_cover` and gridded by `ground.gd`.
- Async callbacks after a scene reload go through a weakref (see `G.nav_tile_baked`).
- Assets are procedural: ships come from Blender (`blender/ship_generator.py`), and vehicles, buildings and terrain are built in GDScript.

## Not finished (from the original roadmap)
- Stations and outposts:
  - A core ship that starts new stations.
  - Player outposts with RTS-style building.
- Ships and boarding:
  - Two-storey hangar.
  - Zero-g / EVA, airlocks.
  - Breachable walls.
  - Walkable pod and shuttle interiors.
- Ground and vehicles:
  - Player driving of vehicles.
  - Supply ship landing and loading cargo from the ground.
- Systems: fog of war and radar.
