extends Node
## Logistics: keeping ships manned, armed and supplied.
##
## Stations make what a fleet runs on:
##   * reserve  robots waiting in the station barracks (built from alloys + cores over time)
##   * supplies ammunition, medical stores and spare parts (made from alloys)
## Ships use it up: every boarding pod or shuttle takes boarders out of the troop berths,
## the armories spend supplies on every gear-up and reload, engineers spend supplies on
## repairs, and dead crew leave posts empty.
##
## SUPPLY SHIPS (SMALL_SUPPORT) carry the station's stock out to the fleet: a big store
## of supplies plus boarders in their berths. A supply ship shadows its side's flagship,
## tops up any friendly ship within 600 m of it directly, launches the Darter supply runs
## for ships further out, and goes home to restock when it runs low.
##
## It gets back to the ships two ways:
##   * DOCKED: a ship within 800 m of its home station is topped up directly: boarders
##     into the berths, supplies into the stores, replacement crew walk aboard
##   * SUPPLY RUNS: a ship out in the field that runs low gets a supply shuttle (a Darter)
##     from home: six seats (boarders or replacement crew) and 80 supplies. It lands in the
##     ship's cargo bay (or hangar), unloads and flies home. Shoot one down and its cargo is lost.

const SUPPLY := preload("res://scripts/supply_shuttle.gd")
const DOCK_RANGE := 800.0
const RUN_SEATS := 6
const RUN_SUPPLIES := 80.0
const MAX_RUNS := 2               # shuttles a station (or supply ship) can have out at once
const ALONGSIDE := 600.0          # a supply ship tops up ships this close directly
const RUN_FROM_SHIP := 2600.0     # ...and flies Darter runs to ships out to here

var runs := {}                    # ship -> supply shuttle on its way
var _t := 0.0


func _physics_process(dt: float) -> void:
	if G.is_client() or G.game_over:
		return
	_dock_ships(dt)
	_t -= dt
	if _t > 0.0:
		return
	_t = 2.0
	for st in G.vessels:
		if st.kind != "station" or st.destroyed or not st.has_method("produce"):
			continue
		st.produce(2.0)
		for sup in _supply_ships(st.team):
			_supply_ship_tick(sup, st)
		for v in G.vessels:
			if v.kind != "ship" or v.destroyed or v.team != st.team or v.drifting or v.is_supply_ship:
				continue
			if v.global_position.distance_to(st.global_position) < DOCK_RANGE:
				_dock_transfer(st, v)
				continue
			var sup2: Node = _nearest_supply_ship(v)
			if sup2 and sup2.global_position.distance_to(v.global_position) < ALONGSIDE:
				_dock_transfer(sup2, v)                     # alongside the supply ship
			elif sup2 and sup2.global_position.distance_to(v.global_position) < RUN_FROM_SHIP and _stock_troops(sup2) + sup2.supplies > 30.0:
				_maybe_send_run(sup2, v)
			else:
				_maybe_send_run(st, v)
	for v in runs.keys():
		if not is_instance_valid(runs[v]):
			runs.erase(v)


# ------------------------------------------------------------------ docking at a station berth

## Send a ship home to hold station in one of the station's parking zones: a ring of spots
## in open space around it (no more flying into the station's model). Stores, crew and
## troops cross over by Darter while it waits there.
func send_to_dock(v: Node, st: Node) -> bool:
	if not is_instance_valid(st) or st.kind != "station":
		return false
	var spot := parking_spot(st, v)
	v.follow = null
	v.attack_target = null
	v.set_meta("dock_at", st)
	v.move_target = spot
	return true


## Where ship v waits by station st: evenly spaced round the station, clear of its hull.
func parking_spot(st: Node, v: Node) -> Vector3:
	var slots: Dictionary = st.get_meta("parking", {})
	for k in slots.keys():
		if not is_instance_valid(k) or k.destroyed or not k.has_meta("dock_at") or k.get_meta("dock_at") != st:
			slots.erase(k)
	if not slots.has(v):
		var used: Array = slots.values()
		var i := 0
		while i in used:
			i += 1
		slots[v] = i
	st.set_meta("parking", slots)
	var idx: int = slots[v]
	var r: float = st.aabb.size.length() * 0.5 + 160.0 + 90.0 * float(idx / 8)
	var a: float = float(idx % 8) * TAU / 8.0 + 0.3
	return st.global_position + Vector3(cos(a), 0, sin(a)) * r


