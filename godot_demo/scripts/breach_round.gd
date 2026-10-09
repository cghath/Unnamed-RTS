extends Node3D
## A breaching round for the grenadier's launcher (like Ash's in Siege): a finned dark-grey
## cylinder with a red band and a hole-saw crown on the nose. Four curved fins lie folded along
## the body and flip out when it's fired.
## The model is built here so the pack holders (character.gd) and the projectile share it.
## Its axis is +z, nose forward; it is about 0.14 m long.

const BODY_R := 0.02


## The round's model. Its meta "fins" holds the four fin hinges (see set_fins) and "crown"
## the hole-saw node, which spins about +z.
static func build_model() -> Node3D:
	var root := Node3D.new()
	root.name = "BreachRound"
	var grey := _mat(Color(0.2, 0.21, 0.23), 0.5, 0.55)
	var steel := _mat(Color(0.62, 0.64, 0.67), 0.85, 0.3)
	var red := _mat(Color(0.75, 0.08, 0.06), 0.0, 0.6)
	var dark := _mat(Color(0.05, 0.05, 0.06), 0.0, 0.9)
	# body and its red band
	_cyl(root, BODY_R, 0.1, Vector3(0, 0, -0.02), grey)
	_cyl(root, BODY_R + 0.0008, 0.012, Vector3(0, 0, 0.0), red)
	_cyl(root, BODY_R * 0.75, 0.012, Vector3(0, 0, -0.074), dark)          # tail nozzle
	# the hole-saw crown: a collar, a ring rim with a dark cup inside, and ten teeth
	var crown := Node3D.new()
	crown.name = "Crown"
	crown.position.z = 0.03
	root.add_child(crown)
	_cyl(crown, BODY_R + 0.002, 0.018, Vector3(0, 0, 0.009), steel)
	var rim := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 0.016
	tm.outer_radius = 0.0235
	tm.rings = 20
	tm.ring_segments = 6
	rim.mesh = tm
	rim.material_override = steel
	rim.rotation.x = PI * 0.5
	rim.position.z = 0.019
	crown.add_child(rim)
	_cyl(crown, 0.016, 0.002, Vector3(0, 0, 0.0185), dark)                 # inside the cup
	var tooth := BoxMesh.new()
	tooth.size = Vector3(0.006, 0.004, 0.011)
	for i in 10:
		var a := TAU * i / 10.0
		var t := MeshInstance3D.new()
		t.mesh = tooth
		t.material_override = steel
		t.position = Vector3(cos(a), sin(a), 0) * 0.0198 + Vector3(0, 0, 0.026)
		t.rotation = Vector3(0, 0, a + PI * 0.5)
		t.rotate_object_local(Vector3.RIGHT, 0.35)                      # raked, like saw teeth
		crown.add_child(t)
	root.set_meta("crown", crown)
	# fins: each hinges at the tail and lies forward along the body until it flips out
	var fin := BoxMesh.new()
	fin.size = Vector3(0.003, 0.022, 0.058)
	var fins: Array = []
	for i in 4:
		var spoke := Node3D.new()
		spoke.position.z = -0.066
		spoke.rotation.z = TAU * i / 4.0 + PI * 0.25
		root.add_child(spoke)
		var hinge := Node3D.new()
		hinge.position.x = BODY_R
		spoke.add_child(hinge)
		var f := MeshInstance3D.new()
		f.mesh = fin
		f.material_override = grey
		f.position = Vector3(0.0018, 0, 0.029)
		f.rotation.y = -0.05                                             # curved toward the body
		hinge.add_child(f)
		fins.append(hinge)
	root.set_meta("fins", fins)
	return root


## Fins from folded (0) to fully out (1): they swing back past square, like a dart's.
static func set_fins(model: Node3D, t: float) -> void:
	for h in model.get_meta("fins", []):
		(h as Node3D).rotation.y = lerpf(0.0, deg_to_rad(125.0), clampf(t, 0.0, 1.0))


static func _cyl(parent: Node3D, r: float, h: float, at: Vector3, m: Material) -> void:
	var cm := CylinderMesh.new()
	cm.top_radius = r
	cm.bottom_radius = r
	cm.height = h
	cm.radial_segments = 14
	cm.rings = 1
	var mi := MeshInstance3D.new()
	mi.mesh = cm
	mi.material_override = m
	mi.rotation.x = PI * 0.5                                             # the mesh's axis is y; ours is z
	mi.position = at
	parent.add_child(mi)


static func _mat(c: Color, metal: float, rough: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.metallic = metal
	m.roughness = rough
	return m
