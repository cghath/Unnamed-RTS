"""
Economy data: resources, fuel, Cores, recipes, station modules, and the cost of
every ship, craft and robot. The game is real time, so every rate is PER MINUTE
and every time is in SECONDS.

Edit the numbers here, then run:   python economy_data.py
It checks the data and writes data/economy.json for Godot.

THE LOOP
  mine raw resources -> haul them (Darters / supply ships) -> refine -> build
  Ore -> Alloys        (hulls, armor, robot bodies, station modules)
  Crystals -> Circuitry (electronics, weapons, ship systems, Cores)
  Ice / Gas -> Hydrogen (sublight fuel)
  Lithium -> Tritium    (jump fuel; slow to breed, strategic)
  Cores                 (the robots' minds = your population; slow to make)

STORAGE
  Each star system has one shared stockpile across the stations you own there.
  Moving resources BETWEEN systems needs a supply ship to jump with the cargo.
  1 cargo pallet = 25 units. A Darter carries 4 pallets (100 units).
"""

import json
import os

# ------------------------------------------------------------------ resources
RESOURCES = {
    # name: (tier, what players are told)
    "ore":       ("raw", "Metal-rich rock from asteroid fields. Refined into Alloys."),
    "crystals":  ("raw", "Rare conductive crystals from rich fields and derelicts. Refined into Circuitry."),
    "ice":       ("raw", "Water ice from ice fields and moons. Split into Hydrogen."),
    "gas":       ("raw", "Gas giant atmosphere, scooped by skimmers. Refined into Hydrogen."),
    "lithium":   ("raw", "Rare lithium deposits. Bred into Tritium in breeder reactors."),
    "alloys":    ("refined", "Structural metal: hulls, armor, robot bodies, station modules."),
    "circuitry": ("refined", "Electronics: weapons, ship systems, robot brains."),
    "hydrogen":  ("fuel", "Sublight fuel. Burned while flying inside a star system."),
    "tritium":   ("fuel", "Jump fuel. Burned to jump between star systems."),
    "cores":     ("population", "AI cores - the minds of your robots. Every crew member and "
                                "soldier needs one. Recover cores from your fallen or lose them."),
}
PALLET_UNITS = 25
DARTER_PALLETS = 4

# ------------------------------------------------------------------ fuel per ship class
#   hydrogen_tank / hydrogen_per_km: sublight (km = real meters in the arena / 1000)
#   tritium_tank / tritium_per_ly:   jumping (lanes are 1-4 light years long)
#   XS craft can't jump on their own; they ride in hangars, cargo bays and tubes.
FUEL = {
    "XS":     dict(hydrogen_tank=40,   hydrogen_per_km=0.5, tritium_tank=0,  tritium_per_ly=0, can_jump=False),
    "SMALL":  dict(hydrogen_tank=300,  hydrogen_per_km=1.0, tritium_tank=10, tritium_per_ly=1, can_jump=True),
    "MEDIUM": dict(hydrogen_tank=700,  hydrogen_per_km=2.0, tritium_tank=16, tritium_per_ly=2, can_jump=True),
    "LARGE":  dict(hydrogen_tank=1400, hydrogen_per_km=4.0, tritium_tank=30, tritium_per_ly=4, can_jump=True),
    "XL":     dict(hydrogen_tank=2800, hydrogen_per_km=8.0, tritium_tank=48, tritium_per_ly=8, can_jump=True),
}
FUEL_OVERRIDES = {   # craft that differ from their size class
    "XS_MINER": dict(hydrogen_tank=120, hydrogen_per_km=0.8, tritium_tank=4, tritium_per_ly=1, can_jump=True,
                     note="Mining ships carry a small jump drive so they can move to new fields."),
}
JUMP = dict(spool_up_s=20, cooldown_s=30, seconds_per_ly=15,
            note="Ships charge for spool_up_s at a jump point (vulnerable), then spend "
                 "seconds_per_ly in transit per light year of lane.")
SUPPLY_SHIP_CARGO_UNITS = 300          # SMALL_SUPPORT hold (12 storage slots of 25)
SUPPLY_SHIP_FUEL = dict(hydrogen=1500, tritium=40)   # extra fuel it can hand out to the fleet