## Ships heading for a parking zone: once there they hold, and top up.
func _dock_ships(_dt: float) -> void:
	for v in G.vessels:
		if v.kind != "ship" or v.destroyed or not v.has_meta("dock_at"):
			continue
		var st: Node = v.get_meta("dock_at")
		if not is_instance_valid(st) or st.destroyed or G.enemies(st.team, v.team) or v.helm != null:
			_undock(v)
			continue
		var spot := parking_spot(st, v)
		var d: float = Vector2(v.global_position.x - spot.x, v.global_position.z - spot.z).length()
		if d < 70.0:
			v.move_target = Vector3.INF
			if not v.get_meta("docked", false):
				v.set_meta("docked", true)
				G.stat("ships_docked")
				if v.team == G.player_team:
					G.say("%s is holding at %s" % [v.display_name, st.display_name], v.team)
			if v.team == st.team and v.troops >= v.berth_cap and v.supplies >= v.supply_cap * 0.95 \
					and v.crew_missing().is_empty() and not v.is_supply_ship:
				_undock(v)
		elif v.move_target == Vector3.INF or v.move_target.distance_to(spot) > 30.0:
			v.move_target = spot


func _undock(v: Node) -> void:
	var st = v.get_meta("dock_at") if v.has_meta("dock_at") else null
	if st and is_instance_valid(st) and st.has_meta("parking"):
		st.get_meta("parking").erase(v)
	v.remove_meta("dock_at")
	v.remove_meta("docked")


func _supply_ships(team: int) -> Array:
	return G.vessels.filter(func(v): return v.kind == "ship" and v.get("is_supply_ship") and v.team == team and not v.destroyed)


func _nearest_supply_ship(v: Node) -> Node:
	var best: Node = null
	var bd := INF
	for s in _supply_ships(v.team):
		var d: float = s.global_position.distance_to(v.global_position)
		if d < bd:
			bd = d
			best = s
	return best


## Robots a source can hand over: a station's reserve, or the boarders in a supply ship's berths.
func _stock_troops(src: Node) -> int:
	return src.reserve if src.kind == "station" else src.troops


func _take_troops(src: Node, n: int) -> void:
	if src.kind == "station":
		src.reserve -= n
	else:
		src.troops -= n


## A supply ship's routine: restock at home when low, otherwise keep station on the
## flagship (a few hundred metres astern) where the fleet can find it.
func _supply_ship_tick(sup: Node, st: Node) -> void:
	if sup.helm != null:
		return                                            # a player is flying it: their call
	var at_home: bool = sup.global_position.distance_to(st.global_position) < DOCK_RANGE
	var low: bool = sup.supplies < sup.supply_cap * 0.35 or sup.troops < sup.berth_cap * 0.3
	var state: String = sup.get_meta("supply_state", "fleet")
	var cd: float = sup.get_meta("restock_cd", 0.0)
	if state == "fleet" and low and G.time > cd and (st.supplies > sup.supply_cap * 0.3 or st.reserve >= 6):
		state = "restock"
		if sup.team == G.player_team:
			G.say("%s heading home to restock" % sup.display_name, sup.team)
	if state == "restock":
		if at_home:
			sup.follow = null
			sup.move_target = Vector3.INF
			var t: int = mini(4, mini(sup.berth_cap - sup.troops, st.reserve))
			if t > 0:
				sup.troops += t
				st.reserve -= t
			var s: float = minf(120.0, minf(sup.supply_cap - sup.supplies, st.supplies))
			if s > 0.5:
				sup.supplies += s
				st.supplies -= s
			var full: bool = sup.supplies >= sup.supply_cap * 0.95 or st.supplies < 10.0
			var manned: bool = sup.troops >= sup.berth_cap * 0.9 or st.reserve <= 0
			if full and manned:
				state = "fleet"
				_undock(sup)
				sup.set_meta("restock_cd", G.time + 90.0)     # don't turn straight round again
				G.stat("supply_ship_restocked")
		elif not sup.has_meta("dock_at"):
			send_to_dock(sup, st)
	if state == "fleet":
		var flag: Node = null
		var best := -1
		for v in G.vessels:
			if v.kind == "ship" and v.team == sup.team and not v.destroyed and not v.is_supply_ship:
				var rank: int = {"XL": 4, "LARGE": 3, "MEDIUM": 2}.get(v.cls, 1)
				if rank > best:
					best = rank
					flag = v
		if flag and sup.follow != flag:
			sup.move_target = Vector3.INF
			sup.follow = flag
			sup.follow_off = Vector3(0, 0, flag.aabb.size.z * 0.5 + 260.0)     # astern of the flagship
	sup.set_meta("supply_state", state)


