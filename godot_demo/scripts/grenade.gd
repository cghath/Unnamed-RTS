extends Node3D
## A thrown grenade: flies in an arc, bounces off walls, goes off after its fuse.

var vel := Vector3.ZERO
var fuse := 2.6
var thrower: Node = null
var mesh: Node3D
var emp := false                  # an EMP: staggers and blinds everyone near for 2 s, no damage


func launch(from: Vector3, to: Vector3, who: Node, fac: int) -> void:
	thrower = who
	global_position = from
	var item := "item_F1_FragGrenade" if fac == 1 else "item_F2_PlasmaGrenade"
	mesh = load("res://models/items/%s.glb" % item).instantiate()
	add_child(mesh)
	mesh.scale = Vector3.ONE * 1.6
	if emp:
		for m in mesh.find_children("*", "MeshInstance3D", true, false):
			(m as MeshInstance3D).material_override = G._mat(Color(0.3, 0.7, 1.0), 2.0)
		fuse = 1.8
	var d := to - from
	var t: float = clamp(d.length() / 14.0, 0.4, 1.6)
	vel = d / t + Vector3.UP * 0.5 * 9.8 * t
	if fac == 2:
		fuse = 2.0


func _physics_process(dt: float) -> void:
	vel.y -= 9.8 * dt
	var nxt := global_position + vel * dt
	var hit := G.ray(global_position, nxt, [], G.LAYER_WORLD | G.LAYER_DOOR)
	if not hit.is_empty():
		vel = vel.bounce(hit.normal) * 0.35
		nxt = hit.position + hit.normal * 0.05
	global_position = nxt
	mesh.rotation += Vector3(7, 5, 3) * dt
	fuse -= dt
	if fuse <= 0.0:
		if emp:
			_pulse()
		else:
			G.blast(global_position, 5.0, 95.0, thrower)
		queue_free()


func _pulse() -> void:
	G.flash(global_position, Color(0.4, 0.75, 1.0), 6.0, 8.0, 0.25)
	for c in G.characters:
		if not is_instance_valid(c) or c.state != "alive":
			continue
		var p: Vector3 = c.global_position + Vector3.UP
		if p.distance_to(global_position) > 7.0:
			continue
		if not G.ray(global_position + Vector3.UP * 0.2, p, [], G.LAYER_WORLD | G.LAYER_DOOR).is_empty():
			continue                                   # behind a wall
		c.stun(2.0)