# ------------------------------------------------------------------ build costs
# Ships: alloys, circuitry, build time; crew cores come from STANDARD_CREW (ship_generator.py).
SHIP_COSTS = {
    "XS_FIGHTER":         dict(alloys=60,    circuitry=30,   build_s=90,   cores=1),
    "XS_BOMBER":          dict(alloys=100,   circuitry=50,   build_s=150,  cores=2),
    "XS_DROPSHIP":        dict(alloys=120,   circuitry=40,   build_s=120,  cores=2),
    "XS_DARTER":          dict(alloys=80,    circuitry=20,   build_s=90,   cores=2),
    "XS_POD":             dict(alloys=20,    circuitry=5,    build_s=30,   cores=0),
    "XS_DROPPOD":         dict(alloys=8,     circuitry=2,    build_s=15,   cores=0),
    "XS_MINER":           dict(alloys=300,   circuitry=100,  build_s=120,  cores=3),
    "XS_MINING_DRONE":    dict(alloys=30,    circuitry=15,   build_s=30,   cores=0),   # drones are simple machines, no core
    "SMALL_FRIGATE":      dict(alloys=700,   circuitry=250,  build_s=300,  cores=15),
    "SMALL_SUPPORT":      dict(alloys=600,   circuitry=200,  build_s=300,  cores=15),
    "SMALL_DROP_FRIGATE": dict(alloys=800,   circuitry=300,  build_s=360,  cores=15),
    "MEDIUM":             dict(alloys=1500,  circuitry=500,  build_s=480,  cores=30),
    "LARGE":              dict(alloys=3500,  circuitry=1300, build_s=900,  cores=60),
    "XL":                 dict(alloys=8000,  circuitry=3000, build_s=1500, cores=100),
}
# Which shipyard size can build each class (shipyards come in sizes).
SHIPYARD_FOR = {"XS": "small", "SMALL": "small", "MEDIUM": "medium", "LARGE": "large", "XL": "large"}

# Robots: a body from the Assembly plant + a Core + a role kit from the Fabricator.
ROBOT_BODY = dict(alloys=12, circuitry=4, build_s=30)
ROLE_KITS = {        # armor + weapons + starting inventory, per role (both factions; F2 kits cost more circuitry)
    "combat":   dict(alloys=10, circuitry=6, build_s=20, faction2_extra_circuitry=4),
    "eva":      dict(alloys=14, circuitry=8, build_s=25, faction2_extra_circuitry=4),
    "crew":     dict(alloys=2, circuitry=1, build_s=5, faction2_extra_circuitry=0),
    "security": dict(alloys=6, circuitry=4, build_s=12, faction2_extra_circuitry=2),
    "science":  dict(alloys=8, circuitry=14, build_s=30, faction2_extra_circuitry=0),   # includes a purge emitter
}
RESUPPLY = dict(magazine_or_cell=dict(alloys=0.2, circuitry=0.2), grenade=dict(alloys=0.3, circuitry=0.3),
                medpen=dict(circuitry=0.5), revive_kit=dict(circuitry=2), breach_charge=dict(alloys=1, circuitry=1))

# ------------------------------------------------------------------ mining ships
# Active mining: a mining ship sits at an asteroid field, cuts with its own laser and
# sends out its drones, then flies to a docking ring (or any station with storage)
# to unload. Faster than a static mining rig, but it needs escorts - prime raid bait.
MINING = dict(
    miner=dict(model="XS_MINER", crew_cores=3, hold_units=300, laser_per_min=100, drones=4,
               drone_range_m=1500, unload_at=["docking_ring", "storage_depot"], unload_per_min=300),
    drone=dict(model="XS_MINING_DRONE", hold_units=25, laser_per_min=25, returns_to="its miner",
               note="Drones mine nearby rocks, fly their load back to the mining ship, and repeat."),
    field_types=["ore", "crystals", "ice", "lithium"],
    note="Gas is skimmed by gas_skimmer modules, not mined.",
)