## Docked (or alongside a supply ship): a steady transfer every couple of seconds.
func _dock_transfer(st: Node, v: Node) -> void:
	var moved := false
	var t: int = mini(2, mini(v.berth_cap - v.troops, _stock_troops(st)))
	if t > 0:
		v.troops += t
		_take_troops(st, t)
		moved = true
	var s: float = minf(40.0, minf(v.supply_cap - v.supplies, st.supplies))
	if s > 0.5:
		v.supplies += s
		st.supplies -= s
		moved = true
	var missing: Array = v.crew_missing()
	if not missing.is_empty() and _stock_troops(st) > 0:
		replace_crew(v, [missing[0]], v.arrival_point())
		_take_troops(st, 1)
		moved = true
	# empty drop-pod racks are reloaded
	if (not v.drop_racks.is_empty() or not v.pod_racks.is_empty()) and st.supplies > 40.0:
		var spent: float = v.reload_drop_pods(minf(60.0, st.supplies))
		if spent > 0.0:
			st.supplies -= spent
			moved = true
	# a lost boarding shuttle is replaced at the station, or by a supply ship's spares
	if not v.has_shuttle and not v.shuttle_spot().is_empty() and st.supplies > 150.0 and v.shuttle_out == null:
		st.supplies -= 150.0
		v.park_shuttle()
		moved = true
		G.say("%s has a new boarding shuttle" % v.display_name, v.team)
	if moved:
		G.stat("dock_transfers")
		if st.kind == "ship":
			G.stat("supply_ship_transfers")


func _maybe_send_run(st: Node, v: Node) -> void:
	if runs.has(v) and is_instance_valid(runs[v]):
		return
	var out := 0
	for k in runs:
		if is_instance_valid(runs[k]) and runs[k].home == st:
			out += 1
	if out >= MAX_RUNS + int(st.get_meta("darters", 0)) + int(G.tech_bonus(st.team, "darter_runs")):
		return                                       # every Darter is out (build more at the station)
	var stock: int = _stock_troops(st)
	var missing: Array = v.crew_missing()
	var low_troops: bool = v.troops < v.berth_cap * 0.5 and stock > 0
	var low_supplies: bool = v.supplies < v.supply_cap * 0.4 and st.supplies > 20.0
	if not (low_troops or low_supplies or missing.size() >= 2):
		return
	if v.alarm > 0.0 and v.infected_fraction() > 0.3:
		return                                           # nobody flies into that
	# load: replacement crew first, then boarders, then supplies
	var crew: Array = []
	for r in missing:
		if crew.size() >= RUN_SEATS or stock - crew.size() <= 0:
			break
		crew.append(r)
	var troops: int = mini(RUN_SEATS - crew.size(), mini(v.berth_cap - v.troops, stock - crew.size()))
	troops = maxi(0, troops)
	var sup: float = minf(RUN_SUPPLIES, minf(v.supply_cap - v.supplies, st.supplies))
	if crew.is_empty() and troops == 0 and sup < 10.0:
		return
	_take_troops(st, crew.size() + troops)
	st.supplies -= sup
	var sh: Node3D = SUPPLY.new()
	get_tree().root.add_child(sh)
	sh.setup(st, v, crew, troops, sup)
	runs[v] = sh
	G.stat("supply_runs")
	if v.team == G.player_team:
		G.say("%s: supply run to %s (%d crew, %d boarders, %d supplies)" % [st.display_name, v.display_name,
			crew.size(), troops, int(sup)], v.team)


## New crew step aboard at p (vessel space) and go to their posts.
func replace_crew(v: Node, roles: Array, p: Vector3) -> void:
	var spots: Array = G.match_node.spread_spots(v, p, roles.size())
	for i in roles.size():
		var c: Node = G.match_node.spawn_character(v, spots[i], v.team, v.faction if v.faction in [1, 2, 3] else 1, roles[i])
		if c.role in c.COMBAT_ROLES:
			var sq: RefCounted = null
			for s in G.match_node.squads:
				if s.vessel == v and s.team == v.team and s.members.size() < 8 and s.leader and s.leader.owner_peer == 0 and s.leader != G.possessed:
					sq = s
					break
			if sq == null:
				sq = G.match_node.new_squad(v.team, v)
			sq.add(c)
	G.stat("crew_replaced", roles.size())


## Selected people climb into a Darter and fly to another of our vessels: soldiers go into
## its troop berths (ready for pods and shuttles), crew take up posts aboard.
func ferry(chars: Array, to: Node) -> int:
	var groups := {}
	for c in chars:
		if not is_instance_valid(c) or c.state != "alive" or c.vessel == null or c.vessel == to or c.vessel.team != c.team:
			continue
		if not groups.has(c.vessel):
			groups[c.vessel] = []
		groups[c.vessel].append(c)
	var n := 0
	for home in groups:
		var crew: Array = []
		var troops := 0
		for c in groups[home]:
			if c.is_crew():
				crew.append(c.role)
			else:
				troops += 1
			_remove_person(c)
			n += 1
		var sh: Node3D = SUPPLY.new()
		get_tree().root.add_child(sh)
		sh.setup(home, to, crew, troops, 0.0)
		G.stat("ferries")
	return n


func _remove_person(c: Node) -> void:
	if c == G.possessed and G.commander:
		G.commander.release()
	if c.squad:
		c.squad.members.erase(c)
		if c.squad.leader == c:
			c.squad.leader = null
	if c.vessel:
		c.vessel.occupants.erase(c)
	G.characters.erase(c)
	c.queue_free()
