extends Node3D
## A ship-to-ship missile: launches off the rails, then homes on its target.
## Point defense can shoot it down (it sits in G.missiles, which turrets target).

var team := 1
var faction := 1
var target: Node3D
var vel := Vector3.ZERO
var speed := 90.0
var hp := 30.0
var dmg := 140.0
var life := 25.0
var _trail_t := 0.0
var mesh: MeshInstance3D


func launch(from: Vector3, dir: Vector3, tgt: Node3D, team_: int, faction_: int) -> void:
	team = team_
	faction = faction_
	target = tgt
	global_position = from
	vel = dir.normalized() * 60.0
	mesh = MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.6, 0.6, 3.2)
	mesh.mesh = bm
	mesh.material_override = G._mat(Color(0.75, 0.75, 0.8), 0.0)
	add_child(mesh)
	var glow := MeshInstance3D.new()
	var gm := BoxMesh.new()
	gm.size = Vector3(0.45, 0.45, 0.4)
	glow.mesh = gm
	glow.position.z = 1.8
	glow.material_override = G._mat(Color(1.0, 0.6, 0.25) if faction != 2 else Color(1.0, 0.3, 0.5), 6.0)
	add_child(glow)
	G.missiles.append(self)
	G.register(self)
	G.stat("missiles_fired")


func take_hit(d: float, _from: Vector3 = Vector3.ZERO, _by: Node = null) -> void:
	if G.is_client():
		return
	hp -= d
	if hp <= 0.0:
		_gone(true)


func _gone(boom: bool) -> void:
	if boom:
		G.explosion(global_position, 5.0)
	G.missiles.erase(self)
	queue_free()


func _process(dt: float) -> void:
	life -= dt
	if life <= 0.0 or target == null or not is_instance_valid(target) or target.get("destroyed"):
		_gone(true)
		return
	var aim: Vector3 = target.to_global(target.aabb.get_center()) if target.get("aabb") != null else target.global_position
	speed = min(speed + 160.0 * dt, 360.0)
	var want := (aim - global_position).normalized() * speed
	vel = vel.lerp(want, clampf(dt * 2.2, 0.0, 1.0))
	global_position += vel * dt
	if vel.length() > 1.0:
		look_at(global_position + vel, Vector3.UP)
	_trail_t -= dt
	if _trail_t <= 0.0:
		_trail_t = 0.04
		G.tracer(global_position, global_position - vel.normalized() * 7.0, Color(0.85, 0.85, 0.9), 0.35, 0.35)
	# hit: inside the target's box
	if target.get("aabb") != null and target.aabb.grow(1.0).has_point(target.to_local(global_position)):
		if not G.is_client():
			target.take_hit(dmg, global_position, null)
		_gone(true)