# ------------------------------------------------------------------ station modules
# For each module:
#   anchor:   what it must be built at (None = anywhere the station is)
#   cost:     alloys / circuitry to build, build_s to construct
#   hull, armor: hit points from outside; armor reduces ship-weapon damage
#   power:    + produces / - consumes. Modules without enough power go Offline.
#   crew:     cores needed to run it (a captured module needs YOUR crew)
#   makes:    recipe per minute at full output: {"in": {...}, "out": {...}}
#   interior: size of its boardable interior for the station generator
#             (sections, decks), and how many sabotage points it has
MODULE_STATES = {
    "online":    dict(output=1.0, how="Normal operation."),
    "offline":   dict(output=0.0, how="Switched off from its control room - by the owner, by boarders holding "
                                      "the control room, or automatically when station power runs short. No damage."),
    "sabotaged": dict(output=0.5, how="Boarders planted charges or hacked critical systems. Output halved; "
                                      "defenses and shields flicker."),
    "disabled":  dict(output=0.0, how="Heavily damaged by ship fire or demolition inside. Interior partly wrecked."),
    "destroyed": dict(output=0.0, how="Hull gone. A salvageable wreck remains; the module must be rebuilt."),
    "infected":  dict(output=0.0, how="The infection has taken the module (or a ship compartment). It spreads, "
                                      "converts unrecovered cores and blocks every repair. ONLY scientists with "
                                      "purge emitters can clear it; afterwards the module drops to the damage "
                                      "state underneath and engineers take over."),
}
REPAIR = {   # cost as a fraction of the module's build cost, time, and engineers needed
    "offline":   dict(cost_fraction=0.0,  seconds=15,  engineers=0, note="Reboot from the control room."),
    "sabotaged": dict(cost_fraction=0.05, seconds=60,  engineers=2, note="Engineers with tools at each sabotaged point."),
    "disabled":  dict(cost_fraction=0.30, seconds=240, engineers=4, note="Engineers plus materials delivered to the module."),
    "destroyed": dict(cost_fraction=0.80, seconds=None, engineers=6,
                      note="Rebuild at 80% cost (salvage from the wreck covers the rest), full build time."),
}
REPAIR["infected"] = dict(cost_fraction=0.0, seconds=None, engineers=0, scientists=2,
                         note="Cleared only by scientists sweeping it with purge emitters (see INFECTION).")
SALVAGE_FRACTION = 0.20      # of build cost, recovered by salvaging a destroyed module's wreck

# ------------------------------------------------------------------ infection & purging
INFECTION = dict(
    spread_s_per_compartment=120,     # an uncontested infected compartment takes a neighbor this often
    hull_spread_s=300,                # exterior hull growth spreads to an adjacent module/section
    converts_unrecovered_cores=True,
    blocks_repair=True,
    purge_emitter=dict(
        carried_by="scientist", radius_m=4.0, clear_m2_per_s=6.0, battery_s=180, recharge_s=60,
        note="A field projected around the scientist that burns the infection off surfaces - "
             "like the field the Spirit of Fire passed through on the shield world. Interiors are "
             "cleared compartment by compartment; hull growth is cleared by scientists on EVA."),
    scientist_kit=dict(alloys=8, circuitry=14, build_s=30),
    intel=dict(
        memory_minutes=20,
        records=["enemy units seen (type, count)", "ships seen (class)", "stations and modules seen (type, state)",
                 "where (system + position)", "when (game time)"],
        on_conversion="When the infection converts a core, it inherits that robot's memory log: what it saw, "
                      "where and when. Not live tracking and not everything the faction knows - only that "
                      "robot's own sightings from its last memory_minutes, marked with how old they are.",
        counterplay="Retrieve your fallen cores, and change patrol routes or station defenses after losses "
                    "to the infection - its picture of you goes stale.",
    ),
    note="Nothing else removes infection: not engineers, not weapons, not explosives (those only "
         "destroy the module along with it).",
)

