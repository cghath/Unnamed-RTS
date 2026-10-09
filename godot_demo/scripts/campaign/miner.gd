extends Node3D
## A mining craft: flies from its station to an asteroid field, cuts ore for a while,
## and brings it home. Iron ore goes to the refinery (alloys), ice becomes fuel, crystal
## circuitry and core rock a few cores. It runs home if raiders come close.

const LOAD := 150.0
const CUT_S := 20.0

var home: Node3D
var entry := {}                    # campaign.miners record
var team := 1
var hp := 260.0
var stage := 0                     # 0 on the pad, 1 out to the field, 2 cutting, 3 home, 4 unload
var stage_t := 0.0
var field := {}
var spot := Vector3.ZERO
var rock := Vector3.ZERO
var cargo := 0.0
var vel := Vector3.ZERO
var model: Node3D
var _pad := Vector3.INF
var _beam_t := 0.0


func setup(home_: Node3D, e: Dictionary) -> void:
	home = home_
	entry = e
	team = home.team
	model = load("res://models/ships_F1/ship_XS_MINER.glb").instantiate()
	add_child(model)
	for sb in model.find_children("*", "StaticBody3D", true, false):
		(sb as StaticBody3D).collision_layer = 0
	global_position = _home_point()
	var pk := Area3D.new()
	pk.collision_layer = G.LAYER_PICK
	pk.monitoring = false
	var cs := CollisionShape3D.new()
	var sp := SphereShape3D.new()
	sp.radius = 6.0
	cs.shape = sp
	pk.add_child(cs)
	pk.set_meta("unit", self)
	add_child(pk)
	G.pods.append(self)                      # point defense can shoot at it like any small craft
	stage_t = randf() * 4.0


func _home_point() -> Vector3:
	if _pad == Vector3.INF:
		_pad = home.craft_pad() if home.has_method("craft_pad") else home.aabb.get_center()
	return home.to_global(_pad + Vector3(0, 3.0, 0))


func take_hit(d: float, _from: Vector3 = Vector3.ZERO, _by: Node = null) -> void:
	hp -= d
	if hp <= 0.0:
		G.explosion(global_position, 7.0)
		G.say("A mining craft was destroyed", team)
		G.stat("miners_lost")
		if G.campaign:
			G.campaign.miners.erase(entry)
		G.pods.erase(self)
		queue_free()


func _fly_to(p: Vector3, spd: float, dt: float, turn: float = 1.6) -> bool:
	var to := p - global_position
	if to.length() <= maxf(spd * dt, 2.0):
		global_position = p
		return true
	vel = vel.lerp(to.normalized() * spd, clampf(dt * turn, 0.0, 1.0))
	global_position += vel * dt
	var flat := Vector3(vel.x, 0, vel.z)
	if flat.length() > 1.0:
		look_at(global_position + flat, Vector3.UP)
	return false


func _danger() -> bool:
	for v in G.vessels:
		if is_instance_valid(v) and not v.destroyed and v.kind == "ship" and G.enemies(team, v.team) and not v.drifting \
				and v.global_position.distance_to(global_position) < 900.0:
			return true
	return false


func _pick_field() -> bool:
	var best := {}
	var bd := 1.0e9
	for f in G.match_node.system.get("fields", []):
		var d: float = home.global_position.distance_to(f["center"])
		if d < bd:
			bd = d
			best = f
	if best.is_empty():
		return false
	field = best
	var big: Array = best["big"]
	if not big.is_empty():
		var b: Dictionary = big[randi() % big.size()]
		rock = b["pos"]
		var out := Vector3(randf_range(-1, 1), 0.3, randf_range(-1, 1)).normalized()
		spot = rock + out * (float(b["radius"]) + 18.0)
	else:
		rock = best["center"]
		spot = rock + Vector3(randf_range(-1, 1), 0, randf_range(-1, 1)).normalized() * 40.0
	return true


func _process(dt: float) -> void:
	if home == null or not is_instance_valid(home) or home.destroyed or home.team != team:
		G.pods.erase(self)
		queue_free()
		return
	stage_t += dt
	match stage:
		0:
			global_position = global_position.lerp(_home_point(), clampf(dt * 2.0, 0.0, 1.0))
			if stage_t > 6.0 and not _danger() and _pick_field():
				stage = 1
				stage_t = 0.0
		1:
			if _danger() and stage_t > 3.0:
				stage = 3
				stage_t = 0.0
			elif _fly_to(spot, 90.0, dt) or stage_t > 120.0:
				stage = 2
				stage_t = 0.0
		2:
			# hold station by the rock and cut
			global_position = global_position.lerp(spot, clampf(dt, 0.0, 1.0))
			look_at(rock, Vector3.UP)
			_beam_t -= dt
			if _beam_t <= 0.0:
				_beam_t = 0.12
				G.tracer(global_position, rock + (global_position - rock).normalized() * 6.0, Color(1.0, 0.6, 0.25), 0.25, 0.14)
			var load_cap: float = LOAD * (1.0 + G.tech_bonus(team, "miner_load"))
			cargo = minf(load_cap, cargo + load_cap / CUT_S * dt)
			if cargo >= load_cap or _danger():
				stage = 3
				stage_t = 0.0
		3:
			if _fly_to(_home_point() + Vector3.UP * 6.0, 100.0, dt) or stage_t > 120.0:
				stage = 4
				stage_t = 0.0
		4:
			global_position = global_position.lerp(_home_point(), clampf(dt * 2.0, 0.0, 1.0))
			if stage_t > 2.5:
				_unload()
				stage = 0
				stage_t = 0.0


func _unload() -> void:
	if cargo <= 0.0:
		return
	var res: String = {"iron": "ore", "ice": "fuel", "crystal": "crystal", "core": "cores"}.get(field.get("ore", "iron"), "ore")
	var amt: float = cargo * {"ore": 1.0, "fuel": 0.8, "crystal": 0.8, "cores": 0.05}[res]
	var r: Dictionary = G.resources.get(team, {})
	r[res] = float(r.get(res, 0.0)) + amt
	G.stat("ore_delivered", int(cargo))
	cargo = 0.0
