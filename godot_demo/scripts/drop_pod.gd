extends Node3D
## An ODST-style drop pod: one trooper, fired from a drop frigate's belly at a SURFACE
## installation (ground mine, ground fort). Never at stations: there's no ground to land on.
## It falls clear of the ship, burns toward a spot above the target, then plunges into
## the ground beside the base. The trooper cuts in through the nearest airlock.

var team := 1
var faction := 1
var target: Node3D                 # the ground installation
var entry: Array = []              # [approach, airlock outside marker, inside marker, door pattern]
var role := "drop_trooper"
var hp := 60.0
var stage := 0
var vel := Vector3.ZERO
var land := Vector3.ZERO           # where it hits the ground (world, refreshed from the target)
var land_local := Vector3.ZERO
var _t := 0.0
var _trail := 0.0
var model: Node3D
var net_pos := Vector3.INF
var net_rot := Vector3.ZERO


func setup(from: Transform3D, team_: int, faction_: int, tgt: Node3D, entry_: Array, role_: String, spot: int,
		aim: Vector3 = Vector3.INF) -> void:
	team = team_
	faction = faction_
	target = tgt
	entry = entry_
	role = role_
	var folder := "ships_F%d" % faction if faction in [1, 2] else "ships_F1"
	var path := "res://models/%s/ship_XS_DROPPOD.glb" % folder
	model = load(path).instantiate()
	for sb in model.find_children("*", "StaticBody3D", true, false):
		(sb as StaticBody3D).collision_layer = 0
	add_child(model)
	global_transform = from
	# the designated spot (or the airlock) on the ground below, spread so pods don't stack
	var ground_y: float = (entry[1] as Node3D).global_position.y - 1.2
	var base: Vector3 = aim if aim != Vector3.INF else (entry[1] as Node3D).global_position
	var a := spot * 2.39996
	var r := 3.0 + sqrt(float(spot)) * 3.2
	var land_w := Vector3(base.x + cos(a) * r, ground_y, base.z + sin(a) * r)
	land_local = tgt.to_local(land_w)
	vel = Vector3.DOWN * 20.0
	var pk := Area3D.new()
	pk.collision_layer = G.LAYER_PICK
	pk.monitoring = false
	var cs := CollisionShape3D.new()
	var sp := SphereShape3D.new()
	sp.radius = 2.5
	cs.shape = sp
	pk.add_child(cs)
	pk.set_meta("unit", self)
	add_child(pk)
	G.pods.append(self)
	G.register(self)


## (network kind marker: drop pods share the pod puppet)
func take_hit(d: float, _from: Vector3 = Vector3.ZERO, _by: Node = null) -> void:
	if G.is_client() or stage >= 3:
		return
	hp -= d
	if hp <= 0.0:
		G.explosion(global_position, 3.0)
		G.pods.erase(self)
		queue_free()


func _process(dt: float) -> void:
	if G.is_client():
		if net_pos != Vector3.INF:
			global_position = global_position.lerp(net_pos, clampf(dt * 10.0, 0.0, 1.0))
			global_rotation = net_rot
		return
	if target == null or not is_instance_valid(target) or target.destroyed:
		G.pods.erase(self)
		queue_free()
		return
	if stage >= 3:
		return
	_t += dt
	land = target.to_global(land_local)
	# straight down out of the belly, accelerating; a hard retro burn just above the ground
	var to := land - global_position
	var h: float = global_position.y - land.y
	var spd: float = 30.0 + _t * 60.0
	if h < 60.0:
		spd = maxf(25.0, h * 1.6)                     # retro burn
	spd = minf(spd, 240.0)
	var want := Vector3(to.x * 0.8, -absf(to.y) - 1.0, to.z * 0.8).normalized()   # never upward
	vel = vel.lerp(want * spd, clampf(dt * 3.0, 0.0, 1.0))
	if vel.y > -5.0:
		vel.y = -5.0
	global_position += vel * dt
	global_basis = Basis()                             # the model stands nose-cone down: keep it upright
	_trail -= dt
	if _trail <= 0.0:
		_trail = 0.04
		G.tracer(global_position + Vector3.UP * 2.0, global_position + Vector3.UP * 9.0,
			Color(1.0, 0.55, 0.2) if h < 60.0 else Color(1.0, 0.8, 0.5), 0.5, 0.2)
	if h <= 0.6 or to.length() < 1.0:
		global_position = land
		_landed()


## The pod's nose (model -Z) along its flight: ODST pods come in feet-first... nose-first here.
func _face(dir: Vector3) -> void:
	if dir.length() < 0.01:
		return
	var up := Vector3.UP if absf(dir.normalized().dot(Vector3.UP)) < 0.98 else Vector3.RIGHT
	global_basis = Basis.looking_at(dir.normalized(), up)


func _landed() -> void:
	stage = 3
	G.pods.erase(self)
	G.explosion(global_position, 4.0, Color(1.0, 0.6, 0.25))
	reparent(target, true)                  # stays planted in the ground by the base
	global_basis = target.global_basis      # upright on the surface, hatch open
	var door: String = entry[3]
	if door != "":
		target.breach(door)                 # the airlock's outer door: cut and blown
	var inside: Vector3 = target.to_local((entry[2] as Node3D).global_position)
	target.raise_alarm(inside)
	if G.match_node:
		var spots: Array = G.match_node.spread_spots(target, inside, 1 + randi() % 4)
		var c: Node = G.match_node.spawn_character(target, spots[spots.size() - 1], team, faction, role)
		c.run = true
		G.match_node.join_drop_squad(c, target)
	G.stat("odst_landed")