# POWER IS THE LIMIT. A station's grid can carry at most its root's grid_capacity
# (command core 400, outpost core 80), no matter how many reactors it has. Heavy
# industry draws a lot, so no single station can run everything at once: switch
# modules Offline to free power, or spread production over several stations
# (which also gives the enemy more to raid). Modules that can't get power go Offline.
MODULES = {
    "command_core":    dict(anchor=None, cost=dict(alloys=800, circuitry=250), build_s=420, hull=6000, armor=0.40,
                            power=-10, grid_capacity=400, crew=12, makes=None, interior=(3, 2), sabotage_points=3,
                            does="Required root of every station. Holding its control room captures the station."),
    "outpost_core":    dict(anchor=None, cost=dict(alloys=500, circuitry=150), build_s=240, hull=2500, armor=0.30,
                            power=+40, grid_capacity=80, crew=4, makes=None, interior=(2, 1), sabotage_points=2,
                            does="Root of a small outpost (a mining or skimming site): a compact command core "
                                 "with its own small reactor. Holding its control room captures the outpost."),
    "reactor":         dict(anchor=None, cost=dict(alloys=400, circuitry=150), build_s=240, hull=3500, armor=0.30,
                            power=+130, crew=6, makes=None, interior=(2, 2), sabotage_points=3,
                            does="Powers the station. Knock it out and every module it feeds goes Offline."),
    "mining_rig":      dict(anchor="asteroid_field", cost=dict(alloys=300, circuitry=80), build_s=180, hull=2000,
                            armor=0.20, power=-20, crew=4, makes={"in": {}, "out": {"field_resource": 80}},
                            interior=(2, 1), sabotage_points=2,
                            does="Mines its field's resource: ore, crystals, ice or lithium."),
    "gas_skimmer":     dict(anchor="gas_giant", cost=dict(alloys=700, circuitry=200), build_s=270, hull=2000,
                            armor=0.20, power=-20, crew=4, makes={"in": {}, "out": {"gas": 60}},
                            interior=(2, 1), sabotage_points=2, does="Scoops gas from a gas giant."),
    "refinery":        dict(anchor=None, cost=dict(alloys=600, circuitry=200), build_s=240, hull=2500, armor=0.25,
                            power=-60, crew=6, interior=(2, 2), sabotage_points=3,
                            makes={"in": {"ore": 600, "crystals": 300, "ice": 60, "gas": 80},
                                   "out": {"alloys": 300, "circuitry": 150, "hydrogen": 140}},
                            does="Ore->Alloys (2:1), Crystals->Circuitry (2:1), Ice/Gas->Hydrogen (1:1). "
                                 "Each line runs only while it has input."),
    "breeder_reactor": dict(anchor=None, cost=dict(alloys=1100, circuitry=700), build_s=420, hull=2500, armor=0.30,
                            power=-60, crew=6, makes={"in": {"lithium": 8}, "out": {"tritium": 2}},
                            interior=(2, 2), sabotage_points=3, does="Breeds Tritium from Lithium (4:1). Slow."),
    "fabricator":      dict(anchor=None, cost=dict(alloys=700, circuitry=400), build_s=300, hull=2000, armor=0.20,
                            power=-30, crew=4, makes="role_kits_and_resupply", interior=(2, 1), sabotage_points=2,
                            does="Makes weapons, armor kits and resupply (mags, cells, grenades, medpens, charges)."),
    "core_foundry":    dict(anchor=None, cost=dict(alloys=600, circuitry=400), build_s=300, hull=2200, armor=0.30,
                            power=-70, crew=6, makes={"in": {"circuitry": 12, "alloys": 6}, "out": {"cores": 3}},
                            interior=(2, 2), sabotage_points=3,
                            does="Makes Cores - your population. Slow and power hungry."),
    "assembly_plant":  dict(anchor=None, cost=dict(alloys=800, circuitry=300), build_s=300, hull=2200, armor=0.20,
                            power=-35, crew=4, makes="robot_bodies", interior=(2, 1), sabotage_points=2,
                            does="Builds robot bodies and fits them with a Core and a role kit."),
    "shipyard_small":  dict(anchor=None, cost=dict(alloys=1500, circuitry=500), build_s=480, hull=4000, armor=0.25,
                            power=-50, crew=10, makes="ships_up_to_small", interior=(3, 1), sabotage_points=3,
                            does="Builds XS craft and SMALL ships."),
    "shipyard_medium": dict(anchor=None, cost=dict(alloys=1200, circuitry=400), build_s=360, hull=6000, armor=0.25,
                            power=-80, crew=16, makes="ships_up_to_medium", interior=(4, 2), sabotage_points=4,
                            does="Builds up to MEDIUM ships."),
    "shipyard_large":  dict(anchor=None, cost=dict(alloys=7000, circuitry=2500), build_s=1080, hull=9000, armor=0.30,
                            power=-130, crew=24, makes="ships_up_to_xl", interior=(5, 2), sabotage_points=5,
                            does="Builds up to XL ships."),
    "storage_depot":   dict(anchor=None, cost=dict(alloys=400, circuitry=50), build_s=180, hull=2500, armor=0.20,
                            power=-5, crew=2, makes=None, storage=5000, interior=(2, 1), sabotage_points=1,
                            does="+5000 stockpile capacity for the system."),
    "fuel_depot":      dict(anchor=None, cost=dict(alloys=600, circuitry=150), build_s=240, hull=2000, armor=0.20,
                            power=-10, crew=2, makes=None, fuel_storage=dict(hydrogen=8000, tritium=200),
                            refuel_rate=dict(hydrogen=400, tritium=10), interior=(2, 1), sabotage_points=2,
                            does="Stores fuel and refuels docked ships. Sabotage it to strand a fleet."),
    "docking_ring":    dict(anchor=None, cost=dict(alloys=300, circuitry=80), build_s=120, hull=2500, armor=0.20,
                            power=-10, crew=4, makes=None, darter_pads=3, miner_berths=2, unload_per_min=300,
                            airlocks=4, interior=(2, 1),
                            sabotage_points=1, does="Supply ships and Darters load and unload here."),
    "barracks":        dict(anchor=None, cost=dict(alloys=600, circuitry=200), build_s=240, hull=2500, armor=0.25,
                            power=-10, crew=2, makes=None, garrison=60, interior=(2, 2), sabotage_points=1,
                            does="Houses up to 60 troops as the station's garrison."),
    "defense_platform": dict(anchor=None, cost=dict(alloys=1200, circuitry=600), build_s=360, hull=4000, armor=0.40,
                             power=-30, crew=6, makes=None, weapons="2 heavy turrets + point defense",
                             interior=(1, 1), sabotage_points=2,
                             does="Guns. Switch it Offline from inside to approach without destroying it."),
    "shield_generator": dict(anchor=None, cost=dict(alloys=900, circuitry=900), build_s=420, hull=2500, armor=0.30,
                             power=-60, crew=4, makes=None, shield=8000, interior=(2, 1), sabotage_points=2,
                             does="Shields every module of the station while powered."),
    # ---- ground installations: built ON a large asteroid (anchor "large_asteroid") ----
    "ground_core":     dict(anchor="large_asteroid", cost=dict(alloys=900, circuitry=300), build_s=300, hull=5000,
                            armor=0.50, power=+60, grid_capacity=100, crew=6, makes=None, interior=(2, 1),
                            sabotage_points=2,
                            does="Root of a ground base dug into a large asteroid: buried command post with a small "
                                 "reactor. Tough from orbit; take it with troops (drop pods, dropships, Darters)."),
    "surface_drill":   dict(anchor="large_asteroid", cost=dict(alloys=500, circuitry=150), build_s=210, hull=2500,
                            armor=0.40, power=-25, crew=3, makes={"in": {}, "out": {"asteroid_resource": 25}},
                            interior=(1, 1), sabotage_points=2, does="Drills the asteroid's own resource."),
    "ground_battery":  dict(anchor="large_asteroid", cost=dict(alloys=1000, circuitry=500), build_s=300, hull=4500,
                            armor=0.55, power=-35, crew=5, makes=None, weapons="long-range surface guns + flak",
                            interior=(1, 1), sabotage_points=2,
                            does="System defense from a hardened surface emplacement. Switch it Offline from inside."),
    "landing_pads":    dict(anchor="large_asteroid", cost=dict(alloys=400, circuitry=100), build_s=180, hull=3000,
                            armor=0.40, power=-10, crew=3, makes=None, darter_pads=2, dropship_pads=2,
                            interior=(1, 1), sabotage_points=1,
                            does="Where Darters and dropships land. Enemies land here too - or drop pods hit the surface."),
    "comm_relay":      dict(anchor=None, cost=dict(alloys=300, circuitry=300), build_s=180, hull=1200, armor=0.15,
                            power=-10, crew=2, makes=None, sensor_range_lanes=1, interior=(1, 1), sabotage_points=1,
                            does="Reveals neighboring systems on the galaxy map."),
}

