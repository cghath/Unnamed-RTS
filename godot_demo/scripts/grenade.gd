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


## A 40 mm launcher shell (brass case, olive warhead with a yellow band), axis +z, nose forward,
## about 0.08 m long. Shown on the grenadier's bandolier and flown as the launched round.
static func shell_model() -> Node3D:
	var root := Node3D.new()
	root.name = "Shell40"
	var parts := [[0.02, 0.042, -0.021, Color(0.66, 0.52, 0.24), 0.75],     # case
		[0.0205, 0.004, -0.04, Color(0.5, 0.39, 0.17), 0.75],             # rim
		[0.0195, 0.016, 0.008, Color(0.3, 0.33, 0.2), 0.1],                # warhead body
		[0.0198, 0.004, 0.006, Color(0.85, 0.7, 0.1), 0.1]]                # band
	for p in parts:
		var cm := CylinderMesh.new()
		cm.top_radius = p[0]
		cm.bottom_radius = p[0]
		cm.height = p[1]
		cm.radial_segments = 12
		cm.rings = 1
		var mi := MeshInstance3D.new()
		mi.mesh = cm
		mi.material_override = _shell_mat(p[3], p[4])
		mi.rotation.x = PI * 0.5
		mi.position.z = p[2]
		root.add_child(mi)
	var nose := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.0195
	sm.height = 0.03
	sm.radial_segments = 12
	sm.rings = 6
	nose.mesh = sm
	nose.material_override = _shell_mat(Color(0.3, 0.33, 0.2), 0.1)
	nose.position.z = 0.016
	root.add_child(nose)
	return root


static func _shell_mat(c: Color, metal: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.metallic = metal
	m.roughness = 0.45
	return m


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
