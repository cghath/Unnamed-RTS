extends Node
## Fog of war and radar. What the player can see comes from their own ships, stations,
## fighters and craft, and on a world from their troops, vehicles and outposts:
##   sensors  everything inside is shown normally
##   radar    (twice the sensor range for ships and stations) an unknown contact: a grey
##            blip on the minimap and an "UNKNOWN CONTACT" marker, nothing more
##   beyond   hidden
## Stations and ground installations, once seen, stay on the map (you know where they are).
## Off with G.settings["fog"] = false.

const SENSOR := {"SMALL": 2400.0, "MEDIUM": 3000.0, "LARGE": 3800.0, "XL": 4200.0}
const STATION_SENSOR := 4200.0
const RADAR_MULT := 2.0

var state := {}                    # node -> "vis" / "radar" / "" (hidden)
var known := {}                    # stations / installations seen at least once
var eyes: Array = []               # [pos, sensor, radar]
var _t := 0.0


func enabled() -> bool:
	return bool(G.settings.get("fog", true))


func state_of(n: Node) -> String:
	if not enabled() or n == null:
		return "vis"
	if n.get("team") == G.player_team:
		return "vis"
	return state.get(n, "vis")


func _process(dt: float) -> void:
	_t -= dt
	if _t > 0.0:
		return
	_t = 0.25
	var me: int = G.player_team
	var m: Node = G.match_node
	if m == null:
		return
	if not enabled():
		if not state.is_empty():
			_reveal_all()
		return
	var surf: bool = m.get("on_surface") == true
	eyes.clear()
	var boarded := {}
	for c in G.characters:
		if is_instance_valid(c) and c.team == me and c.state == "alive" and c.vessel != null:
			boarded[c.vessel] = true
			if c.vessel.get("kind") == "ground":
				eyes.append([c.global_position, 110.0, 0.0])
	for v in G.vessels:
		if not is_instance_valid(v) or v.destroyed or v.team != me:
			continue
		if v.kind == "station":
			eyes.append([v.global_position, STATION_SENSOR, STATION_SENSOR * RADAR_MULT])
		else:
			var sz: String = v.size_class(String(v.cls)) if v.has_method("size_class") else "SMALL"
			var r: float = float(SENSOR.get(sz, 2400.0))
			if surf:
				r = 700.0                                  # down on a world the horizon is close
			eyes.append([v.global_position, r, r * RADAR_MULT])
	for f in G.fighters:
		if is_instance_valid(f) and f.team == me:
			eyes.append([f.global_position, 1500.0, 0.0])
	for p in G.pods:
		if is_instance_valid(p) and p.get("team") == me:
			eyes.append([p.global_position, 800.0, 0.0])
	for veh in G.vehicles:
		if is_instance_valid(veh) and veh.team == me:
			eyes.append([veh.global_position, 260.0, 0.0])
	if m.get("outposts") != null:
		for o in m.outposts:
			if is_instance_valid(o) and not o.destroyed and o.team == me:
				eyes.append([o.global_position, 380.0, 0.0])
	# vessels
	for v in G.vessels:
		if not is_instance_valid(v) or v.team == me:
			continue
		var st: String = "vis" if boarded.has(v) else _look(v.global_position)
		if st == "vis" and v.kind == "station":
			known[v] = true
		state[v] = st
		var show: bool = st == "vis" or known.has(v)
		if v.visible != show:
			v.visible = show
	for list in [G.fighters, G.pods, G.missiles, G.vehicles]:
		for n in list:
			if not is_instance_valid(n) or n.get("team") == me:
				continue
			var st2 := _look(n.global_position)
			state[n] = st2
			var sh2: bool = st2 == "vis"
			if n.visible != sh2:
				n.visible = sh2
	if m.get("outposts") != null:
		for o in m.outposts:
			if not is_instance_valid(o) or o.team == me:
				continue
			var st3 := _look(o.global_position)
			if st3 == "vis":
				known[o] = true
			state[o] = st3
			var sh3: bool = st3 == "vis" or known.has(o)
			if o.visible != sh3:
				o.visible = sh3
	# salvage caches: hidden until seen, then marked
	if m.get("caches") != null:
		for cache in m.caches:
			if not is_instance_valid(cache):
				continue
			var st4 := _look(cache.global_position)
			if st4 == "vis":
				known[cache] = true
			var sh4: bool = known.has(cache)
			if cache.visible != sh4:
				cache.visible = sh4
	# people out on the open ground (aboard a vessel they go with it)
	for c in G.characters:
		if not is_instance_valid(c) or c.team == me or c.vessel == null:
			continue
		var hide := false
		if c.vessel.get("kind") == "ground":
			hide = _look(c.global_position) != "vis"
		c.fog_hidden = hide


func _look(p: Vector3) -> String:
	var best := ""
	for e in eyes:
		var d: float = (e[0] as Vector3).distance_to(p)
		if d <= float(e[1]):
			return "vis"
		if d <= float(e[2]):
			best = "radar"
	return best


func _reveal_all() -> void:
	for n in state:
		if is_instance_valid(n):
			n.visible = true
			if n.get("fog_hidden") != null:
				n.fog_hidden = false
	for c in G.characters:
		if is_instance_valid(c):
			c.fog_hidden = false
	state.clear()