GROUND_BASES = dict(
    anchor="large_asteroid",
    allowed=["ground_core", "surface_drill", "ground_battery", "landing_pads", "storage_depot", "barracks",
             "comm_relay", "fuel_depot"],
    note="Large asteroids host small ground installations for system defense or mining. Low gravity, "
         "exposed surface fights between buildings, and tunnels inside them. Small power grid (100), so "
         "a ground base specializes: a defense battery site OR a drilling site, rarely both.",
)

CONSTRUCTION = dict(
    builders=["SMALL_SUPPORT"],
    note="Modules at an existing station are built by that station. A NEW station or outpost in another "
         "spot is built by a supply ship parked there, paying the module costs from the stockpile it "
         "carries or from the system stockpile.",
    station_kits=dict(
        industrial_station=["command_core", "reactor", "reactor", "refinery", "shipyard_medium", "core_foundry",
                            "docking_ring"],
        fortress=["command_core", "reactor", "reactor", "defense_platform", "defense_platform", "shield_generator",
                  "barracks", "docking_ring"],
        fuel_hub=["command_core", "reactor", "breeder_reactor", "fuel_depot", "storage_depot", "docking_ring"],
    ),
    outpost_kits=dict(
        mining_outpost=["outpost_core", "mining_rig"],
        skimmer_outpost=["outpost_core", "gas_skimmer"],
        ground_mine=["ground_core", "surface_drill"],
        ground_fort=["ground_core", "ground_battery", "landing_pads"],
    ),
)

