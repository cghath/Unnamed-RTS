"""
Economy pace check: plays a scripted "competent player" for the first 120 minutes of
real time, so you can see what the numbers in economy/economy_data.py produce.

    python tools/simulate_economy.py

Targets (12-system map, games of about 2 hours):
  * Medium ships coming off the line about once every 5 minutes by minute 40.
  * Cores, alloys and circuitry not collapsing afterwards (production is sustainable).

What the scripted player does
  * Small shipyard (home): builds the queue in SMALL_YARD_PLAN (mining ships, a
    second supply ship...). Each new mining ship goes to the next field in
    MINER_TARGETS and hauls its own load home (65% of its full rate).
  * Supply ships: build each job in CONSTRUCTION_PLAN, in order - mining outposts
    (Darters haul their output home at 90%) and a second, undefended industrial
    station with its own refinery, medium shipyard and core foundry.
  * Medium shipyards (home + industrial station): build Mediums back to back.
  * Every station's manager gives its spare power, in order, to: a shipyard that is
    building or can afford to start, the refinery, the core foundry (when cores run
    short), the breeder reactor, the fabricator. The home station keeps its defenses on.
It does not model combat or pirates (clearing a system just delays an outpost).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "economy"))
import economy_data as E  # noqa: E402

MINUTES = 120
TRAVEL_MIN = 3                 # supply ship / new miner getting to a neighboring system
REMOTE_HAUL = 0.65             # a miner hauling its own load home between loads
DARTER_HAUL = 0.90             # outpost output carried home by Darters
CORE_TARGET = 60               # foundries run while cores are below this
SAVE_FOR_STATION = True        # the opening saves for the industrial station before building Mediums

SMALL_YARD_PLAN = ["XS_MINER", "XS_MINER", "XS_MINER", "SMALL_SUPPORT", "XS_MINER", "XS_MINER", "XS_MINER"]
MINER_TARGETS = ["crystals", "ore", "ore", "crystals", "ore", "ore", "crystals"]
CONSTRUCTION_PLAN = [("outpost", "mining_outpost", "crystals"), ("station", "industrial_station", None),
                     ("outpost", "mining_outpost", "ore"), ("outpost", "mining_outpost", "crystals"),
                     ("outpost", "mining_outpost", "ore"), ("outpost", "mining_outpost", "crystals")]
ESSENTIALS = ["command_core", "storage_depot", "fuel_depot", "docking_ring", "barracks", "comm_relay",
              "defense_platform", "shield_generator"]


def cost_of(modules):
    c = dict(alloys=0, circuitry=0)
    for m in modules:
        for k in c:
            c[k] += E.MODULES[m]["cost"][k]
    return c


class Station:
    def __init__(self, name, modules):
        self.name, self.modules = name, list(modules)
        M = E.MODULES
        root = "command_core" if "command_core" in modules else "outpost_core"
        supply = sum(M[m]["power"] for m in modules if M[m]["power"] > 0)
        usable = min(supply, M[root]["grid_capacity"])
        self.budget = usable + sum(M[m]["power"] for m in modules if m in ESSENTIALS)
        self.yard_job, self.yard_progress = None, 0.0


def simulate(minutes=MINUTES, verbose=True):
    M, H, MI = E.MODULES, E.HOME_STATION, E.MINING
    stock = dict(H["start_stock"])
    stations = [Station("home", H["modules"])]
    miner_full = (MI["miner"]["laser_per_min"] + MI["miner"]["drones"] * MI["drone"]["laser_per_min"]) * 0.75
    rig = M["mining_rig"]["makes"]["out"]["field_resource"]
    income = [("ore", rig * 1.2, 0), ("ice", rig, 0), ("gas", M["gas_skimmer"]["makes"]["out"]["gas"], 0),
              ("ore", miner_full * 0.9, 0)]                         # home rigs, skimmer, starting miner
    small_plan, construction = list(SMALL_YARD_PLAN), list(CONSTRUCTION_PLAN)
    miner_targets = list(MINER_TARGETS)
    builders = [dict(job=None, progress=0.0) for s in H["start_fleet"] if s == "SMALL_SUPPORT"]
    station_started = not SAVE_FOR_STATION
    small_yard = dict(job=None, progress=0.0)
    log, mediums, history, power_min = [], [], [], {}

    def note(t, msg):
        if not log or log[-1][1] != msg:
            log.append((t, msg))

    reserve = {}

    def can_pay(c, use_reserve=False):
        held = reserve if use_reserve else {}
        return all(stock.get(k, 0) - held.get(k, 0) >= v for k, v in c.items())

    def pay(c):
        for k, v in c.items():
            stock[k] -= v

    for t in range(1, minutes + 1):
        for res, rate, start in income:
            if t >= start:
                stock[res] += rate
        # ---- expansion comes first: hold back what the next construction job needs
        reserve = {}
        if construction and any(b["job"] is None for b in builders):
            kind, kit, _ = construction[0]
            reserve = cost_of(E.CONSTRUCTION["outpost_kits"][kit] if kind == "outpost"
                              else E.CONSTRUCTION["station_kits"][kit])
        # ---- supply ships build outposts and stations
        for b in builders:
            if b["job"] is None and construction:
                kind, kit, res = construction[0]
                mods = (E.CONSTRUCTION["outpost_kits"][kit] if kind == "outpost" else E.CONSTRUCTION["station_kits"][kit])
                c = cost_of(mods)
                if can_pay(c):
                    pay(c)
                    construction.pop(0)
                    if kind == "station":
                        station_started = True
                    build_s = max(M[m]["build_s"] for m in mods) * 1.2        # crews build modules in parallel
                    b.update(job=(kind, kit, res, mods), progress=-TRAVEL_MIN * 60.0, need=build_s)
                    note(t, f"supply ship starts {kit}" + (f" ({res})" if res else ""))
            if b["job"]:
                b["progress"] += 60
                if b["progress"] >= b["need"]:
                    kind, kit, res, mods = b["job"]
                    if kind == "outpost":
                        income.append((res, rig * 0.9 * DARTER_HAUL, t + 1))
                    else:
                        stations.append(Station(kit, mods))
                    note(t, f"{kit} ONLINE" + (f" ({res})" if res else ""))
                    b["job"] = None
        # ---- small shipyard (home)
        if small_yard["job"] is None and small_plan:
            c = {k: E.SHIP_COSTS[small_plan[0]][k] for k in ("alloys", "circuitry", "cores")}
            if can_pay(c):                              # mining ships are cheap and grow income: never wait
                pay(c)
                small_yard.update(job=small_plan.pop(0), progress=0.0)
        if small_yard["job"]:
            small_yard["progress"] += 60
            power_min["shipyard_small"] = power_min.get("shipyard_small", 0) + 1
            if small_yard["progress"] >= E.SHIP_COSTS[small_yard["job"]]["build_s"]:
                job = small_yard["job"]
                note(t, f"built {job}")
                if job == "XS_MINER" and miner_targets:
                    income.append((miner_targets.pop(0), miner_full * REMOTE_HAUL, t + TRAVEL_MIN))
                if job == "SMALL_SUPPORT":
                    builders.append(dict(job=None, progress=0.0))
                small_yard["job"] = None
        # ---- every station: power its industry, refine, make cores, build Mediums
        medium_cost = {k: E.SHIP_COSTS["MEDIUM"][k] for k in ("alloys", "circuitry", "cores")}
        for st in stations:
            want = []
            if "shipyard_medium" in st.modules and station_started and (st.yard_job or can_pay(medium_cost, use_reserve=True)):
                want.append("shipyard_medium")
            want.append("refinery")
            if stock["cores"] < CORE_TARGET:
                want.append("core_foundry")
            if stock["lithium"] > 0:
                want.append("breeder_reactor")
            want.append("fabricator")
            active, left = [], st.budget
            for m in want:
                if m in st.modules and -M[m]["power"] <= left:
                    active.append(m)
                    left += M[m]["power"]
            for m in active:
                power_min[m] = power_min.get(m, 0) + 1
            if "refinery" in active:
                r = M["refinery"]["makes"]
                for raw, out, ratio in (("ore", "alloys", 2), ("crystals", "circuitry", 2), ("ice", "hydrogen", 1),
                                        ("gas", "hydrogen", 1)):
                    take = min(stock[raw], r["in"][raw])
                    stock[raw] -= take
                    stock[out] += take / ratio
            if "breeder_reactor" in active:
                take = min(stock["lithium"], M["breeder_reactor"]["makes"]["in"]["lithium"])
                stock["lithium"] -= take
                stock["tritium"] += take / 4
            if "core_foundry" in active:
                mk = M["core_foundry"]["makes"]
                if can_pay(mk["in"]):
                    pay(mk["in"])
                    stock["cores"] += mk["out"]["cores"]
            if "shipyard_medium" in active:
                if st.yard_job is None:
                    pay(medium_cost)
                    st.yard_job, st.yard_progress = "MEDIUM", 0.0
                st.yard_progress += 60
                if st.yard_progress >= E.SHIP_COSTS["MEDIUM"]["build_s"]:
                    mediums.append(t)
                    note(t, f"MEDIUM #{len(mediums)} launched ({st.name})")
                    st.yard_job = None
        history.append(dict(t=t, **{k: round(v) for k, v in stock.items()}))

    if verbose:
        print("Stations:", ", ".join(f"{s.name} ({s.budget} power for industry)" for s in stations), "\n")
        print("Timeline:")
        for t, msg in log:
            print(f"  {t:3d} min  {msg}")
        print("\nMinutes each industry module had power (summed over stations):", dict(sorted(power_min.items())))
        for t in (20, 40, 60, 90, minutes):
            h = history[t - 1]
            print(f"  at {t:3d} min: alloys {h['alloys']:6d}  circuitry {h['circuitry']:6d}  cores {h['cores']:4d}  "
                  f"ore {h['ore']:6d}  crystals {h['crystals']:6d}")
        report(mediums)
    return mediums, history, log


def report(mediums):
    def per(a, b):
        n = sum(1 for m in mediums if a < m <= b)
        return n, (b - a) / n if n else None
    print(f"\nMediums launched: {len(mediums)}  (first at minute {mediums[0] if mediums else '-'})")
    for a, b in ((20, 40), (35, 55), (40, 60), (60, 90), (90, 120)):
        n, gap = per(a, b)
        print(f"  minutes {a:3d}-{b:3d}: {n:2d} Mediums" + (f"  = one every {gap:.1f} min" if gap else ""))


if __name__ == "__main__":
    simulate()