# ------------------------------------------------------------------ system control
CONTROL = dict(
    rule="You control a system when you own a station core in it (command core, outpost core or ground "
         "core) AND no armed pirate or enemy installation in the system is still active (online).",
    uncontrolled="You can fly, fight, mine with mining ships and salvage in any system, but you can only "
                 "build modules, share the system stockpile and refuel at depots in systems you control.",
    contested="If two factions both own cores in a system, nobody controls it until one side's cores are "
              "destroyed or captured.",
    founding="A supply ship can drop a new core in an uncontrolled system even while pirates are present; "
             "the core is yours, but the system stays contested until the pirates' armed installations "
             "are destroyed, captured or switched Offline.",
)

# ------------------------------------------------------------------ pirates
# A third faction, hostile to everyone. Pirates hold systems, defend them, and never
# expand; their strength and abilities come from what the system contains. They are
# a challenge on the way out, not a wall: the galaxy generator caps their strength by
# how far the system is from the nearest home, so there is always a beatable route.
PIRATES = dict(
    power=dict(XS_FIGHTER=0.25, SMALL_FRIGATE=1.0, MEDIUM=3.0, LARGE=6.0, defense_platform=1.5,
               ground_battery=1.5, shield_bonus=0.3),
    player_reference=dict(start_fleet=2.0, note="Power of the starting fleet (frigate + support + fighters), "
                                                "for comparing against pirate presences."),
    tier_cap_by_hops={1: 1, 2: 2, 3: 3, 4: 4},
    tier_power_cap={1: 2.0, 2: 5.0, 3: 9.0, 4: 14.0, 5: 20.0},
    capabilities_from_resources={
        "ore":            "pirate shipyard: replaces lost fighters/frigates every few minutes",
        "gas":            "fuel: pirate ships fight longer and pursue",
        "ice":            "fuel depot: pirates refuel and repair between fights",
        "crystals":       "shields on installations and energy turrets (+30% power)",
        "lithium":        "jump-capable raiders: occasionally raid neighboring player outposts",
        "large_asteroid": "ground fort dug into the asteroid (ground core + batteries + garrison)",
        "derelict":       "a refitted flagship salvaged from the wreck",
        "ancient_site":   "fanatics guarding the site: strongest presence, and the infection is near",
    },
    respawn_min=6,            # pirate shipyards replace losses this often (if the system has ore)
    raid_interval_min=15,     # lithium-rich pirates raid a neighbor this often
    garrison_per_tier=8,      # troops per installation, per tier (for boarding fights)
    loot=dict(alloys_per_value=120, circuitry_per_value=50, captured_modules="kept intact if taken by boarding"),
)

# ------------------------------------------------------------------ home stations
HOME_STATION = dict(
    modules=["command_core", "reactor", "reactor", "reactor", "refinery", "breeder_reactor", "fabricator",
             "core_foundry", "assembly_plant", "shipyard_small", "shipyard_medium", "storage_depot",
             "fuel_depot", "docking_ring", "barracks", "defense_platform", "defense_platform",
             "shield_generator", "comm_relay"],
    start_stock=dict(ore=500, crystals=0, ice=500, gas=0, lithium=100, alloys=3500, circuitry=1200,
                     hydrogen=3000, tritium=40, cores=80),
    start_fleet=["SMALL_FRIGATE", "SMALL_SUPPORT", "XS_DARTER", "XS_DARTER", "XS_FIGHTER", "XS_FIGHTER",
                 "XS_MINER"],
    base_storage=10000,
    note="Home systems also start with one ore field, one ice field and a gas giant with mining "
         "rigs / a skimmer already built (added by the galaxy generator).",
)

# ------------------------------------------------------------------ cores
CORE_RULES = dict(
    drop="A destroyed robot drops its core where it fell (in a corridor, on a hull, floating in space).",
    retrieval="The core stays retrievable by ITS OWN SIDE for as long as it lies there - there is no "
              "timer. Walk over it, use a revive kit on the body, or tow it with a ship or drone.",
    infection="If the infection reaches an unretrieved core first, the core is converted and lost: it "
              "becomes an infected unit. Clearing the area with purge emitters does not bring it back.",
    enemies="Enemies cannot use your cores, but they can deny them by holding the ground (or by "
            "letting the infection get there first).",
)


def check():
    problems = []
    for m, d in MODULES.items():
        if isinstance(d["makes"], dict):
            for side in ("in", "out"):
                for r in d["makes"][side]:
                    if r not in RESOURCES and r not in ("field_resource", "asteroid_resource"):
                        problems.append(f"{m}: unknown resource {r}")
    for s in HOME_STATION["modules"]:
        if s not in MODULES:
            problems.append(f"home station: unknown module {s}")
    supply = sum(MODULES[m]["power"] for m in HOME_STATION["modules"] if MODULES[m]["power"] > 0)
    grid = MODULES["command_core"]["grid_capacity"]
    demand = -sum(MODULES[m]["power"] for m in HOME_STATION["modules"] if MODULES[m]["power"] < 0)
    essentials = -sum(MODULES[m]["power"] for m in HOME_STATION["modules"]
                      if m in ("command_core", "storage_depot", "fuel_depot", "docking_ring", "barracks", "comm_relay",
                               "defense_platform", "shield_generator"))
    if essentials > min(supply, grid):
        problems.append("home station can't even power its essentials and defenses")
    return problems, dict(supply=supply, grid=grid, usable=min(supply, grid), demand_if_all_on=demand,
                          essentials=essentials, left_for_industry=min(supply, grid) - essentials)


def export(path):
    data = dict(resources={k: dict(tier=t, description=d) for k, (t, d) in RESOURCES.items()},
                pallet_units=PALLET_UNITS, darter_pallets=DARTER_PALLETS, fuel=FUEL, fuel_overrides=FUEL_OVERRIDES, jump=JUMP, mining=MINING,
                supply_ship=dict(cargo_units=SUPPLY_SHIP_CARGO_UNITS, fuel=SUPPLY_SHIP_FUEL),
                ship_costs=SHIP_COSTS, shipyard_for=SHIPYARD_FOR, robot_body=ROBOT_BODY, role_kits=ROLE_KITS,
                resupply=RESUPPLY, module_states=MODULE_STATES, repair=REPAIR, salvage_fraction=SALVAGE_FRACTION,
                modules=MODULES, ground_bases=GROUND_BASES, construction=CONSTRUCTION, control=CONTROL, pirates=PIRATES, home_station=HOME_STATION, core_rules=CORE_RULES, infection=INFECTION)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    probs, power = check()
    if probs:
        print("PROBLEMS:", *probs, sep="\n  ")
        raise SystemExit(1)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "economy.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    export(out)
    print(f"Economy data OK. Home station power: {power}. Wrote {os.path.normpath(out)}")
